// ── Constants ───────────────────────────────────────────────────────
// Proxy through our own server (handles Yahoo CORS)
const YF_CHART = (window.YF_PROXY ? window.YF_PROXY.replace(/\/+$/, '') : '') + '/api/chart';
const DEFAULT_RANGE = '1y';
const DEFAULT_INTERVAL = '1d';

// Popular TW stocks preloaded on first visit
const POPULAR_DEFAULTS = [
  '2330','2317','2454','2881','2882','2891','2886',
  '2002','2308','2382','3711','1301','1303','1326'
];

// ── AI / Semi supply-chain catalog with industry categorization ────
const STOCK_INFO = {
  2330:{name_zh:'台積電',industry:'晶圓代工',role:'AI GPU / ASIC 晶片製造、先進製程'},
  2303:{name_zh:'聯電',industry:'晶圓代工',role:'成熟製程'},
  2454:{name_zh:'聯發科',industry:'IC設計/IP',role:'AI、ASIC、SoC'},
  2379:{name_zh:'瑞昱',industry:'IC設計',role:'網通/高速傳輸'},
  3661:{name_zh:'世芯-KY',industry:'ASIC',role:'AI ASIC'},
  3443:{name_zh:'創意',industry:'ASIC',role:'ASIC / AI 晶片設計'},
  3035:{name_zh:'智原',industry:'ASIC',role:'ASIC / IP'},
  6643:{name_zh:'M31',industry:'IP',role:'半導體 IP'},
  3711:{name_zh:'日月光投控',industry:'先進封裝/封測',role:'封裝測試'},
  2449:{name_zh:'京元電子',industry:'封測',role:'AI/HPC 晶片測試'},
  2408:{name_zh:'南亞科',industry:'記憶體',role:'DRAM'},
  2344:{name_zh:'華邦電',industry:'記憶體',role:'DRAM / NOR Flash'},
  2337:{name_zh:'旺宏',industry:'記憶體',role:'NOR / NAND'},
  8299:{name_zh:'群聯',industry:'記憶體控制器',role:'NAND Controller / SSD'},
  3260:{name_zh:'威剛',industry:'記憶體模組',role:'DRAM / SSD'},
  2451:{name_zh:'創見',industry:'記憶體模組',role:'DRAM / SSD / Flash'},
  8271:{name_zh:'宇瞻',industry:'記憶體模組',role:'DRAM / SSD'},
  5289:{name_zh:'宜鼎',industry:'工控記憶體',role:'工業記憶體 / AI Edge'},
  2368:{name_zh:'金像電',industry:'PCB',role:'AI Server 高階 PCB'},
  3037:{name_zh:'欣興',industry:'PCB',role:'PCB / ABF載板'},
  3044:{name_zh:'健鼎',industry:'PCB',role:'高階 PCB'},
  2313:{name_zh:'華通',industry:'PCB',role:'PCB'},
  8155:{name_zh:'博智',industry:'PCB',role:'Server PCB'},
  2383:{name_zh:'台光電',industry:'CCL/高速材料',role:'高速 CCL'},
  6274:{name_zh:'台燿',industry:'CCL/高速材料',role:'高速 CCL'},
  6213:{name_zh:'聯茂',industry:'CCL/高速材料',role:'高速 CCL'},
  8046:{name_zh:'南電',industry:'ABF載板',role:'ABF'},
  3189:{name_zh:'景碩',industry:'ABF載板',role:'ABF'},
  2327:{name_zh:'國巨',industry:'被動元件',role:'MLCC / 電阻 / 電感'},
  2492:{name_zh:'華新科',industry:'被動元件',role:'MLCC / 電阻 / 電感'},
  3026:{name_zh:'禾伸堂',industry:'被動元件',role:'MLCC / 被動元件'},
  2478:{name_zh:'大毅',industry:'電阻',role:'電阻'},
  6449:{name_zh:'鈺邦',industry:'電容',role:'電容'},
  3357:{name_zh:'臺慶科',industry:'電感',role:'電感'},
  2308:{name_zh:'台達電',industry:'電源',role:'電源 / AI Data Center'},
  2301:{name_zh:'光寶科',industry:'電源',role:'電源'},
  3017:{name_zh:'奇鋐',industry:'散熱',role:'氣冷 / 液冷 / Cold Plate'},
  3324:{name_zh:'雙鴻',industry:'散熱',role:'散熱 / 液冷'},
  2421:{name_zh:'建準',industry:'散熱',role:'風扇'},
  3652:{name_zh:'健策',industry:'散熱',role:'散熱 / 金屬零件'},
  2317:{name_zh:'鴻海',industry:'伺服器 ODM',role:'AI Server / Rack'},
  2382:{name_zh:'廣達',industry:'ODM',role:'AI Server'},
  3231:{name_zh:'緯創',industry:'ODM',role:'AI Server'},
  6669:{name_zh:'緯穎',industry:'ODM',role:'Cloud / AI Server'},
  2356:{name_zh:'英業達',industry:'ODM',role:'Server'},
  3706:{name_zh:'神達',industry:'ODM',role:'Server'},
  8210:{name_zh:'勤誠',industry:'伺服器機櫃',role:'Server chassis'},
  3013:{name_zh:'晟銘電',industry:'機櫃',role:'Server chassis'},
  3693:{name_zh:'營邦',industry:'機櫃',role:'Server / Storage chassis'},
  3533:{name_zh:'嘉澤',industry:'連接器',role:'CPU/GPU Socket、Connector'},
  2345:{name_zh:'智邦',industry:'網通',role:'AI Switch / Network'},
  5274:{name_zh:'信驊',industry:'BMC',role:'Server 管理晶片'},
};

let CATEGORY_ORDER = [
  '晶圓代工','IC設計/IP','IC設計','ASIC','IP','先進封裝/封測','封測',
  '記憶體','記憶體控制器','記憶體模組','工控記憶體','PCB','CCL/高速材料',
  'ABF載板','被動元件','電阻','電容','電感','電源','散熱','伺服器 ODM',
  'ODM','伺服器機櫃','機櫃','連接器','網通','BMC','其他'
];

const CATALOG_SYMBOLS = Object.keys(STOCK_INFO);
// Snapshot of the built-in catalog — used to tell user-added entries apart
const STATIC_CATALOG = { ...STOCK_INFO };

// A stock's categorization counts as user-customized if it was user-added
// or if its category/role/name differs from the built-in default.
function hasCategoryOverride(sym) {
  const base = STATIC_CATALOG[sym];
  const cur = STOCK_INFO[sym];
  if (!cur) return false;
  if (!base) return true;
  return cur.industry !== base.industry || cur.role !== base.role || cur.name_zh !== base.name_zh;
}

// Traditional Chinese names fallback
const TW_NAMES_ZH = {
  2330:'台積電',2317:'鴻海',2454:'聯發科',2881:'富邦金',2882:'國泰金',
  2891:'中信金',2886:'兆豐金',2002:'中鋼',2308:'台達電',2382:'廣達',
  3711:'日月光投控',1301:'台塑',1303:'南亞',1326:'台化',3008:'大立光',
  2498:'宏達電',2357:'華碩',2353:'宏碁',2412:'中華電',1101:'台泥',
  1216:'統一',2912:'統一超',2603:'長榮',2609:'陽明',2618:'長榮航',
  2610:'華航',2409:'友達',3481:'群創',0050:'元大台灣50',0056:'元大高股息',
  00878:'國泰永續高股息',2883:'開發金',2884:'玉山金',2801:'彰銀',2812:'台中銀',
  9904:'寶成',1605:'華新',2316:'楠梓電',2327:'國巨',2345:'智邦',
  2356:'英業達',2379:'瑞昱',2474:'可成',3017:'奇鋐',3034:'聯詠',
  3231:'緯創',3661:'世芯-KY',4938:'和碩',6446:'藥華藥',6770:'力積電',
  2313:'華通',2324:'仁寶',2376:'技嘉',2377:'微星',9910:'豐泰',
  9917:'中保科',6139:'亞翔',6239:'力成',2417:'圓剛',8069:'元太',
};

const DB_NAME = 'TWStockApp';
const DB_VER  = 2;

// ── IndexedDB ──────────────────────────────────────────────────────
function openDB() {
  return new Promise((resolve, reject) => {
    const r = indexedDB.open(DB_NAME, DB_VER);
    r.onupgradeneeded = () => {
      const db = r.result;
      if (!db.objectStoreNames.contains('watchlist')) db.createObjectStore('watchlist');
      if (!db.objectStoreNames.contains('favorites')) db.createObjectStore('favorites', { keyPath: 'symbol' });
      if (!db.objectStoreNames.contains('catalog'))   db.createObjectStore('catalog');   // key=symbol → info
    };
    r.onsuccess = () => resolve(r.result);
    r.onerror   = () => reject(r.error);
  });
}

async function idbGet(store) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const r = db.transaction(store, 'readonly').objectStore(store).getAll();
    r.onsuccess = () => res(r.result);
    r.onerror   = () => rej(r.error);
  });
}
async function idbGetOne(store, key) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const r = db.transaction(store, 'readonly').objectStore(store).get(key);
    r.onsuccess = () => res(r.result);
    r.onerror   = () => rej(r.error);
  });
}
async function idbPut(store, key, val) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(store, 'readwrite');
    const os = tx.objectStore(store);
    // favorites store uses in-line key (keyPath: 'symbol') → never pass a key arg
    const r = (store === 'favorites') ? os.put(val) : os.put(val, key);
    r.onsuccess = () => res();
    r.onerror   = () => rej(r.error);
  });
}
async function idbDel(store, key) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const r = db.transaction(store, 'readwrite').objectStore(store).delete(key);
    r.onsuccess = () => res();
    r.onerror   = () => rej(r.error);
  });
}

// ── Yahoo Finance Fetch ────────────────────────────────────────────
async function yfFetch(symbol) {
  const url = `${YF_CHART}/${symbol}?range=${DEFAULT_RANGE}&interval=${DEFAULT_INTERVAL}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const json = await r.json();
  const result = json?.chart?.result?.[0];
  if (!result) throw new Error('No result');
  return result;
}

function parseStockData(symbol, yf) {
  const meta = yf.meta || {};
  const price = meta.regularMarketPrice ?? meta.chartPreviousClose ?? null;
  const prevClose = meta.previousClose ?? meta.chartPreviousClose ?? null;
  const ts = yf.timestamp || [];
  const quote = (yf.indicators?.quote || [])[0] || {};
  const closes = quote.close || [];
  const volumes = quote.volume || [];

  // Last N trading days (non-null)
  function tail(arr, n) {
    const clean = arr.filter(v => v != null);
    return clean.slice(-n);
  }

  // Latest prices window wide enough for MA200 (1y of daily bars)
  const closesClean = tail(closes, 260);
  const recent5 = ts.slice(-5).map((t, i) => {
    const idx = ts.length - 5 + i;
    if (idx < 0) return null;
    return {
      date: new Date(t * 1000).toISOString().slice(0,10),
      open:  quote.open?.[idx]  != null ? +quote.open[idx].toFixed(2)  : null,
      high:  quote.high?.[idx]  != null ? +quote.high[idx].toFixed(2)  : null,
      low:   quote.low?.[idx]   != null ? +quote.low[idx].toFixed(2)   : null,
      close: quote.close?.[idx] != null ? +quote.close[idx].toFixed(2) : null,
      volume: quote.volume?.[idx] != null ? Math.round(quote.volume[idx]) : null,
    };
  }).filter(Boolean);

  // Moving averages (20/40/60/120/200)
  const ma = {};
  const maVs = {};
  MA_PERIODS.forEach(p => {
    const win = closesClean.slice(-p);
    if (win.length >= Math.min(p, 60)) {
      ma[p] = +(win.reduce((a,b) => a+b, 0) / win.length).toFixed(2);
    } else {
      ma[p] = null;
    }
    maVs[p] = (ma[p] != null && price != null) ? +((price - ma[p]) / ma[p] * 100).toFixed(2) : null;
  });

  // Day high/low/volume from last bar
  const lastIdx = ts.length - 1;
  const dayHigh  = quote.high?.[lastIdx]  ?? meta.regularMarketDayHigh  ?? null;
  const dayLow   = quote.low?.[lastIdx]   ?? meta.regularMarketDayLow   ?? null;
  const dayVol   = quote.volume?.[lastIdx]?? meta.regularMarketVolume   ?? null;
  const dayOpen  = quote.open?.[lastIdx]  ?? null;

  // Dividends from events
  const divEvents = yf.events?.dividends;
  const dividends = [];
  if (divEvents) {
    Object.keys(divEvents)
      .sort((a,b) => Number(b) - Number(a))
      .slice(0, 6)
      .forEach(k => {
        const d = divEvents[k];
        if (d?.amount) dividends.push({ date: new Date(d.date * 1000).toISOString().slice(0,10), amount: +d.amount.toFixed(2) });
      });
  }

  // Dividend yield approximation: sum last 4 quarters (or 2 semi-annual) / price
  let divYield = null;
  if (dividends.length >= 1 && price) {
    const annualDiv = dividends.slice(0,4).reduce((s,d) => s + d.amount, 0);
    divYield = +(annualDiv / price * 100).toFixed(2);
  }

  const changePct = (price != null && prevClose != null && prevClose !== 0)
    ? +((price - prevClose) / prevClose * 100).toFixed(2)
    : null;

  const info = STOCK_INFO[symbol] || {};
  return {
    symbol,
    yahooSym: meta.symbol || symbol,
    name_en: meta.shortName || meta.longName || '',
    name_zh: info.name_zh || TW_NAMES_ZH[symbol] || meta.shortName || symbol,
    industry: info.industry,
    role: info.role,
    price,
    prevClose,
    open: dayOpen != null ? +dayOpen.toFixed(2) : null,
    dayHigh: dayHigh != null ? +dayHigh.toFixed(2) : null,
    dayLow:  dayLow  != null ? +dayLow.toFixed(2)  : null,
    wk52High: meta.fiftyTwoWeekHigh ?? null,
    wk52Low:  meta.fiftyTwoWeekLow  ?? null,
    volume:   dayVol,
    changePct,
    ma,
    maVs,
    history5: recent5,
    dividends,
    divYield,
    fetchedAt: new Date().toISOString(),
  };
}

// ── State ──────────────────────────────────────────────────────────
const MA_PERIODS = [20, 40, 60, 120, 200];
// TPEX/OTC stocks use the .TWO suffix on Yahoo
const OTC_SYMBOLS = new Set(['6643', '3357', '8155', '3693', '5289']);
function yahooQuoteUrl(s) {
  const sym = String(s.symbol || '');
  const full = (s && s.yahooSym && String(s.yahooSym).match(/\.TW|\.TWO$/))
    ? s.yahooSym
    : sym + (OTC_SYMBOLS.has(sym) ? '.TWO' : '.TW');
  return 'https://finance.yahoo.com/quote/' + encodeURIComponent(full) + '/';
}
let watchlistSymbols = [];          // ordered array of symbols
let liveStocks = {};                // symbol -> parsedStockData (watchlist)
let favoritesSnapshots = {};        // symbol -> full snapshot (favorites)
let favoritesSet = new Set();
let isLoading = false;

// ── Watchlist Persistence ──────────────────────────────────────────
const WATCHLIST_VERSION = 3;

async function loadWatchlist() {
  const raw = await idbGet('watchlist');
  const symbols = raw.filter(x => typeof x === 'string' && !x.startsWith('__'));
  const storedVer = Number(raw.find(x => typeof x === 'string' && x.startsWith('__ver'))?.slice(5)) || 0;

  if (storedVer < WATCHLIST_VERSION) {
    // Merge catalog + popular defaults, keep user's existing picks
    const base = symbols.length ? symbols : POPULAR_DEFAULTS;
    watchlistSymbols = Array.from(new Set([...base, ...CATALOG_SYMBOLS]));
    await saveWatchlist(WATCHLIST_VERSION);
  } else {
    watchlistSymbols = symbols;
  }
}

async function saveWatchlist(ver = WATCHLIST_VERSION) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction('watchlist', 'readwrite');
    const store = tx.objectStore('watchlist');
    store.clear();
    watchlistSymbols.forEach(s => store.put(s, s));
    store.put(`__ver${ver}`, '__ver');
    tx.oncomplete = () => res();
    tx.onerror = () => rej(tx.error);
  });
}

// User-defined categorization overrides (persisted)
let customCategories = [];

function allCategories() {
  const base = CATEGORY_ORDER.filter(c => c !== '其他');
  const custom = customCategories.filter(c => !base.includes(c) && c !== '其他');
  return [...base, ...custom, '其他'];
}

async function loadCatalog() {
  const rows = await idbGet('catalog');
  (rows || []).forEach(r => {
    if (r && r.symbol) STOCK_INFO[r.symbol] = { ...(STOCK_INFO[r.symbol] || {}), ...r, symbol: r.symbol };
  });
  const cc = (rows || []).find(r => r && r.key === '__custom_categories');
  customCategories = cc && Array.isArray(cc.value) ? cc.value : [];
  const co = (rows || []).find(r => r && r.key === '__category_order');
  if (co && Array.isArray(co.value) && co.value.length) {
    const order = [...co.value].filter(c => typeof c === 'string');
    if (order.length) CATEGORY_ORDER = order;
  }
}

async function saveCatalog() {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction('catalog', 'readwrite');
    const store = tx.objectStore('catalog');
    store.clear();
    // Persist every user-customized entry: user-added stocks AND any
    // built-in stock whose category/role/name was changed.
    Object.entries(STOCK_INFO).forEach(([sym, info]) => {
      if (hasCategoryOverride(sym)) {
        store.put({ symbol: sym, name_zh: info.name_zh, industry: info.industry, role: info.role }, sym);
      }
    });
    store.put({ value: customCategories, key: '__custom_categories' }, '__custom_categories');
    store.put({ value: CATEGORY_ORDER, key: '__category_order' }, '__category_order');
    tx.oncomplete = () => res();
    tx.onerror = () => rej(tx.error);
  });
}

// ── Fetch All Watchlist Stocks ─────────────────────────────────────
async function refreshAll() {
  if (isLoading) return;
  isLoading = true;
  document.getElementById('stocksList').innerHTML = '<p class="empty-state">Fetching live data...</p>';

  const results = [];
  for (let i = 0; i < watchlistSymbols.length; i += 8) {
    const chunk = watchlistSymbols.slice(i, i + 8);
    const chunkResults = await Promise.allSettled(
      chunk.map(sym => yfFetch(sym).then(raw => [sym, parseStockData(sym, raw)]))
    );
    results.push(...chunkResults);
  }

  for (const k of Object.keys(liveStocks)) delete liveStocks[k];
  const got = new Set();
  results.forEach(r => {
    if (r.status === 'fulfilled') {
      const [sym, data] = r.value;
      liveStocks[sym] = data;
      got.add(sym);
    }
  });

  // Keep symbols that returned data; leave the rest for next pass
  watchlistSymbols = watchlistSymbols.filter(s => got.has(s));

  isLoading = false;
  renderAll();
  document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit', hour12:false });
}

// ── Add / Remove ───────────────────────────────────────────────────
async function addStock() {
  const input = document.getElementById('stockSymbol');
  const sym = input.value.trim().toUpperCase().replace(/\.TW$/,'');
  if (!sym || /^\d{1,4}$/.test(sym) === false) {
    alert('Enter 1-4 digit TW stock code (e.g. 2330)');
    return;
  }
  if (watchlistSymbols.includes(sym)) { alert(`${sym} already tracked.`); return; }

  input.disabled = true;
  try {
    const raw = await yfFetch(sym);
    const data = parseStockData(sym, raw);
    liveStocks[sym] = data;
    watchlistSymbols.push(sym);
    await saveWatchlist();
    input.value = '';
    renderAll();
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit', hour12:false });
    // New, uncategorized stock → ask for a category right away
    if (!STATIC_CATALOG[sym]) {
      setTimeout(() => openCatPicker(sym), 300);
    }
  } catch(e) {
    alert(`Could not fetch ${sym} — check the code and try again.`);
  }
  input.disabled = false;
}

async function removeStock(sym) {
  watchlistSymbols = watchlistSymbols.filter(s => s !== sym);
  delete liveStocks[sym];
  await saveWatchlist();
  renderAll();
}

// ── Favorites ──────────────────────────────────────────────────────
async function loadFavorites() {
  const snaps = await idbGet('favorites');
  favoritesSnapshots = {};
  favoritesSet = new Set();
  snaps.forEach(s => {
    favoritesSnapshots[s.symbol] = s;
    favoritesSet.add(s.symbol);
  });
}

async function toggleFavorite(sym) {
  if (favoritesSet.has(sym)) {
    await idbDel('favorites', sym);
    favoritesSet.delete(sym);
    delete favoritesSnapshots[sym];
  } else {
    const snap = liveStocks[sym]
      || (STOCK_INFO[sym] ? { ...STOCK_INFO[sym], symbol: sym } : { symbol: sym });
    const payload = { ...snap, symbol: sym, savedAt: new Date().toISOString() };
    await idbPut('favorites', sym, payload);
    favoritesSet.add(sym);
    favoritesSnapshots[sym] = payload;
  }
  renderAll();
}

// ── Rendering ──────────────────────────────────────────────────────
function fmt(n, d=2) {
  if (n == null || isNaN(n)) return '—';
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
}
function fmtPct(n) {
  if (n == null || isNaN(n)) return '—';
  return (n >= 0 ? '+' : '') + Number(n).toFixed(2) + '%';
}
function fmtVol(n) {
  if (n == null || isNaN(n)) return '—';
  if (n >= 1e9)  return (n/1e9).toFixed(1)  + 'B';
  if (n >= 1e6)  return (n/1e6).toFixed(1)  + 'M';
  if (n >= 1e3)  return (n/1e3).toFixed(1)  + 'K';
  return n.toLocaleString();
}
function chgCls(n) { return n == null ? '' : n >= 0 ? 'up' : 'down'; }

function renderAll() {
  document.getElementById('stockCount').textContent = watchlistSymbols.length;
  document.getElementById('favCount').textContent   = favoritesSet.size;
  renderWatchlist();
  renderFavorites();
  renderMaFinder();
}

function renderWatchlist() {
  const el = document.getElementById('stocksList');
  if (watchlistSymbols.length === 0) {
    el.innerHTML = '<p class="empty-state">Add a TW stock symbol (1-4 digits) to start.</p>';
    return;
  }

  renderCategoryFilter();

  // Determine which symbols to show for the active filter
  const shown = activeCategory
    ? watchlistSymbols.filter(s => (STOCK_INFO[s]?.industry || '其他') === activeCategory)
    : watchlistSymbols;

  if (shown.length === 0) {
    el.innerHTML = '<p class="empty-state">No stocks in this category.</p>';
    return;
  }

  if (activeCategory) {
    // Single category → flat grid
    el.className = 'stocks-list';
    el.innerHTML = shown.map(s => renderCard(liveStocks[s] || { symbol:s, name_zh: STOCK_INFO[s]?.name_zh || s, industry: STOCK_INFO[s]?.industry, role: STOCK_INFO[s]?.role }, favoritesSet.has(s))).join('');
    return;
  }

  // Grouped by industry
  el.className = 'stock-blocks';
  const groups = {};
  shown.forEach(s => {
    const cat = STOCK_INFO[s]?.industry || '其他';
    (groups[cat] = groups[cat] || []).push(s);
  });
  const orderedCats = allCategories().filter(c => groups[c])
    .concat(Object.keys(groups).filter(c => !allCategories().includes(c)));

  el.innerHTML = orderedCats.map(cat => `
    <div class="cat-block">
      <div class="cat-header">
        <span class="cat-title">${cat}</span>
        <span class="cat-count">${groups[cat].length}</span>
      </div>
      <div class="cat-grid">
        ${groups[cat].map(s => renderCard(liveStocks[s] || { symbol:s, name_zh: STOCK_INFO[s]?.name_zh || s, industry: STOCK_INFO[s]?.industry, role: STOCK_INFO[s]?.role }, favoritesSet.has(s))).join('')}
      </div>
    </div>
  `).join('');
}

// Active industry filter
let activeCategory = null;

function renderCategoryFilter() {
  const bar = document.getElementById('catFilter');
  if (!bar) return;

  const present = {};
  watchlistSymbols.forEach(s => { present[STOCK_INFO[s]?.industry || '其他'] = true; });
  const cats = Array.from(new Set([...allCategories().filter(c => present[c]), ...Object.keys(present).filter(c => !allCategories().includes(c))]));

  bar.innerHTML = `
    <button class="cat-chip ${!activeCategory ? 'active' : ''}" onclick="setCategory(null)">All</button>
    ${cats.map(c => `<button class="cat-chip ${activeCategory === c ? 'active' : ''}" onclick="setCategory('${c.replace(/'/g, "\\'")}')">${c}</button>`).join('')}
  `;
}

function setCategory(cat) {
  activeCategory = (cat === activeCategory) ? null : cat;
  renderWatchlist();
}

// ── Category Picker (bottom sheet) ─────────────────────────────────
let pickingSymbol = null;

function openCatPicker(sym) {
  pickingSymbol = sym;
  const info = STOCK_INFO[sym] || {};
  document.getElementById('catModalTitle').textContent =
    `Categorize · ${sym}${info.name_zh ? ' ' + info.name_zh : ''}`;
  const current = info.industry || '其他';
  document.getElementById('catModalChips').innerHTML =
    allCategories().map(c => {
      const esc = c.replace(/'/g, "\\'");
      const del = c !== '其他'
        ? `<span class="ch-del" onclick="event.stopPropagation();deleteCategory('${esc}')">✕</span>`
        : '';
      return `<button class="cat-chip ${c === current ? 'active' : ''}" onclick="pickCategory('${esc}')">${c}${del}</button>`;
    }).join('') +
    `<button class="cat-chip add-chip" onclick="toggleCatInput()">＋ Add</button>`;
  document.getElementById('catNewInput').value = '';
  document.getElementById('catAddRow').classList.add('hidden');
  document.getElementById('catModal').classList.remove('hidden');
}

function deleteCategory(cat) {
  if (cat === '其他') return alert('不能刪除「其他」');
  const affected = Object.values(STOCK_INFO).filter(i => i.industry === cat).length;
  if (!confirm(`Delete category "${cat}"?\n${affected} stock(s) will move to 其他.`)) return;

  customCategories = customCategories.filter(c => c !== cat);
  Object.values(STOCK_INFO).forEach(i => {
    if (i.industry === cat) i.industry = '其他';
  });
  saveCatalog();
  if (activeCategory === cat) activeCategory = null;

  let sym = null;
  if (pickingSymbol && STOCK_INFO[pickingSymbol]) sym = pickingSymbol;
  if (sym) { openCatPicker(sym); } else { renderAll(); }
}

function toggleCatInput() {
  const row = document.getElementById('catAddRow');
  const show = row.classList.contains('hidden');
  row.classList.toggle('hidden', !show);
  if (show) document.getElementById('catNewInput').focus({ preventScroll: true });
}

function pickCategory(cat) {
  if (pickingSymbol) {
    const sym = pickingSymbol;
    const existing = STOCK_INFO[sym] || {};
    STOCK_INFO[sym] = { ...existing, symbol: sym, industry: cat };
    saveCatalog();
    pickingSymbol = null;
    renderAll();
  }
  closeCatPicker();
}

function pickNewCategory() {
  const input = document.getElementById('catNewInput');
  const val = input.value.trim();
  if (!val) return;
  if (allCategories().some(c => c.toLowerCase() === val.toLowerCase())) {
    input.value = '';
    pickCategory(allCategories().find(c => c.toLowerCase() === val.toLowerCase()));
    return;
  }
  customCategories.push(val);
  saveCatalog();
  renderCategoryFilter();
  pickCategory(val);
}

function closeCatPicker() {
  document.getElementById('catModal').classList.add('hidden');
  document.getElementById('catAddRow').classList.add('hidden');
  pickingSymbol = null;
}

function renderFavorites() {
  const el = document.getElementById('favoritesList');
  if (favoritesSet.size === 0) {
    el.innerHTML = '<p class="empty-state">No favorites yet.</p>';
    return;
  }
  el.innerHTML = Array.from(favoritesSet)
    .map(s => renderCard(favoritesSnapshots[s] || liveStocks[s] || { symbol: s }, true))
    .join('');
}

// ── Near Moving Average Screener ───────────────────────────────────
let thresholdPct = 1;

function setThreshold(v) {
  thresholdPct = v;
  document.querySelectorAll('.th-chip').forEach(el =>
    el.classList.toggle('active', Number(el.dataset.th) === v));
  renderMaFinder();
}

function renderMaFinder() {
  const el = document.getElementById('maFinder');
  if (!el) return;

  const stocks = Object.values(liveStocks).filter(s => s.price != null && s.maVs);
  if (stocks.length === 0) {
    el.innerHTML = '<div class="empty-state">Price data loads with the watchlist.</div>';
    return;
  }

  el.innerHTML = MA_PERIODS.map(p => {
    const near = stocks
      .map(s => ({ sym: s.symbol, dev: s.maVs[p] }))
      .filter(x => x.dev != null && Math.abs(x.dev) <= thresholdPct)
      .sort((a, b) => Math.abs(a.dev) - Math.abs(b.dev));

    const listHtml = near.length
      ? near.map(x => `<span class="ma-stock-chip ${chgCls(x.dev)}" onclick="focusStock('${x.sym}')">${x.sym} ${fmtPct(x.dev)}</span>`).join('')
      : '<span class="ma-none">none</span>';

    return `
      <div class="ma-group">
        <div class="ma-group-head">
          <span class="ma-group-title">MA${p}</span>
          <span class="ma-group-count">${near.length}</span>
        </div>
        <div class="ma-group-list">${listHtml}</div>
      </div>`;
  }).join('');
}

function focusStock(sym) {
  const card = document.querySelector(`#stocksList .stock-card[data-symbol="${sym}"]`);
  if (!card) return;
  card.scrollIntoView({ behavior: 'smooth', block: 'center' });
  card.classList.remove('flash');
  void card.offsetWidth;
  card.classList.add('flash');
  setTimeout(() => card.classList.remove('flash'), 2000);
}

function renderCard(s, isFav=false) {
  const cc = chgCls(s.changePct);

  // 52-week bar
  let rangePct = 50;
  if (s.wk52High && s.wk52Low && s.wk52High !== s.wk52Low)
    rangePct = Math.max(0, Math.min(100, (s.price - s.wk52Low) / (s.wk52High - s.wk52Low) * 100));

  // 5-day rows
  let rows5 = '';
  if (s.history5?.length) {
    rows5 = s.history5.map(h => {
      const cls = (h.close >= h.open) ? 'up' : 'down';
      return `<tr class="${cls}"><td>${h.date.slice(5)}</td><td>${fmt(h.open)}</td><td>${fmt(h.high)}</td><td>${fmt(h.low)}</td><td>${fmt(h.close)}</td><td>${fmtVol(h.volume)}</td></tr>`;
    }).join('');
  }

  // Dividends
  let divs = '—';
  if (s.dividends?.length) divs = s.dividends.map(d => `${d.date.slice(5)}: NT$${d.amount}`).join(' ,');

  return `
  <div class="stock-card ${isFav?'fav':''}" data-symbol="${s.symbol}">
    <div class="card-header">
      <div class="card-title">
        <span class="stock-symbol">${s.symbol}</span>
        <span class="stock-name">${s.name_zh || s.symbol}</span>
        <span class="stock-name-en">${(s.name_en && s.name_zh && s.name_en !== s.name_zh) ? s.name_en : ''}</span>
        <span class="stock-role">${s.role || s.industry || ''}</span>
      </div>
      <div class="card-actions">
        <a class="ext-link" href="${yahooQuoteUrl(s)}" target="_blank" rel="noopener noreferrer" title="Open Yahoo Finance page" aria-label="Open Yahoo Finance page">&#8599;</a>
        <button class="fav-btn ${isFav?'active':''}" onclick="toggleFavorite('${s.symbol}')" aria-label="Toggle favorite">&#9733;</button>
        <button class="cat-btn" onclick="openCatPicker('${s.symbol}')" title="Categorize">分類</button>
        ${isFav
          ? `<button class="remove-fav-btn" onclick="removeStock('${s.symbol}');toggleFavorite('${s.symbol}')">x</button>`
          : `<button class="remove-btn" onclick="removeStock('${s.symbol}')">x</button>`}
      </div>
    </div>

    <div class="price-row">
      <span class="price">NT$${fmt(s.price)}</span>
      <span class="change ${cc}">${fmtPct(s.changePct)}</span>
    </div>

    <div class="data-grid">
      <div class="data-cell"><span class="lbl">Open</span><span class="val">${fmt(s.open)}</span></div>
      <div class="data-cell"><span class="lbl">Prev</span><span class="val">${fmt(s.prevClose)}</span></div>
      <div class="data-cell"><span class="lbl">High</span><span class="val">${fmt(s.dayHigh)}</span></div>
      <div class="data-cell"><span class="lbl">Low</span><span class="val">${fmt(s.dayLow)}</span></div>
      <div class="data-cell"><span class="lbl">Volume</span><span class="val">${fmtVol(s.volume)}</span></div>
      <div class="data-cell"><span class="lbl">Yield</span><span class="val">${s.divYield != null ? s.divYield+'%' : '—'}</span></div>
    </div>

    <div class="bar-section">
      <div class="bar-label">52-Week Range</div>
      <div class="bar-container"><div class="bar-fill" style="width:${rangePct}%"></div></div>
      <div class="bar-range"><span>${fmt(s.wk52Low)}</span><span>${fmt(s.wk52High)}</span></div>
    </div>

    <div class="ma-box">
      <div class="ma-title">Moving Averages · % above/below price</div>
      <div class="ma-grid">
        ${MA_PERIODS.map(p => `
          <div class="ma-cell">
            <span class="ma-lbl">MA${p}</span>
            <span class="ma-val">${fmt(s.ma?.[p])}</span>
            <span class="ma-vs ${chgCls(s.maVs?.[p])}">${s.maVs?.[p] != null ? fmtPct(s.maVs[p]) : '—'}</span>
          </div>`).join('')}
      </div>
    </div>

    ${rows5 ? `
    <div class="history-section">
      <div class="history-title">Last 5 Trading Days</div>
      <div class="history-scroll">
        <table class="history-table">
          <thead><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Vol</th></tr></thead>
          <tbody>${rows5}</tbody>
        </table>
      </div>
    </div>` : ''}

    <div class="dividend-section">
      <span class="lbl">Dividends</span>
      <span class="val dividend-val">${divs}</span>
    </div>
  </div>`;
}

// ── Export / Import (full backup) ──────────────────────────────────
async function exportBackup() {
  const [favs, wlRaw] = await Promise.all([idbGet('favorites'), idbGet('watchlist')]);
  const watchlist = wlRaw.filter(x => typeof x === 'string' && !x.startsWith('__'));
  const favSyms = favs.map(f => (f && f.symbol) || f).filter(Boolean);

  const groups = {};
  watchlist.forEach(s => {
    const cat = (STOCK_INFO[s] && STOCK_INFO[s].industry) || '其他';
    (groups[cat] = groups[cat] || []).push(s);
  });
  const orderedCats = allCategories().filter(c => groups[c])
    .concat(Object.keys(groups).filter(c => !allCategories().includes(c)));

  const backup = {
    version: 3,
    exportedAt: new Date().toISOString(),
    favorites: favSyms,
    watchlist: orderedCats.map(c => ({ [c]: groups[c] })),
  };
  const blob = new Blob([JSON.stringify(backup, null, 2)], { type:'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `twstock-backup-${new Date().toISOString().slice(0,10)}.json`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
  alert(`Exported ${watchlist.length} stock(s) across ${orderedCats.length} categor${orderedCats.length === 1 ? 'y' : 'ies'} + ${favSyms.length} favorite(s).`);
}

async function importCategoryList(list) {
  const valid = list.filter(r => r && r.symbol && /^\d{1,6}$/.test(String(r.symbol).trim()));
  if (!valid.length) { alert('No valid entries (need "symbol" + "category").'); return; }

  const newSymbols = [];
  valid.forEach(r => {
    const sym = String(r.symbol).trim();
    if (!watchlistSymbols.includes(sym) && !newSymbols.includes(sym)) newSymbols.push(sym);
  });
  const addNote = newSymbols.length ? `${newSymbols.length} new stock(s) will be added to your watchlist.` : 'No new stocks needed.';
  if (!confirm(`Import ${valid.length} category entr${valid.length > 1 ? 'ies' : 'y'}?\n${addNote}`)) return;

  valid.forEach(r => {
    const sym = String(r.symbol).trim();
    const prior = STOCK_INFO[sym] || {};
    STOCK_INFO[sym] = {
      ...prior, symbol: sym,
      name_zh: r.name_zh || prior.name_zh || '',
      industry: r.category || r.industry || prior.industry || '其他',
      role: r.role || prior.role || '',
    };
  });

  const db = await openDB();
  await new Promise((res, rej) => {
    const tx = db.transaction(['catalog', 'watchlist'], 'readwrite');
    const catStore = tx.objectStore('catalog');
    valid.forEach(r => {
      const sym = String(r.symbol).trim();
      const info = STOCK_INFO[sym];
      catStore.put({ symbol: sym, name_zh: info.name_zh, industry: info.industry, role: info.role }, sym);
    });
    if (newSymbols.length) {
      const wlStore = tx.objectStore('watchlist');
      newSymbols.forEach(s => wlStore.put(s, s));
      wlStore.put(`__ver${WATCHLIST_VERSION}`, '__ver');
    }
    tx.oncomplete = () => res();
    tx.onerror = () => rej(tx.error);
  });

  await loadCatalog();
  await loadWatchlist();
  activeCategory = null;
  renderAll();
  if (newSymbols.length) refreshAll();
  alert(`Imported ${valid.length} category entr${valid.length > 1 ? 'ies' : 'y'}.`);
}

async function importBackup(e) {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const data = JSON.parse(await file.text());

    // Category list format: [ {symbol, name_zh, category, role}, ... ]
    if (Array.isArray(data)) {
      if (!data.length) { alert('The file has no entries.'); return; }
      await importCategoryList(data);
      return;
    }

    // Parse favorites: symbols or snapshot objects
    const favSyms = (data.favorites || [])
      .map(f => typeof f === 'string' ? f : (f && f.symbol))
      .filter(s => s && /^\d{1,6}$/.test(String(s)));

    // Parse v2 catalog (entries with symbol/industry/role)
    (data.catalog || []).forEach(c => {
      if (c && c.symbol) {
        const t = String(c.symbol);
        if (/^\d{1,6}$/.test(t)) {
          const prior = STOCK_INFO[t] || {};
          STOCK_INFO[t] = {
            ...prior, symbol: t,
            name_zh: c.name_zh || prior.name_zh || '',
            industry: c.industry || prior.industry || '其他',
            role: c.role || prior.role || '',
          };
        }
      }
    });

    // Parse watchlist: grouped [{category:[syms]}] OR flat [syms]
    const symCats = {};
    const wlSyms = [];
    const parseWatchlist = (w) => {
      if (w && !Array.isArray(w)) return;
      (w || []).forEach(item => {
        if (item && typeof item === 'object' && !Array.isArray(item)) {
          Object.entries(item).forEach(([cat, syms]) => {
            (Array.isArray(syms) ? syms : []).forEach(s => {
              const t = String(s).trim();
              if (/^\d{1,6}$/.test(t)) {
                if (!wlSyms.includes(t)) wlSyms.push(t);
                if (!(t in symCats)) symCats[t] = cat;
              }
            });
          });
        } else if (typeof item === 'string') {
          const t = item.trim();
          if (/^\d{1,6}$/.test(t) && !wlSyms.includes(t)) wlSyms.push(t);
        }
      });
    };
    parseWatchlist(data.watchlist);

    if (!favSyms.length && !wlSyms.length) { alert('Invalid backup file — no favorites or watchlist found.'); return; }

    // Apply grouped categories
    Object.entries(symCats).forEach(([sym, cat]) => {
      const prior = STOCK_INFO[sym] || {};
      STOCK_INFO[sym] = { ...prior, symbol: sym, industry: cat };
    });

    const parts = [];
    if (favSyms.length) parts.push(`${favSyms.length} favorites`);
    if (wlSyms.length) parts.push(`${wlSyms.length} watchlist stocks`);
    if (!confirm(`Import: ${parts.join(', ') || 'data'}.\nThis replaces your current data.`)) return;

    const db = await openDB();
    return new Promise((res) => {
      const tx = db.transaction(['favorites','watchlist','catalog'], 'readwrite');
      const favStore = tx.objectStore('favorites');
      const wlStore  = tx.objectStore('watchlist');
      const catStore = tx.objectStore('catalog');

      // Favorites
      favStore.clear();
      favSyms.forEach(s => favStore.put({ symbol: s }));

      // Watchlist
      wlStore.clear();
      wlSyms.forEach(s => wlStore.put(s, s));
      wlStore.put(`__ver${WATCHLIST_VERSION}`, '__ver');

      // Catalog + custom categories + ordering
      catStore.clear();
      Object.entries(symCats).forEach(([sym, cat]) => {
        const info = STOCK_INFO[sym] || {};
        catStore.put({ symbol: sym, name_zh: info.name_zh, industry: cat, role: info.role }, sym);
      });
      const ccVal = Array.isArray(data.customCategories) ? data.customCategories : [];
      catStore.put({ value: ccVal, key: '__custom_categories' }, '__custom_categories');
      const coVal = Array.isArray(data.categoryOrder) && data.categoryOrder.length
        ? data.categoryOrder.filter(c => typeof c === 'string') : CATEGORY_ORDER;
      catStore.put({ value: coVal, key: '__category_order' }, '__category_order');

      tx.oncomplete = async () => {
        await loadCatalog();
        await loadWatchlist();
        await loadFavorites();
        activeCategory = null;
        renderAll();
        alert(`Imported ${parts.join(', ') || 'data'}.`);
        res();
      };
      tx.onerror = () => { alert('Import failed.'); res(); };
    });
  } catch (err) {
    alert('Failed to import — invalid JSON.');
    console.error(err);
  } finally {
    e.target.value = '';
  }
}

// ── Init ───────────────────────────────────────────────────────────
(async () => {
  await loadCatalog();
  await loadWatchlist();
  await loadFavorites();
  renderAll();
  refreshAll();

  document.getElementById('stockSymbol').addEventListener('keypress', e => {
    if (e.key === 'Enter') addStock();
  });

  // Register service worker for PWA
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').then(reg => reg.update()).catch(() => {});
  }
})();
