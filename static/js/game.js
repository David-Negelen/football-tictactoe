// ─── Icons ──────────────────────────────────────────────────────────────────

// One small hand-authored line-icon set replacing every decorative emoji in
// the app (system emoji renders in fixed, uncontrollable multi-color glyphs
// that clash with the rest of the flat, single-accent design language — see
// the earlier header-menu icon pass). Every icon uses currentColor, so the
// wrapping element's `color` decides whether it reads as neutral chrome or
// picks up the accent — no separate color parameter needed here.
// Flags (real content, not decoration) and plain typographic glyphs (✓ ✕ ☰)
// are intentionally left alone — see CLAUDE.md-adjacent design notes in
// earlier commits on why those are exempt.
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
  // 1v1 board marks (see cellHtml) — same stroke-width-2 line-icon
  // treatment as everything above, and deliberately matched bounding
  // boxes (both span the 4-20 range) so X doesn't visually outweigh O the
  // way the same font glyphs at an equal font-size used to.
  x: `<path d="M4 4l16 16"/><path d="M20 4 4 20"/>`,
  o: `<circle cx="12" cy="12" r="8"/>`,
};
// "play" stays filled — a solid triangle is the universal play-button
// convention, not an emoji-like exception. Every other icon, fire
// included, is an outline to match the rest of the icon system.
const ICON_FILLED = new Set(['play']);

function svgIcon(name, size = 18) {
  const attrs = ICON_FILLED.has(name)
    ? `fill="currentColor" stroke="none"`
    : `fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`;
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" ${attrs} style="flex-shrink:0">${ICON_PATHS[name]}</svg>`;
}

// Icon + text inline, for the many places an emoji used to sit directly in
// front of a label (banners, buttons, status text).
function iconText(name, text, { size = 16, gap = 6 } = {}) {
  return `<span style="display:inline-flex;align-items:center;gap:${gap}px">${svgIcon(name, size)}<span>${text}</span></span>`;
}

// ─── SVG & badges ───────────────────────────────────────────────────────────

function shirtSvg() {
  // Flat, single-color "+" — an empty slot, nothing more. No shading, no
  // gradient, no icon library glyph. Accent-colored so "orange = tap here,
  // this is interactive" reads consistently across the board.
  return `<span style="font-size:28px;line-height:1;font-weight:300;color:var(--accent)">+</span>`;
}

// The one place the app's palette grows a second color (--o-color, next to
// --accent for X): player identity in 1v1 local/online — the filled-cell
// background (see cellHtml), its corner glyph, and the turn-indicator dot.
function playerColor(player) {
  return player === 1 ? 'var(--accent)' : 'var(--o-color)';
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
  soloGridCode: null, // the saved-grid code when soloVariant === 'custom' (see /solo/<code>)
  dailyDate: null,    // the server's date string for the currently-loaded daily grid
  rows: [], cols: [],
  board: [[null,null,null],[null,null,null],[null,null,null]],
  current: 1,         // whose turn (local/online); unused in solo
  winner: null,       // null | 1 | 2 | 'draw' | 'complete' (solo)
  winCells: [],
  usedIds: new Set(),
  activeCell: null,   // {r, c}
  streak: { 1: 0, 2: 0 },
  // local retake mode only (see setRetakeMode/checkWinnerLocal/retakeLocal):
  retakeMode: false,  // chosen at setup time, fixed for the whole round
  phase: 'fill',       // 'fill' | 'retake' — flips once the grid fills with no winner
  // A 3-in-a-row formed during the retake phase doesn't win outright — the
  // opponent gets exactly one more turn to break it by retaking one of its
  // cells (see checkPendingThreatOutcome). null once there's nothing pending.
  pendingThreat: null, // null | { owner: 1|2, lines: [[[r,c],[r,c],[r,c]], ...] }
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
  lobbyEventSource: null, // SSE for the public lobby-browsing list — see connectLobbyListEvents
  onlineBoardEntered: false,
  onlineFinished: false,
  // The `version` of the last wrong-guess flash we've already shown (see
  // applyOnlineState) — undefined until the first state sync, which seeds
  // it silently instead of flashing a guess that happened before we connected.
  onlineLastWrongGuessVersion: undefined,
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
  // streak/bestStreak: consecutive correct guesses in a row, across every
  // solo round (daily/custom/random alike) — resets on any miss, same
  // "hot streak" idea as local mode's per-player streak. scoreDistribution:
  // count of random-practice rounds ending with each score 0-9, for the
  // Wordle-style histogram in the stats modal.
  solo: { rounds: 0, correct: 0, cells: 0, bestCorrect: 0, streak: 0, bestStreak: 0, scoreDistribution: new Array(10).fill(0) },
  // streak/bestStreak here: consecutive round *wins*, not guesses — a
  // draw or a loss both break it, matching how a match-based mode's
  // "streak" is usually understood.
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
let onlineVisibility = 'private'; // 'private' | 'public' — see setVisibility, only used when hosting
let retakeMode = false; // see setRetakeMode, only used when starting a 1v1 Lokal round

function genParams() {
  const p = new URLSearchParams({ difficulty: String(difficulty) });
  if (selectedLeague) p.set('league', selectedLeague);
  return p;
}

// ─── Router ───────────────────────────────────────────────────────────────────
// Every top-level screen gets a real URL via the History API — the app stays
// a single document (a live round's timer and the 1v1 Online SSE connection
// must never be torn down by a full page navigation), but back/forward,
// direct links, and a hard refresh all now land on the right screen instead
// of always bouncing to mode-select. Modal overlays (#modal, #stats-modal,
// etc.) are deliberately NOT part of this — they're not top-level screens.

// A URL identifies a *resource*, not a raw DOM screen name — several of the
// 6 screen-* divs are just different render states of the same resource
// (online-lobby/board are both driven by one room's state; board/daily-done
// are both driven by one day's puzzle), so this maps to /solo, /local,
// /solo/<code>, /online/<code> etc. instead of a single generic /board. The
// game lives at the site root (see the game() route in app.py) — /combos and
// /squad-guesser are the only other top-level pages, and both are matched
// ahead of this router's own catch-all. Setup, an online room, and a saved/
// shared grid can be reconstructed from the URL alone (server state lives
// under a code); a plain solo/local round has no server-side representation,
// so a cold load of its URL instead falls back to tryResumeRound's
// sessionStorage snapshot (see below) and, failing that, to that mode's
// setup screen.
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
      return '/board'; // unreachable in practice — g.mode is always set before showScreen('board')
    case 'mode-select': default: return '/';
  }
}

// Reads the current URL, used only for a cold load (see init()) — popstate
// (back/forward within an already-open session) instead reads the concrete
// screen straight off history.state, since `g` is still fully live then and
// doesn't need to be re-derived from the URL at all (see the popstate
// listener below).
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

// The pure DOM half of a screen change, with no history side effect — used
// directly by showScreen below, and on its own by the popstate handler
// (the browser already moved history for us there, re-pushing would just
// create a duplicate/broken entry).
function renderScreenDom(name) {
  document.getElementById('screen-mode-select').classList.toggle('hidden', name !== 'mode-select');
  document.getElementById('screen-setup').classList.toggle('hidden', name !== 'setup');
  document.getElementById('screen-online-lobby').classList.toggle('hidden', name !== 'online-lobby');
  document.getElementById('screen-daily-done').classList.toggle('hidden', name !== 'daily-done');
  document.getElementById('screen-editor').classList.toggle('hidden', name !== 'editor');
  document.getElementById('screen-board').classList.toggle('hidden', name !== 'board');
  closeMenuDropdown();
  // The public-lobby SSE connection (see connectLobbyListEvents) is only
  // meaningful while actually browsing online-lobby's "home" sub-state —
  // leaving the screen entirely always means leaving that sub-state too, so
  // this one check covers every transition away (menu, setup, board, ...)
  // without each of them separately remembering to call it. Reopened by
  // renderLobbyHome the next time this screen is (re-)entered.
  if (name !== 'online-lobby') closeLobbyListEvents();
}

// push=true (the default) is every screen change a user actually navigated
// to — clicking a mode, starting a round, opening the editor — so the
// browser's own back button steps back through them one at a time. push:
// false is for changes that aren't a new step: the very first screen on
// load, a failed action reverting to where you already were, and automatic
// SSE-driven transitions (entering the online board once an opponent
// connects) — those replace the current entry instead of growing history.
function showScreen(name, { push = true } = {}) {
  renderScreenDom(name);
  const url = urlForScreen(name);
  const state = { screen: name };
  if (push) history.pushState(state, '', url);
  else history.replaceState(state, '', url);
}

// Entry point for a URL with NO live `g` state behind it — a cold page
// load (init()) or the rare popstate with no history.state payload. Each
// branch either reconstructs the screen from data the URL/server/
// sessionStorage/localStorage can actually supply, or — if there's no
// saved round to resume either — bounces one level to that mode's setup
// screen (replace, not push: this corrects an unresumable URL, it isn't a
// new step) rather than all the way home, so relaunching is one tap
// instead of a full re-navigation. A saved/shared grid (solo-custom) and
// an online room can additionally be reconstructed cold from just the URL
// (their state lives server-side under a code) even with no saved round —
// tryResumeRound only ever gets in the way there if it were to restore
// stale progress for a *different* code, which its match check rules out.
function enterFromPath(parsed) {
  switch (parsed.screen) {
    case 'setup': enterSetupScreen(parsed.mode, { push: false }); break;
    case 'editor': goToEditor({ push: false }); break;
    case 'daily': startDaily({ push: false }); break;
    case 'online':
      g.mode = 'online';
      renderScreenDom('online-lobby');
      updateModeChrome();
      // Bypasses showScreen/urlForScreen (which derives the URL from
      // g.onlineCode, not yet meaningfully set at this point — a resume
      // attempt hasn't run yet, and even on failure the code stays worth
      // keeping visible in the URL, e.g. so a stale/expired invite link
      // still shows what room the join UI is pre-filled for).
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
  // No state (e.g. the user hand-edited the URL, or landed on the very
  // first entry from before any of our pushState calls) — same "no live
  // session behind this URL" situation as a cold load.
  enterFromPath(parseLocation());
});

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

// Host-only setting (see setup-visibility-picker, toggled visible in
// enterSetupScreen): whether the room additionally gets listed in the
// public lobby (see connectLobbyListEvents) or stays link/code-only.
function setVisibility(value) {
  onlineVisibility = value;
  document.querySelectorAll('.visibility-btn').forEach(btn => {
    btn.classList.toggle('is-active', btn.dataset.visibility === value);
  });
}

document.querySelectorAll('.visibility-btn').forEach(btn => {
  btn.addEventListener('click', () => setVisibility(btn.dataset.visibility));
});

// Local-only (see setup-retake-picker, toggled visible in enterSetupScreen):
// once the grid fills up, instead of ending in a draw, players keep taking
// turns retaking the opponent's cells — see checkWinnerLocal/retakeLocal.
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

// Difficulty and league are chosen once, on their own screen — for solo/
// local right after picking the mode; for online, only after choosing to
// host (see renderLobbyHome's "Raum erstellen" handler), since a joiner
// never needs it at all — the room creator's settings apply to them too, and
// making them pick unused settings before even seeing the host/join choice
// was the previous (wrong) order.
function enterSetupScreen(pendingMode, { push = true } = {}) {
  g.pendingMode = pendingMode;
  document.getElementById('btn-setup-continue').disabled = false;
  // Loading a grid by code always starts a solo round — only relevant
  // (and only shown) when solo is actually what's being set up.
  document.getElementById('setup-load-grid').classList.toggle('hidden', pendingMode !== 'solo');
  document.getElementById('setup-load-error').classList.add('hidden');
  document.getElementById('setup-load-code').value = '';
  // Room visibility only makes sense when hosting a room in the first place.
  document.getElementById('setup-visibility-picker').classList.toggle('hidden', pendingMode !== 'online-host');
  // Retake mode is a 1v1 Lokal-only variant for now (see setRetakeMode).
  document.getElementById('setup-retake-picker').classList.toggle('hidden', pendingMode !== 'local');
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

// Lets a hard refresh on /online/<code> silently re-attach to a room
// instead of landing on a bare join screen — the room itself already lives
// server-side, this is just enough client-side memory of "which seat was
// mine" to reuse it. sessionStorage (not localStorage): a stale token from a
// finished session in an old tab shouldn't resurrect itself in a new one.
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

// Same idea, for solo/local rounds — these have no server-side game state to
// reattach to at all, so this holds the actual board (not just an identity
// token): rows/cols, filled cells, whose turn, elapsed time. Saved on every
// move and cleared the instant a round ends or the player leaves to the
// menu — a finished round's reload still bounces to setup (nothing of value
// is lost there; they already saw the result) rather than trying to
// reconstruct a result banner from storage too.
const ROUND_SESSION_KEY = 'ttt_round_session';

function saveRoundSession() {
  if (g.mode !== 'solo' && g.mode !== 'local') return;
  sessionStorage.setItem(ROUND_SESSION_KEY, JSON.stringify({
    mode: g.mode, soloVariant: g.soloVariant, soloGridCode: g.soloGridCode, dailyDate: g.dailyDate,
    rows: g.rows, cols: g.cols, board: g.board, current: g.current,
    usedIds: [...g.usedIds], streak: g.streak, elapsedSeconds: g.elapsedSeconds,
    soloAttempted: g.soloAttempted, soloCorrect: g.soloCorrect,
    retakeMode: g.retakeMode, phase: g.phase, pendingThreat: g.pendingThreat,
  }));
}

function clearRoundSession() {
  sessionStorage.removeItem(ROUND_SESSION_KEY);
}

// Rebuilds g and the board DOM from a saved round session if one matches the
// screen being entered — returns whether it did, so callers know whether to
// fall back to their normal fresh-start path (no saved session, or it's for
// a different mode/grid/day).
function tryResumeRound(match) {
  let saved = null;
  try { saved = JSON.parse(sessionStorage.getItem(ROUND_SESSION_KEY) || 'null'); } catch { /* corrupt entry — ignore */ }
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

// ─── Kopfzeilen-Menü (☰) ────────────────────────────────────────────────────

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

// Shrinks el's font-size, starting from whatever its CSS (usually a
// clamp()) already resolved to, down to `min` — one step at a time — until
// its content actually fits. `axis: 'width'` is for single-line text where
// text-overflow:ellipsis is the fallback (player names); `axis: 'height'`
// is for the multi-line line-clamped labels, where the clamp's own
// ellipsis is the fallback. Either way, shrinking to fit is the default
// behavior and truncation only kicks in if `min` itself still overflows.
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

// A cell already owned by the opponent, while the retake phase is live, can
// still be tapped (to retake it) — every other filled cell is inert. Only
// applies in 1v1 Lokal; solo/online cells are never retake targets.
function isRetakeTarget(r, c) {
  const entry = g.board[r][c];
  return !g.winner && g.mode === 'local' && g.phase === 'retake' && !!entry && entry.player !== g.current;
}

// Filled/missed cells have nothing to do on tap, except a retake-phase cell
// owned by the opponent; an empty cell before the round ends opens the
// player search; an empty cell after the round ends (once solutions are
// loaded) opens the full-answer sheet instead — same data-cell wiring
// either way, the state at click time decides.
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

// Last name alone identifies a player and is far shorter than the full
// name — that's the default everywhere on the board. The only time it's
// genuinely ambiguous is if two different filled cells on this board
// happen to resolve to the same last name; only then do both get a
// first-initial prefix back, to stay distinguishable. Mononyms (Neymar,
// Pelé, Ronaldinho) have no "last name" to strip, so they pass through
// unchanged either way.
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
  // Real crest/flag artwork and team/position brand colors are content, not
  // decoration — they stay in full color. Only the generic fallback icons
  // (trophy/globe/calendar/ball — not tied to any specific team) are
  // flattened to grayscale, so the palette still can't pick up arbitrary
  // extra hues. See app.py's _cat_display for how `icon`/`icon_letter`/
  // `icon_color`/`icon_image` get set — every category resolves to exactly
  // one of the four branches below, never a raw emoji character.
  // Real downloaded flag/crest image (see fetch_flags.py, fetch_club_logos.py)
  // wins whenever available — looks far better than any icon/badge.
  if (cat.icon_image) {
    // Crest/flag downloads occasionally 404 (source removed the file, a
    // scrape gap, etc.) — fall back to the same letter-badge/ball icon
    // used when there's no image at all, instead of leaving a broken-image
    // glyph in the cell.
    // Single-quoted, hand-escaped JS string literals — the whole call then
    // sits inside a double-quoted HTML attribute, so JSON.stringify's
    // double quotes would collide with (and truncate) that attribute.
    const jsStr = s => `'${String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'")}'`;
    const onerror = `iconImgFallback(this, ${jsStr(cat.icon_letter || '')}, ${jsStr(cat.icon_color || '')})`;
    return `<img src="${esc(cat.icon_image)}" alt="" class="tt-icon tt-icon-img flex-shrink-0" onerror="${esc(onerror)}">`;
  }
  // No real image for this category (the vast majority of ~6,500 clubs, all
  // positions, and letter categories) — a small badge in a deliberate
  // color, showing real text: a club/position initial, or the specific
  // letter an initial/contains-letter category is actually about.
  if (!cat.icon && cat.icon_letter) {
    return `<div class="tt-icon rounded-full flex items-center justify-center text-white font-black text-sm flex-shrink-0"
      style="background:${esc(cat.icon_color || 'var(--card-border)')}">${esc(cat.icon_letter)}</div>`;
  }
  // A named icon from the shared line-icon set (globe/calendar/trophy — see
  // ICON_PATHS above) — category types with no real photo and no specific
  // letter/abbreviation to show (continents, age brackets, awards, ...).
  if (cat.icon && ICON_PATHS[cat.icon]) {
    // '100%' (not a fixed pixel size) so the SVG itself fills the
    // responsive .tt-icon box on the wrapping div, the same way a real
    // crest/flag <img> already scales with it — a fixed size here left it
    // visibly smaller than photographic icons on wider screens.
    return `<div class="tt-icon-mono tt-icon flex-shrink-0 flex items-center justify-center">${svgIcon(cat.icon, '100%')}</div>`;
  }
  // A plain typographic symbol (e.g. "€" for market-value brackets) — not
  // an SVG, not emoji, just text in the same treatment.
  if (cat.icon) {
    return `<div class="tt-icon-mono tt-icon leading-none flex-shrink-0 flex items-center justify-center"
      style="font-size:clamp(18px,6vw,26px)">${esc(cat.icon)}</div>`;
  }
  return `<div class="tt-icon-mono tt-icon flex-shrink-0 flex items-center justify-center">${svgIcon('ball', '100%')}</div>`;
}

// Swaps a broken crest/flag <img> for the same letter-badge (or generic
// ball icon) categoryIconHtml would have rendered had icon_image been
// absent to begin with — called from the img's onerror handler.
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
  // The icon (crest/flag/emoji) carries the primary identification — the
  // label backs it up, wrapping at word boundaries (overflow-wrap:anywhere
  // is only a fallback for the rare single "word" — a long club name with
  // no spaces — that still can't fit on its own line). Font size and icon
  // size both scale down on narrow phones (.tt-icon, .tt-cat-label) so a
  // name like "Bor. M'gladbach" gets enough room across 3 lines instead of
  // being cut mid-word at 2.
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

  // Every state below shares the same .tt-cell card (fill, border, radius) —
  // only the content changes, and the only border-color states are
  // .is-active (search modal open on this cell) and .is-win, both using
  // the one accent color, flat, no glow/animation.
  if (entry && entry.status === 'missed') {
    return `
      <div class="tt-cell flex flex-col items-center justify-center p-2.5 tt-slot">
        <div class="text-2xl mb-1" style="color:var(--text-dim)">✕</div>
        <div class="tt-label">Falsch</div>
      </div>`;
  }

  if (entry) {
    // The badge/glyph sits absolutely in the corner instead of its own flex
    // row — on a 4-column mobile grid the cell is only ~50px of usable
    // content height, and a dedicated badge row was eating enough of that
    // to crush the name down to an unreadable sliver (a flex item with
    // overflow: hidden — needed for the line-clamp below — loses its
    // automatic min-height protection, so a too-tall stack doesn't just
    // wrap, it silently shrinks below its own content size).
    if (g.mode === 'solo') {
      // Solo has no "which player" concept, just correct-or-not — a small
      // accent checkmark is enough (a missed guess never reaches this
      // branch, it's the 'missed' one above).
      return `
        <div class="tt-cell ${isWin ? 'is-win' : ''} flex flex-col items-center justify-center p-3 tt-slot relative"
             data-cell="${r},${c}">
          <div class="absolute top-1.5 right-1.5">
            <span class="text-xs font-black w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style="border:1.5px solid var(--accent);color:var(--accent)">✓</span>
          </div>
          <div class="tt-cell-name text-center" style="color:var(--text)">${esc(formatPlayerName(entry.name))}</div>
        </div>`;
    }
    // Local/online: the cell background carries a soft tint of that
    // player's color (not a fully saturated block — two of those side by
    // side just fight each other), while a big, bold but slightly
    // translucent (opacity .8, softer than the fully solid stroke it
    // started as) X/O mark sits centered behind the name as the actual
    // "who owns this cell" signal — legible as a game mark on its own,
    // before the name is even read. X and O share one line-icon (matched
    // bounding box, same
    // stroke-width — see ICON_PATHS) instead of the browser's X/O font glyphs,
    // which don't carry equal visual weight at the same font-size (X's
    // diagonal strokes read "bigger" than O's circle). Text stays the
    // app's one usual near-white --text regardless of player — the tint
    // is soft enough that dark ink is no longer needed for contrast.
    // position:relative on the name (it's later in the DOM than the mark)
    // is what lifts it above the mark — an absolutely-positioned box
    // always paints above a plain static one regardless of source order,
    // so the name needs to be "positioned" too to win that stacking fight.
    const color = playerColor(entry.player);
    const bg = entry.player === 1 ? 'var(--accent-cell-bg)' : 'var(--o-cell-bg)';
    const markPath = entry.player === 1 ? ICON_PATHS.x : ICON_PATHS.o;
    // Retake mode: a threatened cell (part of a pending 3-in-a-row awaiting
    // defense) gets a dashed ring; a cell the current player could tap right
    // now to retake it gets a pointer cursor — see checkPendingThreatOutcome
    // and isRetakeTarget.
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
    // A real name list overflows a mobile-width cell fast ("Mattia
    // Graffiedi, Marco Donadel, Cristian Brocchi +2 weitere" wraps to 4-5
    // lines and breaks the grid's rhythm) — so the cell itself only shows
    // the most prominent answer (last name, same rule as a filled cell) on
    // its own line, shrink-to-fit, and — only if there's more than one
    // answer — a small "+N weitere" on a second line below it, rather than
    // crowding both onto one line. Tapping the cell opens the full list in
    // a sheet (openSolutionSheet) for the detail.
    const cellSol = g.solution[r][c];
    const count = cellSol.count || 0;
    const first = cellSol.players?.[0] ? esc(formatPlayerName(cellSol.players[0].name)) : '';
    const more = count - 1;
    // No "LÖSUNG" caption — repeated on every one of these cells it was
    // just noise, and the muted color plus the checkmark on cells you did
    // answer (see above) already says "this one wasn't yours" on its own.
    return `
      <button data-cell="${r},${c}" class="tt-cell tt-card-hover flex flex-col items-center justify-center p-3 tt-slot text-center">
        <div class="tt-cell-name" style="color:var(--text-dim)">${count === 0 ? '–' : first}</div>
        ${more > 0 ? `<div class="text-xs mt-0.5" style="color:var(--text-faint)">+${more} weitere</div>` : ''}
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
      class="tt-cell ${isActive ? 'is-active' : ''} flex flex-col items-center justify-center px-2 py-2 tt-slot w-full">
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
  fitBoardText(newEl);
  // Always rebound, not just for empty cells — a filled cell can still be a
  // live retake target (see handleCellClick/isRetakeTarget), which
  // handleCellClick itself is what actually gates.
  newEl.addEventListener('click', () => handleCellClick(r, c));
}

// A newly-filled cell can turn a previously-unambiguous last name into a
// collision with this one (see formatPlayerName) — refresh every filled
// cell, not just the one that just changed, so an earlier cell picks up
// its disambiguating initial too instead of only the new cell getting it.
function refreshFilledCells() {
  g.board.forEach((row, r) => row.forEach((entry, c) => {
    if (entry && entry.status !== 'missed') refreshCell(r, c);
  }));
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
  // Scoped to #board — .is-active is a shared class also used by the
  // difficulty/league/visibility pickers and the header menu toggle, all of
  // which live in the same document at once (screens are hidden via CSS,
  // never removed from the DOM). An unscoped query here would silently
  // clear whichever of those happened to be active whenever a cell opens —
  // e.g. the setup screen's Schwierigkeit/Liga picker would show no
  // selection at all on the next visit, even though difficulty/
  // selectedLeague are still tracking a real value internally.
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
  // The dot doubles as a preview of that player's cell color (see
  // playerColor/cellHtml) — whose turn it is reads at a glance, not just
  // from the glyph.
  const sym = g.current === 1 ? 'X' : 'O';
  // Retake mode: a pending threat is always against g.current (the other
  // player raised it last turn, then the turn passed) — see
  // checkPendingThreatOutcome/retakeLocal. Spell out that this is their one
  // chance to defend, since a normal turn-indicator dot alone doesn't say
  // "the game ends now if you don't".
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

// Briefly replaces the status line with a one-off message (e.g. "Gegner hat
// XY versucht – falsch!") — online-only, since it's the one mode where the
// opponent has no other way to see what just happened on the other client.
// Reverts to the normal turn indicator on its own once the round is still
// live; a round that ends mid-flash leaves the result banner alone instead
// of stomping it back to a turn indicator that's no longer true.
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

// The round result folds into the existing status card instead of a
// separate popup/overlay: the live "X / 9" or turn indicator in status-text
// is replaced by the final result, and the button row swaps "Aufgeben" for
// the result actions — no new block, no dimmed backdrop, and the revealed
// board underneath stays fully visible and tappable the whole time (see
// openSolutionSheet).
function showEndBanner(icon, title, showReplay = true) {
  document.getElementById('status-text').innerHTML = iconText(icon, title);

  const replayBtn = document.getElementById('end-new-game');
  replayBtn.classList.toggle('hidden', !showReplay);
  replayBtn.disabled = false;
  replayBtn.innerHTML = g.mode === 'online' ? iconText('rematch', 'Revanche', { size: 14 }) : 'Nochmal spielen';
  // Only the daily-completion branch in endGameSolo shows this — reset it
  // here so a stale "shown" state from an earlier daily round never leaks
  // into a later solo/local/online banner.
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
    retakeMode, phase: 'fill', pendingThreat: null,
  });
  updateStreakDisplay();
  updateTimerDisplay();

  const resp = await fetch(`/api/game/new?${genParams().toString()}`);
  if (!resp.ok) {
    setStatus('Kein Grid gefunden – bitte erneut versuchen.');
    return;
  }
  const data = await resp.json();
  g.rows = data.rows;
  g.cols = data.cols;

  renderBoard();
  updateStatus();
  startTimer();
  saveRoundSession();
}

// Fill-phase win check — unchanged from classic mode even in retake mode: a
// 3-in-a-row while cells are still empty wins outright, same as always. The
// only retake-mode-specific branch is what a *full board with no winner*
// means: normally that's a draw, but retake mode instead opens the retake
// phase (see retakeLocal) rather than ending the round.
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
  // Flip before rendering (not after) — refreshFilledCells reads g.current
  // to decide which cells are retake targets (see isRetakeTarget), so the
  // render has to see whoever's turn it actually is next, not the mover who
  // just went. Doesn't matter for the win case (isRetakeTarget is always
  // false once g.winner is set).
  if (g.winner) { refreshFilledCells(); endGameLocal(); return; }
  g.current = g.current === 1 ? 2 : 1;
  refreshFilledCells();
  updateStatus();
  saveRoundSession();
}

function linesFullyOwnedBy(player) {
  return WIN_LINES.filter(line => line.every(([r, c]) => g.board[r][c]?.player === player));
}

// Called once per retake-phase turn, right after that turn's action (a
// placed retake, or a wrong guess that placed nothing) is fully resolved.
// If the OTHER player left a threat pending last turn, this is the "did you
// defend it" check: any one of the threatened lines still intact means the
// defense failed and the threat owner wins now. A fork (two lines from one
// move) is always defensible with a single retake because both lines
// necessarily share the cell that move just played — so "every line
// broken" is the right bar, not "at least one".
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

// Once the grid is full (see checkWinnerLocal), retake mode replaces
// further placement with retaking: g.current overwrites one of the
// opponent's cells with their own pick (see handleCellClick/openCell for
// the "opponent's cells only" restriction). A resulting 3-in-a-row doesn't
// win immediately — it becomes a pending threat the opponent gets exactly
// one more turn to break (checkPendingThreatOutcome, called at the top of
// their next turn).
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

  // Same flip-before-render reasoning as placeLocal.
  if (g.winner) { refreshFilledCells(); endGameLocal(); return; }
  g.current = g.current === 1 ? 2 : 1;
  refreshFilledCells();
  updateStatus();
  saveRoundSession();
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
      // A wrong guess doesn't touch the board, so a threat left pending by
      // the opponent stands unbroken — this is exactly the "failed to
      // defend in time" case (see checkPendingThreatOutcome). No-op outside
      // the retake phase, since g.pendingThreat is only ever set there.
      if (checkPendingThreatOutcome()) { endGameLocal(); return; }
      g.current = g.current === 1 ? 2 : 1;
      // Board contents didn't change, but which cells count as retake
      // targets did (see isRetakeTarget) — re-render to match.
      if (g.phase === 'retake') refreshFilledCells();
      updateStatus();
      saveRoundSession();
    }, 1500);
  }
}

async function endGameLocal() {
  stopTimer();
  clearRoundSession();
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
  const resp = await fetch(`/api/game/new?${genParams().toString()}`);
  if (!resp.ok) {
    setStatus('Kein Grid gefunden – bitte erneut versuchen.');
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
  clearRoundSession();
  resetGiveUpConfirm();
  document.getElementById('btn-give-up').disabled = true;
  g.rows.forEach((_, r) => g.cols.forEach((__, c) => refreshCell(r, c)));

  const perfect = g.soloCorrect === 9;

  if (g.soloVariant === 'daily') {
    // Giving up still "completes" today's puzzle and keeps the streak alive
    // — the streak is about showing up daily, not about getting a perfect
    // score (getting all 9 right is much harder here than guessing a
    // Wordle, so requiring perfection would make streaks nearly unreachable).
    recordDailyCompletion(g.dailyDate, g.soloCorrect);
    updateDailyCardBadge();
    showEndBanner(perfect ? 'trophy' : 'calendar', `${g.soloCorrect} / 9 richtig`, false); // already played today — no "Nochmal spielen"
    document.getElementById('end-share').classList.remove('hidden');
  } else if (g.soloVariant === 'custom') {
    // Doesn't count toward the "Solo" stats — a shared/custom grid is a
    // different activity, not a random practice round.
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

// ─── Modus: Daily Grid ────────────────────────────────────────────────
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

// ─── Editor: eigenes Grid bauen, speichern & teilen, per Code laden ──────

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

// Same load-by-code affordance as the editor, surfaced directly on the
// solo setup screen too — the editor's own copy is one menu layer deeper
// and easy to miss for someone who just has a code, not a grid to build.
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

// ─── Modus: 1v1 Online ──────────────────────────────────────────────────────────

function renderLobbyHome() {
  document.getElementById('online-lobby-body').innerHTML = `
    <div class="tt-card p-6 flex flex-col gap-4 items-center text-center">
      <svg class="tt-icon-app" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/></svg>
      <button id="btn-create-room" class="tt-btn-accent w-full text-sm px-4 py-2.5 rounded-xl">Raum erstellen</button>
      <div class="text-xs" style="color:var(--text-dim)">— oder —</div>
      <div class="w-full flex gap-2">
        <input id="join-code-input" maxlength="5" placeholder="CODE" autocomplete="off"
          class="tt-input flex-1 uppercase tracking-widest text-center rounded-lg px-3 py-2 text-sm font-bold">
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
  // Hosting needs difficulty/league first — that's the setup screen, shown
  // only now (not before this host-vs-join choice) since a joiner never
  // needs it at all (the room's creator-chosen settings apply to them too).
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
  // Bound once on the container itself, not per-row — renderPublicLobbyList
  // below only ever replaces the container's innerHTML (on every SSE-driven
  // refresh), which would silently drop a per-row listener each time.
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
  if (!container) return; // navigated away since the fetch/event fired
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

// Keeps the public lobby list live for everyone browsing it: an initial
// fetch for fast first paint, then an SSE connection (same version-diff
// pattern as a room's own /events) that just signals "the list changed" —
// the client always refetches the full list rather than trusting a payload
// on the event itself.
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
    // Nothing more we can do — the button's "Kopiert" feedback still
    // fires, but that's a pre-existing tradeoff, not something new here.
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
    // Creation happens from the setup screen — surface the failure back on
    // the lobby screen (where #lobby-error already lives from renderLobbyHome)
    // rather than leaving the user stranded looking at the setup screen with
    // nothing having visibly happened. Replace, not push: this reverts to a
    // screen we were already conceptually at, it isn't a new step.
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
    connectLobbyListEvents(); // e.g. a public-lobby row that just filled up — refresh it away
    return;
  }
  const data = await resp.json();
  g.onlineCode = data.code;
  g.onlineToken = data.token;
  g.onlineSlot = data.slot;
  saveOnlineSession();
  // Not shown before this point in every caller (e.g. the ?join= deep-link
  // path lands here before online-lobby has ever been the active screen) —
  // (re-)showing it now is what actually puts the room code into the URL.
  showScreen('online-lobby', { push });
  renderLobbyWaiting(data.code);
  connectOnlineEvents();
  await refreshOnlineState();
}

// Cold-load-only: called from enterFromPath when landing on /online/<code>
// with no live session behind it (a hard refresh, or a fresh tab
// opened on a shared room link). Tries the sessionStorage seat first —
// /state doesn't reject a bad/expired token with an HTTP error, it just
// omits yourSlot, so that field (not resp.ok) is the actual validity
// signal — and falls back to the normal join flow (pre-filled with the
// code from the URL) if there's no stored session or it no longer holds.
function attemptOnlineResume(code) {
  let stored = null;
  try { stored = JSON.parse(sessionStorage.getItem(ONLINE_SESSION_KEY) || 'null'); } catch { /* ignore */ }
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
  // No push: this fires automatically once the SSE state poll sees the
  // opponent connect, not from a user click, and the URL doesn't actually
  // change anyway — /online/<code> covers both the lobby and the live
  // board for a room, the server-fetched state is what decides which one
  // renders.
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

  // The opponent's only signal a wrong guess just happened, otherwise
  // indistinguishable from "their turn just ended" (both just flip
  // `current`) — see last_wrong_guess in multiplayer.py. `undefined` means
  // this is the first sync since connecting (fresh load or a resumed
  // session) — adopt silently instead of flashing a guess that happened
  // before we were watching.
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
    // Otherwise this immediately overwrites the flash with the normal turn
    // indicator in the same tick — flashOnlineMessage's own timeout is what
    // reverts it once it's actually had time to be seen.
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
    return;
  }
  await refreshOnlineState();
}

// `reason` (from Room.end_reason — see multiplayer.py) is null for a normal
// 3-in-a-row/draw, "forfeit" for an explicit give-up, or "disconnect" for
// the ~20s auto-forfeit timeout — without it, "Du gewinnst!" reads like you
// were outplayed when the opponent actually just left.
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

// Same inline two-step confirm pattern as giveUpConfirming (see the
// "Aufgeben" button) — click once to arm, click again to actually reset.
let statsResetConfirming = false;

// Shared Wordle-style histogram renderer — one flat accent bar per score
// bucket (0-9), length relative to the largest bucket, used for both the
// Solo and Daily Grid sections so "how much got solved" shows up as a
// shape, not just one aggregate percentage.
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
  // Derived straight from d.completed each render, same as dailyAccuracy
  // above — no separate persisted counter needed, unlike Solo's
  // scoreDistribution (that one counts *rounds*, which aren't otherwise
  // stored anywhere; a completed day's score already lives in d.completed).
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
    // Same inline two-step confirm as "Aufgeben" — no browser confirm()
    // popup — so a stray tap can never wipe every stat by accident.
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
  // ?join=/?grid= predate the path-based router (they used to be the only
  // URL state this app had) — kept working as a compat shim since a link
  // in that shape could still be sitting in a chat/bookmark somewhere, but
  // both link generators (renderLobbyWaiting, the editor's copy-link
  // button) now emit the canonical /online/<code> and /solo/<code> paths
  // directly, so this branch is dead weight from here on, not a format
  // this app still produces.
  const params = new URLSearchParams(location.search);
  const joinCode = params.get('join');
  const gridCode = params.get('grid');
  if (joinCode) {
    // Normalizes the URL up front (not left dangling as the old ?join=
    // form even if the resume/join below fails) — matches enterFromPath's
    // 'online' case, which does the same for a code arriving via the path
    // directly.
    const code = joinCode.toUpperCase();
    history.replaceState({ screen: 'online-lobby' }, '', `/online/${code}`);
    g.mode = 'online';
    renderScreenDom('online-lobby');
    updateModeChrome();
    attemptOnlineResume(code);
  } else if (gridCode) {
    // No pre-emptive replaceState here: unlike the join case above, there's
    // no meaningful "loading" screen to name it after, and loadAndStartCustomGrid
    // already replaceState's to the real /solo/<code> itself once (and
    // only if) the grid actually loads — claiming {screen:'board'} before
    // that succeeds would leave history.state pointing at a screen that was
    // never actually shown if the fetch fails.
    loadAndStartCustomGrid(gridCode, undefined, undefined, { push: false });
  } else {
    enterFromPath(parseLocation());
  }
  updateDailyCardBadge();
})();
