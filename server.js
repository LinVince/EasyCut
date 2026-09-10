const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.static(path.join(__dirname, 'public')));

// Yahoo Finance proxy — handles CORS and rate-limiting for the browser
app.get('/api/chart/:symbol', async (req, res) => {
  const { symbol } = req.params;
  const { range = '1y', interval = '1d' } = req.query;
  const enc = encodeURIComponent(symbol);
  // Listed stocks use .TW, OTC (TPEX) stocks use .TWO
  const candidates = [
    `https://query1.finance.yahoo.com/v8/finance/chart/${enc}.TW?range=${range}&interval=${interval}&events=div%2Csplits`,
    `https://query1.finance.yahoo.com/v8/finance/chart/${enc}.TWO?range=${range}&interval=${interval}&events=div%2Csplits`,
  ];
  const headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36' };

  for (const url of candidates) {
    try {
      const r = await fetch(url, { headers });
      if (r.status === 404) continue;
      if (!r.ok) return res.status(r.status).json({ error: 'Yahoo Finance error' });
      const data = await r.json();
      res.set('Cache-Control', 'public, max-age=30');
      return res.json(data);
    } catch (err) {
      return res.status(502).json({ error: err.message });
    }
  }
  res.status(404).json({ error: 'Symbol not found on TWSE/TPEX' });
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`TW Stocks running on http://localhost:${PORT}`);
});
