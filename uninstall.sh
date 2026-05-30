#!/usr/bin/env bash
# ============================================================
#  Cupertino — geri alma (eski masaüstüne dönüş)
# ============================================================
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
say() { echo -e "\n\033[1;36m>> $*\033[0m"; }

say "Cupertino kaldırılıyor..."

# 1) picom (blur) kapat + autostart sil + XFCE compositing geri aç
rm -f "$HOME/.config/autostart/cupertino-picom.desktop"
pkill -x picom 2>/dev/null || true
xfconf-query -c xfwm4 -p /general/use_compositing -s true 2>/dev/null || true
echo "   ✓ picom kapatıldı, XFCE compositing geri açıldı"

# 2) Control Center daemon kapat + autostart sil
rm -f "$HOME/.config/autostart/cupertino-control-center.desktop"
for p in $(pgrep -f "control_center.py"); do kill "$p" 2>/dev/null; done
echo "   ✓ Control Center daemon kapatıldı"

# 3) Kısayolları sil
rm -f "$HOME/.local/share/applications/cupertino-trash.desktop"
rm -f "$HOME/.local/share/applications/cupertino-settings.desktop"
echo "   ✓ Kısayollar silindi"

# 4) Panel ayarını yedekten geri yükle (üst panel + dock kaldırılır)
BK="$(ls -t "$HERE"/backup/xfce4-panel.xml.*.bak 2>/dev/null | head -1)"
if [ -n "$BK" ]; then
  pkill -f xfconfd 2>/dev/null || true
  sleep 1
  cp "$BK" "$HOME/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
  echo "   ✓ Panel ayarı yedekten geri yüklendi"
fi

# 5) gtk.css importunu kaldır
GTK_CSS="$HOME/.config/gtk-3.0/gtk.css"
if [ -f "$GTK_CSS" ]; then
  grep -v "gtk-panel.css" "$GTK_CSS" > "$GTK_CSS.tmp" && mv "$GTK_CSS.tmp" "$GTK_CSS"
  echo "   ✓ gtk.css importu kaldırıldı"
fi

# 6) Plank'ı geri getir
if [ -f "$HERE/backup/plank.desktop.bak" ]; then
  cp "$HERE/backup/plank.desktop.bak" "$HOME/.config/autostart/plank.desktop"
  nohup plank >/dev/null 2>&1 & disown
  echo "   ✓ Plank geri getirildi"
fi

echo -e "\n\033[1;32m✓ Geri alındı. Oturumu kapatıp açınca tamamen eski haline döner.\033[0m"
echo "  Not: ~/.profile ve ~/.xprofile içindeki 'appmenu-gtk-module' satırlarını"
echo "       istersen elle silebilirsin. docklike paketi kuruluysa: sudo rm /usr/lib/xfce4/panel/plugins/libdocklike.so"
