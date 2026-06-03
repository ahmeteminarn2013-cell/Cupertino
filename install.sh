#!/usr/bin/env bash
# ============================================================
#  Cupertino — macOS masaüstü TEK KOMUT kurulumu (XFCE)
#  Kullanım:  ./install.sh
#  Tekrar çalıştırılabilir (idempotent). XFCE gerektirir.
# ============================================================
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
say()  { echo -e "\n\033[1;36m>> $*\033[0m"; }
ok()   { echo -e "   \033[1;32m✓\033[0m $*"; }
warn() { echo -e "   \033[1;33m!\033[0m $*"; }

# ---------- 0) Ön kontroller ----------
case "${XDG_CURRENT_DESKTOP:-}" in
  *XFCE*) ;;
  *) warn "Bu kurulum XFCE içindir (şu an: ${XDG_CURRENT_DESKTOP:-bilinmiyor}). Yine de devam ediliyor."; ;;
esac
say "Cupertino kurulumu başlıyor. sudo parolası istenebilir."
sudo -v

# ---------- 1) Paketler ----------
say "1/9  Paketler kuruluyor (appmenu, picom, playerctl, build araçları)..."
sudo apt-get update -qq || true
sudo apt-get install -y \
  xfce4-appmenu-plugin appmenu-gtk2-module appmenu-gtk3-module appmenu-registrar \
  picom playerctl xdotool wmctrl xdg-utils git patch \
  brightnessctl python3-gi gir1.2-gtk-3.0 python3-pil pulseaudio-utils \
  build-essential xfce4-dev-tools libxfce4panel-2.0-dev libxfce4ui-2-dev libgtk-3-dev \
  libwnck-3-dev libcairo2-dev gettext autopoint autoconf automake libtool intltool pkg-config \
  >/dev/null
ok "Paketler tamam"
# PySide6 (Control Center + Ayar Merkezi GUI için)
if ! python3 -c "import PySide6" 2>/dev/null; then
  warn "PySide6 yok, kuruluyor..."
  sudo apt-get install -y python3-pyside6.qtwidgets python3-pyside6.qtsvg 2>/dev/null \
    || pip3 install --user PySide6 2>/dev/null \
    || pip3 install --user --break-system-packages PySide6
fi
python3 -c "import PySide6" 2>/dev/null && ok "PySide6 hazır" || warn "PySide6 kurulamadı — GUI çalışmayabilir"

# ---------- 2) WhiteSur ikon teması ----------
say "2/9  WhiteSur (macOS) ikon teması..."
if [ ! -d "$HOME/.local/share/icons/WhiteSur-dark" ]; then
  tmp="$(mktemp -d)"
  git clone --depth=1 https://github.com/vinceliuice/WhiteSur-icon-theme.git "$tmp/wsi" >/dev/null 2>&1
  "$tmp/wsi/install.sh" -d "$HOME/.local/share/icons" >/dev/null 2>&1
  rm -rf "$tmp"
fi
xfconf-query -c xsettings -p /Net/IconThemeName -s "WhiteSur-dark" 2>/dev/null || true
ok "İkon teması ayarlandı"

# ---------- 3) docklike eklentisi (önizleme + magnification) ----------
say "3/9  docklike derleniyor (pencere önizlemeli, hover büyütmeli dock)..."
if ! find /usr/lib -name libdocklike.so 2>/dev/null | grep -q .; then
  bd="$(mktemp -d)"
  git clone --depth=1 --branch xfce4-docklike-plugin-0.4.2 \
    https://gitlab.xfce.org/panel-plugins/xfce4-docklike-plugin.git "$bd/dl" >/dev/null 2>&1
  ( cd "$bd/dl"
    patch -p1 < "$HERE/docklike-cupertino.patch" >/dev/null
    ./autogen.sh --prefix=/usr >/dev/null 2>&1
    make -j2 >/dev/null 2>&1
    sudo make install >/dev/null 2>&1 )
  rm -rf "$bd"
  ok "docklike derlendi + kuruldu"
else
  ok "docklike zaten kurulu"
fi

# ---------- 4) Menü çubuğu stili (apple, cam CSS, saat, env) ----------
say "4/9  Üst menü çubuğu stili..."
bash "$HERE/02-apply-style.sh" >/dev/null
ok "Apple + cam panel + macOS saat + global menü env"

# ---------- 5) Üst panel: appmenu + spotlight + control center butonu ----------
say "5/9  Global menü + Spotlight + Control Center..."
bash "$HERE/04-wire-panel.sh" >/dev/null
ok "Üst panel bağlandı"

# ---------- 6) Dock (Plank kaldır, panel-2 + docklike + pinli uygulamalar) ----------
say "6/9  Dock kuruluyor (Plank yerine)..."
bash "$HERE/07-create-dock.sh" >/dev/null

# docklike ayarları (önizleme, köşe, pinli uygulamalar + trash)
# Pinli listeyi SADECE kurulu uygulamalardan oluştur (yoksa dock seyrek/bozuk görünür)
PINS=""
for app in thunar firefox google-chrome thunderbird xfce4-terminal code org.gnome.Rhythmbox3 xfce-settings-manager; do
  if [ -f /usr/share/applications/"$app".desktop ] || [ -f "$HOME/.local/share/applications/$app.desktop" ]; then
    PINS="${PINS}${app};"
  fi
done
PINS="${PINS}cupertino-settings;cupertino-trash;"
RC="$HOME/.config/xfce4/panel/docklike-30.rc"
if [ ! -f "$RC" ]; then
  cat > "$RC" <<EOF
[user]
showPreviews=true
previewScale=0.18
previewSleep=200
indicatorOrientation=0
indicatorStyle=1
inactiveIndicatorStyle=0
pinned=$PINS
EOF
fi
# dock görünüm: yuvarlak frosted + boyut
xfconf-query -c xfce4-panel -p /panels/panel-2/background-style -t uint -s 1 --create 2>/dev/null || true
xfconf-query -c xfce4-panel -p /panels/panel-2/background-rgba \
  -t double -s 0.13 -t double -s 0.13 -t double -s 0.16 -t double -s 0.58 --create --force-array 2>/dev/null || true
xfconf-query -c xfce4-panel -p /panels/panel-2/size -t uint -s 64 2>/dev/null || true
ok "Dock + önizleme + pinli uygulamalar"

# ---------- 7) Trash + GUI kısayolları (.desktop) ----------
say "7/9  Trash + Ayar Merkezi kısayolları..."
APPS="$HOME/.local/share/applications"; mkdir -p "$APPS"
# Trash (Çöpü Boşalt action'lı, macOS ikonu)
cat > "$APPS/cupertino-trash.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Trash
Name[tr]=Çöp Kutusu
Exec=xdg-open trash:///
Icon=user-trash
Terminal=false
Actions=empty-trash;
Categories=Utility;

[Desktop Action empty-trash]
Name=Empty Trash
Name[tr]=Çöpü Boşalt
Exec=gio trash --empty
EOF
# Ayar Merkezi GUI
cat > "$APPS/cupertino-settings.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Cupertino Ayar Merkezi
Comment=macOS panel ve dock ayarları
Exec=python3 "$HERE/control_panel.py"
Icon=$HERE/assets/gear.svg
Terminal=false
Categories=Settings;
StartupWMClass=control_panel.py
EOF
update-desktop-database "$APPS" 2>/dev/null || true
ok "Trash + Ayar Merkezi eklendi"

# ---------- 8) Cupertino v2: Elma menüsü · Spotlight · OSD · bildirimler · no-picom dock ----------
say "8/9  Cupertino v2 özellikleri (Elma menüsü, Spotlight, OSD, macOS bildirimler)..."
chmod +x "$HERE"/*.sh "$HERE"/*.py 2>/dev/null || true
bash "$HERE/08-cupertino-v2.sh"
ok "v2 özellikleri + 5 daemon (Control Center, Elma, OSD, Spotlight, dock-watcher)"

# ---------- 9) Panel'i temiz başlat ----------
say "9/9  Panel başlatılıyor..."
for p in $(pgrep -x xfce4-panel); do kill "$p" 2>/dev/null; done
sleep 1.5
nohup xfce4-panel >/dev/null 2>&1 & disown
sleep 2
ok "Panel + no-picom yuvarlak dock çalışıyor"

# ---------- BİTTİ ----------
echo -e "\n\033[1;32m============================================\033[0m"
echo -e "\033[1;32m  Cupertino v2 kuruldu! 🍎\033[0m"
echo -e "\033[1;32m============================================\033[0m"
echo "  • Menü çubuğu + yuvarlak dock + Elma menüsü + Spotlight + OSD + bildirimler"
echo "  • 🍎 Elma logosu → macOS menüsü  ·  ⌘(Win)+Space → Spotlight  ·  🔍 buton da açar"
echo "  • Ses/parlaklık tuşları → macOS OSD  ·  Control Center: çubuktaki toggle ikonu"
echo "  • Global menüler (File/Edit) için: ÇIKIŞ YAP / TEKRAR GİRİŞ"
echo "  • Ayarlar: dock'taki ⚙️  ·  Dock boşluğu: ./set-gap.sh 12  ·  Geri al: ./uninstall.sh"
echo ""
