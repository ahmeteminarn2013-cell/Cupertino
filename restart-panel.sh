#!/usr/bin/env bash
# Paneli temiz, tam ayrık yeniden başlat (yeni eklentiler + sıra yüklensin).
for p in $(pgrep -x xfce4-panel); do kill "$p" 2>/dev/null; done
sleep 1
setsid -f xfce4-panel >/dev/null 2>&1 < /dev/null
sleep 2
echo "panel pid: $(pgrep -x xfce4-panel)"
