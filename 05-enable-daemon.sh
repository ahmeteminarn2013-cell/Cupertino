#!/usr/bin/env bash
# ADIM 5 — Control Center'ı RAM'de sürekli açık daemon yap (tıklama anında açılsın).
#   - panel butonunu cc-toggle.sh'a bağlar
#   - login'de daemon'u önyükler (autostart)
#   - daemon'u şimdi başlatır
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$HERE/cc-toggle.sh"

# 1) Panel butonu artık toggle scriptini çağırsın
DESK="$HOME/.config/xfce4/panel/launcher-22/control-center.desktop"
if [ -f "$DESK" ]; then
    sed -i "s|^Exec=.*|Exec=$HERE/cc-toggle.sh|" "$DESK"
    echo ">> Panel butonu -> cc-toggle.sh"
fi

# 2) Login'de RAM'e önyükle
AUTO="$HOME/.config/autostart/cupertino-control-center.desktop"
mkdir -p "$(dirname "$AUTO")"
cat > "$AUTO" <<EOF
[Desktop Entry]
Type=Application
Name=Cupertino Control Center (daemon)
Comment=Control Center'i RAM'de hazir tutar
Exec=python3 "$HERE/control_center.py" --daemon
Terminal=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF
echo ">> Autostart eklendi (login'de önyükleme)"

# 3) Daemon'u şimdi başlat (varsa eskiyi kapat)
OLD="$(cat "$HOME/.cache/cupertino-cc.pid" 2>/dev/null || true)"
[ -n "$OLD" ] && kill "$OLD" 2>/dev/null || true
sleep 0.3
nohup python3 "$HERE/control_center.py" --daemon >/dev/null 2>&1 &
disown
sleep 1
echo ">> Daemon başlatıldı pid=$(cat "$HOME/.cache/cupertino-cc.pid" 2>/dev/null)"
echo ">> Artık Control Center butonu anında açılır."
