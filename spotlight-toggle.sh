#!/usr/bin/env bash
# Cupertino — Spotlight aç/kapat. Super+Space (⌘+Space) bunu çağırır.
# Daemon RAM'de açıksa ANINDA SIGUSR1; değilse başlatıp gösterir.
HERE="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$HOME/.cache/cupertino-spotlight.pid"

PID="$(cat "$PIDFILE" 2>/dev/null)"
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    kill -USR1 "$PID"
    exit 0
fi

nohup python3 "$HERE/spotlight.py" --daemon >/dev/null 2>&1 &
disown
for _ in $(seq 1 40); do
    NP="$(cat "$PIDFILE" 2>/dev/null)"
    [ -n "$NP" ] && kill -0 "$NP" 2>/dev/null && break
    sleep 0.05
done
sleep 0.4
NP="$(cat "$PIDFILE" 2>/dev/null)"
[ -n "$NP" ] && kill -USR1 "$NP" 2>/dev/null
