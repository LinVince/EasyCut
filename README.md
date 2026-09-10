# TW Stocks — PWA

A **fully static** Progressive Web App for tracking Taiwan stocks with live prices, 120-day moving averages, 5-day OHLCV history, dividends, and 52-week range — all fetched directly from Yahoo Finance in the browser (no backend, no proxy).

Favorites are stored locally via **IndexedDB** and can be exported/imported as JSON backup. Installable on iPhone Home Screen via **Add to Home Screen**.

## Features

- **Live prices** — Yahoo Finance `chart` API (browser direct)
- **TW stock code + Traditional Chinese names** — built-in mapping for 170+ stocks
- **52-week range bar** — visual position within the year
- **120-day MA** — computed from daily close history
- **5-day OHLCV table** — last 5 trading days
- **Dividend history** — recent payments from Yahoo events
- **Favorites** — star any stock, saved locally (IndexedDB)
- **Export / Import** — JSON backup of favorites
- **Offline support** — app shell cached by service worker
- **PWA installable** — Add to Home Screen (iOS standalone)

## Deploy as Static

Just serve the `public/` directory from any static host:

| Platform | How |
|---|---|
| GitHub Pages | Push `public/` contents to repo → Settings → Pages |
| Netlify / Cloudflare Pages | Drag-drop `public/` in dashboard |
| Any web server | Copy `public/` to web root |

## Local Preview

```bash
npm install
npm start
# → http://localhost:5000
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
├── index.html
├── styles.css
├── script.js      # Yahoo Finance fetch + IndexedDB favorites + PWA init
├── sw.js          # Service worker (caches app shell)
├── manifest.json  # PWA manifest
└── icons/
    ├── icon-192.png
    ├── icon-512.png
    └── apple-touch-icon.png
```

## Data Notes

Data comes from Yahoo Finance's public `chart` API, which works in-browser when `fetch()` sends standard `Sec-Fetch-*` headers. No CORS proxy or backend needed.

**Unavailable without a Yahoo crumb:** P/E ratio, EPS, market cap, beta. These fields show "—".

## License

MIT
