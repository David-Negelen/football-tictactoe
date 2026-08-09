// ─── SVG & badges ───────────────────────────────────────────────────────────

function shirtSvg() {
  return `<svg class="text-green-500 w-10 h-10 mx-auto mb-1 opacity-60" viewBox="0 0 80 72" fill="currentColor">
    <path d="M22 4 L10 14 L2 36 L18 42 L18 68 L62 68 L62 42 L78 36 L70 14 L58 4
             C54 14 46 18 40 18 C34 18 26 14 22 4 Z"/>
  </svg>`;
}

function markBadge(player) {
  const color = player === 1 ? 'bg-red-500' : 'bg-blue-500';
  const sym   = player === 1 ? 'X' : 'O';
  return `<span class="${color} text-white text-xs font-black w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0">${sym}</span>`;
}

function esc(v) {
  if (v == null) return '';
  const d = document.createElement('div');
  d.textContent = String(v);
  return d.innerHTML;
}

// ─── Zustand ──────────────────────────────────────────────────────────────────

const g = {
  mode: null,        // 'solo' | 'local' | 'online'
  rows: [], cols: [],
  board: [[null,null,null],[null,null,null],[null,null,null]],
  current: 1,         // whose turn (local/online); unused in solo
  winner: null,       // null | 1 | 2 | 'draw' | 'complete' (solo)
  winCells: [],
  usedIds: new Set(),
  activeCell: null,   // {r, c}
  streak: { 1: 0, 2: 0 },
  elapsedSeconds: 0,
  solution: null,     // filled in after the round ends
  // solo:
  soloAttempted: 0,
  soloCorrect: 0,
  // online:
  onlineCode: null,
  onlineToken: null,
  onlineSlot: null,
  onlineConnected: 0,
  onlineEventSource: null,
  onlineBoardEntered: false,
  onlineFinished: false,
};
let difficulty = 3;

// ─── Anonyme Identität & Statistik ─────────────────────────────────────────────
// Kein Login — nur eine zufällige Geräte-ID + Statistik im localStorage des Browsers.

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
  solo: { rounds: 0, correct: 0, cells: 0, bestCorrect: 0 },
  online: { rounds: 0, wins: 0, losses: 0, draws: 0 },
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

// ─── Einstellungen (welche Kategorien dürfen im Raster vorkommen) ─────────────

const DEFAULT_SETTINGS = { excludedTypes: [], excludedCategoryIds: [] };

function loadSettings() {
  try {
    const raw = localStorage.getItem('ttt_settings');
    if (!raw) return structuredClone(DEFAULT_SETTINGS);
    const parsed = JSON.parse(raw);
    return {
      excludedTypes: Array.isArray(parsed.excludedTypes) ? parsed.excludedTypes : [],
      excludedCategoryIds: Array.isArray(parsed.excludedCategoryIds) ? parsed.excludedCategoryIds : [],
    };
  } catch {
    return structuredClone(DEFAULT_SETTINGS);
  }
}

function saveSettings() {
  localStorage.setItem('ttt_settings', JSON.stringify(settings));
}

let settings = loadSettings();
let selectedLeague = '';

function genParams() {
  const p = new URLSearchParams({ difficulty: String(difficulty) });
  if (selectedLeague) p.set('league', selectedLeague);
  if (settings.excludedTypes.length) p.set('excluded_types', settings.excludedTypes.join(','));
  if (settings.excludedCategoryIds.length) p.set('excluded', settings.excludedCategoryIds.join(','));
  return p;
}

// ─── Router ───────────────────────────────────────────────────────────────────

function showScreen(name) {
  document.getElementById('screen-mode-select').classList.toggle('hidden', name !== 'mode-select');
  document.getElementById('screen-setup').classList.toggle('hidden', name !== 'setup');
  document.getElementById('screen-online-lobby').classList.toggle('hidden', name !== 'online-lobby');
  document.getElementById('screen-board').classList.toggle('hidden', name !== 'board');
  document.getElementById('screen-settings').classList.toggle('hidden', name !== 'settings');
  closeMenuDropdown();
}

function updateModeChrome() {
  resetGiveUpConfirm();
}

// Give-up uses an inline two-step confirm (click once to arm, click again
// to confirm) instead of a browser confirm() popup, in every mode; clicking
// anywhere else cancels it.
let giveUpConfirming = false;

function resetGiveUpConfirm() {
  const btn = document.getElementById('btn-give-up');
  giveUpConfirming = false;
  btn.textContent = 'Aufgeben';
  btn.classList.remove('bg-red-600', 'hover:bg-red-500');
  btn.classList.add('bg-orange-500', 'hover:bg-orange-400');
}

function setLeague(value) {
  selectedLeague = value;
  document.querySelectorAll('.league-btn').forEach(btn => {
    const active = btn.dataset.league === value;
    btn.classList.toggle('bg-yellow-400', active);
    btn.classList.toggle('text-slate-900', active);
    btn.classList.toggle('bg-green-900/40', !active);
    btn.classList.toggle('text-green-200', !active);
  });
}

document.querySelectorAll('.league-btn').forEach(btn => {
  btn.addEventListener('click', () => setLeague(btn.dataset.league));
});

document.querySelectorAll('[data-mode]').forEach(btn => {
  btn.addEventListener('click', () => selectMode(btn.dataset.mode));
});

// Difficulty and league are chosen once, right after picking a mode, on
// their own screen — this also covers online (previously the room creator
// had no way to choose them at all, since the header pickers were hidden
// outright in online mode).
const SETUP_TITLES = { solo: 'Solo einstellen', local: '1v1 Lokal einstellen', online: '1v1 Online einstellen' };

function selectMode(mode) {
  g.pendingMode = mode;
  document.getElementById('setup-title').textContent = SETUP_TITLES[mode] || 'Rätsel einstellen';
  showScreen('setup');
}

document.getElementById('btn-setup-back').addEventListener('click', () => showScreen('mode-select'));
document.getElementById('btn-setup-continue').addEventListener('click', () => {
  const mode = g.pendingMode;
  if (mode === 'solo') { startSolo(); return; }
  if (mode === 'local') { startLocal(); return; }
  g.mode = 'online';
  showScreen('online-lobby');
  updateModeChrome();
  renderLobbyHome();
});

function goToMenu() {
  stopTimer();
  if (g.mode === 'online' && g.onlineCode && !g.winner) {
    fetch(`/api/multiplayer/rooms/${g.onlineCode}/forfeit`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: g.onlineToken }),
    }).catch(() => {});
  }
  if (g.onlineEventSource) { g.onlineEventSource.close(); g.onlineEventSource = null; }
  Object.assign(g, { mode: null, onlineCode: null, onlineToken: null, onlineSlot: null, onlineBoardEntered: false, onlineFinished: false });
  showScreen('mode-select');
}
document.getElementById('btn-logo').addEventListener('click', goToMenu);

// ─── Kopfzeilen-Menü (☰) ────────────────────────────────────────────────────

function closeMenuDropdown() {
  document.getElementById('menu-dropdown').classList.add('hidden');
}
document.getElementById('btn-menu-toggle').addEventListener('click', e => {
  e.stopPropagation();
  document.getElementById('menu-dropdown').classList.toggle('hidden');
});
document.addEventListener('click', e => {
  const dropdown = document.getElementById('menu-dropdown');
  if (!dropdown.classList.contains('hidden') && !dropdown.contains(e.target) && e.target.id !== 'btn-menu-toggle') {
    closeMenuDropdown();
  }
});

// Closing the tab, navigating away, or reloading mid-game should forfeit
// immediately instead of leaving the opponent waiting for the server's
// ~20s disconnect timeout (see multiplayer.py's check_opponent_disconnected
// for the fallback that still covers a crash/network loss, where no JS ever
// gets to run). A regular fetch() gets cancelled when the page unloads —
// sendBeacon is specifically designed to survive that.
window.addEventListener('pagehide', () => {
  if (g.mode === 'online' && g.onlineCode && !g.winner) {
    const body = new Blob([JSON.stringify({ token: g.onlineToken })], { type: 'application/json' });
    navigator.sendBeacon?.(`/api/multiplayer/rooms/${g.onlineCode}/forfeit`, body);
  }
});

// ─── Einstellungen-Screen ───────────────────────────────────────────────────────

const CATEGORY_TYPE_LABELS = {
  club: 'Vereine', nationality: 'Nationalitäten', position: 'Positionen',
  award: 'Trophäen', league: 'Ligen', continent: 'Kontinente',
  initial: 'Anfangsbuchstabe', contains_letter: 'Enthält Buchstabe',
  age: 'Alter', market_value: 'Marktwert',
};

document.getElementById('btn-settings').addEventListener('click', () => {
  renderSettingsScreen();
  showScreen('settings');
});
document.getElementById('btn-settings-back').addEventListener('click', () => showScreen('mode-select'));

function renderSettingsScreen() {
  const toggles = document.getElementById('settings-type-toggles');
  toggles.innerHTML = Object.entries(CATEGORY_TYPE_LABELS).map(([type, label]) => `
    <label class="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-2 cursor-pointer text-white">
      <input type="checkbox" data-type-toggle="${type}" ${settings.excludedTypes.includes(type) ? '' : 'checked'}>
      ${esc(label)}
    </label>`).join('');
  toggles.querySelectorAll('[data-type-toggle]').forEach(cb => {
    cb.addEventListener('change', () => {
      const type = cb.dataset.typeToggle;
      settings.excludedTypes = cb.checked
        ? settings.excludedTypes.filter(t => t !== type)
        : [...new Set([...settings.excludedTypes, type])];
      saveSettings();
    });
  });

  renderExcludedList();

  const typeSelect = document.getElementById('settings-exclude-type');
  const searchInput = document.getElementById('settings-exclude-search');
  let searchTimer = null;
  const runSearch = () => searchCategoriesForExclusion(typeSelect.value, searchInput.value.trim());
  typeSelect.onchange = runSearch;
  searchInput.oninput = () => { clearTimeout(searchTimer); searchTimer = setTimeout(runSearch, 250); };
  runSearch();
}

async function searchCategoriesForExclusion(type, query) {
  const container = document.getElementById('settings-exclude-results');
  const resp = await fetch(`/api/categories?type=${encodeURIComponent(type)}&q=${encodeURIComponent(query)}&limit=40`);
  const data = await resp.json();
  if (!data.categories?.length) {
    container.innerHTML = '<p class="text-slate-400 text-xs text-center py-2">Keine Treffer</p>';
    return;
  }
  container.innerHTML = data.categories.map(c => {
    const excluded = settings.excludedCategoryIds.includes(c.id);
    return `<label class="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-50 text-sm cursor-pointer">
      <input type="checkbox" data-exclude-id="${esc(c.id)}" ${excluded ? 'checked' : ''}>
      <span>${esc(c.label)}</span>
    </label>`;
  }).join('');
  container.querySelectorAll('[data-exclude-id]').forEach(cb => {
    cb.addEventListener('change', () => {
      const id = cb.dataset.excludeId;
      settings.excludedCategoryIds = cb.checked
        ? [...new Set([...settings.excludedCategoryIds, id])]
        : settings.excludedCategoryIds.filter(x => x !== id);
      saveSettings();
      renderExcludedList();
    });
  });
}

function renderExcludedList() {
  document.getElementById('settings-excluded-count').textContent = settings.excludedCategoryIds.length;
  const list = document.getElementById('settings-excluded-list');
  if (!settings.excludedCategoryIds.length) {
    list.innerHTML = '<span class="text-green-200/50 text-xs">Keine</span>';
    return;
  }
  list.innerHTML = settings.excludedCategoryIds.map(id => `
    <button data-remove-excluded="${esc(id)}" class="bg-red-900/40 hover:bg-red-900/60 text-red-200 text-xs px-2 py-1 rounded-full transition-colors">
      ${esc(id)} ×
    </button>`).join('');
  list.querySelectorAll('[data-remove-excluded]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.removeExcluded;
      settings.excludedCategoryIds = settings.excludedCategoryIds.filter(x => x !== id);
      saveSettings();
      renderExcludedList();
      searchCategoriesForExclusion(document.getElementById('settings-exclude-type').value, document.getElementById('settings-exclude-search').value.trim());
    });
  });
}

// ─── Spielfeld rendern (gemeinsam für alle Modi) ───────────────────────────────

function renderBoard() {
  const board = document.getElementById('board');
  const cells = [];

  cells.push(`<div class="h-32"></div>`);
  g.cols.forEach(cat => cells.push(headerCellHtml(cat)));
  g.rows.forEach((rowCat, r) => {
    cells.push(headerCellHtml(rowCat));
    g.cols.forEach((_, c) => cells.push(cellHtml(r, c)));
  });

  board.innerHTML = cells.join('');
  board.querySelectorAll('[data-cell]').forEach(el => {
    el.addEventListener('click', () => {
      const [r, c] = el.dataset.cell.split(',').map(Number);
      openCell(r, c);
    });
  });
}

function categoryIconHtml(cat) {
  // Real downloaded flag/crest image (see fetch_flags.py, fetch_club_logos.py)
  // wins whenever available — looks far better than the emoji font or the
  // generic colored-initial badge.
  if (cat.icon_image) {
    return `<img src="${esc(cat.icon_image)}" alt="" class="w-9 h-9 object-contain flex-shrink-0">`;
  }
  // Dynamically generated clubs without a hand-picked emoji (the vast
  // majority of ~6,500 clubs) carry icon_letter/icon_color instead of an
  // icon string — render a small colored initial badge for those.
  if (!cat.icon && cat.icon_letter) {
    return `<div class="w-9 h-9 rounded-full flex items-center justify-center text-white font-black text-sm flex-shrink-0"
      style="background:${esc(cat.icon_color || '#14532d')}">${esc(cat.icon_letter)}</div>`;
  }
  return `<div class="text-3xl leading-none flex-shrink-0">${cat.icon || '⚽'}</div>`;
}

function headerCellHtml(cat) {
  return `
    <div class="rounded-xl flex flex-col items-center justify-center p-3 h-32 overflow-hidden gap-2"
         style="background:rgba(20,83,45,.9);border:1px solid rgba(74,222,128,.15);box-shadow:inset 0 1px 0 rgba(255,255,255,.04)"
         title="${esc(cat.label)}">
      ${categoryIconHtml(cat)}
      <div class="text-white/90 font-semibold text-center leading-snug px-1"
           style="font-size:11px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word;">
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
      <div class="rounded-xl bg-slate-800/60 border border-red-900/40 flex flex-col items-center justify-center h-32">
        <div class="text-red-400 text-2xl mb-1">✕</div>
        <div class="text-red-300/70 text-[10px] font-semibold uppercase tracking-wide">Falsch</div>
      </div>`;
  }

  if (entry) {
    const p1  = entry.player === 1;
    const bg  = p1 ? 'bg-red-900/50'  : 'bg-blue-900/50';
    const ring = isWin
      ? 'win-cell ring-4 ring-yellow-400'
      : `ring-2 ${p1 ? 'ring-red-400' : 'ring-blue-400'}`;
    return `
      <div class="rounded-xl ${bg} ${ring} flex flex-col items-center justify-center p-3 h-32"
           data-cell="${r},${c}">
        ${g.mode !== 'solo' ? `<div class="flex justify-end w-full mb-1">${markBadge(entry.player)}</div>` : ''}
        <div class="text-white font-bold text-center leading-tight px-1 text-sm">${esc(entry.name)}</div>
        <div class="text-green-300 text-xs mt-1 truncate max-w-full px-1">${esc(entry.club || '')}</div>
      </div>`;
  }

  if (gone && g.solution) {
    const cellSol = g.solution[r][c];
    const names = (cellSol.players || []).slice(0, 3).map(p => esc(p.name)).join(', ');
    return `
      <div class="rounded-xl bg-green-900/30 border border-green-700/30 flex flex-col items-center justify-center p-2 h-32 text-center">
        <div class="text-green-400/80 text-[9px] font-bold uppercase tracking-wide mb-1">Lösung</div>
        <div class="text-green-200/90 text-[11px] leading-snug px-1">${names || '–'}</div>
        ${cellSol.count > 3 ? `<div class="text-green-500/70 text-[9px] mt-1">+${cellSol.count - 3} weitere</div>` : ''}
      </div>`;
  }

  // Online mode: names can only be entered on your own turn — the server
  // already rejects an out-of-turn move, but the cell itself should refuse
  // to even open the search modal instead of letting you type/search/pick
  // a name first and only finding out afterward.
  const notYourTurn = g.mode === 'online' && g.onlineSlot && g.current !== g.onlineSlot;
  const disabled = gone || notYourTurn;
  const hoverBg = disabled
    ? 'bg-green-800/40 opacity-40'
    : 'bg-green-700/60 hover:bg-green-600/70 cursor-pointer';
  return `
    <button ${disabled ? 'disabled' : ''} data-cell="${r},${c}"
      class="cell-btn rounded-xl ${hoverBg} border border-green-600/50 flex flex-col items-center justify-center h-32 w-full">
      ${shirtSvg()}
      <span class="text-green-300 font-semibold tracking-wide text-[10px] mt-1">SPIELER WÄHLEN</span>
    </button>`;
}

function refreshCell(r, c) {
  const board = document.getElementById('board');
  const idx = 1 + 3 + r * 4 + 1 + c; // title + 3 col headers + row*(header + 3 cells)
  const existing = board.children[idx];
  if (!existing) return;
  const tmp = document.createElement('div');
  tmp.innerHTML = cellHtml(r, c);
  const newEl = tmp.firstElementChild;
  existing.replaceWith(newEl);
  if (!g.board[r][c]) {
    newEl.addEventListener('click', () => openCell(r, c));
  }
}

async function revealSolutions() {
  if (!g.rows.length || !g.cols.length) return;
  const rowIds = g.rows.map(c => c.id).join(',');
  const colIds = g.cols.map(c => c.id).join(',');
  try {
    const resp = await fetch(`/api/game/solve?rows=${rowIds}&cols=${colIds}`);
    if (!resp.ok) return;
    const data = await resp.json();
    g.solution = data.grid;
    g.rows.forEach((_, r) => g.cols.forEach((__, c) => { if (!g.board[r][c]) refreshCell(r, c); }));
  } catch {
    // Reveal is a nice-to-have; a network hiccup here shouldn't disrupt anything else.
  }
}

// ─── Zell-Interaktion (gemeinsam) ──────────────────────────────────────────────

function openCell(r, c) {
  if (g.winner || g.board[r][c]) return;
  if (g.mode === 'online' && g.onlineSlot && g.current !== g.onlineSlot) return;
  g.activeCell = { r, c };
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

async function doSearch(q) {
  if (!g.activeCell) return;
  const resp = await fetch(`/api/game/search?q=${encodeURIComponent(q)}`);
  const data = await resp.json();
  const container = document.getElementById('search-results');

  if (!data.players?.length) {
    container.innerHTML = '<p class="text-slate-400 text-xs text-center py-2">Keine Spieler gefunden</p>';
    return;
  }

  container.innerHTML = data.players.map(p => {
    const used = g.usedIds.has(p.id);
    const cls  = used
      ? 'opacity-40 cursor-not-allowed bg-slate-50'
      : 'hover:bg-green-50 cursor-pointer';
    return `
      <div class="flex items-center justify-between rounded-lg px-3 py-2 text-sm border border-transparent hover:border-green-200 transition-colors ${cls}"
           data-pid="${p.id}" data-name="${esc(p.name)}" data-club="${esc(p.current_club_name || '')}">
        <div class="min-w-0">
          <span class="font-semibold">${esc(p.name)}</span>
          ${p.current_club_name
            ? `<span class="text-slate-400 text-xs ml-1 truncate">${esc(p.current_club_name)}</span>`
            : ''}
        </div>
        ${used ? '<span class="text-xs text-red-400 ml-2 flex-shrink-0">bereits gespielt</span>' : ''}
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

async function selectPlayer(pid, name, club) {
  if (g.usedIds.has(pid) || !g.activeCell) return;
  const { r, c } = g.activeCell;
  if (g.mode === 'solo') return soloSelectPlayer(pid, name, club, r, c);
  if (g.mode === 'online') return onlineSelectPlayer(pid, name, club, r, c);
  return localSelectPlayer(pid, name, club, r, c);
}

// ─── Status, Timer, Konfetti, Endspiel-Overlay (gemeinsam) ─────────────────────

function updateStatus() {
  updateStreakDisplay();
  if (g.winner) return;
  if (g.mode === 'solo') {
    document.getElementById('status-text').textContent = `Zelle ${g.soloAttempted + 1} von 9`;
    return;
  }
  if (g.mode === 'online') {
    const yourTurn = g.current === g.onlineSlot;
    document.getElementById('status-text').textContent = yourTurn ? 'Du bist dran' : 'Gegner ist dran…';
    return;
  }
  const color = g.current === 1 ? '#ef4444' : '#3b82f6';
  const sym   = g.current === 1 ? 'X' : 'O';
  document.getElementById('status-text').innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px;">
    <span style="width:10px;height:10px;border-radius:50%;background:${color};flex-shrink:0;display:inline-block"></span>
    ${sym} ist dran
  </span>`;
}

function setStatus(msg) {
  document.getElementById('status-text').textContent = msg;
}

function updateStreakDisplay() {
  const el = document.getElementById('streak-display');
  if (g.mode !== 'local') { el.classList.add('hidden'); el.classList.remove('flex'); return; }
  const s = g.streak[g.current] || 0;
  if (s >= 2 && !g.winner) {
    el.classList.remove('hidden');
    el.classList.add('flex');
    el.textContent = `🔥 ${s}`;
  } else {
    el.classList.add('hidden');
    el.classList.remove('flex');
  }
}

// The round result is shown as a banner inline above the board — not a
// blocking popup — so the revealed solution underneath is visible right away
// without needing to dismiss anything first.
function showEndBanner(icon, title, sub, extra, showReplay = true) {
  document.getElementById('end-icon').textContent  = icon;
  document.getElementById('end-title').textContent = title;
  document.getElementById('end-sub').textContent   = sub;
  document.getElementById('end-extra').textContent = extra || '';
  const replayBtn = document.getElementById('end-new-game');
  replayBtn.classList.toggle('hidden', !showReplay);
  replayBtn.disabled = false;
  replayBtn.textContent = g.mode === 'online' ? '🔁 Revanche' : 'Nochmal spielen';
  document.getElementById('end-banner').classList.remove('hidden');
}

function hideEndBanner() {
  document.getElementById('end-banner').classList.add('hidden');
}

// Online rematches need both players' agreement — see updateRematchButtonState,
// which keeps this button in sync (waiting / accept / ask) on every poll
// while the round is over. Solo/local restart immediately on click since
// there's no one else to ask.
document.getElementById('end-new-game').addEventListener('click', () => {
  if (g.mode === 'solo') { hideEndBanner(); newSoloRound(); }
  else if (g.mode === 'local') { hideEndBanner(); newLocalRound(); }
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
  document.getElementById('timer-display').textContent = `⏱ ${formatTime(g.elapsedSeconds)}`;
}

function fireConfetti() {
  const colors = ['#fbbf24', '#ef4444', '#3b82f6', '#22c55e', '#ffffff'];
  const layer = document.getElementById('confetti-layer');
  const pieces = 70;
  for (let i = 0; i < pieces; i++) {
    const el = document.createElement('div');
    const color = colors[i % colors.length];
    const left = Math.random() * 100;
    const delay = Math.random() * 0.35;
    const duration = 1.6 + Math.random() * 1.3;
    const rotate = Math.random() * 360;
    const w = 6 + Math.random() * 6;
    el.style.cssText = `position:absolute;top:-20px;left:${left}%;width:${w}px;height:${w * 0.4}px;` +
      `background:${color};opacity:.9;transform:rotate(${rotate}deg);` +
      `animation:confetti-fall ${duration}s ease-in ${delay}s forwards;`;
    layer.appendChild(el);
    setTimeout(() => el.remove(), (duration + delay) * 1000 + 150);
  }
}

// ─── Modus: 1v1 Lokal ───────────────────────────────────────────────────────────

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
  setStatus('Rätsel wird geladen…');
  stopTimer();
  hideEndBanner();
  document.getElementById('board').innerHTML = '';
  document.getElementById('btn-give-up').disabled = false;

  Object.assign(g, {
    rows: [], cols: [],
    board: [[null,null,null],[null,null,null],[null,null,null]],
    current: 1, winner: null, usedIds: new Set(), activeCell: null, winCells: [],
    streak: { 1: 0, 2: 0 }, elapsedSeconds: 0, solution: null,
  });
  updateStreakDisplay();
  updateTimerDisplay();

  const resp = await fetch(`/api/game/new?${genParams().toString()}`);
  if (!resp.ok) {
    setStatus('Kein Rätsel gefunden – bitte erneut versuchen.');
    return;
  }
  const data = await resp.json();
  g.rows = data.rows;
  g.cols = data.cols;

  renderBoard();
  updateStatus();
  startTimer();
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
  if (g.board.flat().every(c => c !== null)) g.winner = 'draw';
}

function placeLocal(r, c, playerId, name, club) {
  g.board[r][c] = { status: 'correct', player: g.current, id: playerId, name, club };
  g.usedIds.add(playerId);

  g.streak[g.current]++;
  stats.local.correct++;
  if (g.streak[g.current] > stats.local.bestStreak) stats.local.bestStreak = g.streak[g.current];
  saveStats();

  checkWinnerLocal();
  refreshCell(r, c);
  if (g.winner) { endGameLocal(); return; }
  g.current = g.current === 1 ? 2 : 1;
  updateStatus();
}

async function localSelectPlayer(pid, name, club, r, c) {
  const resp = await fetch('/api/game/validate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ player_id: pid, row_id: g.rows[r].id, col_id: g.cols[c].id }),
  });
  const data = await resp.json();
  if (data.valid) {
    closeModal();
    placeLocal(r, c, pid, name, club);
  } else {
    stats.local.wrong++;
    g.streak[g.current] = 0;
    saveStats();
    const err = document.getElementById('search-error');
    err.textContent = `${name} passt hier nicht – nächster Spieler ist dran!`;
    err.classList.remove('hidden');
    setTimeout(() => {
      closeModal();
      g.current = g.current === 1 ? 2 : 1;
      updateStatus();
    }, 1500);
  }
}

async function endGameLocal() {
  stopTimer();
  // The banner below now carries the result — the status bar just needs to
  // stop showing a stale "X ist dran" from before the game ended (it used
  // to sit unnoticed behind the old blocking modal).
  setStatus('Runde beendet.');
  document.getElementById('btn-give-up').disabled = true;
  g.rows.forEach((_, r) => g.cols.forEach((__, c) => refreshCell(r, c)));

  stats.local.gamesPlayed++;
  const timeStr = formatTime(g.elapsedSeconds);

  if (g.winner === 'draw') {
    stats.local.draws++;
    saveStats();
    showEndBanner('🤝', 'Unentschieden!', 'Gut gespielt – kein Gewinner diesmal.', `⏱ ${timeStr}`);
  } else {
    stats.local.wins[g.winner] = (stats.local.wins[g.winner] || 0) + 1;
    if (stats.local.fastestWinSeconds == null || g.elapsedSeconds < stats.local.fastestWinSeconds) {
      stats.local.fastestWinSeconds = g.elapsedSeconds;
    }
    saveStats();
    fireConfetti();
    const gaveUp = g.winCells.length === 0;
    const winnerSym = g.winner === 1 ? 'X' : 'O';
    const loserSym  = g.winner === 1 ? 'O' : 'X';
    showEndBanner(
      g.winner === 1 ? '🔴' : '🔵',
      `${winnerSym} gewinnt!`,
      gaveUp ? `${loserSym} hat aufgegeben.` : `${winnerSym} hat das Spiel gewonnen!`,
      `⏱ ${timeStr} · 🔥 Beste Serie: ${stats.local.bestStreak}`
    );
  }
  await revealSolutions();
}

// ─── Modus: Solo ────────────────────────────────────────────────────────────────

async function startSolo() {
  g.mode = 'solo';
  showScreen('board');
  updateModeChrome();
  await newSoloRound();
}

async function newSoloRound() {
  setStatus('Rätsel wird geladen…');
  stopTimer();
  hideEndBanner();
  document.getElementById('board').innerHTML = '';
  document.getElementById('btn-give-up').disabled = false;

  Object.assign(g, {
    rows: [], cols: [],
    board: [[null,null,null],[null,null,null],[null,null,null]],
    current: 1, winner: null, usedIds: new Set(), activeCell: null, winCells: [],
    elapsedSeconds: 0, solution: null, soloAttempted: 0, soloCorrect: 0,
  });
  updateTimerDisplay();

  const resp = await fetch(`/api/game/new?${genParams().toString()}`);
  if (!resp.ok) {
    setStatus('Kein Rätsel gefunden – bitte erneut versuchen.');
    return;
  }
  const data = await resp.json();
  g.rows = data.rows;
  g.cols = data.cols;

  renderBoard();
  updateStatus();
  startTimer();
}

async function soloSelectPlayer(pid, name, club, r, c) {
  const resp = await fetch('/api/game/validate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ player_id: pid, row_id: g.rows[r].id, col_id: g.cols[c].id }),
  });
  const data = await resp.json();
  closeModal();
  g.usedIds.add(pid);
  g.soloAttempted++;
  if (data.valid) {
    g.board[r][c] = { status: 'correct', player: 1, id: pid, name, club };
    g.soloCorrect++;
  } else {
    g.board[r][c] = { status: 'missed' };
  }
  refreshCell(r, c);
  updateStatus();
  if (g.soloAttempted >= 9) {
    g.winner = 'complete';
    await endGameSolo();
  }
}

function giveUpSolo() {
  // Leave untouched cells empty (not 'missed') so endGameSolo's
  // revealSolutions() renders the actual answer in them, per cellHtml's
  // `gone && g.solution` branch — "Falsch" is reserved for cells the
  // player actually got wrong.
  g.soloAttempted = 9;
  g.winner = 'complete';
  endGameSolo();
}

async function endGameSolo() {
  stopTimer();
  resetGiveUpConfirm();
  document.getElementById('btn-give-up').disabled = true;
  g.rows.forEach((_, r) => g.cols.forEach((__, c) => refreshCell(r, c)));

  stats.solo.rounds++;
  stats.solo.correct += g.soloCorrect;
  stats.solo.cells += 9;
  if (g.soloCorrect > stats.solo.bestCorrect) stats.solo.bestCorrect = g.soloCorrect;
  saveStats();

  const perfect = g.soloCorrect === 9;
  if (perfect) fireConfetti();
  showEndBanner(
    perfect ? '🏆' : '🧩',
    `${g.soloCorrect} / 9 richtig`,
    perfect ? 'Perfekte Runde!' : 'Runde beendet.',
    `⏱ ${formatTime(g.elapsedSeconds)}`
  );
  await revealSolutions();
}

// ─── Modus: 1v1 Online ──────────────────────────────────────────────────────────

function renderLobbyHome() {
  document.getElementById('online-lobby-body').innerHTML = `
    <div class="bg-green-800/60 border border-green-600/40 rounded-2xl p-6 flex flex-col gap-4 items-center text-center">
      <div class="text-4xl">🌐</div>
      <button id="btn-create-room" class="w-full bg-yellow-400 hover:bg-yellow-300 text-slate-900 font-bold text-sm px-4 py-2.5 rounded-xl transition-colors">Raum erstellen</button>
      <div class="text-green-200/60 text-xs">— oder —</div>
      <div class="w-full flex gap-2">
        <input id="join-code-input" maxlength="5" placeholder="CODE" autocomplete="off"
          class="flex-1 uppercase tracking-widest text-center border-2 border-green-300 rounded-lg px-3 py-2 text-sm font-bold focus:outline-none focus:border-green-600">
        <button id="btn-join-room" class="bg-slate-700 hover:bg-slate-600 text-white font-bold text-sm px-4 py-2 rounded-lg transition-colors">Beitreten</button>
      </div>
      <p id="lobby-error" class="text-red-300 text-xs hidden"></p>
    </div>`;
  document.getElementById('btn-create-room').addEventListener('click', createOnlineRoom);
  document.getElementById('btn-join-room').addEventListener('click', () => {
    const code = document.getElementById('join-code-input').value.trim();
    if (code.length >= 4) joinOnlineRoom(code);
  });
  document.getElementById('join-code-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('btn-join-room').click();
  });
}

// navigator.clipboard requires a "secure context" (https:, or http://
// localhost/127.0.0.1) — it's simply undefined everywhere else, e.g. when
// two people test multiplayer across devices via the host's plain-http LAN
// address. Falls back to the older execCommand('copy') approach, which
// works in insecure contexts too.
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
    // Nothing more we can do — the button's "✅ Kopiert" feedback still
    // fires, but that's a pre-existing tradeoff, not something new here.
  }
  document.body.removeChild(el);
}

function renderLobbyWaiting(code) {
  const link = `${location.origin}/game?join=${code}`;
  document.getElementById('online-lobby-body').innerHTML = `
    <div class="bg-green-800/60 border border-green-600/40 rounded-2xl p-6 flex flex-col gap-3 items-center text-center">
      <div class="text-sm text-green-200/80">Warte auf Gegner…</div>
      <div class="text-4xl font-black tracking-[0.3em] text-yellow-400">${esc(code)}</div>
      <button id="btn-copy-link" class="text-xs bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded-lg transition-colors">🔗 Link kopieren</button>
      <div class="flex items-center gap-2 text-green-200/60 text-xs mt-2">
        <span class="inline-block w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
        Sobald dein Freund beitritt, geht's los
      </div>
    </div>`;
  document.getElementById('btn-copy-link').addEventListener('click', () => {
    copyToClipboard(link);
    const btn = document.getElementById('btn-copy-link');
    if (!btn) return;
    btn.textContent = '✅ Kopiert';
    setTimeout(() => { btn.textContent = '🔗 Link kopieren'; }, 1500);
  });
}

function showLobbyError(msg) {
  const el = document.getElementById('lobby-error');
  if (!el) return;
  el.textContent = msg;
  el.classList.remove('hidden');
}

async function createOnlineRoom() {
  Object.assign(g, { onlineBoardEntered: false, onlineFinished: false });
  const resp = await fetch('/api/multiplayer/rooms', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      difficulty, league: selectedLeague || undefined,
      excludedTypes: settings.excludedTypes, excludedCategoryIds: settings.excludedCategoryIds,
    }),
  });
  if (!resp.ok) { showLobbyError('Raum konnte nicht erstellt werden.'); return; }
  const data = await resp.json();
  g.onlineCode = data.code;
  g.onlineToken = data.token;
  g.onlineSlot = data.slot;
  renderLobbyWaiting(data.code);
  connectOnlineEvents();
}

async function joinOnlineRoom(code) {
  Object.assign(g, { onlineBoardEntered: false, onlineFinished: false });
  code = code.toUpperCase();
  const resp = await fetch(`/api/multiplayer/rooms/${code}/join`, { method: 'POST' });
  if (!resp.ok) { showLobbyError('Raum nicht gefunden oder schon voll.'); return; }
  const data = await resp.json();
  g.onlineCode = data.code;
  g.onlineToken = data.token;
  g.onlineSlot = data.slot;
  renderLobbyWaiting(data.code);
  connectOnlineEvents();
  await refreshOnlineState();
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
  showScreen('board');
  updateModeChrome();
  hideEndBanner();
  document.getElementById('btn-give-up').disabled = false;
  g.elapsedSeconds = 0;
  g.solution = null;
  startTimer();
}

function applyOnlineState(data) {
  const justConnected = data.playersConnected === 2 && !g.onlineBoardEntered;
  // A rematch looks like "the round we already finished is now back to no
  // winner and an empty board" — reset the finished-flag and re-enter the
  // board the same way both players do on first connecting.
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

  renderBoard();
  if (g.winner) {
    document.getElementById('btn-give-up').disabled = true;
    if (!g.onlineFinished) {
      g.onlineFinished = true;
      finishOnline();
    }
    updateRematchButtonState(data.rematchRequested || []);
  } else {
    updateStatus();
  }
}

// Keeps the "Revanche" button in sync with both players' state on every
// poll/SSE tick while the round is over: nobody has asked yet, you asked and
// are waiting on the opponent, or the opponent asked and a click from you
// would complete the match (handled server-side by request_rematch).
function updateRematchButtonState(requested) {
  if (g.mode !== 'online') return;
  const btn = document.getElementById('end-new-game');
  if (btn.classList.contains('hidden')) return;
  const youRequested = requested.includes(g.onlineSlot);
  const oppRequested = requested.some(s => s !== g.onlineSlot);
  if (youRequested) {
    btn.disabled = true;
    btn.textContent = '⏳ Warte auf Gegner…';
  } else if (oppRequested) {
    btn.disabled = false;
    btn.textContent = '✅ Revanche annehmen';
  } else {
    btn.disabled = false;
    btn.textContent = '🔁 Revanche';
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
  // Records this player's vote server-side; the round only actually resets
  // once the opponent has voted too. Refresh right away (rather than
  // waiting for the next ~1s SSE tick) so the button's waiting/accepted
  // state — or the actual round reset once both have agreed, picked up by
  // applyOnlineState's "rematch detected" branch — shows up immediately.
  const resp = await fetch(`/api/multiplayer/rooms/${g.onlineCode}/rematch`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: g.onlineToken }),
  });
  if (!resp.ok) {
    alert('Revanche nicht möglich – Raum eventuell nicht mehr aktiv.');
    document.getElementById('end-banner').classList.remove('hidden');
    return;
  }
  await refreshOnlineState();
}

async function finishOnline() {
  stopTimer();
  setStatus('Runde beendet.');
  stats.online.rounds++;

  const timeStr = formatTime(g.elapsedSeconds);
  if (g.winner === 'draw') {
    stats.online.draws++;
    saveStats();
    showEndBanner('🤝', 'Unentschieden!', 'Gut gespielt – kein Gewinner diesmal.', `⏱ ${timeStr}`, true);
  } else {
    const youWon = g.winner === g.onlineSlot;
    if (youWon) stats.online.wins++; else stats.online.losses++;
    saveStats();
    if (youWon) fireConfetti();
    showEndBanner(
      youWon ? '🏆' : '💔',
      youWon ? 'Du gewinnst!' : 'Du verlierst',
      youWon ? 'Gut gespielt!' : 'Nächstes Mal klappt’s!',
      `⏱ ${timeStr}`,
      true
    );
  }
  await revealSolutions();
}

document.getElementById('btn-give-up').addEventListener('click', async (e) => {
  if (g.winner) return;
  // Same inline two-step confirm (click to arm, click again to confirm) for
  // every mode — no browser confirm() popup, in solo or local/online either.
  if (!giveUpConfirming) {
    giveUpConfirming = true;
    e.currentTarget.textContent = 'Wirklich aufgeben?';
    e.currentTarget.classList.remove('bg-orange-500', 'hover:bg-orange-400');
    e.currentTarget.classList.add('bg-red-600', 'hover:bg-red-500');
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

// ─── Statistik-Anzeige ─────────────────────────────────────────────────────────

function renderStats() {
  const l = stats.local, s = stats.solo, o = stats.online;
  const accuracy = (l.correct + l.wrong) ? Math.round((l.correct / (l.correct + l.wrong)) * 100) : 0;
  const fastest = l.fastestWinSeconds != null ? formatTime(l.fastestWinSeconds) : '–';
  const soloAccuracy = s.cells ? Math.round((s.correct / s.cells) * 100) : 0;

  document.getElementById('stats-body').innerHTML = `
    <div>
      <div class="text-xs font-bold uppercase tracking-wide text-slate-400 mb-2">🛋️ 1v1 Lokal</div>
      <div class="grid grid-cols-2 gap-2 text-center">
        <div class="bg-slate-50 rounded-xl p-2.5"><div class="text-xl font-black text-slate-700">${l.gamesPlayed}</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Spiele</div></div>
        <div class="bg-slate-50 rounded-xl p-2.5"><div class="text-xl font-black text-amber-500">${l.bestStreak} 🔥</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Beste Serie</div></div>
        <div class="bg-red-50 rounded-xl p-2.5"><div class="text-base font-black text-red-500">${l.wins[1]}</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Siege X</div></div>
        <div class="bg-blue-50 rounded-xl p-2.5"><div class="text-base font-black text-blue-500">${l.wins[2]}</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Siege O</div></div>
        <div class="bg-slate-50 rounded-xl p-2.5"><div class="text-base font-black text-slate-700">${accuracy}%</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Trefferquote</div></div>
        <div class="bg-slate-50 rounded-xl p-2.5"><div class="text-base font-black text-slate-700">${fastest}</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Schnellster Sieg</div></div>
      </div>
    </div>
    <div>
      <div class="text-xs font-bold uppercase tracking-wide text-slate-400 mb-2">🧩 Solo</div>
      <div class="grid grid-cols-2 gap-2 text-center">
        <div class="bg-slate-50 rounded-xl p-2.5"><div class="text-xl font-black text-slate-700">${s.rounds}</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Runden</div></div>
        <div class="bg-slate-50 rounded-xl p-2.5"><div class="text-xl font-black text-emerald-500">${s.bestCorrect}/9</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Bestes Ergebnis</div></div>
        <div class="bg-slate-50 rounded-xl p-2.5 col-span-2"><div class="text-base font-black text-slate-700">${soloAccuracy}%</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Trefferquote gesamt</div></div>
      </div>
    </div>
    <div>
      <div class="text-xs font-bold uppercase tracking-wide text-slate-400 mb-2">🌐 1v1 Online</div>
      <div class="grid grid-cols-3 gap-2 text-center">
        <div class="bg-slate-50 rounded-xl p-2.5"><div class="text-base font-black text-slate-700">${o.rounds}</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Spiele</div></div>
        <div class="bg-emerald-50 rounded-xl p-2.5"><div class="text-base font-black text-emerald-600">${o.wins}</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Siege</div></div>
        <div class="bg-red-50 rounded-xl p-2.5"><div class="text-base font-black text-red-500">${o.losses}</div><div class="text-[10px] text-slate-400 font-semibold uppercase">Niederlagen</div></div>
      </div>
    </div>`;
}

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

// ─── Schwierigkeitsgrad-Buttons ───────────────────────────────────────────────

function setDifficulty(d) {
  difficulty = d;
  document.querySelectorAll('.diff-btn').forEach(btn => {
    const active = parseInt(btn.dataset.diff) === d;
    btn.className = `diff-btn flex-1 px-2.5 py-2 text-xs font-semibold transition-colors ${
      active ? 'bg-yellow-400 text-slate-900' : 'bg-green-900/40 text-green-200 hover:text-white'
    }`;
    if (btn.dataset.diff === '2') btn.classList.add('border-x', 'border-green-600/40');
  });
}

document.querySelectorAll('.diff-btn').forEach(btn => {
  btn.addEventListener('click', () => setDifficulty(parseInt(btn.dataset.diff)));
});

// ─── Sonstige Event-Listener ───────────────────────────────────────────────────

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal').addEventListener('click', e => {
  if (e.target.id === 'modal') closeModal();
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// ─── Start ────────────────────────────────────────────────────────────────────

(function init() {
  const joinCode = new URLSearchParams(location.search).get('join');
  if (joinCode) {
    g.mode = 'online';
    showScreen('online-lobby');
    updateModeChrome();
    renderLobbyHome();
    history.replaceState({}, '', '/game');
    joinOnlineRoom(joinCode);
  } else {
    showScreen('mode-select');
  }
})();
