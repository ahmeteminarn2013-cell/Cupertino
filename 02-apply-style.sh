#!/usr/bin/env bash
# ADIM 2 — macOS menü çubuğu görünümü (sudo GEREKMEZ).
#   - apple ikonu kurulur, whisker düğmesine atanır
#   - panel inceltilir, yarı saydam cam GTK CSS uygulanır
#   - saat macOS formatına çevrilir
#   - global menü için ortam değişkenleri yazılır
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- 1) Apple ikonu ---
ICON_DST="$HOME/.local/share/icons"
mkdir -p "$ICON_DST"
cp "$HERE/assets/apple-white.svg" "$ICON_DST/cupertino-apple.svg"
APPLE_ICON="$ICON_DST/cupertino-apple.svg"
echo ">> Apple ikonu: $APPLE_ICON"

# --- 2) GTK CSS @import ---
GTK_CSS="$HOME/.config/gtk-3.0/gtk.css"
mkdir -p "$(dirname "$GTK_CSS")"
[ -f "$GTK_CSS" ] && cp "$GTK_CSS" "$HERE/backup/gtk.css.bak" || true
IMPORT_LINE="@import url(\"$HERE/gtk-panel.css\");"
if ! grep -qF "gtk-panel.css" "$GTK_CSS" 2>/dev/null; then
    printf '%s\n%s\n' "$IMPORT_LINE" "$(cat "$GTK_CSS" 2>/dev/null)" > "$GTK_CSS"
    echo ">> gtk.css'e import eklendi"
else
    echo ">> gtk.css import zaten var"
fi

# --- 3) Whisker düğmesini Apple yap ---
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-icon       -t string -s "$APPLE_ICON" --create
xfconf-query -c xfce4-panel -p /plugins/plugin-1/show-button-title -t bool   -s false --create
xfconf-query -c xfce4-panel -p /plugins/plugin-1/show-button-icon  -t bool   -s true  --create
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-single-row -t bool   -s true  --create
echo ">> Whisker düğmesi -> Apple"

# --- 4) Panel: ÜSTE taşı + ince + cam ---
# ÖNEMLİ: panel-1'i üste, tam genişlik, yatay yapar (Mint XFCE'de varsayılan
# panel ALTTA olabilir; menü çubuğunun üstte olması için zorla konumlandırıyoruz).
xfconf-query -c xfce4-panel -p /panels/panel-1/mode            -t uint   -s 0    --create  # yatay
xfconf-query -c xfce4-panel -p /panels/panel-1/length          -t double -s 100  --create  # tam genişlik
xfconf-query -c xfce4-panel -p /panels/panel-1/length-adjust   -t bool   -s false --create
xfconf-query -c xfce4-panel -p /panels/panel-1/position        -t string -s "p=6;x=960;y=0" --create  # üst-orta
xfconf-query -c xfce4-panel -p /panels/panel-1/position-locked -t bool   -s true --create
xfconf-query -c xfce4-panel -p /panels/panel-1/size            -t uint -s 26 --create
xfconf-query -c xfce4-panel -p /panels/panel-1/icon-size       -t uint -s 16 --create
xfconf-query -c xfce4-panel -p /panels/panel-1/background-style -t uint -s 0  --create
xfconf-query -c xfce4-panel -p /panels/panel-1/enable-struts   -t bool -s true --create
echo ">> Panel üste taşındı + inceltildi (26px) + cam arka plan"

# --- 5) Saat: macOS formatı  "Cum 30 May  14:32" ---
xfconf-query -c xfce4-panel -p /plugins/plugin-13/mode                -t uint   -s 2 --create
xfconf-query -c xfce4-panel -p /plugins/plugin-13/digital-layout      -t uint   -s 3 --create
xfconf-query -c xfce4-panel -p /plugins/plugin-13/digital-time-format -t string -s "%a %d %b  %H:%M" --create
xfconf-query -c xfce4-panel -p /plugins/plugin-13/digital-time-font   -t string -s "SF Pro Text 9" --create
echo ">> Saat macOS formatına çevrildi"

# --- 6) Global menü ortam değişkenleri (yeniden giriş sonrası aktif) ---
write_env () {
    local f="$1"
    touch "$f"
    if ! grep -q "appmenu-gtk-module" "$f" 2>/dev/null; then
        {
            echo ''
            echo '# Cupertino — macOS global menü'
            echo 'export GTK_MODULES="${GTK_MODULES:+$GTK_MODULES:}appmenu-gtk-module"'
            echo 'export UBUNTU_MENUPROXY=1'
        } >> "$f"
        echo ">> ortam değişkeni yazıldı: $f"
    fi
}
write_env "$HOME/.profile"
write_env "$HOME/.xprofile"

# --- 7) Paneli yeniden başlat (stil hemen görünsün) ---
xfce4-panel -r >/dev/null 2>&1 || true
echo ""
echo ">> BİTTİ. Görünüm uygulandı."
echo ">> Global menünün uygulamalarda çıkması için ÇIKIŞ YAPIP TEKRAR GİRİŞ yap."
echo ">> Global menü eklentisini panele eklemek için: 03-add-appmenu.sh"
