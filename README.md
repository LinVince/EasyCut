# 🇹🇼 Taiwanese Stock Tracker

A real-time web application for tracking Taiwanese stocks with live prices and 120-day moving averages.

## Features (Skeleton Version)

✨ **Real-time Stock Tracking** - Add and track Taiwanese stocks
📊 **120-Day Moving Average** - Technical analysis ready
🎯 **Easy Portfolio Management** - Add/remove stocks
📱 **Responsive Design** - Works on all devices
🌐 **Public Website** - Accessible to everyone

## Quick Start

### Prerequisites
- Node.js (v14+)
- npm

### Installation

```bash
# Install dependencies
npm install

# Start the server
npm start
```

The website will be available at `http://localhost:5000`

## Project Structure

```
EasyCut/
├── server.js           # Express backend
├── package.json        # Dependencies
├── .env               # Configuration
└── public/
    ├── index.html     # Main page
    ├── styles.css     # Styling
    └── script.js      # Client logic
```

## API Endpoints

- `GET /api/stocks` - Get all tracked stocks
- `GET /api/stocks/:symbol` - Get specific stock
- `POST /api/stocks/add/:symbol` - Add stock
- `DELETE /api/stocks/:symbol` - Remove stock

## Next Steps

- [ ] Integrate Taiwan Stock Exchange API
- [ ] Implement real-time price fetching
- [ ] Add 120-day moving average calculation
- [ ] Database integration
- [ ] User authentication
- [ ] Deploy to production

## License

MIT

---

Made with ❤️ for Taiwan stock market enthusiasts
