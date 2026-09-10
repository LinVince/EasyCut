const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Store stock data in memory
const stockData = {};

// API Routes - Skeleton
app.get('/api/stocks', (req, res) => {
  res.json(Object.values(stockData));
});

app.get('/api/stocks/:symbol', (req, res) => {
  const symbol = req.params.symbol.toUpperCase();
  if (stockData[symbol]) {
    res.json(stockData[symbol]);
  } else {
    res.status(404).json({ error: 'Stock not found' });
  }
});

app.post('/api/stocks/add/:symbol', (req, res) => {
  const symbol = req.params.symbol.toUpperCase();
  stockData[symbol] = {
    symbol: symbol,
    price: 0,
    date: new Date().toISOString(),
    volume: 0,
    open: 0,
    high: 0,
    low: 0,
    ma120: 'N/A',
    tracked_since: new Date().toISOString(),
    historical_prices: []
  };
  res.json({ success: true, data: stockData[symbol] });
});

app.delete('/api/stocks/:symbol', (req, res) => {
  const symbol = req.params.symbol.toUpperCase();
  if (stockData[symbol]) {
    delete stockData[symbol];
    res.json({ success: true });
  } else {
    res.status(404).json({ error: 'Stock not found' });
  }
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'Server is running' });
});

// Serve index.html for all other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`🇹🇼 Taiwanese Stock Tracker running on http://localhost:${PORT}`);
});
