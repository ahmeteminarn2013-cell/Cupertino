#!/usr/bin/env python3
"""Cupertino — macOS ses/parlaklık OSD (on-screen display).

picom YOK; xfwm4 compositoru saydam köşeleri sağlar. RAM'de daemon olarak bekler
(Control Center / Elma menüsü gibi), SIGUSR1 ile anında gösterir. Tetik:
osd-ctl.sh ses/parlaklığı ayarlar, ~/.cache/cupertino-osd.state'e "TÜR SEVİYE"
yazar, SIGUSR1 yollar → ekran ortasında ~1.3sn yuvarlak kare overlay belirir
(büyük ikon + 16 segmentli bar), sonra kaybolur.

Kullanım: osd.py --daemon
state biçimi: "volume 65" | "mute 0" | "brightness 40"
"""
import os
import sys
import math
import signal
import configparser

import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf  # noqa: E402

STATE = os.path.expanduser("~/.cache/cupertino-osd.state")
PIDF = os.path.expanduser("~/.cache/cupertino-osd.pid")
UI_STATE = os.path.expanduser("~/.config/cupertino/state.ini")
SIZE = 168
RADIUS = 26
HIDE_MS = 1300


def is_dark():
    try:
        c = configparser.ConfigParser(); c.optionxform = str
        c.read(UI_STATE)
        return c.get("ui", "theme", fallback="dark") != "light"
    except Exception:
        return True


def icon_for(kind, level):
    if kind == "mute" or (kind == "volume" and level <= 0):
        return "audio-volume-muted-symbolic"
    if kind == "brightness":
        return "display-brightness-symbolic"
    if level < 34:
        return "audio-volume-low-symbolic"
    if level < 67:
        return "audio-volume-medium-symbolic"
    return "audio-volume-high-symbolic"


def load_symbolic(name, size, rgb):
    """Simgesel ikonu fg rengine boyayıp pixbuf döndür (yoksa None)."""
    try:
        theme = Gtk.IconTheme.get_default()
        info = theme.lookup_icon(name, size, 0)
        if info is None:
            return None
        col = Gdk.RGBA(); col.red, col.green, col.blue, col.alpha = (*rgb, 1.0)
        pb, _ = info.load_symbolic(col, None, None, None)
        return pb
    except Exception:
        return None


def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()


class OSD(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_accept_focus(False)
        self.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
        self.set_app_paintable(True)
        self.set_default_size(SIZE, SIZE)
        vis = self.get_screen().get_rgba_visual()
        if vis:
            self.set_visual(vis)
        self.connect("draw", self._draw)
        self.kind, self.level = "volume", 50
        self.icon_pb = None
        self._timer = None

    def _place(self):
        try:
            disp = Gdk.Display.get_default()
            mon = disp.get_primary_monitor() or disp.get_monitor(0)
            g = mon.get_geometry()
            x = g.x + (g.width - SIZE) // 2
            y = g.y + int(g.height * 0.62) - SIZE // 2 + 35   # merkezin altı + 35px (kullanıcı tercihi)
            self.move(x, y)
        except Exception:
            pass

    def show_osd(self, kind, level):
        self.kind = kind
        self.level = max(0, min(100, level))
        dark = is_dark()
        fg = (1, 1, 1) if dark else (0.10, 0.10, 0.11)
        self.icon_pb = load_symbolic(icon_for(kind, self.level), 72, fg)
        self._dark = dark
        self._place()
        self.queue_draw()
        self.show_all()
        if self._timer:
            GLib.source_remove(self._timer)
        self._timer = GLib.timeout_add(HIDE_MS, self._hide)

    def _hide(self):
        self.hide()
        self._timer = None
        return False

    def _draw(self, w, cr):
        dark = getattr(self, "_dark", True)
        # saydama temizle (köşeler şeffaf kalsın)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        W = H = SIZE
        bg = (0.15, 0.15, 0.17, 0.92) if dark else (0.95, 0.95, 0.96, 0.93)
        fg = (1, 1, 1) if dark else (0.10, 0.10, 0.11)
        # yuvarlak arka plan
        rrect(cr, 0, 0, W, H, RADIUS)
        cr.set_source_rgba(*bg)
        cr.fill()
        # ikon (üst-orta)
        if self.icon_pb:
            iw, ih = self.icon_pb.get_width(), self.icon_pb.get_height()
            Gdk.cairo_set_source_pixbuf(cr, self.icon_pb, (W - iw) / 2, 36)
            cr.paint()
        # segmentli bar (alt)
        segs, bw, bh, by, gap = 16, 116, 6, H - 36, 3
        bx = (W - bw) / 2
        sw = (bw - gap * (segs - 1)) / segs
        filled = round(self.level / 100 * segs)
        for i in range(segs):
            x = bx + i * (sw + gap)
            rrect(cr, x, by, sw, bh, 1.5)
            cr.set_source_rgba(*fg, 0.95 if i < filled else 0.22)
            cr.fill()


def backlight_dir():
    base = "/sys/class/backlight"
    try:
        for d in sorted(os.listdir(base)):
            return os.path.join(base, d)
    except Exception:
        pass
    return None


def bri_pct(bl):
    try:
        cur = int(open(os.path.join(bl, "actual_brightness")).read())
        mx = int(open(os.path.join(bl, "max_brightness")).read())
        return round(cur * 100 / mx) if mx else None
    except Exception:
        return None


def daemon():
    # kopya-guard
    try:
        if os.path.exists(PIDF):
            old = open(PIDF).read().strip()
            if old and old != str(os.getpid()) and os.path.exists(f"/proc/{old}"):
                if "osd.py" in open(f"/proc/{old}/cmdline").read():
                    return
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(PIDF), exist_ok=True)
        open(PIDF, "w").write(str(os.getpid()))
    except Exception:
        pass

    win = OSD()

    def on_sig():
        try:
            kind, lvl = open(STATE).read().split()
            win.show_osd(kind, int(lvl))
        except Exception:
            pass
        return True

    GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR1, on_sig)

    # Parlaklık DOSYA izleyici: tuş koduna bakmadan, parlaklık NEYLE değişirse
    # değişsin (power-manager/çekirdek/GUI) OSD'yi göster. Volume = sinyal yolu.
    bl = backlight_dir()
    last = {"b": bri_pct(bl) if bl else None}

    def watch_bri():
        v = bri_pct(bl)
        if v is not None and last["b"] is not None and v != last["b"]:
            win.show_osd("brightness", v)
        last["b"] = v
        return True

    if bl:
        GLib.timeout_add(250, watch_bri)

    Gtk.main()


def main():
    if "--daemon" in sys.argv:
        daemon()
    else:
        # tek seferlik test: osd.py volume 65
        win = OSD()
        kind = sys.argv[1] if len(sys.argv) > 1 else "volume"
        lvl = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        win.connect("hide", Gtk.main_quit)
        GLib.idle_add(lambda: (win.show_osd(kind, lvl), False)[1])
        Gtk.main()


if __name__ == "__main__":
    main()
