// Cloudflare Worker: Yahoo Finance CORS proxy for the EasyCut PWA.
// Routes /api/chart/:symbol and /chart/:symbol, tries .TW then .TWO.

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    const m = path.match(/^\/(?:api\/chart|chart)\/([^/]+)$/);
    if (!m) return json({ error: 'Not found' }, 404);

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
  },
};

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