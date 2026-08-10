// ─── SVG & badges ───────────────────────────────────────────────────────────

function shirtSvg() {
  // Flat, single-color "+" — an empty slot, nothing more. No shading, no
  // gradient, no icon library glyph. Accent-colored so "orange = tap here,
  // this is interactive" reads consistently across the board.
  return `<span style="font-size:28px;line-height:1;font-weight:300;color:var(--accent)">+</span>`;
}

function markBadge(player) {
  // Players are told apart by glyph (X vs O), not by a second/third color —
  // the palette stays background + neutral + accent.
  const sym = player === 1 ? 'X' : 'O';
  return `<span class="text-xs font-black w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style="border:1px solid var(--card-border);color:var(--text-dim)">${sym}</span>`;
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
  soloVariant: null,  // null | 'daily' | 'custom' — a solo round that isn't a plain random one
  dailyDate: null,    // the server's date string for the currently-loaded daily grid
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
  // editor:
  editor: { row: [null, null, null], col: [null, null, null] },
  editorSavedCode: null,
  editorCounts: null, // 3x3, entry is null until both that row+col are picked
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

let selectedLeague = '';

function genParams() {
  const p = new URLSearchParams({ difficulty: String(difficulty) });
  if (selectedLeague) p.set('league', selectedLeague);
  return p;
}

// ─── Router ───────────────────────────────────────────────────────────────────

function showScreen(name) {
  document.getElementById('screen-mode-select').classList.toggle('hidden', name !== 'mode-select');
  document.getElementById('screen-setup').classList.toggle('hidden', name !== 'setup');
  document.getElementById('screen-online-lobby').classList.toggle('hidden', name !== 'online-lobby');
  document.getElementById('screen-daily-done').classList.toggle('hidden', name !== 'daily-done');
  document.getElementById('screen-editor').classList.toggle('hidden', name !== 'editor');
  document.getElementById('screen-board').classList.toggle('hidden', name !== 'board');
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

document.querySelectorAll('[data-mode]').forEach(btn => {
  btn.addEventListener('click', () => selectMode(btn.dataset.mode));
});

// Difficulty and league are chosen once, on their own screen — for solo/
// local right after picking the mode; for online, only after choosing to
// host (see renderLobbyHome's "Raum erstellen" handler), since a joiner
// never needs it at all — the room creator's settings apply to them too, and
// making them pick unused settings before even seeing the host/join choice
// was the previous (wrong) order.
function enterSetupScreen(pendingMode) {
  g.pendingMode = pendingMode;
  document.getElementById('btn-setup-continue').disabled = false;
  showScreen('setup');
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
    // Creating a room is a ~0.5s round-trip — without this guard a fast
    // double-click fires it twice, creating two rooms and leaving the
    // client attached to whichever response happens to land last. Capture
    // the button now, synchronously — Event.currentTarget is nulled out by
    // the browser once dispatch finishes, so it can't be read inside the
    // .finally() below (after the await in createOnlineRoom has yielded).
    const btn = e.currentTarget;
    if (btn.disabled) return;
    btn.disabled = true;
    createOnlineRoom().finally(() => { btn.disabled = false; });
  }
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

// ─── Spielfeld rendern (gemeinsam für alle Modi) ───────────────────────────────

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
}

// Filled/missed cells have nothing to do on tap; an empty cell before the
// round ends opens the player search; an empty cell after the round ends
// (once solutions are loaded) opens the full-answer sheet instead — same
// data-cell wiring either way, the state at click time decides.
function handleCellClick(r, c) {
  if (g.board[r][c]) return;
  if (g.winner !== null) {
    if (g.solution) openSolutionSheet(r, c);
    return;
  }
  openCell(r, c);
}

function categoryIconHtml(cat) {
  // Real crest/flag artwork and team brand colors are content, not
  // decoration — they stay in full color. Only the generic emoji fallback
  // (trophy/ball/etc. — not tied to any specific team) is flattened to
  // grayscale, so the palette still can't pick up arbitrary extra hues
  // from whatever the emoji font happens to render.
  // Real downloaded flag/crest image (see fetch_flags.py, fetch_club_logos.py)
  // wins whenever available — looks far better than the emoji font or the
  // generic initial badge.
  if (cat.icon_image) {
    return `<img src="${esc(cat.icon_image)}" alt="" class="tt-icon object-contain flex-shrink-0">`;
  }
  // Dynamically generated clubs without a hand-picked emoji (the vast
  // majority of ~6,500 clubs) carry icon_letter/icon_color instead of an
  // icon string — render a small badge in that club's own color.
  if (!cat.icon && cat.icon_letter) {
    return `<div class="tt-icon rounded-full flex items-center justify-center text-white font-black text-sm flex-shrink-0"
      style="background:${esc(cat.icon_color || 'var(--card-border)')}">${esc(cat.icon_letter)}</div>`;
  }
  return `<div class="tt-icon-mono tt-icon leading-none flex-shrink-0 flex items-center justify-center"
    style="font-size:clamp(18px,6vw,26px)">${cat.icon || '⚽'}</div>`;
}

function headerCellHtml(cat) {
  // The icon (crest/flag/emoji) carries the primary identification — the
  // label backs it up, wrapping at word boundaries (overflow-wrap:anywhere
  // is only a fallback for the rare single "word" — a long club name with
  // no spaces — that still can't fit on its own line). Font size and icon
  // size both scale down on narrow phones (.tt-icon, .tt-cat-label) so a
  // name like "Bor. M'gladbach" gets enough room across 3 lines instead of
  // being cut mid-word at 2.
  return `
    <div class="tt-cell flex flex-col items-center justify-center p-2.5 tt-slot overflow-hidden gap-1"
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

  // Every state below shares the same .tt-cell card (fill, border, radius) —
  // only the content changes, and the only border-color states are
  // .is-active (search modal open on this cell) and .is-win, both using
  // the one accent color, flat, no glow/animation.
  if (entry && entry.status === 'missed') {
    return `
      <div class="tt-cell flex flex-col items-center justify-center p-2 tt-slot">
        <div class="text-2xl mb-1" style="color:var(--text-dim)">✕</div>
        <div class="tt-label">Falsch</div>
      </div>`;
  }

  if (entry) {
    // Correct answers need a clear "you got this" signal — everywhere but
    // solo, the X/O badge already implies it (a missed guess never reaches
    // this branch, it's the 'missed' one above). Solo suppresses that
    // badge, which left correct cells looking like plain bold text with
    // no marker at all — easy to mistake for a "Lösung" reveal cell at a
    // glance. A small accent checkmark closes that gap.
    const badge = g.mode === 'solo'
      ? `<span class="text-xs font-black w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style="border:1.5px solid var(--accent);color:var(--accent)">✓</span>`
      : markBadge(entry.player);
    return `
      <div class="tt-cell ${isWin ? 'is-win' : ''} flex flex-col items-center justify-center p-3 tt-slot"
           data-cell="${r},${c}">
        <div class="flex justify-end w-full mb-1">${badge}</div>
        <div class="font-bold text-center leading-tight" style="color:var(--text)">${esc(entry.name)}</div>
        <div class="tt-cell-sub text-xs mt-1 text-center" style="color:var(--text-dim)">${esc(entry.club || '')}</div>
      </div>`;
  }

  if (gone && g.solution) {
    // A real name list overflows a mobile-width cell fast ("Mattia
    // Graffiedi, Marco Donadel, Cristian Brocchi +2 weitere" wraps to 4-5
    // lines and breaks the grid's rhythm) — so the cell itself only shows
    // a short summary, and tapping it opens the full list in a sheet
    // (openSolutionSheet) instead of cramming it in.
    const cellSol = g.solution[r][c];
    const count = cellSol.count || 0;
    const first = cellSol.players?.[0] ? esc(cellSol.players[0].name) : '';
    const summary = count === 0 ? '–' : count === 1 ? first : `${first} +${count - 1}`;
    // No "LÖSUNG" caption — repeated on every one of these cells it was
    // just noise, and the muted color plus the checkmark on cells you did
    // answer (see above) already says "this one wasn't yours" on its own.
    return `
      <button data-cell="${r},${c}" class="tt-cell tt-card-hover flex flex-col items-center justify-center p-2.5 tt-slot text-center">
        <div class="tt-cell-sub text-xs leading-snug" style="color:var(--text-dim)">${summary}</div>
      </button>`;
  }

  // Online mode: names can only be entered on your own turn — the server
  // already rejects an out-of-turn move, but the cell itself should refuse
  // to even open the search modal instead of letting you type/search/pick
  // a name first and only finding out afterward.
  const notYourTurn = g.mode === 'online' && g.onlineSlot && g.current !== g.onlineSlot;
  const disabled = gone || notYourTurn;
  // The cell currently open in the search modal gets .is-active, recomputed
  // here (not just set on click) so it survives an incidental re-render
  // (e.g. an online-mode poll) while the modal is still open.
  const isActive = !disabled && g.activeCell && g.activeCell.r === r && g.activeCell.c === c;
  return `
    <button ${disabled ? 'disabled' : ''} data-cell="${r},${c}"
      class="tt-cell ${isActive ? 'is-active' : ''} flex flex-col items-center justify-center px-2 tt-slot w-full">
      ${shirtSvg()}
      <span class="tt-label mt-1">Spieler wählen</span>
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
    newEl.addEventListener('click', () => handleCellClick(r, c));
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

// The full answer list for a cell the player never filled — opened from
// the compact "Lösung" summary in the cell itself (see cellHtml).
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

// ─── Zell-Interaktion (gemeinsam) ──────────────────────────────────────────────

function markActiveCell(r, c) {
  document.querySelectorAll('.is-active').forEach(el => el.classList.remove('is-active'));
  document.querySelector(`[data-cell="${r},${c}"]`)?.classList.add('is-active');
}

function clearActiveCell() {
  document.querySelectorAll('.is-active').forEach(el => el.classList.remove('is-active'));
}

function openCell(r, c) {
  if (g.winner || g.board[r][c]) return;
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

async function doSearch(q) {
  if (!g.activeCell) return;
  const resp = await fetch(`/api/game/search?q=${encodeURIComponent(q)}`);
  const data = await resp.json();
  const container = document.getElementById('search-results');

  if (!data.players?.length) {
    container.innerHTML = `<p class="text-xs text-center py-2" style="color:var(--text-faint)">Keine Spieler gefunden</p>`;
    return;
  }

  // The club used to be shown here as a second line, but it was mostly
  // noise (the guess is the player's name, not their club) — dropped, but
  // still carried via data-club so the filled cell can still record it.
  // The one case a second line actually helps: two results with the exact
  // same name are otherwise indistinguishable, so those (only those) show
  // age instead, as a disambiguator.
  const nameCounts = {};
  data.players.forEach(p => { nameCounts[p.name] = (nameCounts[p.name] || 0) + 1; });

  container.innerHTML = data.players.map(p => {
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
    // A running score (correct answers so far) instead of an attempt
    // counter — "0/9" reads instantly, no "Zelle N von 9" framing needed.
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
  // Whose turn it is (X vs O) is told apart by the glyph, not by a
  // per-player color — the dot just marks "this is the live turn", always
  // in the one accent color.
  const sym = g.current === 1 ? 'X' : 'O';
  document.getElementById('status-text').innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px;">
    <span style="width:8px;height:8px;border-radius:50%;background:var(--accent);flex-shrink:0;display:inline-block"></span>
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

// The round result folds into the existing status card instead of a
// separate popup/overlay: the live "X / 9" or turn indicator in status-text
// is replaced by the final result, a thin one-line sub-message appears
// right below it (still inside the same card), and the button row swaps
// "Aufgeben" for the result actions — no new block, no dimmed backdrop, and
// the revealed board underneath stays fully visible and tappable the whole
// time (see openSolutionSheet).
function showEndBanner(icon, title, sub, extra, showReplay = true) {
  document.getElementById('status-text').textContent = `${icon} ${title}`;
  const subEl = document.getElementById('end-banner');
  subEl.textContent = extra ? `${sub} · ${extra}` : sub;
  subEl.classList.remove('hidden');

  const replayBtn = document.getElementById('end-new-game');
  replayBtn.classList.toggle('hidden', !showReplay);
  replayBtn.disabled = false;
  replayBtn.textContent = g.mode === 'online' ? '🔁 Revanche' : 'Nochmal spielen';
  // Only the daily-completion branch in endGameSolo shows this — reset it
  // here so a stale "shown" state from an earlier daily round never leaks
  // into a later solo/local/online banner.
  document.getElementById('end-share').classList.add('hidden');

  document.getElementById('btn-give-up').classList.add('hidden');
  document.getElementById('end-actions').classList.remove('hidden');
  document.getElementById('end-actions').classList.add('flex');
}

function hideEndBanner() {
  document.getElementById('end-banner').classList.add('hidden');
  document.getElementById('end-actions').classList.add('hidden');
  document.getElementById('end-actions').classList.remove('flex');
  document.getElementById('btn-give-up').classList.remove('hidden');
}

// Online rematches need both players' agreement — see updateRematchButtonState,
// which keeps this button in sync (waiting / accept / ask) on every poll
// while the round is over. Solo/local restart immediately on click since
// there's no one else to ask.
document.getElementById('end-new-game').addEventListener('click', () => {
  if (g.mode === 'solo' && g.soloVariant === 'custom') {
    // Replay the exact same shared grid, not a new random one — matches
    // what "Nochmal spielen" says (daily hides this button entirely, since
    // it's already played for today; see endGameSolo).
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
    showEndBanner('🤝', 'Unentschieden!', 'Gut gespielt – kein Gewinner diesmal.');
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
      '🏆',
      `${winnerSym} gewinnt!`,
      gaveUp ? `${loserSym} hat aufgegeben.` : `${winnerSym} hat das Spiel gewonnen!`,
      `🔥 Beste Serie: ${stats.local.bestStreak}`
    );
  }
  await revealSolutions();
}

// ─── Modus: Solo ────────────────────────────────────────────────────────────────

async function startSolo() {
  g.mode = 'solo';
  g.soloVariant = null;
  showScreen('board');
  updateModeChrome();
  await newSoloRound();
}

// Shared by plain solo, the daily grid, and a loaded/custom grid — all three
// are mechanically identical (fill 9 cells alone, no opponent); they only
// differ in where rows/cols come from and what happens once the round ends
// (see endGameSolo's soloVariant branches). Split into a "clear the screen
// and start loading" half and a "rows/cols are ready, build the board" half
// so callers can fetch from wherever their puzzle actually comes from in
// between.
function beginSoloRound() {
  setStatus('Rätsel wird geladen…');
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
  });
  updateTimerDisplay();
  renderBoard();
  updateStatus();
  startTimer();
}

async function newSoloRound() {
  g.soloVariant = null;
  beginSoloRound();
  const resp = await fetch(`/api/game/new?${genParams().toString()}`);
  if (!resp.ok) {
    setStatus('Kein Rätsel gefunden – bitte erneut versuchen.');
    return;
  }
  const data = await resp.json();
  finishSoloRoundSetup(data.rows, data.cols);
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

  const perfect = g.soloCorrect === 9;

  if (g.soloVariant === 'daily') {
    // Giving up still "completes" today's puzzle and keeps the streak alive
    // — the streak is about showing up daily, not about getting a perfect
    // score (getting all 9 right is much harder here than guessing a
    // Wordle, so requiring perfection would make streaks nearly unreachable).
    const daily = recordDailyCompletion(g.dailyDate, g.soloCorrect);
    updateDailyCardBadge();
    if (perfect) fireConfetti();
    showEndBanner(
      perfect ? '🏆' : '📅',
      `${g.soloCorrect} / 9 richtig`,
      `🔥 Streak: ${daily.currentStreak} Tag${daily.currentStreak === 1 ? '' : 'e'}`,
      `Beste Serie: ${daily.bestStreak}`,
      false // already played today — no "Nochmal spielen"
    );
    document.getElementById('end-share').classList.remove('hidden');
  } else if (g.soloVariant === 'custom') {
    // Doesn't count toward the "Solo" stats — a shared/custom grid is a
    // different activity, not a random practice round.
    if (perfect) fireConfetti();
    showEndBanner(
      perfect ? '🏆' : '🧩',
      `${g.soloCorrect} / 9 richtig`,
      perfect ? 'Perfekte Runde!' : 'Rätsel beendet.'
    );
  } else {
    stats.solo.rounds++;
    stats.solo.correct += g.soloCorrect;
    stats.solo.cells += 9;
    if (g.soloCorrect > stats.solo.bestCorrect) stats.solo.bestCorrect = g.soloCorrect;
    saveStats();
    if (perfect) fireConfetti();
    showEndBanner(
      perfect ? '🏆' : '🧩',
      `${g.soloCorrect} / 9 richtig`,
      perfect ? 'Perfekte Runde!' : 'Runde beendet.'
    );
  }
  await revealSolutions();
}

// ─── Modus: Tägliches Rätsel ────────────────────────────────────────────────
// A daily grid the backend generates deterministically from the date (see
// app.py's /api/daily/today) — everyone gets the same puzzle. The "once per
// day" gate and the streak itself live entirely in localStorage, same as
// every other bit of state in this app (stats, settings) — there's no
// server-verified per-device identity anywhere here, and this matches how
// Wordle itself actually works (also localStorage-gated, not server-
// enforced).

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

// Both dates are the server's "YYYY-MM-DD" (UTC) strings — compared as UTC
// midnight instants so this never drifts with the browser's local timezone.
function isNextUtcDay(prevDateStr, nextDateStr) {
  const prev = new Date(`${prevDateStr}T00:00:00Z`).getTime();
  const next = new Date(`${nextDateStr}T00:00:00Z`).getTime();
  return (next - prev) === 86400000;
}

function recordDailyCompletion(date, correct) {
  const d = loadDailyState();
  if (d.completed[date]) return d; // already recorded — idempotent guard
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

async function startDaily() {
  const resp = await fetch('/api/daily/today');
  if (!resp.ok) {
    alert('Tagesrätsel konnte nicht geladen werden.');
    return;
  }
  const data = await resp.json();
  g.dailyDate = data.date;

  const daily = loadDailyState();
  if (daily.completed[data.date]) {
    showDailyAlreadyPlayed(daily, data.date);
    return;
  }

  g.mode = 'solo';
  g.soloVariant = 'daily';
  showScreen('board');
  updateModeChrome();
  beginSoloRound();
  finishSoloRoundSetup(data.rows, data.cols);
}

function showDailyAlreadyPlayed(dailyState, date) {
  const result = dailyState.completed[date];
  document.getElementById('daily-done-score').textContent = `${result.correct} / 9 richtig`;
  document.getElementById('daily-done-streak').textContent = `🔥 ${dailyState.currentStreak} Tag${dailyState.currentStreak === 1 ? '' : 'e'} in Folge`;
  document.getElementById('daily-done-best').textContent = `Beste Serie: ${dailyState.bestStreak}`;
  showScreen('daily-done');
}

document.getElementById('daily-card').addEventListener('click', startDaily);
document.getElementById('daily-done-menu').addEventListener('click', goToMenu);
document.getElementById('end-share').addEventListener('click', () => {
  const daily = loadDailyState();
  const result = daily.completed[g.dailyDate];
  if (!result) return;
  const text = `⚽ Tiki-Taka-Toe Tagesrätsel ${g.dailyDate}\n${result.correct}/9 richtig · 🔥 ${daily.currentStreak} Tage Serie\n${location.origin}/game`;
  copyToClipboard(text);
  const btn = document.getElementById('end-share');
  btn.textContent = '✅ Kopiert';
  setTimeout(() => { btn.textContent = '📤 Teilen'; }, 1500);
});

// ─── Editor: eigenes Rätsel bauen, speichern & teilen, per Code laden ──────

function goToEditor() {
  showScreen('editor');
  renderEditorGrid();
  refreshEditorCounts();
}
document.getElementById('btn-editor').addEventListener('click', () => {
  closeMenuDropdown();
  goToEditor();
});
document.getElementById('btn-editor-back').addEventListener('click', goToMenu);

// Same header-cell look as the real board (headerCellHtml/cellHtml above),
// but clickable and empty until a category is picked — so building a grid
// looks like filling in the board you're about to play, not a form.
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

// Debounced+ordered: a slow late response for a stale grid must never
// overwrite a fresher one, so each call carries a token and only the most
// recent one is allowed to apply its result.
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
    if (token !== editorCountsToken) return; // superseded by a newer pick
    g.editorCounts = data.counts || null;
  } catch {
    if (token !== editorCountsToken) return;
    g.editorCounts = null;
  }
  renderEditorGrid();
}

let editorActiveSlot = null; // {side: 'row'|'col', index: 0|1|2}
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
  // A category already used in another slot can't be picked again — but the
  // slot currently being edited should still show its own existing pick as
  // selectable (re-clicking it is a no-op close, not a blocked click).
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
      errorEl.textContent = data.error || 'Rätsel konnte nicht gespeichert werden.';
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
  copyToClipboard(`${location.origin}/game?grid=${g.editorSavedCode}`);
  const btn = document.getElementById('btn-editor-copy-link');
  btn.textContent = '✅ Kopiert';
  setTimeout(() => { btn.textContent = '🔗 Link kopieren'; }, 1500);
});
document.getElementById('btn-editor-play').addEventListener('click', () => {
  if (g.editorSavedCode) loadAndStartCustomGrid(g.editorSavedCode);
});

document.getElementById('btn-editor-load').addEventListener('click', () => {
  const code = document.getElementById('editor-load-code').value.trim();
  if (code.length < 4) return;
  loadAndStartCustomGrid(code);
});
document.getElementById('editor-load-code').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('btn-editor-load').click();
});

async function loadAndStartCustomGrid(code) {
  const errorEl = document.getElementById('editor-load-error');
  errorEl.classList.add('hidden');
  const resp = await fetch(`/api/grids/${encodeURIComponent(code)}`);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    errorEl.textContent = data.error || 'Rätsel nicht gefunden.';
    errorEl.classList.remove('hidden');
    return;
  }
  g.mode = 'solo';
  g.soloVariant = 'custom';
  showScreen('board');
  updateModeChrome();
  beginSoloRound();
  finishSoloRoundSetup(data.rows, data.cols);
}

// ─── Modus: 1v1 Online ──────────────────────────────────────────────────────────

function renderLobbyHome() {
  document.getElementById('online-lobby-body').innerHTML = `
    <div class="tt-card p-6 flex flex-col gap-4 items-center text-center">
      <div class="text-3xl tt-icon-mono">🌐</div>
      <button id="btn-create-room" class="tt-btn-accent w-full text-sm px-4 py-2.5 rounded-xl">Raum erstellen</button>
      <div class="text-xs" style="color:var(--text-dim)">— oder —</div>
      <div class="w-full flex gap-2">
        <input id="join-code-input" maxlength="5" placeholder="CODE" autocomplete="off"
          class="tt-input flex-1 uppercase tracking-widest text-center rounded-lg px-3 py-2 text-sm font-bold">
        <button id="btn-join-room" class="tt-btn-neutral text-sm px-4 py-2 rounded-lg">Beitreten</button>
      </div>
      <p id="lobby-error" class="text-xs hidden" style="color:var(--accent)"></p>
    </div>`;
  // Hosting needs difficulty/league first — that's the setup screen, shown
  // only now (not before this host-vs-join choice) since a joiner never
  // needs it at all (the room's creator-chosen settings apply to them too).
  document.getElementById('btn-create-room').addEventListener('click', () => enterSetupScreen('online-host'));
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
    <div class="tt-card p-6 flex flex-col gap-3 items-center text-center">
      <div class="text-sm" style="color:var(--text-dim)">Warte auf Gegner…</div>
      <div class="text-4xl font-black tracking-[0.3em]" style="color:var(--accent)">${esc(code)}</div>
      <button id="btn-copy-link" class="tt-btn-neutral text-xs px-3 py-1.5 rounded-lg">🔗 Link kopieren</button>
      <div class="flex items-center gap-2 text-xs mt-2" style="color:var(--text-dim)">
        <span class="inline-block w-2 h-2 rounded-full animate-pulse" style="background:var(--accent)"></span>
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
    body: JSON.stringify({ difficulty, league: selectedLeague || undefined }),
  });
  if (!resp.ok) {
    // Creation happens from the setup screen — surface the failure back on
    // the lobby screen (where #lobby-error already lives from renderLobbyHome)
    // rather than leaving the user stranded looking at the setup screen with
    // nothing having visibly happened.
    showScreen('online-lobby');
    showLobbyError('Raum konnte nicht erstellt werden.');
    return;
  }
  const data = await resp.json();
  g.onlineCode = data.code;
  g.onlineToken = data.token;
  g.onlineSlot = data.slot;
  showScreen('online-lobby');
  renderLobbyWaiting(data.code);
  connectOnlineEvents();
}

async function joinOnlineRoom(code) {
  Object.assign(g, { onlineBoardEntered: false, onlineFinished: false });
  code = code.toUpperCase();
  const resp = await fetch(`/api/multiplayer/rooms/${code}/join`, { method: 'POST' });
  if (!resp.ok) {
    showLobbyError('Raum nicht gefunden oder schon voll.');
    const btn = document.getElementById('btn-join-room');
    if (btn) btn.disabled = false;
    return;
  }
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

  if (g.winner === 'draw') {
    stats.online.draws++;
    saveStats();
    showEndBanner('🤝', 'Unentschieden!', 'Gut gespielt – kein Gewinner diesmal.', '', true);
  } else {
    const youWon = g.winner === g.onlineSlot;
    if (youWon) stats.online.wins++; else stats.online.losses++;
    saveStats();
    if (youWon) fireConfetti();
    showEndBanner(
      youWon ? '🏆' : '💔',
      youWon ? 'Du gewinnst!' : 'Du verlierst',
      youWon ? 'Gut gespielt!' : 'Nächstes Mal klappt’s!',
      '',
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

// ─── Statistik-Anzeige ─────────────────────────────────────────────────────────

function renderStats() {
  const l = stats.local, s = stats.solo, o = stats.online;
  const d = loadDailyState();
  const daysPlayed = Object.keys(d.completed).length;
  const accuracy = (l.correct + l.wrong) ? Math.round((l.correct / (l.correct + l.wrong)) * 100) : 0;
  const fastest = l.fastestWinSeconds != null ? formatTime(l.fastestWinSeconds) : '–';
  const soloAccuracy = s.cells ? Math.round((s.correct / s.cells) * 100) : 0;

  const tile = (value, label, accented) => `
    <div class="tt-card p-2.5"><div class="text-base font-black" style="color:${accented ? 'var(--accent)' : 'var(--text)'}">${value}</div><div class="tt-label">${label}</div></div>`;

  document.getElementById('stats-body').innerHTML = `
    <div>
      <div class="tt-label mb-2">📅 Tages-Rätsel</div>
      <div class="grid grid-cols-3 gap-2 text-center">
        ${tile(daysPlayed, 'Gespielt')}
        ${tile(`${d.currentStreak} 🔥`, 'Serie', true)}
        ${tile(d.bestStreak, 'Beste Serie', true)}
      </div>
    </div>
    <div>
      <div class="tt-label mb-2">🛋️ 1v1 Lokal</div>
      <div class="grid grid-cols-2 gap-2 text-center">
        ${tile(l.gamesPlayed, 'Spiele')}
        ${tile(`${l.bestStreak} 🔥`, 'Beste Serie', true)}
        ${tile(l.wins[1], 'Siege X')}
        ${tile(l.wins[2], 'Siege O')}
        ${tile(`${accuracy}%`, 'Trefferquote')}
        ${tile(fastest, 'Schnellster Sieg')}
      </div>
    </div>
    <div>
      <div class="tt-label mb-2">🧩 Solo</div>
      <div class="grid grid-cols-2 gap-2 text-center">
        ${tile(s.rounds, 'Runden')}
        ${tile(`${s.bestCorrect}/9`, 'Bestes Ergebnis', true)}
        <div class="tt-card p-2.5 col-span-2"><div class="text-base font-black" style="color:var(--text)">${soloAccuracy}%</div><div class="tt-label">Trefferquote gesamt</div></div>
      </div>
    </div>
    <div>
      <div class="tt-label mb-2">🌐 1v1 Online</div>
      <div class="grid grid-cols-3 gap-2 text-center">
        ${tile(o.rounds, 'Spiele')}
        ${tile(o.wins, 'Siege', true)}
        ${tile(o.losses, 'Niederlagen')}
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
    btn.classList.toggle('is-active', active);
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
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  closeModal();
  closeSolutionSheet();
});

// ─── Start ────────────────────────────────────────────────────────────────────

(function init() {
  const params = new URLSearchParams(location.search);
  const joinCode = params.get('join');
  const gridCode = params.get('grid');
  if (joinCode) {
    g.mode = 'online';
    showScreen('online-lobby');
    updateModeChrome();
    renderLobbyHome();
    history.replaceState({}, '', '/game');
    joinOnlineRoom(joinCode);
  } else if (gridCode) {
    history.replaceState({}, '', '/game');
    loadAndStartCustomGrid(gridCode);
  } else {
    showScreen('mode-select');
  }
  updateDailyCardBadge();
})();
