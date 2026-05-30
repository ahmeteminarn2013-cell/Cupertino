#!/usr/bin/env bash
# picom'u GÜVENLİ çalıştır: ölürse/çökerse XFCE compositing'i geri açıp
# siyah ekranı önler. Login'de autostart bunu çağırır.
HERE="$(cd "$(dirname "$0")" && pwd)"

# Tek compositor olsun diye XFCE'ninkini kapat
xfconf-query -c xfwm4 -p /general/use_compositing -s false 2>/dev/null

# picom'u ön planda çalıştır (bu satır picom kapanana kadar bekler)
picom --config "$HERE/picom.conf"

# >>> GÜVENLİK AĞI <<< picom bittiyse XFCE compositing'i geri aç → ekran asla siyah kalmaz
xfconf-query -c xfwm4 -p /general/use_compositing -s true 2>/dev/null
