#!/usr/bin/env bash
nohup xfce4-panel >/dev/null 2>&1 &
disown
sleep 2
echo "pid: $(pgrep -x xfce4-panel)"
