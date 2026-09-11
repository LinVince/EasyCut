// Cloudflare Worker: serves the static PWA AND proxies Yahoo Finance.
// - /api/chart/:symbol  or  /chart/:symbol  → Yahoo proxy (.TW then .TWO)
// - /api/ai-summary (POST) → Workers AI analysis of the watchlist
// - everything else → static files from ../public via env.ASSETS

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (/^\/(?:api\/chart|chart)\/[^/]+$/.test(url.pathname)) {
      return proxyQuote(url);
    }
    if (url.pathname === '/api/ai-summary' && request.method === 'POST') {
      return aiSummary(request, env);
    }
    // CORS preflight for the AI endpoint
    if (url.pathname === '/api/ai-summary' && request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors() });
    }
    if (env && env.ASSETS) return env.ASSETS.fetch(request);
    return new Response('Not found', { status: 404 });
  },
};

// ── Workers AI summary ──────────────────────────────────────────────
const MODEL_CANDIDATES = [
  '@cf/meta/llama-3.2-3b-instruct',
  '@cf/meta/llama-3.1-8b-instruct',
  '@hf/meta-llama/meta-llama-3-8b-instruct',
];
const aiCache = new Map(); // key -> { at: ms, text }

async function aiSummary(request, env) {
  if (!env.AI) return json({ error: 'Workers AI not configured' }, 503);
  let body = {};
  try { body = await request.json(); } catch (e) { /* ignore */ }
  const watchlist = Array.isArray(body.watchlist) ? body.watchlist.filter(w => w && w.symbol) : [];
  if (!watchlist.length) return json({ error: 'Empty watchlist' }, 400);
  const focus = typeof body.focus === 'string' ? String(body.focus) : 'MA proximity screener';

  const tz = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Taipei', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date());
  const key = `ai:${tz}:${simpleHash(JSON.stringify(watchlist) + '|' + focus)}`;

  const hit = aiCache.get(key);
  if (hit && Date.now() - hit.at < 12 * 3600 * 1000) {
    return json({ text: hit.text, cached: true }, 200);
  }

  const rows = watchlist.map(w => {
    const d = (p) => w.maVs && w.maVs[p] != null ? w.maVs[p].toFixed(2) + '%' : 'n/a';
    const w52 = (w.wk52Low != null && w.wk52High != null)
      ? w.wk52Low + '~' + w.wk52High
      : 'n/a';
    return `${w.symbol} ${w.name}: price ${w.price != null ? w.price : 'n/a'}, day chg ${w.changePct != null ? w.changePct + '%' : 'n/a'}, dev MA20 ${d(20)}, MA40 ${d(40)}, MA60 ${d(60)}, MA120 ${d(120)}, MA200 ${d(200)}, 52wk ${w52}, vol ${w.volume != null ? w.volume : 'n/a'}, yield ${w.divYield != null ? w.divYield + '%' : 'n/a'}`;
  }).join('\n');

  const system = 'You are a friendly, plainspoken Taiwan stock analyst writing a quick daily brief for a retail investor. Respond ONLY in Traditional Chinese, in a warm human tone (casual but professional, no stiff lists). Write a short report (~100 words, 3-4 short paragraphs): (1) open with one welcoming sentence and today\'s overall market tone based on the data; (2) pick the top 2-3 stocks worth focusing on RIGHT NOW — prefer ones whose price deviates least from their MA20/MA60 (a likely pullback/entry zone) or that are breaking structure near their 52-week high — and give each one a sentence explaining the situation using the exact MA% figures; (3) close with a one-line honest caveat that this is only an observation, not investment advice. Use the stock symbol and Chinese name when naming stocks. Never invent numbers or facts not present in the data.';
  const user = `Focus: ${focus}\nWatchlist data:\n${rows}`;

  let lastErr = null;
  for (const model of MODEL_CANDIDATES) {
    try {
      const res = await env.AI.run(model, {
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: user },
        ],
        max_tokens: 300,
        temperature: 0.3,
      });
      const text = (res?.response != null ? res.response : res?.result || '').trim();
      if (!text) throw new Error('Empty AI response');
      aiCache.set(key, { at: Date.now(), text });
      return json({ text }, 200);
    } catch (err) {
      lastErr = err;
    }
  }
  return json({ error: 'AI request failed: ' + (lastErr?.message || 'unknown') }, 502);
}

function simpleHash(s) {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0;
  return h.toString(36);
}

function cors() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

async function proxyQuote(url) {
  const m = url.pathname.match(/^\/(?:api\/chart|chart)\/([^/]+)$/);
  const symbol = decodeURIComponent(m[1]);
  const range = url.searchParams.get('range') || '1y';
  const interval = url.searchParams.get('interval') || '1d';
  const enc = encodeURIComponent(symbol);
  const qs = `range=${encodeURIComponent(range)}&interval=${encodeURIComponent(interval)}&events=div%2Csplits`;
  const candidates = [
    `https://query1.finance.yahoo.com/v8/finance/chart/${enc}.TW?${qs}`,
    `https://query1.finance.yahoo.com/v8/finance/chart/${enc}.TWO?${qs}`,
  ];
  const headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
    'Accept': 'application/json',
  };

  for (const c of candidates) {
    try {
      const r = await fetch(c, { headers });
      if (r.status === 404) continue;
      if (!r.ok) return json({ error: 'Yahoo Finance error', status: r.status }, r.status);
      return jsonText(await r.text(), 200);
    } catch (err) {
      return json({ error: err.message }, 502);
    }
  }
  return json({ error: 'Symbol not found on TWSE/TPEX' }, 404);
}

function jsonText(text, status) {
  return new Response(text, {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'public, max-age=30',
    },
  });
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-store',
    },
  });
}