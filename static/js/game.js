const ICON_PATHS = {
  fire: `<path d="M12 2c.5 3-2.5 4.5-2.5 8a2.5 2.5 0 0 0 5 0c0-1-.5-1.8-.9-2.5 1.4 1 2.4 3 2.4 5a4.5 4.5 0 0 1-9 0c0-4 2-6.5 3-7.5.3 1.5 1 2 1.5 1.5-.2-1.7 0-3 .5-4.5Z"/>`,
  trophy: `<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>`,
  handshake: `<path d="M12 3v18"/><path d="M5 8l-3 6a4 4 0 0 0 8 0l-3-6Z"/><path d="M19 8l-3 6a4 4 0 0 0 8 0l-3-6Z"/><path d="M5 8h14"/><path d="M8 21h8"/>`,
  loss: `<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6"/><path d="m15 9-6 6"/>`,
  check: `<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>`,
  link: `<path d="M9 15 15 9"/><path d="M11 6l1.5-1.5a4 4 0 0 1 5.5 5.5L16.5 11.5"/><path d="M13 18l-1.5 1.5a4 4 0 0 1-5.5-5.5L7.5 12.5"/>`,
  share: `<path d="M12 15V4"/><path d="m8 8 4-4 4 4"/><path d="M4 14v5a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"/>`,
  rematch: `<path d="M17 2l4 4-4 4"/><path d="M21 6H8a4 4 0 0 0-4 4v1"/><path d="M7 22l-4-4 4-4"/><path d="M3 18h13a4 4 0 0 0 4-4v-1"/>`,
  calendar: `<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>`,
  puzzle: `<path d="M4 7h4a1 1 0 0 0 1-1 2 2 0 1 1 4 0 1 1 0 0 0 1 1h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1 2 2 0 1 0 0 4 1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1 2 2 0 1 0-4 0 1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1 2 2 0 1 0 0-4 1 1 0 0 1-1-1V8a1 1 0 0 1 1-1Z"/>`,
  users: `<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>`,
  globe: `<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>`,
  chart: `<line x1="6" y1="20" x2="6" y2="12"/><line x1="12" y1="20" x2="12" y2="8"/><line x1="18" y1="20" x2="18" y2="4"/>`,
  controller: `<rect x="2" y="8" width="20" height="10" rx="5"/><path d="M7 11v4"/><path d="M5 13h4"/><circle cx="16" cy="11" r="1"/><circle cx="18" cy="14" r="1"/>`,
  ball: `<circle cx="12" cy="12" r="9"/><path d="M12 8l3 2-1 4H10l-1-4Z"/><path d="M12 3v5"/><path d="M6 8l3.5 2.5"/><path d="M18 8l-3.5 2.5"/><path d="M8 20l2-6"/><path d="M16 20l-2-6"/>`,
  play: `<path d="M6 4l13 8-13 8V4Z"/>`,
  clock: `<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>`,

  x: `<path d="M4 4l16 16"/><path d="M20 4 4 20"/>`,
  o: `<circle cx="12" cy="12" r="8"/>`,
};

const ICON_FILLED = new Set(['play']);

function svgIcon(name, size = 18) {
  const attrs = ICON_FILLED.has(name)
    ? `fill="currentColor" stroke="none"`
    : `fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`;
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" ${attrs} style="flex-shrink:0">${ICON_PATHS[name]}</svg>`;
}

function iconText(name, text, { size = 16, gap = 6 } = {}) {
  return `<span style="display:inline-flex;align-items:center;gap:${gap}px">${svgIcon(name, size)}<span>${text}</span></span>`;
}

function shirtSvg() {

  return `<span style="font-size:28px;line-height:1;font-weight:300;color:var(--accent)">+</span>`;
}

function playerColor(player) {
  return player === 1 ? 'var(--accent)' : 'var(--o-color)';
}

function esc(v) {
  if (v == null) return '';
  const d = document.createElement('div');
  d.textContent = String(v);
  return d.innerHTML;
}

const g = {
  mode: null,
  soloVariant: null,
  soloGridCode: null,
  dailyDate: null,
  rows: [], cols: [],
  board: [[null,null,null],[null,null,null],[null,null,null]],
  current: 1,
  winner: null,
  winCells: [],
  usedIds: new Set(),
  activeCell: null,
  streak: { 1: 0, 2: 0 },

  retakeMode: false,
  phase: 'fill',

  pendingThreat: null,
  elapsedSeconds: 0,
  solution: null,

  offlineSolveGrid: null,

  soloAttempted: 0,
  soloCorrect: 0,

  onlineCode: null,
  onlineToken: null,
  onlineSlot: null,
  onlineConnected: 0,
  onlineEventSource: null,
  lobbyEventSource: null,
  onlineBoardEntered: false,
  onlineFinished: false,

  onlineLastWrongGuessVersion: undefined,

  editor: { row: [null, null, null], col: [null, null, null] },
  editorSavedCode: null,
  editorCounts: null,
};
let difficulty = 3;

function getDeviceId() {
  let id = localStorage.getItem('ttt_device_id');
  if (!id) {
    id = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`);
    localStorage.setItem('ttt_device_id', id);
  }
  return id;
}

const DEFAULT_STATS = {
  local: { gamesPlayed: 0, wins: { 1: 0, 2: 0 }, draws: 0, correct: 0, wrong: 0, bestStreak: 0, fastestWinSeconds: null },

  solo: { rounds: 0, correct: 0, cells: 0, bestCorrect: 0, streak: 0, bestStreak: 0, scoreDistribution: new Array(10).fill(0) },

  online: { rounds: 0, wins: 0, losses: 0, draws: 0, streak: 0, bestStreak: 0 },
};

function loadStats() {
  try {
    const raw = localStorage.getItem('ttt_stats');
    if (!raw) return structuredClone(DEFAULT_STATS);
    const parsed = JSON.parse(raw);
    return {
      local: { ...DEFAULT_STATS.local, ...(parsed.local || {}), wins: { ...DEFAULT_STATS.local.wins, ...((parsed.local || {}).wins || {}) } },
      solo: { ...DEFAULT_STATS.solo, ...(parsed.solo || {}) },
      online: { ...DEFAULT_STATS.online, ...(parsed.online || {}) },
    };
  } catch {
    return structuredClone(DEFAULT_STATS);
  }
}

function saveStats() {
  localStorage.setItem('ttt_stats', JSON.stringify(stats));
}

const deviceId = getDeviceId();
let stats = loadStats();

let selectedLeague = '';
let onlineVisibility = 'private';
let retakeMode = false;

function genParams() {
  const p = new URLSearchParams({ difficulty: String(difficulty) });
  if (selectedLeague) p.set('league', selectedLeague);
  return p;
}

const OFFLINE_POOL_KEY = 'ttt_offline_pool';
const OFFLINE_PREFETCH_COUNT = 10;
const OFFLINE_FETCH_TIMEOUT_MS = 5000;

function loadOfflinePool() {
  try {
    const pool = JSON.parse(localStorage.getItem(OFFLINE_POOL_KEY) || '[]');
    return Array.isArray(pool) ? pool : [];
  } catch {
    return [];
  }
}

function saveOfflinePool(pool) {
  try {
    localStorage.setItem(OFFLINE_POOL_KEY, JSON.stringify(pool));
  } catch {

  }
}

function popOfflinePuzzle() {
  const pool = loadOfflinePool();
  const puzzle = pool.shift();
  if (puzzle) saveOfflinePool(pool);
  return puzzle || null;
}

async function fetchWithTimeout(url, timeoutMs) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    return await fetch(url, { signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}

function updateOfflinePoolCount() {
  const el = document.getElementById('offline-pool-count');
  if (el) el.textContent = `${loadOfflinePool().length} bereit`;
}

let offlinePrefetchInFlight = false;

async function prefetchOfflinePuzzles() {
  if (offlinePrefetchInFlight) return;
  offlinePrefetchInFlight = true;
  const btn = document.getElementById('btn-offline-prefetch');
  const countEl = document.getElementById('offline-pool-count');
  btn.disabled = true;
  const pool = loadOfflinePool();
  let added = 0;
  for (let i = 0; i < OFFLINE_PREFETCH_COUNT; i++) {
    countEl.textContent = `Lade ${i + 1} / ${OFFLINE_PREFETCH_COUNT}…`;
    try {
      const newResp = await fetchWithTimeout(`/api/game/new?${genParams().toString()}`, OFFLINE_FETCH_TIMEOUT_MS);
      if (!newResp.ok) break;
      const { rows, cols } = await newResp.json();
      const rowIds = rows.map(c => c.id).join(',');
      const colIds = cols.map(c => c.id).join(',');
      const solveResp = await fetchWithTimeout(`/api/game/solve?rows=${rowIds}&cols=${colIds}`, OFFLINE_FETCH_TIMEOUT_MS);
      if (!solveResp.ok) break;
      const { grid } = await solveResp.json();
      pool.push({ rows, cols, solveGrid: grid });
      added++;
    } catch {
      break;
    }
  }
  saveOfflinePool(pool);
  btn.disabled = false;
  updateOfflinePoolCount();
  if (added === 0) countEl.textContent = `${pool.length} bereit – keine Verbindung`;
  offlinePrefetchInFlight = false;
}

document.getElementById('btn-offline-prefetch')?.addEventListener('click', prefetchOfflinePuzzles);

let statusFlashTimer = null;
function flashStatus(text, duration = 2500) {
  document.getElementById('status-text').textContent = text;
  clearTimeout(statusFlashTimer);
  statusFlashTimer = setTimeout(() => { if (!g.winner) updateStatus(); }, duration);
}

async function loadRowsAndCols() {
  if (navigator.onLine !== false) {
    try {
      const resp = await fetchWithTimeout(`/api/game/new?${genParams().toString()}`, OFFLINE_FETCH_TIMEOUT_MS);
      if (resp.ok) {
        const data = await resp.json();
        return { rows: data.rows, cols: data.cols, offlineSolveGrid: null };
      }
    } catch {

    }
  }
  const puzzle = popOfflinePuzzle();
  return puzzle ? { rows: puzzle.rows, cols: puzzle.cols, offlineSolveGrid: puzzle.solveGrid } : null;
}

async function validatePlayer(pid, r, c) {
  if (g.offlineSolveGrid) {
    const players = g.offlineSolveGrid[r]?.[c]?.players || [];
    return players.some(p => p.id === pid);
  }
  const resp = await fetch('/api/game/validate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ player_id: pid, row_id: g.rows[r].id, col_id: g.cols[c].id }),
  });
  const data = await resp.json();
  return data.valid;
}

function urlForScreen(name) {
  switch (name) {
    case 'setup': return `/setup/${g.pendingMode}`;
    case 'online-lobby': return g.onlineCode ? `/online/${g.onlineCode}` : '/online';
    case 'daily-done': return '/daily';
    case 'editor': return '/editor';
    case 'board':
      if (g.mode === 'online') return `/online/${g.onlineCode}`;
      if (g.mode === 'solo' && g.soloVariant === 'daily') return '/daily';
      if (g.mode === 'solo' && g.soloVariant === 'custom') return `/solo/${g.soloGridCode}`;
      if (g.mode === 'solo') return '/solo';
      if (g.mode === 'local') return '/local';
      return '/board';
    case 'mode-select': default: return '/';
  }
}

function parseLocation() {
  const path = location.pathname;
  let m;
  if ((m = path.match(/^\/setup\/(solo|local|online-host)\/?$/))) return { screen: 'setup', mode: m[1] };
  if (/^\/editor\/?$/.test(path)) return { screen: 'editor' };
  if (/^\/daily\/?$/.test(path)) return { screen: 'daily' };
  if (/^\/local\/?$/.test(path)) return { screen: 'local' };
  if ((m = path.match(/^\/solo\/([A-Za-z0-9]+)\/?$/))) return { screen: 'solo-custom', code: m[1] };
  if (/^\/solo\/?$/.test(path)) return { screen: 'solo' };
  if ((m = path.match(/^\/online\/([A-Za-z0-9]+)\/?$/))) return { screen: 'online', code: m[1] };
  if (/^\/online\/?$/.test(path)) return { screen: 'online' };
  return { screen: 'mode-select' };
}

function renderScreenDom(name) {
  document.getElementById('screen-mode-select').classList.toggle('hidden', name !== 'mode-select');
  document.getElementById('screen-setup').classList.toggle('hidden', name !== 'setup');
  document.getElementById('screen-online-lobby').classList.toggle('hidden', name !== 'online-lobby');
  document.getElementById('screen-daily-done').classList.toggle('hidden', name !== 'daily-done');
  document.getElementById('screen-editor').classList.toggle('hidden', name !== 'editor');
  document.getElementById('screen-board').classList.toggle('hidden', name !== 'board');
  closeMenuDropdown();

  if (name !== 'online-lobby') closeLobbyListEvents();
}

function showScreen(name, { push = true } = {}) {
  renderScreenDom(name);
  const url = urlForScreen(name);
  const state = { screen: name };
  if (push) history.pushState(state, '', url);
  else history.replaceState(state, '', url);
}

function enterFromPath(parsed) {
  switch (parsed.screen) {
    case 'setup': enterSetupScreen(parsed.mode, { push: false }); break;
    case 'editor': goToEditor({ push: false }); break;
    case 'daily': startDaily({ push: false }); break;
    case 'online':
      g.mode = 'online';
      renderScreenDom('online-lobby');
      updateModeChrome();

      history.replaceState({ screen: 'online-lobby' }, '', parsed.code ? `/online/${parsed.code}` : '/online');
      if (parsed.code) attemptOnlineResume(parsed.code);
      else renderLobbyHome();
      break;
    case 'solo-custom': loadAndStartCustomGrid(parsed.code, undefined, undefined, { push: false }); break;
    case 'solo':
      if (!tryResumeRound({ mode: 'solo', soloVariant: null })) enterSetupScreen('solo', { push: false });
      break;
    case 'local':
      if (!tryResumeRound({ mode: 'local' })) enterSetupScreen('local', { push: false });
      break;
    default: showScreen('mode-select', { push: false });
  }
}

window.addEventListener('popstate', e => {
  if (e.state?.screen) {
    renderScreenDom(e.state.screen);
    return;
  }

  enterFromPath(parseLocation());
});

function updateModeChrome() {
  resetGiveUpConfirm();
}

let giveUpConfirming = false;

function resetGiveUpConfirm() {
  const btn = document.getElementById('btn-give-up');
  giveUpConfirming = false;
  btn.textContent = 'Aufgeben';
  btn.classList.remove('tt-btn-accent-outline');
  btn.classList.add('tt-btn-accent');
}

function setLeague(value) {
  selectedLeague = value;
  document.querySelectorAll('.league-btn').forEach(btn => {
    btn.classList.toggle('is-active', btn.dataset.league === value);
  });
}

document.querySelectorAll('.league-btn').forEach(btn => {
  btn.addEventListener('click', () => setLeague(btn.dataset.league));
});

function setVisibility(value) {
  onlineVisibility = value;
  document.querySelectorAll('.visibility-btn').forEach(btn => {
    btn.classList.toggle('is-active', btn.dataset.visibility === value);
  });
}

document.querySelectorAll('.visibility-btn').forEach(btn => {
  btn.addEventListener('click', () => setVisibility(btn.dataset.visibility));
});

function setRetakeMode(value) {
  retakeMode = value;
  document.querySelectorAll('.retake-btn').forEach(btn => {
    btn.classList.toggle('is-active', btn.dataset.retake === (value ? '1' : '0'));
  });
}

document.querySelectorAll('.retake-btn').forEach(btn => {
  btn.addEventListener('click', () => setRetakeMode(btn.dataset.retake === '1'));
});

document.querySelectorAll('[data-mode]').forEach(btn => {
  btn.addEventListener('click', () => selectMode(btn.dataset.mode));
});

function enterSetupScreen(pendingMode, { push = true } = {}) {
  g.pendingMode = pendingMode;
  document.getElementById('btn-setup-continue').disabled = false;

  document.getElementById('setup-load-grid').classList.toggle('hidden', pendingMode !== 'solo');
  document.getElementById('setup-load-error').classList.add('hidden');
  document.getElementById('setup-load-code').value = '';

  document.getElementById('setup-visibility-picker').classList.toggle('hidden', pendingMode !== 'online-host');

  document.getElementById('setup-retake-picker').classList.toggle('hidden', pendingMode !== 'local');

  document.getElementById('setup-offline-pool').classList.toggle('hidden', pendingMode === 'online-host');
  updateOfflinePoolCount();
  showScreen('setup', { push });
}

function selectMode(mode) {
  if (mode === 'online') {
    g.mode = 'online';
    showScreen('online-lobby');
    updateModeChrome();
    renderLobbyHome();
    return;
  }
  enterSetupScreen(mode);
}

document.getElementById('btn-setup-back').addEventListener('click', () => {
  if (g.pendingMode === 'online-host') {
    g.mode = 'online';
    showScreen('online-lobby');
    renderLobbyHome();
  } else {
    showScreen('mode-select');
  }
});
document.getElementById('btn-setup-continue').addEventListener('click', e => {
  const mode = g.pendingMode;
  if (mode === 'solo') { startSolo(); return; }
  if (mode === 'local') { startLocal(); return; }
  if (mode === 'online-host') {

    const btn = e.currentTarget;
    if (btn.disabled) return;
    btn.disabled = true;
    createOnlineRoom().finally(() => { btn.disabled = false; });
  }
});

const ONLINE_SESSION_KEY = 'ttt_online_session';

function saveOnlineSession() {
  if (!g.onlineCode || !g.onlineToken) return;
  sessionStorage.setItem(ONLINE_SESSION_KEY, JSON.stringify({
    code: g.onlineCode, token: g.onlineToken, slot: g.onlineSlot,
  }));
}

function clearOnlineSession() {
  sessionStorage.removeItem(ONLINE_SESSION_KEY);
}

const ROUND_SESSION_KEY = 'ttt_round_session';

function saveRoundSession() {
  if (g.mode !== 'solo' && g.mode !== 'local') return;
  sessionStorage.setItem(ROUND_SESSION_KEY, JSON.stringify({
    mode: g.mode, soloVariant: g.soloVariant, soloGridCode: g.soloGridCode, dailyDate: g.dailyDate,
    rows: g.rows, cols: g.cols, board: g.board, current: g.current,
    usedIds: [...g.usedIds], streak: g.streak, elapsedSeconds: g.elapsedSeconds,
    soloAttempted: g.soloAttempted, soloCorrect: g.soloCorrect,
    retakeMode: g.retakeMode, phase: g.phase, pendingThreat: g.pendingThreat,
    offlineSolveGrid: g.offlineSolveGrid,
  }));
}

function clearRoundSession() {
  sessionStorage.removeItem(ROUND_SESSION_KEY);
}

function tryResumeRound(match) {
  let saved = null;
  try { saved = JSON.parse(sessionStorage.getItem(ROUND_SESSION_KEY) || 'null'); } catch {   }
  if (!saved || saved.mode !== match.mode) return false;
  if ((saved.soloVariant || null) !== (match.soloVariant || null)) return false;
  if (match.soloVariant === 'custom' && saved.soloGridCode !== match.gridCode) return false;
  if (match.soloVariant === 'daily' && saved.dailyDate !== match.dailyDate) return false;

  Object.assign(g, {
    mode: saved.mode, soloVariant: saved.soloVariant, soloGridCode: saved.soloGridCode, dailyDate: saved.dailyDate,
    rows: saved.rows, cols: saved.cols, board: saved.board, current: saved.current,
    winner: null, winCells: [], usedIds: new Set(saved.usedIds || []),
    streak: saved.streak || { 1: 0, 2: 0 }, elapsedSeconds: saved.elapsedSeconds || 0,
    soloAttempted: saved.soloAttempted || 0, soloCorrect: saved.soloCorrect || 0, solution: null,
    retakeMode: saved.retakeMode || false, phase: saved.phase || 'fill', pendingThreat: saved.pendingThreat || null,
    offlineSolveGrid: saved.offlineSolveGrid || null,
  });
  showScreen('board', { push: false });
  updateModeChrome();
  hideEndBanner();
  document.getElementById('btn-give-up').disabled = false;
  renderBoard();
  updateStatus();
  startTimer();
  return true;
}

function goToMenu() {
  stopTimer();
  if (g.mode === 'online' && g.onlineCode && !g.winner) {
    fetch(`/api/multiplayer/rooms/${g.onlineCode}/forfeit`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: g.onlineToken }),
    }).catch(() => {});
  }
  if (g.onlineEventSource) { g.onlineEventSource.close(); g.onlineEventSource = null; }
  clearOnlineSession();
  clearRoundSession();
  Object.assign(g, { mode: null, onlineCode: null, onlineToken: null, onlineSlot: null, onlineBoardEntered: false, onlineFinished: false, onlineLastWrongGuessVersion: undefined });
  showScreen('mode-select');
}
document.getElementById('btn-logo').addEventListener('click', goToMenu);

function closeMenuDropdown() {
  document.getElementById('menu-dropdown').classList.add('hidden');
  document.getElementById('btn-menu-toggle').classList.remove('is-active');
}
document.getElementById('btn-menu-toggle').addEventListener('click', e => {
  e.stopPropagation();
  const open = document.getElementById('menu-dropdown').classList.toggle('hidden') === false;
  e.currentTarget.classList.toggle('is-active', open);
});
document.addEventListener('click', e => {
  const dropdown = document.getElementById('menu-dropdown');
  if (!dropdown.classList.contains('hidden') && !dropdown.contains(e.target) && e.target.id !== 'btn-menu-toggle') {
    closeMenuDropdown();
  }
});

window.addEventListener('pagehide', () => {
  if (g.mode === 'online' && g.onlineCode && !g.winner) {
    const body = new Blob([JSON.stringify({ token: g.onlineToken })], { type: 'application/json' });
    navigator.sendBeacon?.(`/api/multiplayer/rooms/${g.onlineCode}/forfeit`, body);
  }
});

function shrinkFontToFit(el, axis, min, step = 0.5) {
  el.style.fontSize = '';
  let size = parseFloat(getComputedStyle(el).fontSize);
  const overflows = axis === 'width'
    ? () => el.scrollWidth > el.clientWidth + 0.5
    : () => el.scrollHeight > el.clientHeight + 0.5;
  while (overflows() && size > min) {
    size -= step;
    el.style.fontSize = size + 'px';
  }
}

function fitBoardText(root) {
  root.querySelectorAll('.tt-cell-name').forEach(el => shrinkFontToFit(el, 'width', 8));
  root.querySelectorAll('.tt-cat-label').forEach(el => shrinkFontToFit(el, 'height', 7));
}

function renderBoard() {
  const board = document.getElementById('board');
  const cells = [];

  cells.push(`<div class="tt-slot"></div>`);
  g.cols.forEach(cat => cells.push(headerCellHtml(cat)));
  g.rows.forEach((rowCat, r) => {
    cells.push(headerCellHtml(rowCat));
    g.cols.forEach((_, c) => cells.push(cellHtml(r, c)));
  });

  board.innerHTML = cells.join('');
  board.querySelectorAll('[data-cell]').forEach(el => {
    el.addEventListener('click', () => {
      const [r, c] = el.dataset.cell.split(',').map(Number);
      handleCellClick(r, c);
    });
  });
  fitBoardText(board);
}

function isRetakeTarget(r, c) {
  const entry = g.board[r][c];
  return !g.winner && g.mode === 'local' && g.phase === 'retake' && !!entry && entry.player !== g.current;
}

function handleCellClick(r, c) {
  if (g.board[r][c] && !isRetakeTarget(r, c)) return;
  if (g.winner !== null) {
    if (g.solution) openSolutionSheet(r, c);
    return;
  }
  openCell(r, c);
}

function lastName(name) {
  const parts = (name || '').trim().split(/\s+/);
  return parts[parts.length - 1] || name || '';
}

function formatPlayerName(name) {
  const parts = (name || '').trim().split(/\s+/);
  if (parts.length < 2) return name || '';
  const ln = parts[parts.length - 1];
  const collisions = {};
  g.board.forEach(row => row.forEach(entry => {
    if (entry && entry.name) {
      const otherLn = lastName(entry.name);
      collisions[otherLn] = (collisions[otherLn] || 0) + 1;
    }
  }));
  return collisions[ln] > 1 ? `${parts[0][0]}. ${ln}` : ln;
}

function categoryIconHtml(cat) {

  if (cat.icon_image) {

    const jsStr = s => `'${String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'")}'`;
    const onerror = `iconImgFallback(this, ${jsStr(cat.icon_letter || '')}, ${jsStr(cat.icon_color || '')})`;
    return `<img src="${esc(cat.icon_image)}" alt="" class="tt-icon tt-icon-img flex-shrink-0" onerror="${esc(onerror)}">`;
  }

  if (!cat.icon && cat.icon_letter) {
    return `<div class="tt-icon rounded-full flex items-center justify-center text-white font-black text-sm flex-shrink-0"
      style="background:${esc(cat.icon_color || 'var(--card-border)')}">${esc(cat.icon_letter)}</div>`;
  }

  if (cat.icon && ICON_PATHS[cat.icon]) {

    return `<div class="tt-icon-mono tt-icon flex-shrink-0 flex items-center justify-center">${svgIcon(cat.icon, '100%')}</div>`;
  }

  if (cat.icon) {
    return `<div class="tt-icon-mono tt-icon leading-none flex-shrink-0 flex items-center justify-center"
      style="font-size:clamp(18px,6vw,26px)">${esc(cat.icon)}</div>`;
  }
  return `<div class="tt-icon-mono tt-icon flex-shrink-0 flex items-center justify-center">${svgIcon('ball', '100%')}</div>`;
}

function iconImgFallback(img, letter, color) {
  const div = document.createElement('div');
  if (letter) {
    div.className = 'tt-icon rounded-full flex items-center justify-center text-white font-black text-sm flex-shrink-0';
    div.style.background = color || 'var(--card-border)';
    div.textContent = letter;
  } else {
    div.className = 'tt-icon-mono tt-icon flex-shrink-0 flex items-center justify-center';
    div.innerHTML = svgIcon('ball', '100%');
  }
  img.replaceWith(div);
}

function headerCellHtml(cat) {

  return `
    <div class="tt-cell flex flex-col items-center justify-center p-3 tt-slot overflow-hidden gap-1"
         title="${esc(cat.label)}">
      ${categoryIconHtml(cat)}
      <div class="tt-cat-label font-semibold text-center leading-snug" style="color:var(--text-dim)">
        ${esc(cat.label)}
      </div>
    </div>`;
}

function cellHtml(r, c) {
  const entry = g.board[r][c];
  const isWin = g.winCells.some(([wr, wc]) => wr === r && wc === c);
  const gone  = g.winner !== null;

  if (entry && entry.status === 'missed') {
    return `
      <div class="tt-cell flex flex-col items-center justify-center p-2.5 tt-slot">
        <div class="text-2xl mb-1" style="color:var(--text-dim)">✕</div>
        <div class="tt-label">Falsch</div>
      </div>`;
  }

  if (entry) {

    if (g.mode === 'solo') {

      return `
        <div class="tt-cell ${isWin ? 'is-win' : ''} flex flex-col items-center justify-center p-3 tt-slot relative"
             data-cell="${r},${c}">
          <div class="absolute top-1.5 right-1.5">
            <span class="text-xs font-black w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style="border:1.5px solid var(--accent);color:var(--accent)">✓</span>
          </div>
          <div class="tt-cell-name text-center" style="color:var(--text)">${esc(formatPlayerName(entry.name))}</div>
        </div>`;
    }

    const color = playerColor(entry.player);
    const bg = entry.player === 1 ? 'var(--accent-cell-bg)' : 'var(--o-cell-bg)';
    const markPath = entry.player === 1 ? ICON_PATHS.x : ICON_PATHS.o;

    const isThreatened = g.pendingThreat?.lines.some(line => line.some(([tr, tc]) => tr === r && tc === c));
    const retakeable = isRetakeTarget(r, c);
    return `
      <div class="tt-cell ${isWin ? 'is-win' : ''} ${isThreatened ? 'is-threat' : ''} ${retakeable ? 'is-retake-target' : ''} flex flex-col items-center justify-center p-3 tt-slot relative"
           data-cell="${r},${c}" style="background:${bg};border-color:${color};">
        <svg class="absolute pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"
             style="top:50%;left:50%;transform:translate(-50%,-50%);width:clamp(60px,20vw,90px);height:clamp(60px,20vw,90px);opacity:.6;">${markPath}</svg>
        <div class="tt-cell-name text-center relative" style="color:var(--text)">${esc(formatPlayerName(entry.name))}</div>
      </div>`;
  }

  if (gone && g.solution) {

    const cellSol = g.solution[r][c];
    const count = cellSol.count || 0;
    const first = cellSol.players?.[0] ? esc(formatPlayerName(cellSol.players[0].name)) : '';
    const more = count - 1;

    return `
      <button data-cell="${r},${c}" class="tt-cell tt-card-hover flex flex-col items-center justify-center p-3 tt-slot text-center">
        <div class="tt-cell-name" style="color:var(--text-dim)">${count === 0 ? '–' : first}</div>
        ${more > 0 ? `<div class="text-xs mt-0.5" style="color:var(--text-faint)">+${more} weitere</div>` : ''}
      </button>`;
  }

  const notYourTurn = g.mode === 'online' && g.onlineSlot && g.current !== g.onlineSlot;
  const disabled = gone || notYourTurn;

  const isActive = !disabled && g.activeCell && g.activeCell.r === r && g.activeCell.c === c;
  return `
    <button ${disabled ? 'disabled' : ''} data-cell="${r},${c}"
      class="tt-cell ${isActive ? 'is-active' : ''} flex flex-col items-center justify-center px-2 py-2 tt-slot w-full">
      ${shirtSvg()}
      <span class="tt-label mt-1">Spieler wählen</span>
    </button>`;
}

function refreshCell(r, c) {
  const board = document.getElementById('board');
  const idx = 1 + 3 + r * 4 + 1 + c;
  const existing = board.children[idx];
  if (!existing) return;
  const tmp = document.createElement('div');
  tmp.innerHTML = cellHtml(r, c);
  const newEl = tmp.firstElementChild;
  existing.replaceWith(newEl);
  fitBoardText(newEl);

  newEl.addEventListener('click', () => handleCellClick(r, c));
}

function refreshFilledCells() {
  g.board.forEach((row, r) => row.forEach((entry, c) => {
    if (entry && entry.status !== 'missed') refreshCell(r, c);
  }));
}

async function revealSolutions() {
  if (!g.rows.length || !g.cols.length) return;

  if (g.offlineSolveGrid) {
    g.solution = g.offlineSolveGrid;
    g.rows.forEach((_, r) => g.cols.forEach((__, c) => { if (!g.board[r][c]) refreshCell(r, c); }));
    return;
  }
  const params = g.mode === 'online'
    ? `code=${encodeURIComponent(g.onlineCode)}&token=${encodeURIComponent(g.onlineToken)}`
    : `rows=${g.rows.map(c => c.id).join(',')}&cols=${g.cols.map(c => c.id).join(',')}`;
  try {
    const resp = await fetch(`/api/game/solve?${params}`);
    if (!resp.ok) return;
    const data = await resp.json();
    g.solution = data.grid;
    g.rows.forEach((_, r) => g.cols.forEach((__, c) => { if (!g.board[r][c]) refreshCell(r, c); }));
  } catch {

  }
}

function openSolutionSheet(r, c) {
  const cellSol = g.solution?.[r]?.[c];
  if (!cellSol) return;
  document.getElementById('solution-modal-title').textContent = `${g.rows[r].label} × ${g.cols[c].label}`;
  const names = (cellSol.players || []).map(p => esc(p.name));
  document.getElementById('solution-modal-body').innerHTML = names.length
    ? names.map(n => `<div class="tt-row-hover rounded-lg px-3 py-2.5 text-sm" style="color:var(--text)">${n}</div>`).join('')
    : `<p class="text-xs text-center py-2" style="color:var(--text-faint)">Keine Spieler gefunden</p>`;
  document.getElementById('solution-modal').classList.remove('hidden');
}

function closeSolutionSheet() {
  document.getElementById('solution-modal').classList.add('hidden');
}
document.getElementById('solution-modal-close').addEventListener('click', closeSolutionSheet);
document.getElementById('solution-modal').addEventListener('click', e => {
  if (e.target.id === 'solution-modal') closeSolutionSheet();
});

function markActiveCell(r, c) {

  document.querySelectorAll('#board .is-active').forEach(el => el.classList.remove('is-active'));
  document.querySelector(`[data-cell="${r},${c}"]`)?.classList.add('is-active');
}

function clearActiveCell() {
  document.querySelectorAll('#board .is-active').forEach(el => el.classList.remove('is-active'));
}

function openCell(r, c) {
  if (g.winner) return;
  if (g.board[r][c] && !isRetakeTarget(r, c)) return;
  if (g.mode === 'online' && g.onlineSlot && g.current !== g.onlineSlot) return;
  g.activeCell = { r, c };
  markActiveCell(r, c);
  document.getElementById('modal-title').textContent = `${g.rows[r].label} × ${g.cols[c].label}`;
  document.getElementById('search-input').value = '';
  document.getElementById('search-results').innerHTML = '';
  document.getElementById('search-hint').textContent = 'Mindestens 3 Buchstaben eingeben';
  document.getElementById('search-error').classList.add('hidden');
  document.getElementById('modal').classList.remove('hidden');
  document.getElementById('search-input').focus();
}

function closeModal() {
  document.getElementById('modal').classList.add('hidden');
  clearActiveCell();
  g.activeCell = null;
}

let searchTimer = null;
document.getElementById('search-input').addEventListener('input', e => {
  clearTimeout(searchTimer);
  const q = e.target.value.trim();
  document.getElementById('search-error').classList.add('hidden');
  if (q.length < 3) {
    document.getElementById('search-results').innerHTML = '';
    document.getElementById('search-hint').textContent = 'Mindestens 3 Buchstaben eingeben';
    return;
  }
  document.getElementById('search-hint').textContent = '';
  searchTimer = setTimeout(() => doSearch(q), 280);
});

function normalizeText(s) {
  return (s || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function offlineSearchPlayers(q) {
  if (!g.offlineSolveGrid) return [];
  const seen = new Map();
  g.offlineSolveGrid.forEach(row => row.forEach(cell => {
    (cell.players || []).forEach(p => { if (!seen.has(p.id)) seen.set(p.id, p); });
  }));
  const queryNorm = normalizeText(q).trim();
  const words = queryNorm.split(/\s+/).filter(Boolean);
  return [...seen.values()]
    .filter(p => {
      const nameNorm = normalizeText(p.name);
      return words.every(w => nameNorm.includes(w));
    })
    .map(p => {
      const nameNorm = normalizeText(p.name);
      const nameWords = nameNorm.split(/\s+/);
      let tier;
      if (nameNorm === queryNorm || nameWords.includes(queryNorm)) tier = 0;
      else if (nameNorm.startsWith(queryNorm) || nameWords.some(w => w.startsWith(queryNorm))) tier = 1;
      else tier = 2;
      return { p, tier };
    })
    .sort((a, b) => a.tier - b.tier || a.p.name.localeCompare(b.p.name))
    .map(x => x.p);
}

function renderSearchResults(players) {
  const container = document.getElementById('search-results');
  if (!players.length) {
    container.innerHTML = `<p class="text-xs text-center py-2" style="color:var(--text-faint)">Keine Spieler gefunden</p>`;
    return;
  }

  const nameCounts = {};
  players.forEach(p => { nameCounts[p.name] = (nameCounts[p.name] || 0) + 1; });

  container.innerHTML = players.map(p => {
    const used = g.usedIds.has(p.id);
    const isDup = nameCounts[p.name] > 1;
    return `
      <div class="tt-row-hover flex items-center justify-between rounded-lg px-3 py-2 text-sm ${used ? 'is-disabled' : 'cursor-pointer'}"
           style="color:var(--text)"
           data-pid="${p.id}" data-name="${esc(p.name)}" data-club="${esc(p.current_club_name || '')}">
        <div class="min-w-0">
          <span class="font-semibold">${esc(p.name)}</span>
          ${isDup && p.age
            ? `<span class="text-xs ml-1" style="color:var(--text-dim)">${p.age} Jahre</span>`
            : ''}
        </div>
        ${used ? '<span class="text-xs ml-2 flex-shrink-0" style="color:var(--text-faint)">bereits gespielt</span>' : ''}
      </div>`;
  }).join('');

  container.querySelectorAll('[data-pid]').forEach(el => {
    const pid  = parseInt(el.dataset.pid);
    const name = el.dataset.name;
    const club = el.dataset.club;
    if (g.usedIds.has(pid)) return;
    el.addEventListener('click', () => selectPlayer(pid, name, club));
  });
}

async function doSearch(q) {
  if (!g.activeCell) return;
  if (g.offlineSolveGrid) {
    renderSearchResults(offlineSearchPlayers(q));
    return;
  }
  const resp = await fetch(`/api/game/search?q=${encodeURIComponent(q)}`);
  const data = await resp.json();
  renderSearchResults(data.players || []);
}

async function selectPlayer(pid, name, club) {
  if (g.usedIds.has(pid) || !g.activeCell) return;
  const { r, c } = g.activeCell;
  if (g.mode === 'solo') return soloSelectPlayer(pid, name, club, r, c);
  if (g.mode === 'online') return onlineSelectPlayer(pid, name, club, r, c);
  return localSelectPlayer(pid, name, club, r, c);
}

function updateStatus() {
  updateStreakDisplay();
  if (g.winner) return;
  if (g.mode === 'solo') {

    document.getElementById('status-text').innerHTML =
      `<span style="color:var(--accent)">${g.soloCorrect}</span> / 9`;
    return;
  }
  if (g.mode === 'online') {
    const yourTurn = g.current === g.onlineSlot;
    document.getElementById('status-text').innerHTML = yourTurn
      ? `<span style="color:var(--accent)">Du bist dran</span>`
      : `<span style="color:var(--text-dim)">Gegner ist dran…</span>`;
    return;
  }

  const sym = g.current === 1 ? 'X' : 'O';

  if (g.pendingThreat) {
    const threatSym = g.pendingThreat.owner === 1 ? 'X' : 'O';
    document.getElementById('status-text').innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px;color:${playerColor(g.current)}">
      ⚠️ ${threatSym} gewinnt gleich – ${sym} muss jetzt kontern!
    </span>`;
    return;
  }
  document.getElementById('status-text').innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px;">
    <span style="width:8px;height:8px;border-radius:50%;background:${playerColor(g.current)};flex-shrink:0;display:inline-block"></span>
    ${sym} ist dran${g.phase === 'retake' ? ' – Feld zurückerobern' : ''}
  </span>`;
}

function setStatus(msg) {
  document.getElementById('status-text').textContent = msg;
}

function setStatusLoading(msg) {
  document.getElementById('status-text').innerHTML =
    `<span style="display:inline-flex;align-items:center;gap:8px;"><span class="tt-spinner"></span>${msg}</span>`;
}

let onlineFlashTimer = null;
function flashOnlineMessage(text, duration = 1800) {
  document.getElementById('status-text').textContent = text;
  clearTimeout(onlineFlashTimer);
  onlineFlashTimer = setTimeout(() => { if (g.mode === 'online' && !g.winner) updateStatus(); }, duration);
}

function updateStreakDisplay() {
  const el = document.getElementById('streak-display');
  if (g.mode !== 'local') { el.classList.add('hidden'); el.classList.remove('flex'); return; }
  const s = g.streak[g.current] || 0;
  if (s >= 2 && !g.winner) {
    el.classList.remove('hidden');
    el.classList.add('flex');
    el.innerHTML = iconText('fire', s, { size: 14, gap: 4 });
  } else {
    el.classList.add('hidden');
    el.classList.remove('flex');
  }
}

function showEndBanner(icon, title, showReplay = true) {
  document.getElementById('status-text').innerHTML = iconText(icon, title);

  const replayBtn = document.getElementById('end-new-game');
  replayBtn.classList.toggle('hidden', !showReplay);
  replayBtn.disabled = false;
  replayBtn.innerHTML = g.mode === 'online' ? iconText('rematch', 'Revanche', { size: 14 }) : 'Nochmal spielen';

  document.getElementById('end-share').classList.add('hidden');

  document.getElementById('btn-give-up').classList.add('hidden');
  document.getElementById('end-actions').classList.remove('hidden');
  document.getElementById('end-actions').classList.add('flex');
}

function hideEndBanner() {
  document.getElementById('end-actions').classList.add('hidden');
  document.getElementById('end-actions').classList.remove('flex');
  document.getElementById('btn-give-up').classList.remove('hidden');
}

document.getElementById('end-new-game').addEventListener('click', () => {
  if (g.mode === 'solo' && g.soloVariant === 'custom') {

    hideEndBanner();
    beginSoloRound();
    finishSoloRoundSetup(g.rows, g.cols);
  } else if (g.mode === 'solo') {
    hideEndBanner();
    newSoloRound();
  } else if (g.mode === 'local') { hideEndBanner(); newLocalRound(); }
  else if (g.mode === 'online') rematchOnline();
});
document.getElementById('end-menu').addEventListener('click', () => {
  hideEndBanner();
  goToMenu();
});

let timerInterval = null;

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function startTimer() {
  stopTimer();
  timerInterval = setInterval(() => {
    g.elapsedSeconds++;
    updateTimerDisplay();
  }, 1000);
}

function stopTimer() {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = null;
}

function updateTimerDisplay() {
  document.getElementById('timer-display').textContent = formatTime(g.elapsedSeconds);
}

const WIN_LINES = [
  [[0,0],[0,1],[0,2]], [[1,0],[1,1],[1,2]], [[2,0],[2,1],[2,2]],
  [[0,0],[1,0],[2,0]], [[0,1],[1,1],[2,1]], [[0,2],[1,2],[2,2]],
  [[0,0],[1,1],[2,2]], [[0,2],[1,1],[2,0]],
];

async function startLocal() {
  g.mode = 'local';
  showScreen('board');
  updateModeChrome();
  await newLocalRound();
}

async function newLocalRound() {
  setStatusLoading('Grid wird geladen…');
  stopTimer();
  hideEndBanner();
  document.getElementById('board').innerHTML = '';
  document.getElementById('btn-give-up').disabled = false;

  Object.assign(g, {
    rows: [], cols: [],
    board: [[null,null,null],[null,null,null],[null,null,null]],
    current: 1, winner: null, usedIds: new Set(), activeCell: null, winCells: [],
    streak: { 1: 0, 2: 0 }, elapsedSeconds: 0, solution: null,
    retakeMode, phase: 'fill', pendingThreat: null, offlineSolveGrid: null,
  });
  updateStreakDisplay();
  updateTimerDisplay();

  const loaded = await loadRowsAndCols();
  if (!loaded) {
    setStatus('Kein Grid gefunden – keine Verbindung und keine Offline-Grids übrig.');
    return;
  }
  g.rows = loaded.rows;
  g.cols = loaded.cols;
  g.offlineSolveGrid = loaded.offlineSolveGrid;

  renderBoard();
  updateStatus();
  startTimer();
  saveRoundSession();
  if (g.offlineSolveGrid) flashStatus(`Offline-Grid geladen · noch ${loadOfflinePool().length} übrig`);
}

function checkWinnerLocal() {
  for (const line of WIN_LINES) {
    const vals = line.map(([r, c]) => g.board[r][c]?.player);
    if (vals[0] && vals[0] === vals[1] && vals[1] === vals[2]) {
      g.winner = vals[0];
      g.winCells = line;
      return;
    }
  }
  if (g.board.flat().every(c => c !== null)) {
    if (g.retakeMode) g.phase = 'retake';
    else g.winner = 'draw';
  }
}

function placeLocal(r, c, playerId, name, club) {
  g.board[r][c] = { status: 'correct', player: g.current, id: playerId, name, club };
  g.usedIds.add(playerId);

  g.streak[g.current]++;
  stats.local.correct++;
  if (g.streak[g.current] > stats.local.bestStreak) stats.local.bestStreak = g.streak[g.current];
  saveStats();

  checkWinnerLocal();

  if (g.winner) { refreshFilledCells(); endGameLocal(); return; }
  g.current = g.current === 1 ? 2 : 1;
  refreshFilledCells();
  updateStatus();
  saveRoundSession();
}

function linesFullyOwnedBy(player) {
  return WIN_LINES.filter(line => line.every(([r, c]) => g.board[r][c]?.player === player));
}

function checkPendingThreatOutcome() {
  if (!g.pendingThreat) return false;
  const stillIntact = g.pendingThreat.lines.some(line =>
    line.every(([r, c]) => g.board[r][c]?.player === g.pendingThreat.owner)
  );
  if (stillIntact) {
    g.winner = g.pendingThreat.owner;
    g.winCells = g.pendingThreat.lines.flat();
    g.pendingThreat = null;
    return true;
  }
  g.pendingThreat = null;
  return false;
}

function retakeLocal(r, c, playerId, name, club) {
  const previous = g.board[r][c];
  g.usedIds.delete(previous.id);
  g.board[r][c] = { status: 'correct', player: g.current, id: playerId, name, club };
  g.usedIds.add(playerId);

  g.streak[g.current]++;
  stats.local.correct++;
  if (g.streak[g.current] > stats.local.bestStreak) stats.local.bestStreak = g.streak[g.current];
  saveStats();

  if (!checkPendingThreatOutcome()) {
    const newLines = linesFullyOwnedBy(g.current);
    g.pendingThreat = newLines.length ? { owner: g.current, lines: newLines } : null;
  }

  if (g.winner) { refreshFilledCells(); endGameLocal(); return; }
  g.current = g.current === 1 ? 2 : 1;
  refreshFilledCells();
  updateStatus();
  saveRoundSession();
}

async function localSelectPlayer(pid, name, club, r, c) {
  const valid = await validatePlayer(pid, r, c);
  if (valid) {
    closeModal();
    if (g.phase === 'retake') retakeLocal(r, c, pid, name, club);
    else placeLocal(r, c, pid, name, club);
  } else {
    stats.local.wrong++;
    g.streak[g.current] = 0;
    saveStats();
    const err = document.getElementById('search-error');
    err.textContent = `${name} passt hier nicht – nächster Spieler ist dran!`;
    err.classList.remove('hidden');
    setTimeout(() => {
      closeModal();

      if (checkPendingThreatOutcome()) { endGameLocal(); return; }
      g.current = g.current === 1 ? 2 : 1;

      if (g.phase === 'retake') refreshFilledCells();
      updateStatus();
      saveRoundSession();
    }, 1500);
  }
}

async function endGameLocal() {
  stopTimer();
  clearRoundSession();

  setStatus('Runde beendet.');
  document.getElementById('btn-give-up').disabled = true;
  g.rows.forEach((_, r) => g.cols.forEach((__, c) => refreshCell(r, c)));

  stats.local.gamesPlayed++;
  const timeStr = formatTime(g.elapsedSeconds);

  if (g.winner === 'draw') {
    stats.local.draws++;
    saveStats();
    showEndBanner('handshake', 'Unentschieden!');
  } else {
    stats.local.wins[g.winner] = (stats.local.wins[g.winner] || 0) + 1;
    if (stats.local.fastestWinSeconds == null || g.elapsedSeconds < stats.local.fastestWinSeconds) {
      stats.local.fastestWinSeconds = g.elapsedSeconds;
    }
    saveStats();
    const winnerSym = g.winner === 1 ? 'X' : 'O';
    showEndBanner('trophy', `${winnerSym} gewinnt!`);
  }
  await revealSolutions();
}

async function startSolo() {
  g.mode = 'solo';
  g.soloVariant = null;
  showScreen('board');
  updateModeChrome();
  await newSoloRound();
}

function beginSoloRound() {
  setStatusLoading('Grid wird geladen…');
  stopTimer();
  hideEndBanner();
  document.getElementById('board').innerHTML = '';
  document.getElementById('btn-give-up').disabled = false;
}

function finishSoloRoundSetup(rows, cols) {
  Object.assign(g, {
    rows, cols,
    board: [[null,null,null],[null,null,null],[null,null,null]],
    current: 1, winner: null, usedIds: new Set(), activeCell: null, winCells: [],
    elapsedSeconds: 0, solution: null, soloAttempted: 0, soloCorrect: 0,

    offlineSolveGrid: null,
  });
  updateTimerDisplay();
  renderBoard();
  updateStatus();
  startTimer();
  saveRoundSession();
}

async function newSoloRound() {
  g.soloVariant = null;
  beginSoloRound();
  const loaded = await loadRowsAndCols();
  if (!loaded) {
    setStatus('Kein Grid gefunden – keine Verbindung und keine Offline-Grids übrig.');
    return;
  }
  finishSoloRoundSetup(loaded.rows, loaded.cols);
  g.offlineSolveGrid = loaded.offlineSolveGrid;
  if (g.offlineSolveGrid) flashStatus(`Offline-Grid geladen · noch ${loadOfflinePool().length} übrig`);
}

async function soloSelectPlayer(pid, name, club, r, c) {
  const valid = await validatePlayer(pid, r, c);
  closeModal();
  g.usedIds.add(pid);
  g.soloAttempted++;
  if (valid) {
    g.board[r][c] = { status: 'correct', player: 1, id: pid, name, club };
    g.soloCorrect++;
    stats.solo.streak++;
    if (stats.solo.streak > stats.solo.bestStreak) stats.solo.bestStreak = stats.solo.streak;
    refreshFilledCells();
  } else {
    g.board[r][c] = { status: 'missed' };
    stats.solo.streak = 0;
    refreshCell(r, c);
  }
  saveStats();
  updateStatus();
  saveRoundSession();
  if (g.soloAttempted >= 9) {
    g.winner = 'complete';
    await endGameSolo();
  }
}

function giveUpSolo() {

  g.soloAttempted = 9;
  g.winner = 'complete';
  endGameSolo();
}

async function endGameSolo() {
  stopTimer();
  clearRoundSession();
  resetGiveUpConfirm();
  document.getElementById('btn-give-up').disabled = true;
  g.rows.forEach((_, r) => g.cols.forEach((__, c) => refreshCell(r, c)));

  const perfect = g.soloCorrect === 9;

  if (g.soloVariant === 'daily') {

    recordDailyCompletion(g.dailyDate, g.soloCorrect);
    updateDailyCardBadge();
    showEndBanner(perfect ? 'trophy' : 'calendar', `${g.soloCorrect} / 9 richtig`, false);
    document.getElementById('end-share').classList.remove('hidden');
  } else if (g.soloVariant === 'custom') {

    showEndBanner(perfect ? 'trophy' : 'puzzle', `${g.soloCorrect} / 9 richtig`);
  } else {
    stats.solo.rounds++;
    stats.solo.correct += g.soloCorrect;
    stats.solo.cells += 9;
    if (g.soloCorrect > stats.solo.bestCorrect) stats.solo.bestCorrect = g.soloCorrect;
    stats.solo.scoreDistribution[g.soloCorrect]++;
    saveStats();
    showEndBanner(perfect ? 'trophy' : 'puzzle', `${g.soloCorrect} / 9 richtig`);
  }
  await revealSolutions();
}

const DEFAULT_DAILY = { completed: {}, currentStreak: 0, bestStreak: 0 };

function loadDailyState() {
  try {
    const raw = localStorage.getItem('ttt_daily');
    if (!raw) return structuredClone(DEFAULT_DAILY);
    const parsed = JSON.parse(raw);
    return {
      completed: (parsed.completed && typeof parsed.completed === 'object') ? parsed.completed : {},
      currentStreak: Number.isFinite(parsed.currentStreak) ? parsed.currentStreak : 0,
      bestStreak: Number.isFinite(parsed.bestStreak) ? parsed.bestStreak : 0,
    };
  } catch {
    return structuredClone(DEFAULT_DAILY);
  }
}

function saveDailyState(d) {
  localStorage.setItem('ttt_daily', JSON.stringify(d));
}

function isNextUtcDay(prevDateStr, nextDateStr) {
  const prev = new Date(`${prevDateStr}T00:00:00Z`).getTime();
  const next = new Date(`${nextDateStr}T00:00:00Z`).getTime();
  return (next - prev) === 86400000;
}

function recordDailyCompletion(date, correct) {
  const d = loadDailyState();
  if (d.completed[date]) return d;
  const priorDates = Object.keys(d.completed).sort();
  const prevDate = priorDates.length ? priorDates[priorDates.length - 1] : null;
  d.currentStreak = (prevDate && isNextUtcDay(prevDate, date)) ? d.currentStreak + 1 : 1;
  d.bestStreak = Math.max(d.bestStreak, d.currentStreak);
  d.completed[date] = { correct };
  saveDailyState(d);
  return d;
}

function updateDailyCardBadge() {
  const d = loadDailyState();
  const el = document.getElementById('daily-card-streak');
  if (d.currentStreak > 0) {
    el.classList.remove('hidden');
    el.classList.add('flex');
    document.getElementById('daily-streak-count').textContent = d.currentStreak;
  } else {
    el.classList.add('hidden');
    el.classList.remove('flex');
  }
}

async function startDaily({ push = true } = {}) {
  const resp = await fetch('/api/daily/today');
  if (!resp.ok) {
    alert('Tagesrätsel konnte nicht geladen werden.');
    return;
  }
  const data = await resp.json();
  g.dailyDate = data.date;

  const daily = loadDailyState();
  if (daily.completed[data.date]) {
    showDailyAlreadyPlayed(daily, data.date, { push });
    return;
  }

  if (tryResumeRound({ mode: 'solo', soloVariant: 'daily', dailyDate: data.date })) return;

  g.mode = 'solo';
  g.soloVariant = 'daily';
  showScreen('board', { push });
  updateModeChrome();
  beginSoloRound();
  finishSoloRoundSetup(data.rows, data.cols);
}

function showDailyAlreadyPlayed(dailyState, date, { push = true } = {}) {
  const result = dailyState.completed[date];
  document.getElementById('daily-done-score').textContent = `${result.correct} / 9 richtig`;
  document.getElementById('daily-done-streak').innerHTML = iconText('fire', `${dailyState.currentStreak} Tag${dailyState.currentStreak === 1 ? '' : 'e'} in Folge`);
  document.getElementById('daily-done-best').textContent = `Beste Serie: ${dailyState.bestStreak}`;
  showScreen('daily-done', { push });
}

document.getElementById('daily-card').addEventListener('click', () => startDaily());
document.getElementById('daily-done-menu').addEventListener('click', goToMenu);
document.getElementById('end-share').addEventListener('click', () => {
  const daily = loadDailyState();
  const result = daily.completed[g.dailyDate];
  if (!result) return;
  const text = `Tiki-Taka-Toe Tagesrätsel ${g.dailyDate}\n${result.correct}/9 richtig · ${daily.currentStreak} Tag${daily.currentStreak === 1 ? '' : 'e'} Serie\n${location.origin}/`;
  copyToClipboard(text);
  const btn = document.getElementById('end-share');
  btn.innerHTML = iconText('check', 'Kopiert', { size: 15 });
  setTimeout(() => { btn.innerHTML = iconText('share', 'Teilen', { size: 15 }); }, 1500);
});

function goToEditor({ push = true } = {}) {
  showScreen('editor', { push });
  renderEditorGrid();
  refreshEditorCounts();
}
document.getElementById('btn-editor').addEventListener('click', () => {
  closeMenuDropdown();
  goToEditor();
});
document.getElementById('btn-editor-back').addEventListener('click', goToMenu);

function editorSlotHtml(side, i) {
  const cat = g.editor[side][i];
  if (cat) {
    return `
      <div class="tt-cell tt-card-hover flex flex-col items-center justify-center p-3 tt-slot overflow-hidden gap-2 cursor-pointer"
           data-editor-slot="${side}-${i}" title="${esc(cat.label)}">
        ${categoryIconHtml(cat)}
        <div class="font-semibold text-center leading-snug px-1"
             style="font-size:11px;color:var(--text-dim);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word;">
          ${esc(cat.label)}
        </div>
      </div>`;
  }
  return `
    <div class="tt-cell tt-card-hover flex items-center justify-center tt-slot text-xs font-semibold text-center px-2 cursor-pointer"
         style="color:var(--text-faint)" data-editor-slot="${side}-${i}">
      + Kategorie
    </div>`;
}

function editorCountCellHtml(r, c) {
  if (!g.editor.row[r] || !g.editor.col[c]) {
    return `<div class="tt-slot"></div>`;
  }
  const count = g.editorCounts ? g.editorCounts[r][c] : undefined;
  if (count === undefined || count === null) {
    return `<div class="tt-cell flex items-center justify-center tt-slot text-xs" style="color:var(--text-faint)">…</div>`;
  }
  const empty = count === 0;
  return `
    <div class="tt-cell flex flex-col items-center justify-center tt-slot" style="${empty ? '' : 'border-color:var(--accent)'}">
      <div class="text-2xl font-black" style="color:${empty ? 'var(--text-faint)' : 'var(--accent)'}">${count}</div>
      <div class="tt-label">${empty ? 'keine Spieler' : 'möglich'}</div>
    </div>`;
}

function renderEditorGrid() {
  const grid = document.getElementById('editor-grid');
  const cells = [`<div class="tt-slot"></div>`];
  [0, 1, 2].forEach(c => cells.push(editorSlotHtml('col', c)));
  [0, 1, 2].forEach(r => {
    cells.push(editorSlotHtml('row', r));
    [0, 1, 2].forEach(c => cells.push(editorCountCellHtml(r, c)));
  });
  grid.innerHTML = cells.join('');
  grid.querySelectorAll('[data-editor-slot]').forEach(el => {
    el.addEventListener('click', () => {
      const [side, idx] = el.dataset.editorSlot.split('-');
      openCategoryPicker(side, parseInt(idx));
    });
  });
  const allFilled = [...g.editor.row, ...g.editor.col].every(Boolean);
  document.getElementById('btn-editor-save').disabled = !allFilled;
}

let editorCountsToken = 0;
async function refreshEditorCounts() {
  const anyPicked = [...g.editor.row, ...g.editor.col].some(Boolean);
  if (!anyPicked) {
    g.editorCounts = null;
    renderEditorGrid();
    return;
  }
  const token = ++editorCountsToken;
  const rows = g.editor.row.map(c => c ? c.id : '').join(',');
  const cols = g.editor.col.map(c => c ? c.id : '').join(',');
  try {
    const resp = await fetch(`/api/grids/preview?rows=${encodeURIComponent(rows)}&cols=${encodeURIComponent(cols)}`);
    const data = await resp.json();
    if (token !== editorCountsToken) return;
    g.editorCounts = data.counts || null;
  } catch {
    if (token !== editorCountsToken) return;
    g.editorCounts = null;
  }
  renderEditorGrid();
}

let editorActiveSlot = null;
let categoryPickerTimer = null;

function openCategoryPicker(side, index) {
  editorActiveSlot = { side, index };
  document.getElementById('category-picker-search').value = '';
  document.getElementById('category-picker-modal').classList.remove('hidden');
  document.getElementById('category-picker-search').focus();
  searchEditorCategories('');
}

function closeCategoryPicker() {
  document.getElementById('category-picker-modal').classList.add('hidden');
  editorActiveSlot = null;
}
document.getElementById('category-picker-close').addEventListener('click', closeCategoryPicker);
document.getElementById('category-picker-modal').addEventListener('click', e => {
  if (e.target.id === 'category-picker-modal') closeCategoryPicker();
});
document.getElementById('category-picker-search').addEventListener('input', e => {
  clearTimeout(categoryPickerTimer);
  categoryPickerTimer = setTimeout(() => searchEditorCategories(e.target.value.trim()), 250);
});

async function searchEditorCategories(query) {
  const resp = await fetch(`/api/categories?q=${encodeURIComponent(query)}&limit=30`);
  const data = await resp.json();
  const container = document.getElementById('category-picker-results');
  if (!data.categories?.length) {
    container.innerHTML = `<p class="text-xs text-center py-2" style="color:var(--text-faint)">Keine Treffer</p>`;
    return;
  }

  const activeCat = editorActiveSlot ? g.editor[editorActiveSlot.side][editorActiveSlot.index] : null;
  const usedIds = new Set(
    [...g.editor.row, ...g.editor.col].filter(c => c && c.id !== activeCat?.id).map(c => c.id)
  );
  container.innerHTML = data.categories.map(c => {
    const used = usedIds.has(c.id);
    return `<div class="tt-row-hover flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${used ? 'is-disabled' : 'cursor-pointer'}" style="color:var(--text)" data-cat-id="${esc(c.id)}">
      ${categoryIconHtml(c)}
      <span class="min-w-0 truncate">${esc(c.label)}</span>
    </div>`;
  }).join('');
  container.querySelectorAll('[data-cat-id]').forEach(el => {
    if (usedIds.has(el.dataset.catId)) return;
    el.addEventListener('click', () => {
      const cat = data.categories.find(c => c.id === el.dataset.catId);
      if (cat) selectEditorCategory(cat);
    });
  });
}

function selectEditorCategory(cat) {
  if (!editorActiveSlot) return;
  g.editor[editorActiveSlot.side][editorActiveSlot.index] = cat;
  closeCategoryPicker();
  g.editorCounts = null;
  renderEditorGrid();
  document.getElementById('editor-share').classList.add('hidden');
  document.getElementById('editor-error').classList.add('hidden');
  refreshEditorCounts();
}

document.getElementById('btn-editor-save').addEventListener('click', async e => {
  const btn = e.currentTarget;
  if (btn.disabled) return;
  btn.disabled = true;
  const errorEl = document.getElementById('editor-error');
  errorEl.classList.add('hidden');
  try {
    const resp = await fetch('/api/grids', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        row_ids: g.editor.row.map(c => c.id),
        col_ids: g.editor.col.map(c => c.id),
      }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      errorEl.textContent = data.error || 'Grid konnte nicht gespeichert werden.';
      errorEl.classList.remove('hidden');
      return;
    }
    g.editorSavedCode = data.code;
    document.getElementById('editor-share-code').textContent = data.code;
    document.getElementById('editor-share').classList.remove('hidden');
  } finally {
    btn.disabled = false;
  }
});

document.getElementById('btn-editor-copy-link').addEventListener('click', () => {
  if (!g.editorSavedCode) return;
  copyToClipboard(`${location.origin}/solo/${g.editorSavedCode}`);
  const btn = document.getElementById('btn-editor-copy-link');
  btn.innerHTML = iconText('check', 'Kopiert', { size: 14 });
  setTimeout(() => { btn.innerHTML = iconText('link', 'Link kopieren', { size: 14 }); }, 1500);
});
document.getElementById('btn-editor-play').addEventListener('click', () => {
  if (g.editorSavedCode) loadAndStartCustomGrid(g.editorSavedCode);
});

document.getElementById('btn-editor-load').addEventListener('click', () => {
  const code = document.getElementById('editor-load-code').value.trim();
  if (code.length < 4) return;
  loadAndStartCustomGrid(code, 'editor-load-error', 'btn-editor-load');
});
document.getElementById('editor-load-code').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('btn-editor-load').click();
});

document.getElementById('btn-setup-load').addEventListener('click', () => {
  const code = document.getElementById('setup-load-code').value.trim();
  if (code.length < 4) return;
  loadAndStartCustomGrid(code, 'setup-load-error', 'btn-setup-load');
});
document.getElementById('setup-load-code').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('btn-setup-load').click();
});

async function loadAndStartCustomGrid(code, errorElId = 'editor-load-error', btnId = null, { push = true } = {}) {
  if (tryResumeRound({ mode: 'solo', soloVariant: 'custom', gridCode: code })) return;
  const errorEl = document.getElementById(errorElId);
  errorEl.classList.add('hidden');
  const btn = btnId ? document.getElementById(btnId) : null;
  const btnLabel = btn ? btn.textContent : null;
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px;"><span class="tt-spinner"></span>Laden…</span>`;
  }
  try {
    const resp = await fetch(`/api/grids/${encodeURIComponent(code)}`);
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      errorEl.textContent = data.error || 'Grid nicht gefunden.';
      errorEl.classList.remove('hidden');
      return;
    }
    g.mode = 'solo';
    g.soloVariant = 'custom';
    g.soloGridCode = code;
    showScreen('board', { push });
    updateModeChrome();
    beginSoloRound();
    finishSoloRoundSetup(data.rows, data.cols);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = btnLabel;
    }
  }
}

function renderLobbyHome() {
  document.getElementById('online-lobby-body').innerHTML = `
    <div class="tt-card p-6 flex flex-col gap-4 items-center text-center">
      <svg class="tt-icon-app" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/></svg>
      <button id="btn-create-room" class="tt-btn-accent w-full text-sm px-4 py-2.5 rounded-xl">Raum erstellen</button>
      <div class="text-xs" style="color:var(--text-dim)">— oder —</div>
      <div class="w-full flex gap-2">
        <input id="join-code-input" maxlength="5" placeholder="CODE" autocomplete="off"
          class="tt-input flex-1 min-w-0 uppercase tracking-widest text-center rounded-lg px-3 py-2 text-sm font-bold">
        <button id="btn-join-room" class="tt-btn-neutral text-sm px-4 py-2 rounded-lg">Beitreten</button>
      </div>
      <p id="lobby-error" class="text-xs hidden" style="color:var(--accent)"></p>
    </div>
    <div class="w-full flex flex-col gap-2 mt-4">
      <div class="tt-label">Öffentliche Lobbys</div>
      <div id="public-lobbies-list" class="w-full flex flex-col gap-2">
        <div class="text-xs" style="color:var(--text-dim)">Lädt…</div>
      </div>
    </div>`;

  document.getElementById('btn-create-room').addEventListener('click', () => {
    closeLobbyListEvents();
    enterSetupScreen('online-host');
  });
  document.getElementById('btn-join-room').addEventListener('click', e => {
    if (e.currentTarget.disabled) return;
    const code = document.getElementById('join-code-input').value.trim();
    if (code.length < 4) return;
    e.currentTarget.disabled = true;
    joinOnlineRoom(code);
  });
  document.getElementById('join-code-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('btn-join-room').click();
  });

  document.getElementById('public-lobbies-list').addEventListener('click', e => {
    const btn = e.target.closest('[data-join-code]');
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    joinOnlineRoom(btn.dataset.joinCode);
  });
  connectLobbyListEvents();
}

const DIFFICULTY_LABELS = { 1: 'Leicht', 2: 'Mittel', 3: 'Schwer' };
const LEAGUE_LABELS = {
  league_buli: 'Bundesliga',
  league_pl: 'Premier League',
  league_laliga: 'La Liga',
  league_seriea: 'Serie A',
};

function renderPublicLobbyList(rooms) {
  const container = document.getElementById('public-lobbies-list');
  if (!container) return;
  if (!rooms.length) {
    container.innerHTML = `<div class="text-xs" style="color:var(--text-dim)">Gerade keine offenen Lobbys — erstelle eine!</div>`;
    return;
  }
  container.innerHTML = rooms.map(r => `
    <button data-join-code="${esc(r.code)}" class="tt-card tt-card-hover w-full flex items-center justify-between px-4 py-2.5 text-sm">
      <span class="flex items-center gap-2 font-semibold" style="color:var(--text)">
        ${esc(r.code)}
        <span class="font-medium" style="color:var(--text-dim)">${esc(DIFFICULTY_LABELS[r.difficulty] || '')}${r.league ? ' · ' + esc(LEAGUE_LABELS[r.league] || r.league) : ''}</span>
      </span>
      <span class="font-bold" style="color:var(--accent)">Beitreten</span>
    </button>`).join('');
}

function connectLobbyListEvents() {
  closeLobbyListEvents();
  fetchPublicLobbies();
  const es = new EventSource('/api/multiplayer/lobbies/events');
  es.onmessage = () => fetchPublicLobbies();
  g.lobbyEventSource = es;
}

function closeLobbyListEvents() {
  if (g.lobbyEventSource) { g.lobbyEventSource.close(); g.lobbyEventSource = null; }
}

async function fetchPublicLobbies() {
  const resp = await fetch('/api/multiplayer/lobbies');
  if (!resp.ok) return;
  const data = await resp.json();
  renderPublicLobbyList(data.rooms || []);
}

function copyToClipboard(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).catch(() => execCommandCopy(text));
  } else {
    execCommandCopy(text);
  }
}

function execCommandCopy(text) {
  const el = document.createElement('textarea');
  el.value = text;
  el.style.position = 'fixed';
  el.style.opacity = '0';
  document.body.appendChild(el);
  el.focus();
  el.select();
  try {
    document.execCommand('copy');
  } catch (_) {

  }
  document.body.removeChild(el);
}

function renderLobbyWaiting(code) {
  const link = `${location.origin}/online/${code}`;
  document.getElementById('online-lobby-body').innerHTML = `
    <div class="tt-card p-6 flex flex-col gap-3 items-center text-center">
      <div class="text-sm" style="color:var(--text-dim)">Warte auf Gegner…</div>
      <div class="text-4xl font-black tracking-[0.3em]" style="color:var(--accent)">${esc(code)}</div>
      <button id="btn-copy-link" class="tt-btn-neutral text-xs px-3 py-1.5 rounded-lg flex items-center justify-center gap-1.5">${iconText('link', 'Link kopieren', { size: 14 })}</button>
      <div class="flex items-center gap-2 text-xs mt-2" style="color:var(--text-dim)">
        <span class="inline-block w-2 h-2 rounded-full animate-pulse" style="background:var(--accent)"></span>
        Sobald dein Freund beitritt, geht's los
      </div>
    </div>`;
  document.getElementById('btn-copy-link').addEventListener('click', () => {
    copyToClipboard(link);
    const btn = document.getElementById('btn-copy-link');
    if (!btn) return;
    btn.innerHTML = iconText('check', 'Kopiert', { size: 14 });
    setTimeout(() => { btn.innerHTML = iconText('link', 'Link kopieren', { size: 14 }); }, 1500);
  });
}

function showLobbyError(msg) {
  const el = document.getElementById('lobby-error');
  if (!el) return;
  el.textContent = msg;
  el.classList.remove('hidden');
}

async function createOnlineRoom() {
  closeLobbyListEvents();
  Object.assign(g, { onlineBoardEntered: false, onlineFinished: false, onlineLastWrongGuessVersion: undefined });
  const resp = await fetch('/api/multiplayer/rooms', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ difficulty, league: selectedLeague || undefined, visibility: onlineVisibility }),
  });
  if (!resp.ok) {

    showScreen('online-lobby', { push: false });
    showLobbyError('Raum konnte nicht erstellt werden.');
    connectLobbyListEvents();
    return;
  }
  const data = await resp.json();
  g.onlineCode = data.code;
  g.onlineToken = data.token;
  g.onlineSlot = data.slot;
  saveOnlineSession();
  showScreen('online-lobby');
  renderLobbyWaiting(data.code);
  connectOnlineEvents();
}

async function joinOnlineRoom(code, { push = true } = {}) {
  closeLobbyListEvents();
  Object.assign(g, { onlineBoardEntered: false, onlineFinished: false, onlineLastWrongGuessVersion: undefined });
  code = code.toUpperCase();
  const resp = await fetch(`/api/multiplayer/rooms/${code}/join`, { method: 'POST' });
  if (!resp.ok) {
    showLobbyError('Raum nicht gefunden oder schon voll.');
    const btn = document.getElementById('btn-join-room');
    if (btn) btn.disabled = false;
    connectLobbyListEvents();
    return;
  }
  const data = await resp.json();
  g.onlineCode = data.code;
  g.onlineToken = data.token;
  g.onlineSlot = data.slot;
  saveOnlineSession();

  showScreen('online-lobby', { push });
  renderLobbyWaiting(data.code);
  connectOnlineEvents();
  await refreshOnlineState();
}

function attemptOnlineResume(code) {
  let stored = null;
  try { stored = JSON.parse(sessionStorage.getItem(ONLINE_SESSION_KEY) || 'null'); } catch {   }
  if (stored && stored.code === code) {
    g.onlineCode = stored.code;
    g.onlineToken = stored.token;
    g.onlineSlot = stored.slot;
    fetch(`/api/multiplayer/rooms/${code}/state?token=${encodeURIComponent(stored.token)}`)
      .then(resp => (resp.ok ? resp.json() : null))
      .then(data => {
        if (data && data.yourSlot) {
          connectOnlineEvents();
          applyOnlineState(data);
          return;
        }
        clearOnlineSession();
        g.onlineCode = null; g.onlineToken = null; g.onlineSlot = null;
        renderLobbyHome();
        const input = document.getElementById('join-code-input');
        if (input) input.value = code;
      })
      .catch(() => renderLobbyHome());
    return;
  }
  renderLobbyHome();
  const input = document.getElementById('join-code-input');
  if (input) input.value = code;
}

function connectOnlineEvents() {
  if (g.onlineEventSource) g.onlineEventSource.close();
  const es = new EventSource(`/api/multiplayer/rooms/${g.onlineCode}/events?token=${encodeURIComponent(g.onlineToken)}`);
  es.onmessage = () => refreshOnlineState();
  g.onlineEventSource = es;
}

async function refreshOnlineState() {
  if (!g.onlineCode) return;
  const resp = await fetch(`/api/multiplayer/rooms/${g.onlineCode}/state?token=${encodeURIComponent(g.onlineToken)}`);
  if (!resp.ok) return;
  applyOnlineState(await resp.json());
}

function enterOnlineBoard() {

  showScreen('board', { push: false });
  updateModeChrome();
  hideEndBanner();
  document.getElementById('btn-give-up').disabled = false;
  g.elapsedSeconds = 0;
  g.solution = null;
  startTimer();
}

function applyOnlineState(data) {
  const justConnected = data.playersConnected === 2 && !g.onlineBoardEntered;

  const isRematch = g.onlineFinished && data.winner === null;
  g.onlineConnected = data.playersConnected;
  g.rows = data.rows;
  g.cols = data.cols;
  g.board = data.board.map(row => row.map(cell => cell ? { status: 'correct', ...cell } : null));
  g.current = data.current;
  g.winner = data.winner;
  g.winCells = data.winCells || [];
  g.usedIds = new Set(data.usedIds || []);
  if (data.yourSlot) g.onlineSlot = data.yourSlot;

  if (data.playersConnected < 2) {
    renderLobbyWaiting(g.onlineCode);
    return;
  }
  if (justConnected) {
    g.onlineBoardEntered = true;
    enterOnlineBoard();
  }
  if (isRematch) {
    g.onlineFinished = false;
    hideEndBanner();
    enterOnlineBoard();
  }
  if (document.getElementById('screen-board').classList.contains('hidden')) return;

  let justFlashedWrongGuess = false;
  if (g.onlineLastWrongGuessVersion === undefined) {
    g.onlineLastWrongGuessVersion = data.lastWrongGuess ? data.lastWrongGuess.version : null;
  } else if (data.lastWrongGuess && data.lastWrongGuess.version !== g.onlineLastWrongGuessVersion) {
    g.onlineLastWrongGuessVersion = data.lastWrongGuess.version;
    if (data.lastWrongGuess.slot !== g.onlineSlot) {
      flashOnlineMessage(`Gegner hat ${data.lastWrongGuess.name} versucht – falsch!`);
      justFlashedWrongGuess = true;
    }
  }

  renderBoard();
  if (g.winner) {
    document.getElementById('btn-give-up').disabled = true;
    if (!g.onlineFinished) {
      g.onlineFinished = true;
      finishOnline(data.endReason);
    }
    updateRematchButtonState(data.rematchRequested || []);
  } else if (!justFlashedWrongGuess) {

    updateStatus();
  }
}

function updateRematchButtonState(requested) {
  if (g.mode !== 'online') return;
  const btn = document.getElementById('end-new-game');
  if (btn.classList.contains('hidden')) return;
  const youRequested = requested.includes(g.onlineSlot);
  const oppRequested = requested.some(s => s !== g.onlineSlot);
  if (youRequested) {
    btn.disabled = true;
    btn.innerHTML = iconText('clock', 'Warte auf Gegner…', { size: 14 });
  } else if (oppRequested) {
    btn.disabled = false;
    btn.innerHTML = iconText('check', 'Revanche annehmen', { size: 14 });
  } else {
    btn.disabled = false;
    btn.innerHTML = iconText('rematch', 'Revanche', { size: 14 });
  }
}

async function onlineSelectPlayer(pid, name, club, r, c) {
  const resp = await fetch(`/api/multiplayer/rooms/${g.onlineCode}/moves`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: g.onlineToken, row: r, col: c, player_id: pid }),
  });
  const data = await resp.json();
  if (data.ok) {
    closeModal();
    await refreshOnlineState();
    return;
  }
  const err = document.getElementById('search-error');
  if (data.reason === 'invalid_player') {
    err.textContent = `${name} passt hier nicht – nächster Spieler ist dran!`;
    err.classList.remove('hidden');
    setTimeout(async () => { closeModal(); await refreshOnlineState(); }, 1500);
  } else {
    err.textContent = 'Zug nicht möglich – Status wird aktualisiert…';
    err.classList.remove('hidden');
    setTimeout(async () => { closeModal(); await refreshOnlineState(); }, 1200);
  }
}

async function rematchOnline() {

  const resp = await fetch(`/api/multiplayer/rooms/${g.onlineCode}/rematch`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: g.onlineToken }),
  });
  if (!resp.ok) {
    alert('Revanche nicht möglich – Raum eventuell nicht mehr aktiv.');
    return;
  }
  await refreshOnlineState();
}

async function finishOnline(reason) {
  stopTimer();
  setStatus('Runde beendet.');
  stats.online.rounds++;

  if (g.winner === 'draw') {
    stats.online.draws++;
    stats.online.streak = 0;
    saveStats();
    showEndBanner('handshake', 'Unentschieden!');
  } else {
    const youWon = g.winner === g.onlineSlot;
    if (youWon) {
      stats.online.wins++;
      stats.online.streak++;
      if (stats.online.streak > stats.online.bestStreak) stats.online.bestStreak = stats.online.streak;
    } else {
      stats.online.losses++;
      stats.online.streak = 0;
    }
    saveStats();
    const titles = {
      forfeit: youWon ? 'Gegner hat aufgegeben' : 'Aufgegeben',
      disconnect: youWon ? 'Gegner ist offline' : 'Verbindung verloren',
    };
    const title = titles[reason] || (youWon ? 'Du gewinnst!' : 'Du verlierst');
    showEndBanner(youWon ? 'trophy' : 'loss', title);
  }
  await revealSolutions();
}

document.getElementById('btn-give-up').addEventListener('click', async (e) => {
  if (g.winner) return;

  if (!giveUpConfirming) {
    giveUpConfirming = true;
    e.currentTarget.textContent = 'Wirklich aufgeben?';
    e.currentTarget.classList.remove('tt-btn-accent');
    e.currentTarget.classList.add('tt-btn-accent-outline');
    return;
  }
  resetGiveUpConfirm();
  if (g.mode === 'solo') {
    giveUpSolo();
  } else if (g.mode === 'online') {
    await fetch(`/api/multiplayer/rooms/${g.onlineCode}/forfeit`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: g.onlineToken }),
    });
    await refreshOnlineState();
  } else if (g.mode === 'local') {
    g.winner = g.current === 1 ? 2 : 1;
    g.winCells = [];
    endGameLocal();
  }
});

document.addEventListener('click', e => {
  if (giveUpConfirming && e.target.id !== 'btn-give-up') resetGiveUpConfirm();
});

let statsResetConfirming = false;

function distributionChartHtml(dist, emptyLabel) {
  const total = dist.reduce((a, b) => a + b, 0);
  if (total === 0) {
    return `<div class="text-xs text-center py-1" style="color:var(--text-faint)">${emptyLabel}</div>`;
  }
  const maxBucket = Math.max(1, ...dist);
  return dist.map((count, score) => `
    <div class="flex items-center gap-2">
      <div class="w-3 text-xs text-right font-bold" style="color:var(--text-dim)">${score}</div>
      <div class="flex-1 rounded-full overflow-hidden" style="background:var(--card-border);height:12px;">
        <div class="h-full rounded-full" style="width:${count ? Math.max(6, Math.round((count / maxBucket) * 100)) : 0}%;background:var(--accent);"></div>
      </div>
      <div class="w-5 text-xs text-right" style="color:var(--text-dim)">${count}</div>
    </div>`).join('');
}

function renderStats() {
  const s = stats.solo, o = stats.online;
  const d = loadDailyState();
  const dailyScores = Object.values(d.completed).map(v => v.correct);
  const dailyAccuracy = dailyScores.length
    ? Math.round((dailyScores.reduce((a, b) => a + b, 0) / (dailyScores.length * 9)) * 100) : 0;

  const dailyDistribution = new Array(10).fill(0);
  dailyScores.forEach(correct => { if (correct >= 0 && correct <= 9) dailyDistribution[correct]++; });
  const soloAccuracy = s.cells ? Math.round((s.correct / s.cells) * 100) : 0;
  const onlineWinRate = o.rounds ? Math.round((o.wins / o.rounds) * 100) : 0;

  const tile = (value, label, accented) => `
    <div class="tt-card p-2.5"><div class="text-base font-black" style="color:${accented ? 'var(--accent)' : 'var(--text)'}">${value}</div><div class="tt-label">${label}</div></div>`;

  const sectionLabel = (iconName, text) =>
    `<div class="tt-label mb-2 flex items-center gap-1.5">${svgIcon(iconName, 13)}${text}</div>`;

  document.getElementById('stats-body').innerHTML = `
    <div>
      ${sectionLabel('calendar', 'Daily Grid')}
      <div class="grid grid-cols-2 gap-2 text-center">
        ${tile(iconText('fire', d.currentStreak, { size: 14, gap: 4 }), 'Serie', true)}
        ${tile(`${dailyAccuracy}%`, 'Trefferquote')}
      </div>
      <div class="tt-card p-3 mt-2 flex flex-col gap-1.5">
        <div class="tt-label mb-0.5">Ergebnisverteilung</div>
        ${distributionChartHtml(dailyDistribution, 'Noch keine Tagesrätsel gespielt')}
      </div>
    </div>
    <div>
      ${sectionLabel('puzzle', 'Solo')}
      <div class="grid grid-cols-2 gap-2 text-center">
        ${tile(s.rounds, 'Runden')}
        ${tile(`${s.bestCorrect}/9`, 'Bestes Ergebnis', true)}
        <div class="tt-card p-2.5 col-span-2"><div class="text-base font-black" style="color:var(--text)">${soloAccuracy}%</div><div class="tt-label">Trefferquote gesamt</div></div>
      </div>
      <div class="tt-card p-3 mt-2 flex flex-col gap-1.5">
        <div class="tt-label mb-0.5">Ergebnisverteilung</div>
        ${distributionChartHtml(s.scoreDistribution, 'Noch keine Runden gespielt')}
      </div>
    </div>
    <div>
      ${sectionLabel('globe', '1v1 Online')}
      <div class="grid grid-cols-2 gap-2 text-center">
        ${tile(o.rounds, 'Spiele')}
        ${tile(`${onlineWinRate}%`, 'Gewinnrate', true)}
        ${tile(o.wins, 'Siege', true)}
        ${tile(o.losses, 'Niederlagen')}
        <div class="tt-card p-2.5 col-span-2"><div class="text-base font-black" style="color:var(--text)">${o.draws}</div><div class="tt-label">Unentschieden</div></div>
      </div>
    </div>
    <div class="pt-3" style="border-top:1px solid var(--card-border);">
      <button id="btn-stats-reset" class="tt-btn-neutral w-full text-xs px-4 py-2.5 rounded-xl">Statistik zurücksetzen</button>
    </div>`;

  statsResetConfirming = false;
  document.getElementById('btn-stats-reset').addEventListener('click', e => {

    if (!statsResetConfirming) {
      statsResetConfirming = true;
      e.currentTarget.textContent = 'Wirklich zurücksetzen?';
      e.currentTarget.classList.remove('tt-btn-neutral');
      e.currentTarget.classList.add('tt-btn-accent-outline');
      return;
    }
    stats = structuredClone(DEFAULT_STATS);
    saveStats();
    saveDailyState(structuredClone(DEFAULT_DAILY));
    updateDailyCardBadge();
    renderStats();
  });
}

document.addEventListener('click', e => {
  if (statsResetConfirming && e.target.id !== 'btn-stats-reset') {
    statsResetConfirming = false;
    const btn = document.getElementById('btn-stats-reset');
    if (btn) {
      btn.textContent = 'Statistik zurücksetzen';
      btn.classList.remove('tt-btn-accent-outline');
      btn.classList.add('tt-btn-neutral');
    }
  }
});

document.getElementById('btn-stats').addEventListener('click', () => {
  closeMenuDropdown();
  renderStats();
  document.getElementById('stats-modal').classList.remove('hidden');
});
document.getElementById('stats-close').addEventListener('click', () => {
  document.getElementById('stats-modal').classList.add('hidden');
});
document.getElementById('stats-modal').addEventListener('click', e => {
  if (e.target.id === 'stats-modal') document.getElementById('stats-modal').classList.add('hidden');
});

function setDifficulty(d) {
  difficulty = d;
  document.querySelectorAll('.diff-btn').forEach(btn => {
    const active = parseInt(btn.dataset.diff) === d;
    btn.classList.toggle('is-active', active);
  });
}

document.querySelectorAll('.diff-btn').forEach(btn => {
  btn.addEventListener('click', () => setDifficulty(parseInt(btn.dataset.diff)));
});

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal').addEventListener('click', e => {
  if (e.target.id === 'modal') closeModal();
});
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  closeModal();
  closeSolutionSheet();
});

(function init() {

  const params = new URLSearchParams(location.search);
  const joinCode = params.get('join');
  const gridCode = params.get('grid');
  if (joinCode) {

    const code = joinCode.toUpperCase();
    history.replaceState({ screen: 'online-lobby' }, '', `/online/${code}`);
    g.mode = 'online';
    renderScreenDom('online-lobby');
    updateModeChrome();
    attemptOnlineResume(code);
  } else if (gridCode) {

    loadAndStartCustomGrid(gridCode, undefined, undefined, { push: false });
  } else {
    enterFromPath(parseLocation());
  }
  updateDailyCardBadge();
})();
