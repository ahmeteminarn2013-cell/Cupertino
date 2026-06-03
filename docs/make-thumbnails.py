#!/usr/bin/env python3
"""Cupertino — 3 farklı thumbnail/tanıtım görseli üretir (README + YouTube + sosyal).
Ekran görüntülerini (docs/screenshots/) duvar kağıdı üstünde dizer.
Çıktı: docs/thumbnails/thumb-1.png, thumb-2.png, thumb-3.png  (1920x1080)
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SS = os.path.join(HERE, "screenshots")
OUT = os.path.join(HERE, "thumbnails")
os.makedirs(OUT, exist_ok=True)
WALL = "/usr/share/xfce4/backdrops/linuxmint.jpg"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 1920, 1080


def font(sz):
    try:
        return ImageFont.truetype(FONT, sz)
    except Exception:
        return ImageFont.load_default()


def wallpaper():
    try:
        im = Image.open(WALL).convert("RGB")
        # 1920x1080'e ortadan kırparak sığdır
        s = max(W / im.width, H / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        x = (im.width - W) // 2; y = (im.height - H) // 2
        return im.crop((x, y, x + W, y + H))
    except Exception:
        return Image.new("RGB", (W, H), (40, 70, 120))


def load(name):
    return Image.open(os.path.join(SS, name)).convert("RGBA")


def rounded(im, rad=16):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], rad, fill=255)
    out = im.copy(); out.putalpha(m)
    return out


def card(base, im, x, y, scale=1.0, rad=16, shadow=46):
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    im = rounded(im, rad)
    # gölge
    sh = Image.new("RGBA", (im.width + shadow * 2, im.height + shadow * 2), (0, 0, 0, 0))
    smask = Image.new("L", im.size, 0)
    ImageDraw.Draw(smask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], rad, fill=130)
    sh.paste((0, 0, 0, 130), (shadow, shadow + 8), smask)
    sh = sh.filter(ImageFilter.GaussianBlur(shadow / 2.2))
    base.alpha_composite(sh, (x - shadow, y - shadow))
    base.alpha_composite(im, (x, y))


def text(d, xy, s, f, fill=(255, 255, 255, 255), anchor="la", shadow=True):
    if shadow:
        d.text((xy[0] + 2, xy[1] + 3), s, font=f, fill=(0, 0, 0, 150), anchor=anchor)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def apple_png(size):
    """cupertino-apple.svg → PNG (rsvg-convert varsa); yoksa None."""
    src = os.path.expanduser("~/.local/share/icons/cupertino-apple.svg")
    dst = os.path.join(OUT, "_apple.png")
    if not os.path.exists(src):
        return None
    try:
        subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), src, "-o", dst],
                       check=True, capture_output=True)
        return Image.open(dst).convert("RGBA")
    except Exception:
        return None


# ---- ortak varlıklar ----
menubar = load("02-menubar.png")
dock = load("03-dock.png")
apple = load("04-apple-menu.png")
cc = load("05-control-center.png")
spot = load("06-spotlight.png")
osd = load("07-osd.png")
APPLE = apple_png(120)


def desktop_base():
    """Duvar kağıdı + menü çubuğu + dock (gerçek konumlarında)."""
    b = wallpaper().convert("RGBA")
    b.alpha_composite(menubar.resize((W, menubar.height)), (0, 0))
    b.alpha_composite(dock, (460, 978))
    return b


# ============ THUMBNAIL 1 — Canlı masaüstü + Spotlight odak ============
def thumb1():
    b = desktop_base()
    card(b, spot, (W - spot.width) // 2, 250, rad=18)
    d = ImageDraw.Draw(b)
    # sol-alt başlık
    if APPLE:
        b.alpha_composite(APPLE, (70, H - 230))
    text(d, (210 if APPLE else 70, H - 215), "Cupertino", font(96))
    text(d, (74, H - 110), "Linux Mint → macOS  ·  picom yok, hafif & akıcı", font(34),
         fill=(235, 235, 240, 255))
    b.convert("RGB").save(os.path.join(OUT, "thumb-1.png"))


# ============ THUMBNAIL 2 — Özellik kartları (hepsi bir arada) ============
def thumb2():
    bg = wallpaper()
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    bg = bg.filter(ImageFilter.GaussianBlur(8)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    text(d, (W // 2, 70), "Cupertino v2", font(92), anchor="ma")
    text(d, (W // 2, 185), "Elma Menüsü · Spotlight · Control Center · OSD · Bildirimler",
         font(33), fill=(210, 215, 225, 255), anchor="ma")
    # kartlar (hafif çapraz dizilim)
    card(bg, spot, 150, 300, scale=0.92, rad=18)
    card(bg, cc, 1140, 250, scale=0.92, rad=18)
    card(bg, apple, 760, 540, scale=0.95, rad=14)
    card(bg, osd, 1430, 720, scale=1.0, rad=22)
    bg.convert("RGB").save(os.path.join(OUT, "thumb-2.png"))


# ============ THUMBNAIL 3 — Büyük başlık (YouTube tarzı) ============
def thumb3():
    b = desktop_base()
    # üstte koyu degrade (başlık okunsun)
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        grad.putpixel((0, y), int(180 * max(0, 1 - y / (H * 0.55))))
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    veil.putalpha(grad.resize((W, H)))
    b.alpha_composite(veil)
    d = ImageDraw.Draw(b)
    text(d, (80, 90), "TURN LINUX", font(150))
    text(d, (80, 250), "INTO macOS", font(150), fill=(10, 132, 255, 255))
    text(d, (84, 430), "Built from scratch · XFCE → Cupertino · free & open source", font(34),
         fill=(235, 235, 240, 255))
    # sağda Elma menüsü kartı
    card(b, apple, W - apple.width - 90, 150, rad=14)
    b.convert("RGB").save(os.path.join(OUT, "thumb-3.png"))


thumb1(); thumb2(); thumb3()
print("OK → thumb-1.png, thumb-2.png, thumb-3.png")
