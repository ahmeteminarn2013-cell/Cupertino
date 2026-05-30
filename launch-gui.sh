#!/usr/bin/env bash
# Ayar Merkezi GUI'yi güvenli başlat (eskiyi kapat, yenisini aç).
cd "$(dirname "$0")"
for p in $(pgrep -f control_panel.py); do kill "$p" 2>/dev/null; done
sleep 0.4
nohup python3 control_panel.py >/tmp/cp.log 2>&1 &
disown
sleep 0.5
echo "GUI pid=$(pgrep -f control_panel.py)"
