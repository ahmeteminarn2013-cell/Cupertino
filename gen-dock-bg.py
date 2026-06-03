#!/usr/bin/env python3
"""Cupertino — panel arka plan resimleri üretici (picom YOK, xfwm4 compositing ile).

XFCE'nin KENDİ compositoru (xfwm4) açıkken çalışır — picom DEĞİL. İki resim üretir:

  assets/dock-bg.png : ŞEFFAF köşeli + %opacity renkli YUVARLAK PNG.
                       xfwm4 köşeleri gerçekten saydam basar → arkadaki
                       pencere/duvar kağıdı görünür → gerçek yuvarlak saydamlık.
  assets/bar-bg.png  : opak (veya yarı saydam) SOLID renk — menü çubuğu için.
                       Resim tüm paneli güvenilir kaplar (background-style=1 renk
                       compositor altında tüm genişliği kaplamıyordu; resim kaplıyor).

Her iki resim de panel-N background-image olarak set edilir. Renk verilince
KOYU, AÇIK, ŞEFFAF temaların hepsi aynı mekanizmayla çalışır.

Kullanım:
  python3 gen-dock-bg.py [dock_opacity 0-1] [radius px|0=auto] ["r,g,b"] [bar_alpha 0-1]
Örnek (koyu): python3 gen-dock-bg.py 0.75 0 22,22,24 1.0
Örnek (açık): python3 gen-dock-bg.py 0.78 0 246,246,248 1.0
"""
import os, sys, subprocess
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
DOCK_OUT = os.path.join(ASSETS, "dock-bg.png")
BAR_OUT = os.path.join(ASSETS, "bar-bg.png")
SS = 4   # süper-örnekleme (pürüzsüz köşe)


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def screen_size():
    out = sh("xrandr 2>/dev/null | awk '/\\*/{print $1; exit}'")
    if "x" in out:
        w, h = out.split("x")[:2]
        return int(w), int(h.split()[0])
    return 1920, 1080


def dock_size(sh_):
    """Dock penceresinin (genişlik, yükseklik)'i — menü çubuğu (ince) elenir."""
    out = sh("wmctrl -lG 2>/dev/null | grep -i xfce4-panel")
    best = None
    for line in out.splitlines():
        p = line.split()
        if len(p) < 6:
            continue
        w, h = int(p[4]), int(p[5])
        if w > 200 and 40 <= h <= 220:
            best = (w, h)
    return best or (760, 64)


def parse_color(s):
    try:
        r, g, b = (int(x) for x in s.split(",")[:3])
        return (r, g, b)
    except Exception:
        return (22, 22, 24)


def rounded_dock(w, h, radius, color, a, gap=0):
    """Şeffaf köşeli, %a renkli, yuvarlak RGBA + ince cam kenar.
    gap > 0: yuvarlak gövde ÜST (h-gap) px'e çizilir, ALT gap px tamamen saydam
    kalır → xfwm4 compositoru orada duvar kağıdını gösterir → dock'un ALTINDA
    macOS gibi boşluk (panel kenara yapışık kalsa bile). gap=0 → tüm yükseklik."""
    hh = max(8, h - max(0, gap))          # yuvarlak gövdenin yüksekliği
    big = (w * SS, hh * SS)
    mask = Image.new("L", big, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, big[0] - 1, big[1] - 1], radius=radius * SS, fill=a)
    mask = mask.resize((w, hh), Image.LANCZOS)
    body = Image.new("RGBA", (w, hh), color + (0,))
    body.putalpha(mask)

    # kenar rengi temanın parlaklığına göre (açıkta koyu çizgi, koyuda ışık)
    lum = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
    edge_col, edge_a = ((0, 0, 0), 50) if lum > 150 else ((255, 255, 255), 70)
    edge = Image.new("L", big, 0)
    ImageDraw.Draw(edge).rounded_rectangle(
        [SS, SS, big[0] - 1 - SS, big[1] - 1 - SS], radius=radius * SS,
        outline=edge_a, width=SS)
    edge = edge.resize((w, hh), Image.LANCZOS)
    hi = Image.new("RGBA", (w, hh), edge_col + (0,))
    hi.putalpha(edge)
    body = Image.alpha_composite(body, hi)

    # tam yükseklikli saydam tuval; gövdeyi ÜSTE yapıştır → alt 'gap' px saydam
    layer = Image.new("RGBA", (w, h), color + (0,))
    layer.putalpha(0)
    layer.paste(body, (0, 0))
    return layer


STATE = os.path.expanduser("~/.config/cupertino/state.ini")


def state_defaults():
    """Argüman verilmezse (örn. watcher argümansız çağırınca) state.ini'den oku."""
    import configparser
    d = dict(dock_op=0.75, radius=0, color="22,22,24", bar_alpha=1.0, gap=0)
    cp = configparser.ConfigParser()
    cp.optionxform = str
    try:
        cp.read(STATE)
        if cp.has_section("ui"):
            u = cp["ui"]
            d["dock_op"] = int(u.get("dock_op", 75)) / 100
            d["radius"] = int(u.get("radius", 0))
            d["color"] = u.get("color", "22,22,24")
            d["bar_alpha"] = int(u.get("bar_alpha", 100)) / 100
            d["gap"] = int(u.get("gap", 0))          # dock altı boşluk (px, saydam)
    except Exception:
        pass
    return d


def main():
    argv = sys.argv
    df = state_defaults()
    dock_op = float(argv[1]) if len(argv) > 1 else df["dock_op"]
    radius_hint = int(argv[2]) if len(argv) > 2 else int(df["radius"])
    color = parse_color(argv[3]) if len(argv) > 3 else parse_color(df["color"])
    bar_alpha = float(argv[4]) if len(argv) > 4 else df["bar_alpha"]
    gap = int(df["gap"])                          # dock altı saydam boşluk (px)

    sw, sh_ = screen_size()
    w, h = dock_size(sh_)
    radius = radius_hint or max(12, (h - gap) // 3)

    os.makedirs(ASSETS, exist_ok=True)
    rounded_dock(w, h, radius, color, int(round(dock_op * 255)), gap).save(DOCK_OUT)

    if bar_alpha >= 0.999:
        Image.new("RGB", (64, 64), color).save(BAR_OUT)          # opak solid
    else:
        bar = Image.new("RGBA", (64, 64), color + (int(round(bar_alpha * 255)),))
        bar.save(BAR_OUT)                                        # yarı saydam

    print(f"OK {w}x{h} r={radius} dock_op={dock_op} bar_a={bar_alpha} "
          f"color={color} -> dock-bg.png + bar-bg.png")


if __name__ == "__main__":
    main()
