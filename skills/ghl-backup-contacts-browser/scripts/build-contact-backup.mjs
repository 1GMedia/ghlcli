import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

function arg(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}

if (!arg("--input-dir") || !arg("--audit") || !arg("--output")) {
  throw new Error("Usage: node build-contact-backup.mjs --input-dir PAGES --audit progress.json --output backup.xlsx");
}
const inputDirs = [arg("--input-dir"), arg("--extra-input-dir")]
  .filter(Boolean)
  .map((value) => path.resolve(value));
const auditPath = path.resolve(arg("--audit"));
const outputPath = path.resolve(arg("--output"));
const audit = JSON.parse(await fs.readFile(auditPath, "utf8"));

// Excel's XML package rejects C0 controls and other non-XML code points that
// can appear in user-entered contact names. Preserve valid Unicode (including
// emoji) while dropping only characters that cannot be serialized to .xlsx.
function xmlSafe(value) {
  const cleaned = String(value ?? "").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\uFFFE\uFFFF]/g, "");
  return cleaned.startsWith("=") ? `'${cleaned}` : cleaned;
}

const pageFiles = [];
const contactsById = new Map();
for (const inputDir of inputDirs) {
  const files = (await fs.readdir(inputDir)).filter((name) => /^page-\d+\.json$/.test(name)).sort();
  for (const file of files) {
    pageFiles.push(path.join(inputDir, file));
    const page = JSON.parse(await fs.readFile(path.join(inputDir, file), "utf8"));
    for (const row of page.rows || []) contactsById.set(row.id, row);
  }
}
const contacts = [...contactsById.values()].sort((a, b) =>
  (a.sourcePage - b.sourcePage) || (a.sourceIndex - b.sourceIndex) || String(a.id).localeCompare(String(b.id))
);
if (!audit.finished) throw new Error("Checkpoint is not marked finished.");
if (contacts.length !== audit.finalUiTotal) {
  throw new Error(`Unique contact count ${contacts.length} does not match final UI total ${audit.finalUiTotal}.`);
}

const workbook = Workbook.create();
const contactsSheet = workbook.worksheets.add("Contacts");
const auditSheet = workbook.worksheets.add("Backup Audit");
contactsSheet.showGridLines = false;
auditSheet.showGridLines = false;

contactsSheet.mergeCells("A1:J1");
contactsSheet.getRange("A1").values = [["HighLevel Contacts Backup"]];
contactsSheet.getRange("A2:J2").values = [[
  "Unique contacts", null,
  "UI total at completion", audit.finalUiTotal,
  "Reconciliation", null,
  "Location ID", audit.locationId,
  "Completed", new Date(audit.completedAt || audit.updatedAt || ""),
]];
contactsSheet.getRange("B2").formulas = [[`=COUNTA(H6:H${contacts.length + 5})`]];
contactsSheet.getRange("F2").formulas = [["=IF(B2=D2,\"MATCH\",\"MISMATCH\")"]];
contactsSheet.mergeCells("A3:J3");
contactsSheet.getRange("A3").values = [[`Source: ${audit.sourceUrl}`]];

const headers = [
  "Contact name", "Phone", "Email", "Business name", "Created (PDT)",
  "Last activity (PDT)", "Tags", "Contact ID", "Contact detail URL", "Source page",
];
contactsSheet.getRange("A5:J5").values = [headers];
const rows = contacts.map((row) => [
  xmlSafe(row.name), xmlSafe(row.phone), xmlSafe(row.email), xmlSafe(row.businessName), xmlSafe(row.created),
  xmlSafe(row.lastActivity), xmlSafe(row.tags), xmlSafe(row.id), xmlSafe(row.contactUrl), row.sourcePage || null,
]);
for (let start = 0; start < rows.length; start += 5000) {
  const chunk = rows.slice(start, start + 5000);
  contactsSheet.getRangeByIndexes(start + 5, 0, chunk.length, headers.length).values = chunk;
}

const lastRow = contacts.length + 5;
const table = contactsSheet.tables.add(`A5:J${lastRow}`, true, "HighLevelContacts");
table.style = "TableStyleMedium2";
table.showFilterButton = true;
table.showBandedColumns = false;
contactsSheet.freezePanes.freezeRows(5);
contactsSheet.getRange(`A6:I${lastRow}`).format.numberFormat = "@";
contactsSheet.getRange(`J6:J${lastRow}`).format.numberFormat = "0";

contactsSheet.getRange("A1:J1").format.fill = "#0F172A";
contactsSheet.getRange("A1:J1").format.font = { bold: true, color: "#FFFFFF" };
contactsSheet.getRange("A1:J1").format.rowHeight = 30;
contactsSheet.getRange("A2:J2").format.fill = "#E2E8F0";
contactsSheet.getRange("A2:J2").format.font = { color: "#0F172A" };
contactsSheet.getRange("A2:J2").format.rowHeight = 24;
contactsSheet.getRange("J2").format.numberFormat = "yyyy-mm-dd hh:mm";
for (const cell of ["A2", "C2", "E2", "G2", "I2"]) {
  contactsSheet.getRange(cell).format.font = { bold: true, color: "#334155" };
}
contactsSheet.getRange("A3:J3").format.fill = "#F8FAFC";
contactsSheet.getRange("A3:J3").format.font = { italic: true, color: "#475569" };
contactsSheet.getRange("A5:J5").format.fill = "#0F766E";
contactsSheet.getRange("A5:J5").format.font = { bold: true, color: "#FFFFFF" };
contactsSheet.getRange("A5:J5").format.rowHeight = 26;
contactsSheet.getRange(`A6:J${lastRow}`).format.verticalAlignment = "center";
const widths = [28, 18, 31, 22, 23, 22, 32, 24, 56, 20];
widths.forEach((width, index) => {
  contactsSheet.getRangeByIndexes(0, index, lastRow, 1).format.columnWidth = width;
});

auditSheet.getRange("A1:B1").merge();
auditSheet.getRange("A1").values = [["Backup Audit"]];
auditSheet.getRange("A3:B13").values = [
  ["Location ID", audit.locationId],
  ["Host", audit.host],
  ["Source route", audit.sourceUrl],
  ["Started at", new Date(audit.startedAt)],
  ["Completed at", new Date(audit.completedAt || audit.updatedAt || "")],
  ["Start UI total", audit.startUiTotal],
  ["Final UI total", audit.finalUiTotal],
  ["Unique workbook contacts", null],
  ["Pages captured", pageFiles.length],
  ["UI page count", audit.pageCount],
  ["Status", null],
];
auditSheet.getRange("B10").formulas = [["='Contacts'!B2"]];
auditSheet.getRange("B13").formulas = [["=IF(B10=B9,\"MATCH\",\"MISMATCH\")"]];
auditSheet.getRange("A15:B17").values = [
  ["Method", "Signed-in browser UI and accessible DOM only"],
  ["Export function", "Never used"],
  ["Direct API calls", "Never used"],
];
auditSheet.getRange("A1:B1").format.fill = "#0F172A";
auditSheet.getRange("A1:B1").format.font = { bold: true, color: "#FFFFFF" };
auditSheet.getRange("A1:B1").format.rowHeight = 30;
auditSheet.getRange("A3:A17").format.fill = "#E2E8F0";
auditSheet.getRange("A3:A17").format.font = { bold: true, color: "#334155" };
auditSheet.getRange("A3:B17").format.borders = { preset: "inside", style: "thin", color: "#CBD5E1" };
auditSheet.getRange("B6:B7").format.numberFormat = "yyyy-mm-dd hh:mm";
auditSheet.getRange("A1:A17").format.columnWidth = 27;
auditSheet.getRange("B1:B17").format.columnWidth = 68;
auditSheet.getRange("B3:B17").format.wrapText = true;
auditSheet.freezePanes.freezeRows(1);

const contactsCheck = await workbook.inspect({
  kind: "table", range: "Contacts!A1:J15", include: "values,formulas", tableMaxRows: 15, tableMaxCols: 10,
});
const auditCheck = await workbook.inspect({
  kind: "table", range: "'Backup Audit'!A1:B17", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 3,
});
const errors = await workbook.inspect({
  kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan",
});
await fs.mkdir(path.dirname(outputPath), { recursive: true });
const previewDir = path.join(path.dirname(outputPath), ".preview");
await fs.mkdir(previewDir, { recursive: true });
for (const [sheetName, range, fileName] of [
  ["Contacts", "A1:J20", "contacts.png"],
  ["Backup Audit", "A1:B17", "audit.png"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1.5, format: "png" });
  await fs.writeFile(path.join(previewDir, fileName), new Uint8Array(await preview.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({
  outputPath, uniqueContacts: contacts.length, finalUiTotal: audit.finalUiTotal,
  pageFiles: pageFiles.length, contactsCheck: contactsCheck.ndjson,
  auditCheck: auditCheck.ndjson, formulaErrors: errors.ndjson,
  previews: [path.join(previewDir, "contacts.png"), path.join(previewDir, "audit.png")],
}, null, 2));
