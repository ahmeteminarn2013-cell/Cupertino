#!/usr/bin/env bash
# ============================================================
#  Cupertino v2 — Elma menüsü · Spotlight · OSD · macOS bildirimler
#  · no-picom yuvarlak saydam dock · 5 daemon (hepsi $HERE'e göre, taşınabilir)
#
#  02/04/07 (panel + dock + launcher iskeleti) çalıştıktan SONRA çağrılır.
#  Tüm yollar $HERE (klonun yeri) üzerinden → kullanıcıya özel sabit yol YOK.
#  Hedef: Linux Mint XFCE 21/22 (tam plugin-ID taşınabilirliği v2.1).
# ============================================================
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CH=xfce4-panel
KS=xfce4-keyboard-shortcuts
say() { echo -e "   \033[1;36m· $*\033[0m"; }

CACHE="$HOME/.cache"; mkdir -p "$CACHE"
mkdir -p "$HOME/.config/cupertino"

# ---- 0) state.ini (varsayılan koyu tema) ----
if [ ! -f "$HOME/.config/cupertino/state.ini" ]; then
  cat > "$HOME/.config/cupertino/state.ini" <<EOF
[ui]
theme = dark
dock_op = 75
radius = 22
bar_alpha = 100
color = 22,22,24
gap = 12
EOF
fi
say "state.ini hazır"

# ---- 1) no-picom: xfwm4 compositoru AÇ, picom KAPALI ----
xfconf-query -c xfwm4 -p /general/use_compositing -s true
pkill -x picom 2>/dev/null || true
# picom autostart (varsa) kapat
PA="$HOME/.config/autostart/cupertino-picom.desktop"
[ -f "$PA" ] && sed -i 's/^X-GNOME-Autostart-enabled=.*/X-GNOME-Autostart-enabled=false/' "$PA"
say "xfwm4 compositing açık (picom yok)"

# ---- 2) Dock + çubuk arka planı = ÜRETİLEN RESİMLER (background-style=2) ----
python3 "$HERE/gen-dock-bg.py" >/dev/null
xfconf-query -c $CH -p /panels/panel-2/length-adjust -t bool -s true  --create
xfconf-query -c $CH -p /panels/panel-2/length        -t double -s 1   --create
for p in panel-1 panel-2; do
  st=2; img="$HERE/assets/bar-bg.png"; [ "$p" = panel-2 ] && img="$HERE/assets/dock-bg.png"
  xfconf-query -c $CH -p /panels/$p/background-style -t uint -s $st --create
  xfconf-query -c $CH -p /panels/$p/background-image -t string -s "$img" --create
  for prop in enter-opacity leave-opacity background-alpha; do
    xfconf-query -c $CH -p /panels/$p/$prop -t uint -s 100 --create 2>/dev/null || true
  done
done
# dock'u alttan 12px yukarı (gap, gen-dock-bg saydam alt şeritle yapıyor); konum 07'den
say "no-picom yuvarlak saydam dock"

# ---- 3) Elma menüsü: plugin-1'i (apple/whisker) LAUNCHER'a çevir → apple-toggle.sh ----
APPLE_ICON="$HOME/.local/share/icons/cupertino-apple.svg"
mkdir -p "$HOME/.config/xfce4/panel/launcher-1"
cat > "$HOME/.config/xfce4/panel/launcher-1/cupertino-apple.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Apple Menu
Exec=$HERE/apple-toggle.sh
Icon=$APPLE_ICON
Terminal=false
StartupNotify=false
EOF
xfconf-query -c $CH -p /plugins/plugin-1 -t string -s "launcher"
xfconf-query -c $CH -p /plugins/plugin-1/items -t string -s "cupertino-apple.desktop" --force-array --create
xfconf-query -c $CH -p /plugins/plugin-1/show-label -t bool -s false --create
say "Elma menüsü (plugin-1 → apple-toggle.sh)"

# ---- 4) Spotlight: arama launcher'ını (spotlight.desktop) bul → spotlight-toggle.sh ----
for d in "$HOME"/.config/xfce4/panel/launcher-*; do
  [ -f "$d/spotlight.desktop" ] || continue
  sed -i "s|^Exec=.*|Exec=$HERE/spotlight-toggle.sh|" "$d/spotlight.desktop"
done
# Super+Space (⌘+Space)
xfconf-query -c $KS -p "/commands/custom/<Super>space" -t string -s "$HERE/spotlight-toggle.sh" --create
say "Spotlight (arama butonu + Super+Space)"

# ---- 5) OSD: multimedya tuşları → osd-ctl.sh, XFCE varsayılan OSD'leri KAPAT ----
# pulseaudio plugin'i türünden bul (ID dağıtıma göre değişir)
PA_ID="$(xfconf-query -c $CH -lv 2>/dev/null | awk '/\/plugins\/plugin-[0-9]+ +pulseaudio$/{n=$1; sub(".*plugin-","",n); print n; exit}')"
[ -n "$PA_ID" ] && xfconf-query -c $CH -p /plugins/plugin-$PA_ID/enable-keyboard-shortcuts -t bool -s false 2>/dev/null || true
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/handle-brightness-keys -t bool -s false 2>/dev/null || true
O="$HERE/osd-ctl.sh"
xfconf-query -c $KS -p "/commands/custom/XF86AudioRaiseVolume"   -t string -s "$O vol-up"   --create
xfconf-query -c $KS -p "/commands/custom/XF86AudioLowerVolume"   -t string -s "$O vol-down" --create
xfconf-query -c $KS -p "/commands/custom/XF86AudioMute"          -t string -s "$O mute"     --create
xfconf-query -c $KS -p "/commands/custom/XF86MonBrightnessUp"    -t string -s "$O bri-up"   --create
xfconf-query -c $KS -p "/commands/custom/XF86MonBrightnessDown"  -t string -s "$O bri-down" --create
say "OSD (ses/parlaklık tuşları bağlandı, varsayılan OSD'ler kapatıldı)"

# ---- 6) gtk.css @import (CSS — menü/bildirim/dock stili) ----
GTK_CSS="$HOME/.config/gtk-3.0/gtk.css"; mkdir -p "$(dirname "$GTK_CSS")"
if ! grep -qF "$HERE/gtk-panel.css" "$GTK_CSS" 2>/dev/null; then
  # eski cupertino import'larını temizle, yenisini ekle
  sed -i '\#gtk-panel.css#d' "$GTK_CSS" 2>/dev/null || true
  printf '@import url("%s");\n%s\n' "$HERE/gtk-panel.css" "$(cat "$GTK_CSS" 2>/dev/null)" > "$GTK_CSS"
fi
say "gtk.css import (macOS menü + bildirim stili)"

# ---- 7) Control Center daemon autostart ($HERE; o da apple/osd/spotlight/watcher daemon'larını başlatır) ----
AS="$HOME/.config/autostart"; mkdir -p "$AS"
cat > "$AS/cupertino-control-center.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Cupertino Control Center
Exec=python3 "$HERE/control_center.py" --daemon
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
say "Control Center + tüm daemon'lar autostart"

# ---- 8) Şimdi başlat (oturum yeniden başlatmadan) ----
pkill -x xfce4-notifyd 2>/dev/null || true   # bildirim CSS'i taze okusun
for pf in cupertino-cc cupertino-apple cupertino-osd cupertino-spotlight cupertino-dock-watch; do
  pid="$(cat "$CACHE/$pf.pid" 2>/dev/null)"; [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
done
rm -f "$CACHE"/cupertino-*.pid
setsid -f python3 "$HERE/control_center.py" --daemon >/dev/null 2>&1 < /dev/null || true
$CH -r >/dev/null 2>&1 || true
say "v2 servisleri başlatıldı"

echo -e "\033[1;32m   ✓ Cupertino v2 özellikleri kuruldu (Elma menüsü · Spotlight · OSD · bildirimler)\033[0m"
