#!/usr/bin/env bash
# ADIM 6 — Gerçek buzlu cam (blur): XFCE compositing'i kapat, picom'u blur ile çalıştır.
HERE="$(cd "$(dirname "$0")" && pwd)"

# 1) XFCE'nin kendi compositing'ini kapat (picom ile çakışmasın)
xfconf-query -c xfwm4 -p /general/use_compositing -s false 2>/dev/null

# 2) Login'de picom otomatik başlasın
AUTO="$HOME/.config/autostart/cupertino-picom.desktop"
mkdir -p "$(dirname "$AUTO")"
cat > "$AUTO" <<EOF
[Desktop Entry]
Type=Application
Name=Cupertino picom (blur)
Comment=macOS buzlu cam derleyici
Exec=picom --config "$HERE/picom.conf"
Terminal=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

# 3) Eski picom'u kapat, yenisini ayrık başlat
pkill -x picom 2>/dev/null
sleep 0.6
setsid -f picom --config "$HERE/picom.conf" >/dev/null 2>&1 < /dev/null
sleep 1.2

# 4) Paneli yenile (yeni %15 CSS yüklensin)
for p in $(pgrep -x xfce4-panel); do kill "$p" 2>/dev/null; done
sleep 1
nohup xfce4-panel >/dev/null 2>&1 &
disown
sleep 2

echo "picom pid: $(pgrep -x picom)"
echo "panel pid: $(pgrep -x xfce4-panel)"
