# TW Stocks — PWA

A **static** Progressive Web App for tracking Taiwan stocks with live prices, MA20/40/60/120/200, 5-day OHLCV history, dividends, and 52-week range. Yahoo Finance sends no CORS headers, so live data is relayed through a small proxy:

- **Local dev** — the bundled Node/Express server proxies at `/api/chart`
- **Deployed to GitHub Pages** — a free **Cloudflare Worker** relays the same requests

Favorites, watchlist, categories, and export/import are stored locally via **IndexedDB**. Installable on iPhone Home Screen via **Add to Home Screen**.

## Features

- **Live prices** — Yahoo Finance `chart` API via proxy (Node or Cloudflare Worker)
- **Categories** — built-in AI/semiconductor catalog, custom categories, filter bar
- **Moving averages** — MA20/40/60/120/200 computed from daily closes
- **Near-MA screener** — find watchlist stocks within 0.5/1/2% of any MA
- **52-week range bar** — visual position within the year
- **5-day OHLCV table** — last 5 trading days
- **Dividend history** — recent payments from Yahoo events
- **Favorites** — star any stock, saved locally (IndexedDB)
- **Export / Import** — JSON backup of favorites + watchlist + categories
- **Yahoo link** — ↗ icon on each card opens the stock's Yahoo Finance page
- **Offline support** — app shell cached by service worker
- **PWA installable** — Add to Home Screen (iOS standalone)

## Deploy (recommended: static + Cloudflare Worker)

1. **Create the Worker** — in `worker/`:
   ```bash
   cd worker
   npx wrangler login
   npx wrangler deploy
   ```
   Note the worker URL, e.g. `https://easycut-data-proxy.<account>.workers.dev`.

2. **Point the app at it** — in `public/config.js`:
   ```js
   window.YF_PROXY = 'https://easycut-data-proxy.<account>.workers.dev';
   ```

3. **Deploy the frontend** — push to GitHub and enable Pages from Actions,
   or drop `public/` onto Netlify / Cloudflare Pages.

The `.github/workflows/deploy.yml` workflow auto-publishes `public/` to GitHub Pages on every push to `main`.

## Local Preview

```bash
npm install
npm start
# → http://localhost:5000  (proxy served by Express at /api/chart)
```

## iPhone Install

1. Open the URL in Safari
2. Tap the Share icon
3. Scroll to "Add to Home Screen"
4. Tap Add

The app now launches standalone from your Home Screen like a native app.

## Project Structure

```
public/
├── index.html      # App markup + modal
├── styles.css
├── config.js       # window.YF_PROXY → static-host data proxy URL ('' = local)
├── script.js       # fetch, IndexedDB, categories, MAs, screener, PWA init
├── sw.js           # Service worker (network-first, caches app shell)
├── manifest.json   # PWA manifest
└── icons/
    ├── icon-192.png
    ├── icon-512.png
    └── apple-touch-icon.png

worker/
├── index.js        # Cloudflare Worker — Yahoo chart proxy (.TW → .TWO)
└── wrangler.toml   # Worker config (name: easycut-data-proxy)

server.js           # Local dev server + same proxy at /api/chart
```

## Data Notes

Yahoo Finance's public `chart` API sends **no `Access-Control-Allow-Origin`** header, so a browser cannot fetch it directly. The Node server (local) or the Cloudflare Worker (deployed) relays requests for us, trying the `.TW` suffix first and falling back to `.TWO` for OTC/TPEX stocks.

**Unavailable without a Yahoo crumb:** P/E ratio, EPS, market cap, beta. These fields show "—".

## License

MIT
