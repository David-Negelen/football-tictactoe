# Project instructions

- Commit at the end of every task/session in this repo — don't leave finished work uncommitted. Commit at logical checkpoints along the way too, not just at the very end.
- The dev server caches Jinja templates in-process. After editing `templates/*.html`, restart it (`make kill && make run`) before testing — otherwise you're looking at stale HTML.
- Bump `CACHE_NAME` in `static/sw.js` after changing `templates/game.html` or `static/js/game.js` — the service worker cache-first-serves the game shell, so browsers won't pick up the change otherwise.
