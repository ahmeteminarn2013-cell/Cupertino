#!/usr/bin/env bash
# Tek daemon + taze panel garanti et.
HERE="$(cd "$(dirname "$0")" && pwd)"
# tüm CC daemon'larını kapat
for p in $(pgrep -f "control_center.py"); do kill "$p" 2>/dev/null; done
sleep 0.4
# tek daemon başlat
nohup python3 "$HERE/control_center.py" --daemon >/dev/null 2>&1 &
disown
sleep 1
# paneli yenile
for p in $(pgrep -x xfce4-panel); do kill "$p" 2>/dev/null; done
sleep 1
nohup xfce4-panel >/dev/null 2>&1 &
disown
sleep 2
echo "daemon pid: $(cat "$HOME/.cache/cupertino-cc.pid" 2>/dev/null)"
echo "panel pid:  $(pgrep -x xfce4-panel)"
echo "daemon sayısı: $(pgrep -f control_center.py | wc -l)"
