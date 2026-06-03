#!/usr/bin/env bash
# ============================================================
#  Cupertino — dock arka plan izleyici (picom YOK)
#  Dock genişliği/yüksekliği değişince (uygulama açılıp kapanınca
#  docklike büyür/küçülür) yuvarlak saydam PNG'yi o boyutta YENİDEN
#  üretir ve panel'i tam restart etmeden tazeler. Böylece köşeler
#  her zaman dock'a birebir oturur (XFCE resmi UZATMAZ, TEKRARLAR).
#
#  Sadece resim-tabanlı temalarda (background-style=2) çalışır;
#  picom/blur modunda hiçbir şey yapmaz.
# ============================================================
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMG="$HERE/assets/dock-bg.png"
CH="xfce4-panel"
last=""

# --- kopya-önleme: zaten çalışan bir watcher varsa sessizce çık ---
# (kill -0 sadece canlılık kontrolü — sinyal göndermez, öldürmez; pkill YOK → self-kill yok)
PIDF="$HOME/.cache/cupertino-dock-watch.pid"
if [ -f "$PIDF" ]; then
  _op="$(cat "$PIDF" 2>/dev/null)"
  if [ -n "$_op" ] && kill -0 "$_op" 2>/dev/null && grep -qa dock-bg-watch "/proc/$_op/cmdline" 2>/dev/null; then
    exit 0
  fi
fi
mkdir -p "$HOME/.cache"; echo "$$" > "$PIDF"

# Login'de: resim-tabanlı temadaysak xfwm4 compositoru AÇIK olsun (picom değil),
# yoksa şeffaf köşeler siyah görünür.
if [ "$(xfconf-query -c $CH -p /panels/panel-2/background-style 2>/dev/null)" = "2" ]; then
  if [ "$(xfconf-query -c xfwm4 -p /general/use_compositing 2>/dev/null)" != "true" ]; then
    xfconf-query -c xfwm4 -p /general/use_compositing -s true 2>/dev/null
  fi
fi

dock_geo() {
  wmctrl -lG 2>/dev/null | grep -i xfce4-panel \
    | awk '$5>200 && $6>40 {print $5"x"$6; exit}'
}

while true; do
  # sadece dock resim modundaysa ilgilen
  if [ "$(xfconf-query -c $CH -p /panels/panel-2/background-style 2>/dev/null)" = "2" ]; then
    geo="$(dock_geo)"
    if [ -n "$geo" ] && [ "$geo" != "$last" ]; then
      python3 "$HERE/gen-dock-bg.py" >/dev/null 2>&1        # state.ini'den boyut+renk
      # resmi diskten yeniden yükletmek için property'yi toggle et (tam reload yok)
      xfconf-query -c $CH -p /panels/panel-2/background-image -t string -s "/dev/null" 2>/dev/null
      xfconf-query -c $CH -p /panels/panel-2/background-image -t string -s "$IMG" 2>/dev/null
      last="$geo"
    fi
  fi
  sleep 0.8
done
