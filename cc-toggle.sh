#!/usr/bin/env bash
# Control Center aç/kapat — panel butonu bunu çağırır.
# Daemon RAM'de açıksa anında sinyal gönderir; değilse başlatıp gösterir.
HERE="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$HOME/.cache/cupertino-cc.pid"

PID="$(cat "$PIDFILE" 2>/dev/null)"
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    kill -USR1 "$PID"        # <<< anında aç/kapat
    exit 0
fi

# Daemon yok → başlat (ilk sefer / çökme sonrası), sonra göster
nohup python3 "$HERE/control_center.py" --daemon >/dev/null 2>&1 &
disown
for _ in $(seq 1 40); do          # pidfile + sinyal işleyici hazır olana dek bekle
    NP="$(cat "$PIDFILE" 2>/dev/null)"
    [ -n "$NP" ] && kill -0 "$NP" 2>/dev/null && break
    sleep 0.05
done
sleep 0.4
NP="$(cat "$PIDFILE" 2>/dev/null)"
[ -n "$NP" ] && kill -USR1 "$NP" 2>/dev/null
