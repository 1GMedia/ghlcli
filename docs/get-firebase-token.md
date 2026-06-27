# Getting your GHL Firebase refresh token

You only need this if you want to **build/update workflows** (the internal-API
`--experimental` commands). Everything else works with just `GHL_API_KEY`.

The token is read from your own logged-in GoHighLevel session — no extension, no
install, nothing leaves your browser. You paste a one-line snippet into the browser's
DevTools console and it copies the token to your clipboard.

## What this unlocks

The Firebase/internal lane uses `backend.leadconnectorhq.com` with a Firebase ID token in the `token-id` header. The CLI can get that ID token from:

- `GHL_FIREBASE_REFRESH_TOKEN`, preferred, exchanged through Google Secure Token API.
- `GHL_FIREBASE_TOKEN`, direct short-lived token.

Current internal capability is workflow-focused:

- `ghl --experimental workflows create`
- `ghl --experimental workflows create-n8n`
- workflow folder creation
- workflow draft creation
- tag-trigger creation
- workflow step save/sync
- location tag creation
- builder scripts under `builders/`
- guarded generic backend calls through `ghl --experimental internal request`

This does **not** mean the CLI can access everything in HighLevel. Treat internal endpoints as unstable and session-scoped. Use `--dry-run` first, and use `--confirm` for mutating generic internal calls.

## Steps

1. In Chrome (or any Chromium browser), open and log into `https://app.gohighlevel.com`.
2. Open DevTools: **⌘⌥J** (Mac) / **Ctrl-Shift-J** (Windows/Linux) to jump straight to the
   Console.
3. Paste this and press Enter:

   ```js
   (async () => {
     const db = await new Promise((res, rej) => {
       const r = indexedDB.open("firebaseLocalStorageDb");
       r.onsuccess = e => res(e.target.result);
       r.onerror = () => rej("Cannot open IndexedDB");
     });
     const entries = await new Promise((res, rej) => {
       const tx = db.transaction("firebaseLocalStorage", "readonly");
       const all = tx.objectStore("firebaseLocalStorage").getAll();
       all.onsuccess = () => res(all.result);
       all.onerror = () => rej("Failed to read store");
     });
     for (const e of entries) {
       const stm = (e?.value || e)?.stsTokenManager;
       if (stm?.refreshToken) {
         copy(stm.refreshToken); // DevTools copy() helper → clipboard
         console.log("✓ Refresh token copied. Paste into .env as GHL_FIREBASE_REFRESH_TOKEN=");
         return;
       }
     }
     console.warn("No refresh token found — make sure you're logged into GHL on this tab.");
   })();
   ```

4. The console prints `✓ Refresh token copied.` — the token is now on your clipboard.
5. Paste it into your `.env`:

   ```env
   GHL_FIREBASE_REFRESH_TOKEN=<paste here>
   ```

> If the console shows `No refresh token found`, make sure you ran the snippet on an
> `app.gohighlevel.com` tab where you're logged in (not a marketing page).

## Notes

- The Firebase refresh token is sensitive — it's your full GHL session. Treat it like a
  password and never commit your `.env`.
- The snippet only **reads** from your own browser's IndexedDB and uses the built-in
  DevTools `copy()` helper. It makes no network calls.
- Tokens refresh automatically once in `.env`; re-run the snippet only if you get an
  "expired/revoked" error.
