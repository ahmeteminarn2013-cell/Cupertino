#!/usr/bin/env bash
# ADIM 7 — Plank'ı kaldır, alta macOS dock'u (panel-2 + docklike) kur.
HERE="$(cd "$(dirname "$0")" && pwd)"
CH="xfce4-panel"

# docklike kurulu mu?
if ! find /usr/lib -name libdocklike.so 2>/dev/null | grep -q .; then
    echo "!! docklike kurulu değil."; exit 1
fi

# --- 1) Plank'ı kaldır (yedekle) ---
mkdir -p "$HERE/backup"
if [ -f "$HOME/.config/autostart/plank.desktop" ]; then
    cp "$HOME/.config/autostart/plank.desktop" "$HERE/backup/plank.desktop.bak"
    rm -f "$HOME/.config/autostart/plank.desktop"
fi
for p in $(pgrep -x plank); do kill "$p" 2>/dev/null; done
echo ">> Plank kaldırıldı (yedek: backup/plank.desktop.bak)"

# --- 2) panel-2'yi oluştur (alt dock) ---
xfconf-query -c $CH -p /panels -t int -s 1 -t int -s 2   # panel listesi = [1,2]

# Ekran boyutuna göre dock'u alt-ortaya konumla (her çözünürlükte çalışsın)
RES="$(xrandr 2>/dev/null | awk '/\*/{print $1; exit}')"   # ör: 1920x1080
SW="${RES%x*}"; SH="${RES#*x}"
[ -z "$SW" ] && SW=1920; [ -z "$SH" ] && SH=1080
# DY: dock'un dikey konumu. SH-36 → alttan ~12px YUKARIDA (macOS gibi küçük boşluk).
# (SH-24 tam dibe yapışıktı.) Boşluğu büyütmek için 36'yı artır.
CX=$((SW / 2)); DY=$((SH - 36))

P=/panels/panel-2
xfconf-query -c $CH -p $P/mode            -t uint   -s 0          --create  # yatay
xfconf-query -c $CH -p $P/size            -t uint   -s 47         --create  # dock yüksekliği
xfconf-query -c $CH -p $P/icon-size       -t uint   -s 40         --create
xfconf-query -c $CH -p $P/nrows           -t uint   -s 1          --create
xfconf-query -c $CH -p $P/length          -t double -s 1          --create  # içeriğe göre küçül
xfconf-query -c $CH -p $P/length-adjust   -t bool   -s true       --create
xfconf-query -c $CH -p $P/background-style -t uint  -s 0          --create  # CSS/blur görünsün
xfconf-query -c $CH -p $P/enable-struts   -t bool   -s false      --create  # yüzen (pencereler altına girer)
xfconf-query -c $CH -p $P/position-locked -t bool   -s true       --create
xfconf-query -c $CH -p $P/position        -t string -s "p=12;x=$CX;y=$DY" --create  # alt-orta (dinamik)
xfconf-query -c $CH -p $P/autohide-behavior -t uint -s 0          --create  # 0=hep görünür

# --- 3) docklike eklentisi (plugin-30) ---
xfconf-query -c $CH -p /plugins/plugin-30 -t string -s "docklike" --create
xfconf-query -c $CH -p /panels/panel-2/plugin-ids -t int -s 30 --create --force-array

echo ">> panel-2 (dock) + docklike eklendi"
echo ">> Paneli yeniden başlat: bash start-panel.sh"
