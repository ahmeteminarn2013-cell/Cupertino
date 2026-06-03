#!/usr/bin/env bash
# ============================================================
#  Cupertino — OSD kontrol. Multimedya tuşları buna bağlanır.
#  Ses/parlaklığı ayarlar, durumu yazar, OSD daemon'a SIGUSR1 yollar
#  (yoksa başlatır). picom YOK.
#  Kullanım: osd-ctl.sh vol-up|vol-down|mute|bri-up|bri-down
# ============================================================
HERE="$(cd "$(dirname "$0")" && pwd)"
STATE="$HOME/.cache/cupertino-osd.state"
PIDF="$HOME/.cache/cupertino-osd.pid"
S="@DEFAULT_SINK@"
mkdir -p "$HOME/.cache"

# 1) eylemi uygula
case "$1" in
  vol-up)   pactl set-sink-mute "$S" 0; pactl set-sink-volume "$S" +5% ;;
  vol-down) pactl set-sink-mute "$S" 0; pactl set-sink-volume "$S" -5% ;;
  mute)     pactl set-sink-mute "$S" toggle ;;
  bri-up)   brightnessctl -q set +8% ;;
  bri-down) brightnessctl -q set 8%- ;;
  *) echo "kullanım: osd-ctl.sh vol-up|vol-down|mute|bri-up|bri-down"; exit 1 ;;
esac

# 2) yeni durumu state'e yaz
case "$1" in
  vol-*|mute)
    if pactl get-sink-mute "$S" 2>/dev/null | grep -qi yes; then
      echo "mute 0" > "$STATE"
    else
      v=$(pactl get-sink-volume "$S" 2>/dev/null | grep -oP '\d+(?=%)' | head -1)
      echo "volume ${v:-0}" > "$STATE"
    fi ;;
  bri-*)
    cur=$(brightnessctl get 2>/dev/null); max=$(brightnessctl max 2>/dev/null)
    [ -n "$max" ] && [ "$max" -gt 0 ] && echo "brightness $(( cur * 100 / max ))" > "$STATE" ;;
esac

# 3) OSD daemon'a göster sinyali (yoksa başlat)
pid=$(cat "$PIDF" 2>/dev/null)
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
  kill -USR1 "$pid"
else
  setsid -f python3 "$HERE/osd.py" --daemon >/dev/null 2>&1 < /dev/null
  for _ in $(seq 1 30); do
    p=$(cat "$PIDF" 2>/dev/null)
    [ -n "$p" ] && kill -0 "$p" 2>/dev/null && { kill -USR1 "$p"; break; }
    sleep 0.05
  done
fi
