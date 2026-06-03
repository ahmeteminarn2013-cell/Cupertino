#!/usr/bin/env python3
"""Cupertino — macOS Elma (Apple) menüsü.

Apple logosuna tıklayınca açılan gerçek macOS Elma menüsü. GTK kullanır →
~/.config/gtk-3.0/gtk.css'teki macOS 'menu' stilini otomatik alır (yuvarlak,
koyu, cam). picom GEREKMEZ (xfwm4 compositoru saydamlığı sağlar).

Öğeler (gerçek macOS sırası):
  Bu Mac Hakkında · ─ · Sistem Ayarları… · App Store… · ─ · Son Kullanılanlar ▸
  · ─ · Zorla Çık… · ─ · Uyku · Yeniden Başlat… · Kapat… · ─ · Ekranı Kilitle
  · Oturumu Kapat…

Kullanım:
  apple-menu.py            → menüyü Apple logosunun altında aç
  apple-menu.py --about    → "Bu Mac Hakkında" penceresi
"""
import os
import sys
import platform
import subprocess

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, Gio, GLib, GdkPixbuf  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from i18n import t
except Exception:
    def t(k):  # i18n yoksa anahtarı döndür
        return k

APPLE_ICON = os.path.expanduser("~/.local/share/icons/cupertino-apple.svg")
LAPTOP_SVG = os.path.join(HERE, "assets", "laptop.svg")
STATE_INI = os.path.expanduser("~/.config/cupertino/state.ini")


def launch(cmd):
    """Komutu ayrı oturumda başlat (menü kapansa da yaşar)."""
    try:
        subprocess.Popen(cmd, start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


# ----------------------------- Bu Mac Hakkında -----------------------------
def _read(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""


def system_info():
    info = {}
    # OS adı (PRETTY_NAME)
    pretty = ""
    for line in _read("/etc/os-release").splitlines():
        if line.startswith("PRETTY_NAME="):
            pretty = line.split("=", 1)[1].strip().strip('"')
    info["os"] = pretty or "Linux"
    info["kernel"] = platform.release()
    # İşlemci (ilk 'model name')
    cpu = ""
    for line in _read("/proc/cpuinfo").splitlines():
        if line.lower().startswith("model name"):
            cpu = line.split(":", 1)[1].strip()
            break
    info["cpu"] = cpu or platform.processor() or "—"
    # Bellek (MemTotal kB → GB)
    mem = ""
    for line in _read("/proc/meminfo").splitlines():
        if line.startswith("MemTotal:"):
            kb = int(line.split()[1])
            mem = f"{kb / 1024 / 1024:.1f} GB"
            break
    info["mem"] = mem or "—"
    # Grafik (lspci, hızlı; yoksa boş)
    try:
        out = subprocess.run(["lspci"], capture_output=True, text=True, timeout=2).stdout
        for line in out.splitlines():
            if "VGA" in line or "3D" in line:
                info["gpu"] = line.split(":", 2)[-1].strip()
                break
    except Exception:
        pass
    # Model (DMI) — başlıkta gösterilir (macOS'taki "MacBook Pro" gibi)
    ver = _read("/sys/devices/virtual/dmi/id/product_version").strip()
    nm = _read("/sys/devices/virtual/dmi/id/product_name").strip()
    vnd = _read("/sys/devices/virtual/dmi/id/sys_vendor").strip()
    model = ver or f"{vnd} {nm}".strip() or "Cupertino PC"
    info["model"] = model.replace("ideapad", "IdeaPad").replace("Lenovo Lenovo", "Lenovo")
    # Başlangıç diski (kök bölüm toplam boyutu)
    try:
        st = os.statvfs("/")
        info["disk"] = f"{st.f_blocks * st.f_frsize / 1e9:.0f} GB"
    except Exception:
        info["disk"] = "—"
    return info


def _theme_is_dark():
    """state.ini'den tema — About penceresi açık/koyu ona uyar (macOS gibi)."""
    try:
        import configparser
        c = configparser.ConfigParser(); c.optionxform = str
        c.read(STATE_INI)
        return c.get("ui", "theme", fallback="dark") != "light"
    except Exception:
        return True


def _about_css(dark):
    if dark:
        bg, fg, sub = "rgba(42,42,46,0.98)", "#f2f2f4", "rgba(255,255,255,0.5)"
        btn, btnh = "rgba(255,255,255,0.13)", "rgba(255,255,255,0.22)"
    else:
        bg, fg, sub = "rgba(237,237,239,0.99)", "#1d1d1f", "rgba(0,0,0,0.5)"
        btn, btnh = "rgba(0,0,0,0.07)", "rgba(0,0,0,0.13)"
    css = """
#about { background-color: %s; border-radius: 14px; }
#about, #about label { color: %s; font-family: "SF Pro Text","Inter","Noto Sans",sans-serif; }
#about-title { font-size: 27px; font-weight: 800; }
#about-sub { font-size: 12.5px; color: %s; }
#about-key { color: %s; font-size: 12.5px; }
#about-val { color: %s; font-size: 12.5px; font-weight: 600; }
#about-foot { font-size: 10.5px; color: %s; }
#about button.more { background-color: %s; background-image: none; border: none;
    box-shadow: none; border-radius: 7px; padding: 5px 16px; color: %s; font-weight: 600; }
#about button.more:hover { background-color: %s; }
.tl { min-width: 13px; min-height: 13px; padding: 0; margin: 0;
    border-radius: 50%%; border: none; box-shadow: none; background-image: none; }
.tl-r { background-color: #ff5f57; }
.tl-y { background-color: #febc2e; }
.tl-g { background-color: #28c840; }
.tl:hover { opacity: 0.82; }
""" % (bg, fg, sub, sub, fg, sub, btn, fg, btnh)
    return css.encode()


def about_window():
    info = system_info()
    dark = _theme_is_dark()
    win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    win.set_name("about")
    win.set_title(t("am_about"))
    win.set_decorated(False)
    win.set_resizable(False)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.set_keep_above(True)
    prov = Gtk.CssProvider()
    prov.load_from_data(_about_css(dark))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 20)
    vis = win.get_screen().get_rgba_visual()
    if vis:
        win.set_visual(vis)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    win.add(outer)

    # --- trafik ışıkları (sol üst, macOS) — kırmızı kapatır ---
    tl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    tl.set_halign(Gtk.Align.START)
    tl.set_margin_top(13); tl.set_margin_start(14); tl.set_margin_bottom(2)
    for cls, cb in (("tl-r", win.close), ("tl-y", win.iconify), ("tl-g", lambda: None)):
        b = Gtk.Button()
        b.get_style_context().add_class("tl")
        b.get_style_context().add_class(cls)
        b.set_relief(Gtk.ReliefStyle.NONE)
        b.set_can_focus(False)
        b.connect("clicked", lambda w, f=cb: f())
        tl.pack_start(b, False, False, 0)
    outer.pack_start(tl, False, False, 0)

    # --- içerik ---
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    box.set_margin_top(4); box.set_margin_bottom(22)
    box.set_margin_start(50); box.set_margin_end(50)
    outer.pack_start(box, True, True, 0)

    # laptop görseli
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file_at_size(LAPTOP_SVG, 212, 146)
        box.pack_start(Gtk.Image.new_from_pixbuf(pb), False, False, 6)
    except Exception:
        pass

    title = Gtk.Label(label=info.get("model", "Cupertino")); title.set_name("about-title")
    box.pack_start(title, False, False, 0)
    sub = Gtk.Label(label="Cupertino · " + info["os"]); sub.set_name("about-sub")
    box.pack_start(sub, False, False, 0)

    grid = Gtk.Grid(column_spacing=12, row_spacing=6)
    grid.set_margin_top(18); grid.set_halign(Gtk.Align.CENTER)
    rows = [(t("am_chip"), info["cpu"]),
            (t("am_memory"), info["mem"]),
            (t("am_startupdisk"), info.get("disk", "—"))]
    if info.get("gpu"):
        rows.append((t("am_graphics"), info["gpu"]))
    rows.append((t("am_kernel"), info["kernel"]))
    for i, (k, v) in enumerate(rows):
        kl = Gtk.Label(label=k); kl.set_name("about-key"); kl.set_halign(Gtk.Align.END)
        vl = Gtk.Label(label=v); vl.set_name("about-val"); vl.set_halign(Gtk.Align.START)
        vl.set_max_width_chars(34); vl.set_line_wrap(True)
        grid.attach(kl, 0, i, 1, 1)
        grid.attach(vl, 1, i, 1, 1)
    box.pack_start(grid, False, False, 0)

    more = Gtk.Button(label=t("am_more_info"))
    more.get_style_context().add_class("more")
    more.set_halign(Gtk.Align.CENTER); more.set_margin_top(18)
    more.connect("clicked", lambda *_: (launch(["xfce4-settings-manager"]), win.close()))
    box.pack_start(more, False, False, 0)

    foot = Gtk.Label(label="Cupertino · macOS deneyimi, Linux ruhu · GPL-3.0")
    foot.set_name("about-foot"); foot.set_margin_top(16)
    box.pack_start(foot, False, False, 0)

    # pencere içerikten sürüklensin (başlıksız pencere)
    def _drag(w, e):
        if e.button == 1:
            w.begin_move_drag(e.button, int(e.x_root), int(e.y_root), e.time)
        return False
    win.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
    win.connect("button-press-event", _drag)
    win.connect("destroy", Gtk.main_quit)
    win.connect("key-press-event",
                lambda w, e: w.close() if e.keyval == Gdk.KEY_Escape else None)
    win.show_all()
    Gtk.main()


# ----------------------------- Onay uyarısı (macOS alert) -----------------------------
# Güç eylemleri (xfce4-session-logout --halt/--reboot/--logout) zaten XFCE dialog'u
# GÖSTERMEDEN çalışır → onayı bizim macOS uyarımız sağlar.
# systemctl reboot/poweroff = modern systemd, aktif yerel oturumda şifresiz izinli
# (CanReboot/CanPowerOff = "yes"). xfce4-session-logout --reboot bu sistemde sessizce
# başarısız oluyordu. Oturum kapatma xfce4-session üzerinden (logout systemd işi değil).
CONFIRM = {
    "shutdown": ("am_q_shutdown", "am_do_shutdown", ["systemctl", "poweroff"]),
    "restart":  ("am_q_restart",  "am_do_restart",  ["systemctl", "reboot"]),
    "logout":   ("am_q_logout",   "am_do_logout",   ["xfce4-session-logout", "--logout"]),
}


def _alert_css(dark):
    if dark:
        bg, fg, sub = "rgba(50,50,54,0.99)", "#f2f2f4", "rgba(255,255,255,0.55)"
        btn, btnh = "rgba(255,255,255,0.14)", "rgba(255,255,255,0.24)"
    else:
        bg, fg, sub = "rgba(236,236,238,0.99)", "#1d1d1f", "rgba(0,0,0,0.5)"
        btn, btnh = "rgba(0,0,0,0.08)", "rgba(0,0,0,0.15)"
    css = """
#alert { background-color: %s; border-radius: 14px; }
#alert, #alert label { color: %s; font-family: "SF Pro Text","Inter","Noto Sans",sans-serif; }
#alert-title { font-size: 14px; font-weight: 700; }
#alert-detail { font-size: 11.5px; color: %s; }
#alert button { border-radius: 8px; padding: 8px 0; font-size: 13px; border: none;
    box-shadow: none; background-image: none; }
#alert button.act { background-color: #0a84ff; color: #ffffff; font-weight: 600; }
#alert button.act:hover { background-color: #0a78ec; }
#alert button.cancel { background-color: %s; color: %s; }
#alert button.cancel:hover { background-color: %s; }
""" % (bg, fg, sub, btn, fg, btnh)
    return css.encode()


def confirm_dialog(kind):
    if kind not in CONFIRM:
        return
    qkey, bkey, cmd = CONFIRM[kind]
    dark = _theme_is_dark()
    win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    win.set_name("alert")
    win.set_decorated(False); win.set_resizable(False)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.set_keep_above(True); win.set_modal(True)
    win.set_default_size(300, -1)
    prov = Gtk.CssProvider(); prov.load_from_data(_alert_css(dark))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 20)
    vis = win.get_screen().get_rgba_visual()
    if vis:
        win.set_visual(vis)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    box.set_margin_top(22); box.set_margin_bottom(18)
    box.set_margin_start(26); box.set_margin_end(26)
    win.add(box)

    # uyarı üçgeni
    try:
        pb = Gtk.IconTheme.get_default().load_icon("dialog-warning", 52, 0)
        box.pack_start(Gtk.Image.new_from_pixbuf(pb), False, False, 2)
    except Exception:
        pass

    title = Gtk.Label(label=t(qkey)); title.set_name("alert-title")
    title.set_line_wrap(True); title.set_justify(Gtk.Justification.CENTER)
    title.set_max_width_chars(30)
    box.pack_start(title, False, False, 2)
    detail = Gtk.Label(label=t("am_detail")); detail.set_name("alert-detail")
    detail.set_line_wrap(True); detail.set_justify(Gtk.Justification.CENTER)
    box.pack_start(detail, False, False, 0)

    btns = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    btns.set_margin_top(14)
    act = Gtk.Button(label=t(bkey)); act.get_style_context().add_class("act")
    act.connect("clicked", lambda *_: (launch(cmd), win.close()))
    cancel = Gtk.Button(label=t("am_cancel")); cancel.get_style_context().add_class("cancel")
    cancel.connect("clicked", lambda *_: win.close())
    btns.pack_start(act, True, True, 0)       # eylem üstte (mavi, varsayılan)
    btns.pack_start(cancel, True, True, 0)    # iptal altta
    box.pack_start(btns, False, False, 0)

    act.set_can_default(True); act.grab_default()   # Enter = eylem (macOS gibi); Esc = iptal
    win.connect("key-press-event",
                lambda w, e: w.close() if e.keyval == Gdk.KEY_Escape else None)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


# ----------------------------- Elma menüsü -----------------------------
def recent_submenu():
    sub = Gtk.Menu()
    try:
        mgr = Gtk.RecentManager.get_default()
        items = sorted(mgr.get_items(), key=lambda r: r.get_modified(), reverse=True)
        items = [r for r in items if r.exists()][:8]
    except Exception:
        items = []
    if not items:
        mi = Gtk.MenuItem(label=t("am_no_recent")); mi.set_sensitive(False)
        sub.append(mi)
    else:
        for r in items:
            uri = r.get_uri()
            mi = Gtk.MenuItem(label=r.get_display_name())
            mi.connect("activate", lambda w, u=uri: launch(["xdg-open", u]))
            sub.append(mi)
        sub.append(Gtk.SeparatorMenuItem())
        clr = Gtk.MenuItem(label=t("am_clear_menu"))
        clr.connect("activate", lambda *_: _purge_recent())
        sub.append(clr)
    return sub


def _purge_recent():
    try:
        Gtk.RecentManager.get_default().purge_items()
    except Exception:
        pass


def item(label, cb, accel=None):
    mi = Gtk.MenuItem()
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    lbl = Gtk.Label(label=label); lbl.set_halign(Gtk.Align.START)
    box.pack_start(lbl, True, True, 0)
    if accel:
        ac = Gtk.Label(label=accel); ac.get_style_context().add_class("accel")
        ac.set_halign(Gtk.Align.END); ac.set_opacity(0.5)
        box.pack_end(ac, False, False, 0)
    mi.add(box)
    mi.connect("activate", lambda *_: cb())
    return mi


def build_menu():
    m = Gtk.Menu()
    self_py = [sys.executable, os.path.abspath(__file__)]

    def sep():
        m.append(Gtk.SeparatorMenuItem())

    m.append(item(t("am_about"), lambda: launch(self_py + ["--about"])))
    sep()
    m.append(item(t("am_sysset"), lambda: launch(["xfce4-settings-manager"])))
    m.append(item(t("am_appstore"), lambda: launch(["mintinstall"])))
    sep()
    rec = Gtk.MenuItem(label=t("am_recent"))
    rec.set_submenu(recent_submenu())
    m.append(rec)
    sep()
    m.append(item(t("am_forcequit"), lambda: launch(["xkill"]), "⌥⌘⎋"))
    sep()
    m.append(item(t("am_sleep"), lambda: launch(["systemctl", "suspend"])))
    m.append(item(t("am_restart"), lambda: launch(self_py + ["--confirm", "restart"])))
    m.append(item(t("am_shutdown"), lambda: launch(self_py + ["--confirm", "shutdown"])))
    sep()
    m.append(item(t("am_lock"), lambda: launch(["xflock4"]), "⌃⌘Q"))
    m.append(item(t("am_logout"), lambda: launch(self_py + ["--confirm", "logout"]), "⇧⌘Q"))

    m.show_all()
    return m


def popup_menu(m):
    """Menüyü Apple logosunun altına (sol üst) aç + grab'ı garanti et."""
    root = Gdk.get_default_root_window()
    rect = Gdk.Rectangle()
    rect.x, rect.y, rect.width, rect.height = 2, 26, 28, 2
    m.popup_at_rect(root, rect, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
    try:
        m.grab_add()   # panel tıklamasının button-release'i menüyü kapatmasın
    except Exception:
        pass
    return False


def show_menu():
    """Tek seferlik (launcher doğrudan çağırırsa / test). Yavaş: python+GTK başlar."""
    m = build_menu()
    m.connect("selection-done", lambda *_: Gtk.main_quit())
    GLib.timeout_add(280, lambda: popup_menu(m))   # tıklama release'i geçsin
    Gtk.main()


def daemon():
    """RAM'de hazır bekle; SIGUSR1 ile ANINDA aç (Control Center gibi).
    Apple logosu apple-toggle.sh → SIGUSR1 yollar."""
    import signal
    pidf = os.path.expanduser("~/.cache/cupertino-apple.pid")
    # kopya-guard: zaten canlı bir Elma daemon'ı varsa sessizce çık
    try:
        if os.path.exists(pidf):
            old = open(pidf).read().strip()
            if old and old != str(os.getpid()) and os.path.exists(f"/proc/{old}"):
                if "apple-menu" in open(f"/proc/{old}/cmdline").read():
                    return
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(pidf), exist_ok=True)
        with open(pidf, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

    cur = {"m": None}

    def toggle():
        if cur["m"] is not None:                 # açıksa kapat (toggle)
            try:
                cur["m"].destroy()
            except Exception:
                pass
            cur["m"] = None
            return
        m = build_menu()                         # her açılışta taze (Son Kullanılanlar güncel)

        def done(*_):
            cur["m"] = None
            try:
                m.destroy()
            except Exception:
                pass
        m.connect("selection-done", done)
        cur["m"] = m
        # 110ms: launcher tıklamasının release'i menüye düşmesin
        GLib.timeout_add(110, lambda: popup_menu(m))

    def on_sig():
        toggle()
        return True   # sinyali dinlemeye devam et

    GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR1, on_sig)
    Gtk.main()


def main():
    if "--about" in sys.argv:
        about_window()
    elif "--confirm" in sys.argv:
        try:
            kind = sys.argv[sys.argv.index("--confirm") + 1]
        except Exception:
            kind = ""
        confirm_dialog(kind)
    elif "--daemon" in sys.argv:
        daemon()
    else:
        show_menu()


if __name__ == "__main__":
    main()
