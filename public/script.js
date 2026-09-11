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

  // Never drop symbols on transient fetch failures — cards render with
  // fallback data until live data is available.
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
    .map(s => renderCard(liveStocks[s] || favoritesSnapshots[s] || { symbol: s }, true))
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
        <button class="ext-link" onclick="openStockDetail('${s.symbol}')" title="View price chart" aria-label="View price chart">&#8599;</button>
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

// ── AI Insights (Workers AI) ───────────────────────────────────────
const AI_ENDPOINT = (window.YF_PROXY ? window.YF_PROXY.replace(/\/+$/, '') : '') + '/api/ai-summary';

function buildAiWatchlist() {
  return Object.values(liveStocks)
    .filter(s => s.price != null)
    .map(s => ({
      symbol: s.symbol,
      name: s.name_zh || s.symbol,
      price: s.price,
      changePct: s.changePct,
      maVs: s.maVs,
      wk52Low: s.wk52Low,
      wk52High: s.wk52High,
      volume: s.volume,
      divYield: s.divYield,
    }));
}

function mdToHtml(md) {
  return String(md)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .split('\n')
    .map(line => {
      const l = line.trim();
      if (!l) return '';
      if (/^#{1,3}\s/.test(l)) return `<h4>${l.replace(/^#+\s*/, '')}</h4>`;
      if (/^[-*]\s/.test(l)) return `<div class="ai-li">•&nbsp;${mdInline(l.replace(/^[-*]\s*/, ''))}</div>`;
      return `<div class="ai-line">${mdInline(l)}</div>`;
    })
    .filter(Boolean)
    .join('');
}

function mdInline(s) {
  return s
    .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/\*([^*]+)\*/g, '<i>$1</i>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

async function runAiAnalysis() {
  const list = buildAiWatchlist();
  const out = document.getElementById('aiResult');
  if (!list.length) {
    out.innerHTML = '<p class="empty-state">Fetch live data first (Refresh), then run the analysis.</p>';
    return;
  }
  const btn = document.querySelector('.ai-run');
  btn.disabled = true;
  btn.textContent = 'Analyzing…';
  out.innerHTML = '<div class="ai-loading">Workers AI is scanning your watchlist…</div>';
  try {
    const r = await fetch(AI_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        watchlist: list,
        focus: `MA proximity screener (threshold ${thresholdPct}%)`,
      }),
    });
    const j = await r.json();
    if (!r.ok || j.error) throw new Error(j.error || 'HTTP ' + r.status);
    out.innerHTML = `
      <div class="ai-ts">${j.cached ? 'Cached result' : 'Fresh reply'} · ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })} · <span class="ai-disclaimer">observations only, not advice</span></div>
      ${mdToHtml(j.text)}`;
  } catch (err) {
    out.innerHTML = `<p class="ai-error">AI scan failed: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run AI Analysis';
  }
}

// ── Stock Detail View ──────────────────────────────────────────────
const RANGE_PRESETS = {
  '1d':  { interval: '1m',  candle: false },
  '5d':  { interval: '5m',  candle: false },
  '1mo': { interval: '1d',  candle: true  },
  '3mo': { interval: '1d',  candle: true  },
  '6mo': { interval: '1d',  candle: true  },
  '1y':  { interval: '1d',  candle: true  },
  '5y':  { interval: '1wk', candle: true  },
  'max': { interval: '3mo', candle: true  },
};
const chartCache = {};   // symbol -> { range -> {ts, o, h, l, c, v, meta} }
let detailSymbol = null;
let detailRange = '1y';
let detailMaSel = new Set(['20', '60']);
let liveChartYf = null;
let cursorInfoEl = null;

function openStockDetail(symbol) {
  const target = `#/stock/${encodeURIComponent(symbol)}`;
  if (location.hash === target) {
    showStockView(symbol);
  } else {
    location.hash = target;
  }
}

function closeStockDetail() {
  location.hash = '#/';
}

function getDetailSymbolFromHash() {
  const m = location.hash.match(/^#\/stock\/(.+)$/);
  return m ? decodeURIComponent(m[1]) : null;
}

function showStockView(sym) {
  document.getElementById('stockView').classList.remove('hidden');
  const container = document.querySelector('.container');
  if (container) container.classList.add('hidden');
  window.scrollTo(0, 0);
  detailSymbol = sym;

  const info = STOCK_INFO[sym] || {};
  document.getElementById('detSymbol').textContent = sym;
  document.getElementById('detName').textContent = info.name_zh || liveStocks[sym]?.name_zh || sym;
  document.getElementById('detYahoo').href = yahooQuoteUrl({ symbol: sym });

  if (liveStocks[sym]) {
    const s = liveStocks[sym];
    document.getElementById('detPrice').textContent = 'NT$' + fmt(s.price);
    const ch = document.getElementById('detChange');
    ch.textContent = fmtPct(s.changePct);
    ch.className = 'change ' + (chgCls(s.changePct) || '');
  }

  renderDetailStats(sym, null);
  void switchDetailRange(detailRange);
}

function hideStockView() {
  document.getElementById('stockView').classList.add('hidden');
  const container = document.querySelector('.container');
  if (container) container.classList.remove('hidden');
}

function renderDetailStats(sym, yf) {
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  const stock = liveStocks[sym] || {};
  const meta = yf?.meta || {};
  const quote = yf?.indicators?.quote?.[0] || {};
  const lastIdx = yf ? (yf.timestamp?.length || 1) - 1 : -1;
  const price = meta.regularMarketPrice ?? stock.price ?? null;
  const prev  = meta.previousClose ?? stock.prevClose ?? meta.chartPreviousClose ?? null;

  set('detOpen',  (meta.regularMarketOpen ?? stock.open) != null ? 'NT$' + fmt(meta.regularMarketOpen ?? stock.open) : (quote.open?.[lastIdx] != null ? 'NT$' + fmt(quote.open[lastIdx]) : '—'));
  set('detHigh',  (meta.regularMarketDayHigh ?? stock.dayHigh) != null ? 'NT$' + fmt(meta.regularMarketDayHigh ?? stock.dayHigh) : (quote.high?.[lastIdx] != null ? 'NT$' + fmt(quote.high[lastIdx]) : '—'));
  set('detLow',   (meta.regularMarketDayLow ?? stock.dayLow) != null ? 'NT$' + fmt(meta.regularMarketDayLow ?? stock.dayLow) : (quote.low?.[lastIdx] != null ? 'NT$' + fmt(quote.low[lastIdx]) : '—'));
  set('detPrev',  prev != null ? 'NT$' + fmt(prev) : '—');
  set('detVol',   (meta.regularMarketVolume ?? stock.volume) != null ? fmtVol(meta.regularMarketVolume ?? stock.volume) : (quote.volume?.[lastIdx] != null ? fmtVol(quote.volume[lastIdx]) : '—'));
  set('detYield', (meta.regularMarketDividendYield != null ? +(meta.regularMarketDividendYield * 100).toFixed(2) : stock.divYield) != null ? (meta.regularMarketDividendYield != null ? +(meta.regularMarketDividendYield * 100).toFixed(2) : stock.divYield) + '%' : '—');
  set('det52H',   (meta.fiftyTwoWeekHigh ?? stock.wk52High) != null ? 'NT$' + fmt(meta.fiftyTwoWeekHigh ?? stock.wk52High) : '—');
  set('det52L',   (meta.fiftyTwoWeekLow ?? stock.wk52Low) != null ? 'NT$' + fmt(meta.fiftyTwoWeekLow ?? stock.wk52Low) : '—');

  if (yf) renderDetailPrice(price, prev);
}

function renderDetailPrice(price, prev) {
  if (price == null) return;
  document.getElementById('detPrice').textContent = 'NT$' + fmt(price);
  const chEl = document.getElementById('detChange');
  if (prev != null && prev !== 0) {
    const pct = +((price - prev) / prev * 100).toFixed(2);
    chEl.textContent = fmtPct(pct);
    chEl.className = 'change ' + (chgCls(pct) || '');
  } else {
    chEl.textContent = '—';
    chEl.className = 'change';
  }
}

async function switchDetailRange(range) {
  detailRange = range;
  document.querySelectorAll('.range-btn').forEach(b => b.classList.toggle('active', b.dataset.r === range));
  const canvas = document.getElementById('detChart');
  const loading = document.getElementById('detLoading');
  const errEl = document.getElementById('detError');
  loading.classList.remove('hidden');
  errEl.classList.add('hidden');

  if (!detailSymbol) return;
  const reqSym = detailSymbol;
  const data = await fetchChartData(reqSym, range);
  if (detailSymbol !== reqSym || detailRange !== range) return;
  loading.classList.add('hidden');

  if (!data) {
    errEl.textContent = 'Could not load chart data for this range.';
    errEl.classList.remove('hidden');
    return;
  }

  liveChartYf = data;
  renderDetailStats(detailSymbol, data);
  drawStockChart(canvas, data, { candle: RANGE_PRESETS[range]?.candle !== false, mas: detailMaSel });
}

async function fetchChartData(symbol, range) {
  if (chartCache[symbol]?.[range]) return chartCache[symbol][range];
  const preset = RANGE_PRESETS[range] || { interval: '1d', candle: true };
  const url = `${YF_CHART}/${symbol}?range=${range}&interval=${preset.interval}`;
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const json = await r.json();
    const result = json?.chart?.result?.[0];
    if (!result) throw new Error('No result');
    const quote = result.indicators?.quote?.[0] || {};
    const ts = result.timestamp || [];
    const len = ts.length;
    const o = [], h = [], l = [], c = [], v = [];
    for (let i = 0; i < len; i++) {
      o.push(quote.open?.[i] != null ? +quote.open[i] : NaN);
      h.push(quote.high?.[i] != null ? +quote.high[i] : NaN);
      l.push(quote.low?.[i]  != null ? +quote.low[i]  : NaN);
      c.push(quote.close?.[i] != null ? +quote.close[i] : NaN);
      v.push(quote.volume?.[i] != null ? +quote.volume[i] : 0);
    }
    const clean = { ts, o, h, l, c, v, meta: result.meta || {} };
    chartCache[symbol] = chartCache[symbol] || {};
    chartCache[symbol][range] = clean;
    return clean;
  } catch (e) {
    console.error('chart fetch failed', e);
    return null;
  }
}

function drawStockChart(canvas, d, opts) {
  const dpr = window.devicePixelRatio || 1;
  const cssW = Math.max(canvas.parentElement.clientWidth - 20, 280);
  const cssH = 280;
  canvas.width = Math.round(cssW * dpr);
  canvas.height = Math.round(cssH * dpr);
  canvas.style.width = cssW + 'px';
  canvas.style.height = cssH + 'px';

  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);

  const padR = 52, padL = 8, padTop = 8, padVol = 56;
  const plotW = cssW - padL - padR;
  const plotH = cssH - padTop - padVol;
  const volTop = cssH - padVol + 6;

  const valid = [];
  d.ts.forEach((t, i) => {
    if (isFinite(d.c[i]) && d.c[i] > 0) valid.push(i);
  });
  if (valid.length < 2) return;

  // Price scale
  let minP = Infinity, maxP = -Infinity;
  valid.forEach(i => {
    const lo = isFinite(d.l[i]) ? d.l[i] : d.c[i];
    const hi = isFinite(d.h[i]) ? d.h[i] : d.c[i];
    if (lo < minP) minP = lo;
    if (hi > maxP) maxP = hi;
  });
  const padP = (maxP - minP) * 0.05 || maxP * 0.01 || 1;
  minP -= padP; maxP += padP;
  if (minP === maxP) { minP -= 1; maxP += 1; }

  const x = i => padL + (i / (d.ts.length - 1)) * plotW;
  const y = p => padTop + plotH - ((p - minP) / (maxP - minP)) * plotH;

  // Dashed gridlines
  ctx.strokeStyle = '#eef2f7'; ctx.fillStyle = '#94a3b8'; ctx.font = '10px system-ui'; ctx.lineWidth = 1;
  const tickN = 4;
  for (let t = 0; t <= tickN; t++) {
    const p = minP + (maxP - minP) * t / tickN;
    ctx.beginPath(); ctx.setLineDash([3,4]);
    ctx.moveTo(padL, y(p)); ctx.lineTo(cssW - padR, y(p));
    ctx.strokeStyle = '#eef2f7'; ctx.stroke();
    ctx.setLineDash([]);
    ctx.textAlign = 'left'; ctx.fillText(fmt(p), cssW - padR + 5, y(p) + 3);
  }

  if (opts.mas?.size) {
    const cols = {
      '20': 'rgba(245,158,11,0.9)', '60': 'rgba(6,182,212,0.9)',
      '120': 'rgba(139,92,246,0.9)', '200': 'rgba(236,72,153,0.9)',
    };
    [...opts.mas].forEach(p => {
      const maArr = buildMA(d.c, +p);
      ctx.strokeStyle = cols[p] || '#64748b'; ctx.lineWidth = 1.2; ctx.beginPath();
      let started = false;
      for (let i = 0; i < maArr.length; i++) {
        if (!isFinite(maArr[i])) continue;
        const px = x(i), py = y(maArr[i]);
        if (!started) { ctx.moveTo(px, py); started = true; } else ctx.lineTo(px, py);
      }
      ctx.stroke();
    });
  }

  // Body (candles or line)
  if (opts.candle && d.ts.length < 4000) {
    const bodyW = Math.max(Math.min(plotW / d.ts.length * 0.7, 10), 1);
    const prevClose = d.meta.chartPreviousClose;
    if (prevClose != null && isFinite(prevClose) && prevClose >= minP && prevClose <= maxP) {
      ctx.strokeStyle = 'rgba(100,116,139,0.55)'; ctx.lineWidth = 1; ctx.setLineDash([4,3]);
      ctx.beginPath(); ctx.moveTo(padL, y(prevClose)); ctx.lineTo(cssW - padR, y(prevClose)); ctx.stroke();
      ctx.setLineDash([]);
    }
    valid.forEach(i => {
      const up = d.c[i] >= d.o[i];
      const col = up ? '#16a34a' : '#dc2626';
      const bx = x(i);
      const oy = y(d.o[i] != null ? d.o[i] : d.c[i]);
      const cy = y(d.c[i]);
      const top = Math.min(oy, cy), hgt = Math.max(Math.abs(cy - oy), 1);
      ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 1;
      if (d.h[i] != null && d.l[i] != null && isFinite(d.h[i]) && isFinite(d.l[i])) {
        ctx.beginPath(); ctx.moveTo(bx, y(d.h[i])); ctx.lineTo(bx, y(d.l[i])); ctx.stroke();
      }
      ctx.fillRect(bx - bodyW / 2, top, Math.max(bodyW, 1), hgt);
    });
  } else {
    // Line for intraday
    ctx.strokeStyle = '#1e40af'; ctx.lineWidth = 1.6; ctx.beginPath();
    let started = false;
    valid.forEach(i => {
      const px = x(i), py = y(d.c[i]);
      if (!started) { ctx.moveTo(px, py); started = true; } else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }

  // Volume bars
  let maxV = 1;
  valid.forEach(i => { if (d.v[i] > maxV) maxV = d.v[i]; });
  valid.forEach(i => {
    const up = d.c[i] >= d.o[i];
    const bh = Math.max((d.v[i] / maxV) * (padVol - 16), 1);
    ctx.fillStyle = up ? 'rgba(22,163,74,0.45)' : 'rgba(220,38,38,0.45)';
    ctx.fillRect(x(i) - Math.max(bodyW_for_vol(i, d), 1) / 2, volTop + (padVol - 16) - bh, Math.max(bodyW_for_vol(i, d), 1), bh);
  });
  function bodyW_for_vol(i, dd) { return Math.max(Math.min((cssW - padL - padR) / dd.ts.length * 0.7, 10), 1); }

  // X-axis ticks
  ctx.fillStyle = '#94a3b8'; ctx.textAlign = 'center'; ctx.font = '9px system-ui';
  const xTicks = 4;
  for (let t = 0; t <= xTicks; t++) {
    const idx = Math.round(t * (d.ts.length - 1) / xTicks);
    const dt = new Date(d.ts[idx] * 1000);
    const label = (RANGE_PRESETS[detailRange]?.interval === '1m' || RANGE_PRESETS[detailRange]?.interval === '5m')
      ? dt.toLocaleDateString('zh-TW', { month: 'numeric', day: 'numeric' }) + ' ' + dt.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', hour12: false })
      : dt.toLocaleDateString('zh-TW', { year: 'numeric', month: 'short', day: 'numeric' });
    ctx.fillText(label, x(idx), cssH - padVol + 16);
  }

  drawLegend(ctx, d, opts);
  attachCursor(canvas, d, x, y);
}

function buildMA(arr, p) {
  const out = [];
  let sum = 0;
  for (let i = 0; i < arr.length; i++) {
    if (!isFinite(arr[i])) { out.push(NaN); continue; }
    sum += arr[i];
    if (i >= p) { const prev = arr[i - p]; if (isFinite(prev)) sum -= prev; }
    if (i >= p - 1) out.push(sum / p); else out.push(NaN);
  }
  return out;
}

function drawLegend(ctx, d, opts) {
  let legendEl = document.getElementById('detLegend');
  if (!legendEl) {
    legendEl = document.createElement('div');
    legendEl.id = 'detLegend';
    legendEl.className = 'chart-legend';
    document.querySelector('.chart-card').appendChild(legendEl);
  }
  const cols = {
    '20': 'rgb(245,158,11)', '60': 'rgb(6,182,212)',
    '120': 'rgb(139,92,246)', '200': 'rgb(236,72,153)',
  };
  legendEl.innerHTML = '';
  const last = d.ts.length - 1;
  const priceLabel = isFinite(d.c[last]) ? 'Close ' + fmt(d.c[last]) : '';
  legendEl.insertAdjacentHTML('beforeend', `<span><span class="lg-dot" style="background:#1e40af"></span>${priceLabel}</span>`);
  [...(opts.mas || [])].forEach(p => {
    const maArr = buildMA(d.c, +p);
    const v = maArr[last];
    if (isFinite(v)) {
      legendEl.insertAdjacentHTML('beforeend', `<span><span class="lg-dot" style="background:${cols[p]}"></span>MA${p} ${fmt(v)}</span>`);
    }
  });
}

function attachCursor(canvas, d, x, y) {
  let infoEl = cursorInfoEl;
  if (!infoEl) {
    infoEl = document.createElement('div');
    infoEl.className = 'chart-cursor-info';
    infoEl.style.display = 'none';
    canvas.parentElement.appendChild(infoEl);
    cursorInfoEl = infoEl;
  }
  infoEl.style.display = 'none';

  const showAt = (idx) => {
    if (!isFinite(d.c[idx])) return;
    const dt = new Date(d.ts[idx] * 1000);
    const intraday = RANGE_PRESETS[detailRange]?.interval === '1m' || RANGE_PRESETS[detailRange]?.interval === '5m';
    const dateStr = dt.toLocaleDateString('zh-TW', { year:'numeric', month:'numeric', day:'numeric' })
      + (intraday ? ' ' + dt.toLocaleTimeString('zh-TW', { hour:'2-digit', minute:'2-digit', hour12:false }) : '');
    const info = cursorInfoEl;
    info.innerHTML = `
      <span style="font-weight:700">${dateStr}</span>
      <span>O ${fmt(d.o[idx])}</span><span>H ${fmt(d.h[idx])}</span>
      <span>L ${fmt(d.l[idx])}</span><span>C ${fmt(d.c[idx])}</span>
      <span>Vol ${fmtVol(d.v[idx])}</span>`;
    info.style.display = 'flex';
  };

  const clear = () => { if (cursorInfoEl) cursorInfoEl.style.display = 'none'; };
  const hitIndex = (clientX) => {
    const rect = canvas.getBoundingClientRect();
    const px = clientX - rect.left - 8;
    const frac = px / (canvas.clientWidth - 8 - 52);
    return Math.max(0, Math.min(d.ts.length - 1, Math.round(frac * (d.ts.length - 1))));
  };

  canvas.onmousemove = (e) => showAt(hitIndex(e.clientX));
  canvas.onmouseleave = clear;
  canvas.ontouchmove = (e) => {
    e.preventDefault();
    showAt(hitIndex(e.touches[0].clientX));
  };
  canvas.ontouchend = clear;
  canvas.onclick = (e) => showAt(hitIndex(e.clientX));
}

// ── Stock Detail Routing ───────────────────────────────────────────
function handleHashChange() {
  const sym = getDetailSymbolFromHash();
  if (sym && sym !== detailSymbol) {
    showStockView(sym);
  } else if (!sym) {
    detailSymbol = null;
    hideStockView();
  }
}

document.querySelectorAll('.range-btn').forEach(b => {
  b.addEventListener('click', () => switchDetailRange(b.dataset.r));
});
document.querySelectorAll('.ma-toggle').forEach(b => {
  b.addEventListener('click', () => {
    const p = b.dataset.ma;
    if (b.classList.contains('active')) {
      b.classList.remove('active');
      detailMaSel.delete(p);
    } else {
      b.classList.add('active');
      detailMaSel.add(p);
    }
    if (liveChartYf) drawStockChart(document.getElementById('detChart'), liveChartYf, {
      candle: RANGE_PRESETS[detailRange]?.candle !== false, mas: detailMaSel
    });
  });
});

window.addEventListener('hashchange', handleHashChange);

// ── Init ───────────────────────────────────────────────────────────
(async () => {
  handleHashChange();
})();
