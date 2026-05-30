#!/usr/bin/env bash
# ADIM 4 — Paneli macOS düzenine bağla:
#   - Apple'ın yanına global menü (appmenu)
#   - Sağ kümeye Control Center butonu (kendi widget'ımız)
#   - Saatin soluna Spotlight (xfce4-appfinder)
#   - Sıralama: apple | appmenu | <esnek> | bildirim | tray | pil | ses | CC | spotlight | saat
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PANELDIR="$HOME/.config/xfce4/panel"
CH="xfce4-panel"

# appmenu eklentisi kurulu mu?
if ! ls /usr/lib/*/xfce4/panel/plugins/libappmenu*.so >/dev/null 2>&1; then
    echo "!! xfce4-appmenu-plugin yok. Önce: ./01-install-deps.sh"; exit 1
fi

# --- Spotlight: mevcut boş launcher plugin-20'yi kullan ---
mkdir -p "$PANELDIR/launcher-20"
cat > "$PANELDIR/launcher-20/spotlight.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Spotlight
Comment=Ara
Exec=xfce4-appfinder
Icon=$HERE/assets/spotlight.svg
Terminal=false
StartupNotify=false
EOF
xfconf-query -c $CH -p /plugins/plugin-20 -t string -s "launcher" --create
xfconf-query -c $CH -p /plugins/plugin-20/items -t string -s "spotlight.desktop" --create --force-array
echo ">> Spotlight (plugin-20) hazır"

# --- Control Center: yeni launcher plugin-22 ---
mkdir -p "$PANELDIR/launcher-22"
cat > "$PANELDIR/launcher-22/control-center.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Control Center
Comment=Kontrol Merkezi
Exec=python3 "$HERE/control_center.py"
Icon=$HERE/assets/control-center.svg
Terminal=false
StartupNotify=false
EOF
xfconf-query -c $CH -p /plugins/plugin-22 -t string -s "launcher" --create
xfconf-query -c $CH -p /plugins/plugin-22/items -t string -s "control-center.desktop" --create --force-array
echo ">> Control Center (plugin-22) hazır"

# --- Global menü eklentisi: plugin-21 ---
xfconf-query -c $CH -p /plugins/plugin-21 -t string -s "appmenu" --create
echo ">> Global menü (plugin-21) hazır"

# --- Sıralama ---
xfconf-query -c $CH -p /panels/panel-1/plugin-ids \
    -t int -s 1  \
    -t int -s 21 \
    -t int -s 17 \
    -t int -s 9  \
    -t int -s 10 \
    -t int -s 11 \
    -t int -s 12 \
    -t int -s 22 \
    -t int -s 20 \
    -t int -s 13
echo ">> Panel sırası güncellendi"

# --- Paneli yeniden başlat (tam ayrık) ---
( setsid -f xfce4-panel >/dev/null 2>&1 < /dev/null ) || xfce4-panel -r >/dev/null 2>&1 || true
echo ""
echo ">> BİTTİ. Spotlight + Control Center + global menü panele eklendi."
echo ">> Global menü uygulamalarda boşsa: çıkış yapıp tekrar giriş yap."
