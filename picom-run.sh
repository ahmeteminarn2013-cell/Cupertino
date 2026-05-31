#!/usr/bin/env bash
# picom'u başlat (frosted/blur stili için). XFCE compositing'i kapatır ki
# picom tek compositor olsun. picom ölürse compositor kalmaz — bu GÜVENLİDİR
# (compositorsuz = panel tam solid, siyah ekran olmaz; test edildi).
HERE="$(cd "$(dirname "$0")" && pwd)"
xfconf-query -c xfwm4 -p /general/use_compositing -s false 2>/dev/null
pkill -x picom 2>/dev/null
sleep 0.6
exec picom --config "$HERE/picom.conf"
