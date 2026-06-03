#!/usr/bin/env bash
# ============================================================
#  Cupertino — OSD daemon'ı yeniden başlat.
#  osd.py'yi düzenledikten sonra (px konum, boyut, renk vs.) çalıştır
#  ki değişiklik RAM'deki daemon'a yansısın.
#  Kullanım:  ./osd-restart.sh
# ============================================================
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDF="$HOME/.cache/cupertino-osd.pid"

old="$(cat "$PIDF" 2>/dev/null)"
[ -n "$old" ] && kill "$old" 2>/dev/null && echo "eski daemon durduruldu ($old)"
rm -f "$PIDF"
setsid -f python3 "$HERE/osd.py" --daemon >/dev/null 2>&1 < /dev/null
sleep 0.6
new="$(cat "$PIDF" 2>/dev/null)"
echo "✓ OSD yeniden başladı (PID $new)"
echo "  Test: ses/parlaklık tuşuna bas — ya da: python3 $HERE/osd.py brightness 50"
