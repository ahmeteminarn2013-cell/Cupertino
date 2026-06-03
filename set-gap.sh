#!/usr/bin/env bash
# ============================================================
#  Cupertino — dock'un ALTINDAKİ boşluğu ayarla (macOS hissi)
#  Kullanım:  ./set-gap.sh 12      (12px boşluk)
#             ./set-gap.sh 0       (boşluksuz, tam dibe)
#             ./set-gap.sh 18      (daha çok boşluk)
#  state.ini 'gap' + CSS padding-bottom'u birlikte günceller,
#  resmi yeniden üretir ve uygular. (picom YOK, xfwm4 ile.)
# ============================================================
GAP="${1:-12}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "$GAP" in (*[!0-9]*|"") echo "Kullanım: ./set-gap.sh <px>  (örn. 12)"; exit 1;; esac

# 1) state.ini gap
python3 - "$GAP" <<'PY'
import configparser, os, sys
gap = sys.argv[1]
p = os.path.expanduser("~/.config/cupertino/state.ini")
c = configparser.ConfigParser(); c.optionxform = str; c.read(p)
c.has_section("ui") or c.add_section("ui")
c.set("ui", "gap", gap)
with open(p, "w") as f: c.write(f)
PY

# 2) CSS padding-bottom = gap (ikonları yuvarlak gövdede ortalar)
sed -i "s/padding-bottom: [0-9]\+px;/padding-bottom: ${GAP}px;/" "$HERE/gtk-panel.css"

# 3) resmi üret + diskten tazele + paneli yenile
python3 "$HERE/gen-dock-bg.py" >/dev/null
xfconf-query -c xfce4-panel -p /panels/panel-2/background-image -t string -s "/dev/null" 2>/dev/null
xfconf-query -c xfce4-panel -p /panels/panel-2/background-image -t string -s "$HERE/assets/dock-bg.png" 2>/dev/null
xfce4-panel -r >/dev/null 2>&1
echo "✓ Dock altı boşluk: ${GAP}px"
