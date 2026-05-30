#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
for p in $(pgrep -f control_center.py); do kill "$p" 2>/dev/null; done
sleep 0.6
rm -f "$HOME/.cache/nexus-cc.pid" "$HOME/.cache/cupertino-cc.pid"
nohup python3 "$HERE/control_center.py" --daemon >/dev/null 2>&1 &
disown
sleep 1.2
echo "yeni daemon pid: $(cat "$HOME/.cache/cupertino-cc.pid" 2>/dev/null)"
echo "çalışan daemon sayısı: $(pgrep -f control_center.py | wc -l)"
