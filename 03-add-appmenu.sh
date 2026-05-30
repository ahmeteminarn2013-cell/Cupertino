#!/usr/bin/env bash
# ADIM 3 — Global menü eklentisini (appmenu) panele ekle.
# ÖNCE 01-install-deps.sh ile xfce4-appmenu-plugin kurulmuş olmalı; yoksa
# panelde kırmızı hata kutusu görünür.
set -e

# Eklenti kurulu mu kontrol et
if ! ls /usr/lib/*/xfce4/panel/plugins/libappmenu*.so >/dev/null 2>&1; then
    echo "!! xfce4-appmenu-plugin kurulu değil. Önce: ./01-install-deps.sh"
    exit 1
fi

# Yeni plugin id (kullanılmayan): 21
NEWID=21
xfconf-query -c xfce4-panel -p /plugins/plugin-$NEWID -t string -s "appmenu" --create

# Plugin sırası: apple(1) | appmenu(21) | <esnek ayraç 17> | tray... | saat(13) | launcher(20)
xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids \
    -t int -s 1  \
    -t int -s $NEWID \
    -t int -s 17 \
    -t int -s 9  \
    -t int -s 10 \
    -t int -s 11 \
    -t int -s 12 \
    -t int -s 13 \
    -t int -s 20

xfce4-panel -r >/dev/null 2>&1 || true
echo ">> Global menü eklendi. Bir uygulama aç (ör. Mousepad/Files) ve menülerin üstte çıktığını gör."
echo ">> Boşsa: çıkış yapıp tekrar giriş yap (GTK_MODULES yüklensin)."
