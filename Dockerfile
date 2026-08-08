# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# System deps for compiling any C-extension wheels; kept minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/tictactoe.db is not part of the image (186MB, gitignored, refreshed
# independently of app releases) — mount it as a volume at runtime, e.g.:
#   docker run -v ttt_data:/app/data -p 5001:5001 tiki-taka-toe
RUN mkdir -p /app/data

ENV PORT=5001
EXPOSE 5001

# debug stays off unless FLASK_DEBUG=1 is explicitly set (see app.py) —
# gunicorn is the production entrypoint, app.run()'s __main__ block never runs here.
#
# --workers 1 is deliberate, not a default left unset: online multiplayer room
# state (src/multiplayer.py) lives in that one process's memory. A second
# worker process would have its own, disjoint copy of the room dict, so
# requests randomly routed to it would 404 on rooms that exist in the other
# worker. Concurrency instead comes from --threads, which share memory within
# the one process (see the architecture note in src/multiplayer.py).
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --worker-class gthread --workers 1 --threads 8 --timeout 60 app:app"]
