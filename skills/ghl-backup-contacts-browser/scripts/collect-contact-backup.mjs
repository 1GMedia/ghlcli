import fs from "node:fs/promises";
import path from "node:path";

const PAGE_SIZE = 100;
const PAGE_STATUS_RE = /Page\s+(\d+)\s+of\s+(\d+)/i;

function normalizeHost(host) {
  return String(host || "app.funnel-design.com")
    .replace(/^https?:\/\//i, "")
    .replace(/\/+$/, "");
}

function parsePageStatus(text) {
  const match = String(text || "").match(PAGE_STATUS_RE);
  if (!match) throw new Error(`Could not read pagination status from: ${text}`);
  return { page: Number(match[1]), pageCount: Number(match[2]) };
}

function expectedRowsForPage(page, pageCount, total) {
  if (page < pageCount) return PAGE_SIZE;
  return Math.max(0, total - PAGE_SIZE * (pageCount - 1));
}

async function readUiState(tab) {
  return tab.playwright.evaluate(() => {
    const bodyText = document.body?.innerText || "";
    const totalMatch = bodyText.match(/(?:^|\s)([\d,]+)\s+Contacts(?:\s|$)/i);
    const pageMatch = bodyText.match(/Page\s+(\d+)\s+of\s+(\d+)/i);
    const pageSize = document.querySelector('[aria-label="Page Size"]')?.value || null;
    const onContactsRoute = /\/contacts\/smart_list\//.test(location.pathname);
    const hasContactsLabel = /(?:^|\n)Contacts(?:\n|$)/.test(bodyText);
    const heading = onContactsRoute && hasContactsLabel ? "Contacts" : null;
    return {
      heading,
      total: totalMatch ? Number(totalMatch[1].replace(/,/g, "")) : null,
      pageText: pageMatch ? pageMatch[0] : null,
      pageSize,
      url: location.href,
    };
  });
}

async function mountedRows(tab) {
  return tab.playwright.locator(".tabulator-row").evaluateAll((rows) => {
    const uniqueLines = (cell) => {
      if (!cell) return "";
      const values = (cell.innerText || "")
        .split(/\n+/)
        .map((value) => value.trim())
        .filter(Boolean);
      return [...new Set(values)].join(" ");
    };
    const firstVisibleEllipsisText = (cell) => {
      if (!cell) return "";
      const candidates = Array.from(cell.querySelectorAll("div"));
      const visible = candidates.find((el) => {
        const style = getComputedStyle(el);
        return style.opacity !== "0" && style.visibility !== "hidden" &&
          (el.style.textOverflow === "ellipsis" || style.textOverflow === "ellipsis") &&
          (el.textContent || "").trim();
      });
      return visible ? (visible.textContent || "").trim() : uniqueLines(cell);
    };
    const tagText = (cell) => {
      const container = cell?.firstElementChild;
      if (!container) return "";
      const tags = [];
      for (const item of Array.from(container.children)) {
        const text = (item.textContent || "").trim();
        const tooltip = (item.getAttribute("tooltip") || "").trim();
        if (/^\+\d+$/.test(text) && tooltip && tooltip !== "null") tags.push(tooltip);
        else if (text && !/^\+\d+$/.test(text)) tags.push(text);
      }
      return [...new Set(tags)].join("; ");
    };

    return rows.map((row) => {
      const cell = (field) => row.querySelector(`[tabulator-field="${field}"]`);
      const nameCell = cell("name");
      const link = nameCell?.querySelector("a.contact-name-link, a[href*='/contacts/detail/']");
      const href = link?.getAttribute("href") || "";
      const id = nameCell?.querySelector("[data-id]")?.getAttribute("data-id") ||
        href.split("/").filter(Boolean).pop() || "";
      return {
        id,
        name: (link?.textContent || "").trim(),
        phone: firstVisibleEllipsisText(cell("phone")),
        email: firstVisibleEllipsisText(cell("email")),
        businessName: uniqueLines(cell("companyName")),
        created: uniqueLines(cell("dateAdded")),
        lastActivity: uniqueLines(cell("lastActivity")),
        tags: tagText(cell("tags")),
        contactUrl: href ? new URL(href, location.origin).href : "",
      };
    }).filter((row) => row.id);
  });
}

async function holderMetrics(tab) {
  return tab.playwright.locator(".tabulator-tableholder").evaluate((holder) => {
    const rect = holder.getBoundingClientRect();
    return {
      scrollTop: holder.scrollTop,
      maxScrollTop: Math.max(0, holder.scrollHeight - holder.clientHeight),
      x: Math.max(2, Math.min(innerWidth - 2, rect.left + Math.min(rect.width / 2, 700))),
      y: Math.max(2, Math.min(innerHeight - 2, rect.top + Math.min(rect.height / 2, 300))),
    };
  });
}

async function resetTableScroll(tab) {
  const metrics = await holderMetrics(tab);
  if (metrics.scrollTop > 0) {
    await tab.cua.scroll({ x: metrics.x, y: metrics.y, scrollX: 0, scrollY: -10000 });
    await tab.playwright.waitForTimeout(120);
  }
}

async function collectPageAtStep(tab, step) {
  await resetTableScroll(tab);
  const byId = new Map();
  let previousTop = -1;
  for (let guard = 0; guard < 20; guard += 1) {
    const metrics = await holderMetrics(tab);
    for (const row of await mountedRows(tab)) {
      if (!byId.has(row.id)) byId.set(row.id, row);
    }
    if (metrics.scrollTop >= metrics.maxScrollTop || metrics.scrollTop === previousTop) break;
    previousTop = metrics.scrollTop;
    const delta = Math.min(step, metrics.maxScrollTop - metrics.scrollTop);
    await tab.cua.scroll({ x: metrics.x, y: metrics.y, scrollX: 0, scrollY: delta });
    await tab.playwright.waitForTimeout(120);
  }
  return [...byId.values()];
}

export async function collectCurrentContactPage(tab) {
  const before = await readUiState(tab);
  if (before.heading !== "Contacts") throw new Error("The current page is not the HighLevel Contacts page.");
  if (before.total == null || !before.pageText) throw new Error("Could not read the contacts total or pagination state.");
  const status = parsePageStatus(before.pageText);
  const expected = expectedRowsForPage(status.page, status.pageCount, before.total);
  let rows = await collectPageAtStep(tab, 1000);
  if (rows.length !== expected) rows = await collectPageAtStep(tab, 400);
  if (rows.length !== expected) {
    throw new Error(`Page ${status.page} yielded ${rows.length} unique rows; expected ${expected}.`);
  }
  return {
    page: status.page,
    pageCount: status.pageCount,
    total: before.total,
    sourceUrl: before.url,
    rows: rows.map((row, index) => ({ ...row, sourcePage: status.page, sourceIndex: index + 1 })),
  };
}

async function waitForPage(tab, expectedPage) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const state = await readUiState(tab);
    if (state.pageText && parsePageStatus(state.pageText).page === expectedPage) {
      await tab.playwright.waitForTimeout(250);
      return state;
    }
    await tab.playwright.waitForTimeout(150);
  }
  throw new Error(`Timed out waiting for page ${expectedPage}.`);
}

export async function prepareContactList(tab) {
  const state = await readUiState(tab);
  if (state.heading !== "Contacts") throw new Error("Open the contacts smart-list page before preparing the backup.");
  const pageSize = tab.playwright.getByRole("combobox", { name: "Page Size" });
  if (String(state.pageSize) !== String(PAGE_SIZE)) {
    await pageSize.selectOption(String(PAGE_SIZE));
    await tab.playwright.waitForTimeout(500);
  }
  let current = await readUiState(tab);
  while (parsePageStatus(current.pageText).page > 1) {
    const page = parsePageStatus(current.pageText).page;
    await tab.playwright.getByRole("button", { name: "Prev Page" }).click();
    current = await waitForPage(tab, page - 1);
  }
  await resetTableScroll(tab);
  return readUiState(tab);
}

export async function seekContactPage(tab, targetPage, maxMoves = 40) {
  const target = Math.max(1, Number(targetPage));
  let state = await readUiState(tab);
  let status = parsePageStatus(state.pageText);
  let moves = 0;
  while (status.page !== target && moves < Math.max(1, Number(maxMoves))) {
    const direction = status.page < target ? 1 : -1;
    const buttonName = direction > 0 ? "Next Page" : "Prev Page";
    await tab.playwright.getByRole("button", { name: buttonName }).click();
    state = await waitForPage(tab, status.page + direction);
    status = parsePageStatus(state.pageText);
    moves += 1;
  }
  return { ...state, ...status, targetPage: target, reached: status.page === target, moves };
}

export async function saveCurrentContactPage(tab, options) {
  const outputDir = path.resolve(options.outputDir);
  const pagesDir = path.join(outputDir, options.pagesDir || "reconcile");
  await fs.mkdir(pagesDir, { recursive: true });
  const pageData = await collectCurrentContactPage(tab);
  const fileName = options.fileName || `page-${String(pageData.page).padStart(6, "0")}.json`;
  await writeJson(path.join(pagesDir, fileName), pageData);
  return { page: pageData.page, pageCount: pageData.pageCount, total: pageData.total, rows: pageData.rows.length, pagesDir };
}

async function writeJson(file, value) {
  await fs.writeFile(file, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

export async function runContactBackupChunk(tab, options) {
  const outputDir = path.resolve(options.outputDir);
  const pagesDir = path.join(outputDir, options.pagesDir || "pages");
  const maxPages = Math.max(1, Number(options.maxPages || 20));
  const host = normalizeHost(options.host);
  const locationId = String(options.locationId || "").trim();
  if (!locationId) throw new Error("locationId is required.");
  await fs.mkdir(pagesDir, { recursive: true });

  const progressPath = path.join(outputDir, "progress.json");
  let progress;
  try {
    progress = JSON.parse(await fs.readFile(progressPath, "utf8"));
  } catch {
    const prepared = await prepareContactList(tab);
    const status = parsePageStatus(prepared.pageText);
    progress = {
      version: 1,
      host,
      locationId,
      sourceUrl: `https://${host}/v2/location/${locationId}/contacts/smart_list/All`,
      startedAt: new Date().toISOString(),
      startUiTotal: prepared.total,
      finalUiTotal: null,
      pageCount: status.pageCount,
      completedPages: 0,
      nextPage: 1,
      finished: false,
      pagesDir,
    };
    await writeJson(progressPath, progress);
  }

  let processed = 0;
  while (!progress.finished && processed < maxPages) {
    const state = await readUiState(tab);
    const currentStatus = parsePageStatus(state.pageText);
    if (currentStatus.page !== progress.nextPage) {
      throw new Error(`Browser is on page ${currentStatus.page}; checkpoint expects page ${progress.nextPage}.`);
    }
    const pageData = await collectCurrentContactPage(tab);
    const pageFile = path.join(pagesDir, `page-${String(pageData.page).padStart(6, "0")}.json`);
    await writeJson(pageFile, pageData);
    progress.completedPages = pageData.page;
    progress.pageCount = pageData.pageCount;
    progress.finalUiTotal = pageData.total;
    progress.updatedAt = new Date().toISOString();
    processed += 1;

    if (pageData.page >= pageData.pageCount) {
      progress.finished = true;
      progress.nextPage = null;
      progress.completedAt = new Date().toISOString();
      await writeJson(progressPath, progress);
      break;
    }

    progress.nextPage = pageData.page + 1;
    await writeJson(progressPath, progress);
    await tab.playwright.getByRole("button", { name: "Next Page" }).click();
    if (processed < maxPages) await waitForPage(tab, progress.nextPage);
  }

  await writeJson(progressPath, progress);
  return { ...progress, processedThisChunk: processed };
}

export async function summarizeCheckpoints(outputDir, pagesDirNames = ["pages"]) {
  const root = path.resolve(outputDir);
  const progress = JSON.parse(await fs.readFile(path.join(root, "progress.json"), "utf8"));
  const byId = new Map();
  const dirNames = Array.isArray(pagesDirNames) ? pagesDirNames : [pagesDirNames];
  let pageFiles = 0;
  for (const dirName of dirNames) {
    const pagesDir = path.join(root, dirName);
    const files = (await fs.readdir(pagesDir)).filter((name) => /^page-\d+\.json$/.test(name)).sort();
    pageFiles += files.length;
    for (const file of files) {
      const page = JSON.parse(await fs.readFile(path.join(pagesDir, file), "utf8"));
      for (const row of page.rows || []) byId.set(row.id, row);
    }
  }
  return {
    finished: Boolean(progress.finished),
    pageFiles,
    completedPages: progress.completedPages,
    pageCount: progress.pageCount,
    startUiTotal: progress.startUiTotal,
    finalUiTotal: progress.finalUiTotal,
    uniqueContacts: byId.size,
    matchesFinalUiTotal: progress.finished && byId.size === progress.finalUiTotal,
  };
}

export { parsePageStatus, expectedRowsForPage };
