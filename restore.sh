#!/usr/bin/env bash
# GERİ AL — paneli yedekten eski haline döndürür ve CSS importunu kaldırır.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BK="$(ls -t "$HERE"/backup/xfce4-panel.xml.*.bak 2>/dev/null | head -1)"
if [ -n "$BK" ]; then
    # xfconf daemon'u kapat, XML'i geri yaz, paneli yeniden başlat
    pkill -f xfconfd 2>/dev/null || true
    sleep 1
    cp "$BK" "$HOME/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
    echo ">> Panel ayarı geri yüklendi: $BK"
fi

# gtk.css importunu kaldır
GTK_CSS="$HOME/.config/gtk-3.0/gtk.css"
if [ -f "$GTK_CSS" ]; then
    grep -v "gtk-panel.css" "$GTK_CSS" > "$GTK_CSS.tmp" && mv "$GTK_CSS.tmp" "$GTK_CSS"
    echo ">> gtk.css importu kaldırıldı"
fi

# blur'u geri al: picom'u kapat, autostart'ı sil, XFCE compositing'i aç
rm -f "$HOME/.config/autostart/cupertino-picom.desktop"
pkill -x picom 2>/dev/null || true
xfconf-query -c xfwm4 -p /general/use_compositing -s true 2>/dev/null || true
echo ">> picom (blur) kapatıldı, XFCE compositing geri açıldı"

# Plank'ı geri getir (dock'a dönüş)
if [ -f "$HERE/backup/plank.desktop.bak" ]; then
    cp "$HERE/backup/plank.desktop.bak" "$HOME/.config/autostart/plank.desktop"
    nohup plank >/dev/null 2>&1 &
    echo ">> Plank geri getirildi"
fi

# Control Center daemon autostart'ını da kaldır (isteğe bağlı)
rm -f "$HOME/.config/autostart/cupertino-control-center.desktop"

echo ">> Tam temizlik için ~/.profile ve ~/.xprofile içindeki 'appmenu-gtk-module' satırlarını elle silebilirsin."
echo ">> Oturumu kapatıp açınca eski haline döner."
