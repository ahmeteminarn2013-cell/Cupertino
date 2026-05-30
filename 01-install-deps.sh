#!/usr/bin/env bash
# ADIM 1 — Global menü (macOS gibi File/Edit/View üst barda) için gerekli paketler.
# Bu script sudo ister; senin terminalinde çalıştırman gerekir.
set -e
echo ">> Global menü paketleri kuruluyor..."
sudo apt update
sudo apt install -y \
    xfce4-appmenu-plugin \
    appmenu-gtk2-module \
    appmenu-gtk3-module \
    appmenu-registrar
echo ">> Kuruldu. Şimdi 02-apply-style.sh çalıştır (sudo gerekmez)."
