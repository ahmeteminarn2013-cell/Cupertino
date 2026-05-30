#!/usr/bin/env bash
# Control Center'ı güvenli başlat: eski örneği kapat, yenisini aç.
# Ayrı script olduğu için pgrep deseni çağıran shell'i etkilemez.
cd "$(dirname "$0")"
SCRIPT="control_center.py"
for p in $(pgrep -f "$SCRIPT"); do kill "$p" 2>/dev/null; done
sleep 0.4
if [ "$1" = "test" ]; then
    NEXUS_CC_TEST=1 nohup python3 "$SCRIPT" >cc.log 2>&1 &
else
    nohup python3 "$SCRIPT" >cc.log 2>&1 &
fi
disown
sleep 0.5
echo "CC başlatıldı pid=$(pgrep -f "$SCRIPT")"
