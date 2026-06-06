#!/usr/bin/env python3
"""Cupertino Ayar Merkezi — macOS panel + dock için GUI yönetim paneli.

Tek pencereden ayarlanır:
  Üst panel: transparanlık, yükseklik
  Dock:      transparanlık, ikon boyutu, önizleme aç/kapat + boyutu,
             köşe yuvarlaklığı, otomatik gizle
  Blur:      aç/kapat, şiddet

Değişiklikler ilgili yere yazılır (GTK CSS / picom.conf / xfconf / docklike rc)
ve canlı uygulanır (panel reload / picom SIGUSR1 / xfconf anında).
"""
from __future__ import annotations

import configparser
import os
import re
import shutil
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QFrame,
    QGraphicsDropShadowEffect, QCheckBox, QScrollArea, QPushButton, QLineEdit,
    QFileDialog,
)

from i18n import t

HERE = Path(__file__).resolve().parent
CSS = HERE / "gtk-panel.css"
PICOM = HERE / "picom.conf"
GEN = HERE / "gen-dock-bg.py"
DOCK_IMG = HERE / "assets" / "dock-bg.png"
BAR_IMG = HERE / "assets" / "bar-bg.png"
DOCKLIKE_RC = Path.home() / ".config" / "xfce4" / "panel" / "docklike-30.rc"
STATE = Path.home() / ".config" / "cupertino" / "state.ini"
ACCENT = "#0a84ff"


# ----------------------------- yardımcılar -----------------------------
def run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=4).stdout.strip()
    except Exception:
        return ""


def run_bg(cmd: list[str]) -> None:
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def reload_panel() -> None:
    run_bg(["xfce4-panel", "-r"])


def reload_picom() -> None:
    run_bg(["pkill", "-USR1", "-x", "picom"])


# ----------------------------- durum (state.ini) -----------------------------
def _state() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    cp.optionxform = str
    if STATE.exists():
        cp.read(STATE)
    if not cp.has_section("ui"):
        cp.add_section("ui")
    return cp


def state_get(key: str, default) -> str:
    return _state().get("ui", key, fallback=str(default))


def state_set(key: str, value) -> None:
    cp = _state()
    cp.set("ui", key, str(value))
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE, "w") as f:
        cp.write(f)


# ----------------------------- tema presetleri -----------------------------
# comp: "xfwm"  = XFCE'nin KENDİ compositoru (picom YOK) + resim arka plan
#                 → yuvarlak saydam dock + solid çubuk; zayıf GPU'da bile temiz.
#       "picom" = picom (buzlu cam / blur) — sadece isteyene seçenek.
# dock_op: dock resminin opaklığı (0-1). bg: tema rengi. fg: metin rengi.
STYLES = {
    "frosted":     dict(bg=(28, 28, 32),    a=0.18, dock_op=0.55, fg="rgba(255,255,255,0.92)", comp="picom", icon="WhiteSur-dark"),
    "dark":        dict(bg=(22, 22, 24),    a=1.00, dock_op=0.75, fg="rgba(255,255,255,0.92)", comp="xfwm",  icon="WhiteSur-dark"),
    "light":       dict(bg=(246, 246, 248), a=1.00, dock_op=0.80, fg="rgba(20,20,22,0.95)",    comp="xfwm",  icon="WhiteSur-light"),
    "transparent": dict(bg=(22, 22, 24),    a=1.00, dock_op=0.42, fg="rgba(255,255,255,0.92)", comp="xfwm",  icon="WhiteSur-dark"),
}


def theme_is_image() -> bool:
    """Aktif tema resim-tabanlı mı (xfwm) yoksa picom/blur mu?"""
    return STYLES.get(state_get("theme", "dark"), STYLES["dark"])["comp"] != "picom"


# ----------------------------- GTK CSS yardımcıları -----------------------------
def css_set_window_bg(value: str) -> None:
    """#XfcePanelWindow arka planı (dosyadaki ilk background-color) = value."""
    txt = CSS.read_text()
    txt = re.sub(r"(background-color:\s*)[^;]+;", rf"\g<1>{value};", txt, count=1)
    CSS.write_text(txt)


def css_set_fg(fg: str) -> None:
    txt = CSS.read_text()
    txt = re.sub(r"(\n\s+color:\s*)rgba\([^)]*\)", rf"\g<1>{fg}", txt, count=1)
    CSS.write_text(txt)


def css_set_notify(dark: bool) -> None:
    """Bildirim (xfce4-notifyd) CSS bloğunu temaya göre yeniden yaz + notifyd'yi tazele.
    İşaretli blok (CUPERTINO-NOTIFY-START/END) tamamen değiştirilir."""
    if dark:
        bg, fg, bd = "rgba(40, 40, 44, 0.92)", "rgba(255,255,255,0.92)", "rgba(255,255,255,0.10)"
    else:
        bg, fg, bd = "rgba(245, 245, 247, 0.96)", "rgba(20,20,22,0.95)", "rgba(0,0,0,0.10)"
    block = (
        "/* CUPERTINO-NOTIFY-START — bildirimler macOS yuvarlak + hafif opak */\n"
        "#XfceNotifyWindow {\n    border-radius: 18px;\n"
        f"    background-color: {bg};\n"
        f"    border: 1px solid {bd};\n    padding: 8px 10px;\n}}\n"
        "#XfceNotifyWindow label#summary { font-weight: 700; }\n"
        f"#XfceNotifyWindow label {{ color: {fg}; }}\n"
        "/* CUPERTINO-NOTIFY-END */"
    )
    txt = CSS.read_text()
    if "CUPERTINO-NOTIFY-START" in txt:
        txt = re.sub(r"/\* CUPERTINO-NOTIFY-START.*?CUPERTINO-NOTIFY-END \*/", block, txt, flags=re.S)
        CSS.write_text(txt)
    run_bg(["pkill", "-x", "xfce4-notifyd"])   # yeni CSS'i okusun (sonraki bildirimde doğar)


# ----------------------------- resim üretimi + uygulama -----------------------------
def regen_images() -> None:
    """Mevcut tema + slider değerleriyle dock-bg.png + bar-bg.png üret (senkron)."""
    name = state_get("theme", "dark")
    s = STYLES.get(name, STYLES["dark"])
    r, g, b = s["bg"]
    dock_op = int(state_get("dock_op", int(s["dock_op"] * 100)))
    radius = int(state_get("radius", 22))
    bar_a = int(state_get("bar_alpha", 100))
    run(["python3", str(GEN), f"{dock_op/100:.2f}", str(radius),
         f"{r},{g},{b}", f"{bar_a/100:.2f}"])


def apply_images() -> None:
    """panel-1 = bar resmi, panel-2 = dock resmi (background-style=2). Senkron ki
    panel reload'dan ÖNCE yazılsın."""
    run(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-1/background-style", "-t", "uint", "-s", "2", "--create"])
    run(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-1/background-image", "-t", "string", "-s", str(BAR_IMG), "--create"])
    run(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-2/background-style", "-t", "uint", "-s", "2", "--create"])
    run(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-2/background-image", "-t", "string", "-s", str(DOCK_IMG), "--create"])


def refresh_dock_bg() -> None:
    """Slider değişince (köşe/opaklık/çubuk saydamlığı) resimleri tazele + uygula."""
    regen_images()
    apply_images()
    reload_panel()


# ----------------------------- tema uygula -----------------------------
def menubar_style_set(name: str) -> None:
    s = STYLES[name]
    r, g, b = s["bg"]
    state_set("theme", name)
    state_set("dock_op", int(s["dock_op"] * 100))   # tema değişince dock opaklığını sıfırla
    state_set("color", f"{r},{g},{b}")              # gen/watcher state'ten okusun
    css_set_fg(s["fg"])
    css_set_notify(name != "light")   # bildirimler de temaya uysun (açık/koyu)
    run_bg(["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", s["icon"]])
    # panel opaklık property'leri tam (compositor altında sızıntı olmasın)
    for prop in ("enter-opacity", "leave-opacity", "background-alpha"):
        for p in ("panel-1", "panel-2"):
            run_bg(["xfconf-query", "-c", "xfce4-panel", "-p", f"/panels/{p}/{prop}",
                    "-t", "uint", "-s", "100", "--create"])

    if s["comp"] == "picom":
        # Buzlu cam (blur) — picom. CSS yarı saydam arka plan + picom blur'lar.
        css_set_window_bg(f"rgba({r}, {g}, {b}, {s['a']:.2f})")
        run(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-1/background-style", "-t", "uint", "-s", "0", "--create"])
        run(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-2/background-style", "-t", "uint", "-s", "1", "--create"])
        run(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-2/background-rgba",
             "-t", "double", "-s", "0.13", "-t", "double", "-s", "0.13",
             "-t", "double", "-s", "0.16", "-t", "double", "-s", f"{s['dock_op']:.2f}", "--create"])
        picom_set("blur-method", "dual_kawase")
        run_bg(["xfconf-query", "-c", "xfwm4", "-p", "/general/use_compositing", "-s", "false"])
        subprocess.Popen(["setsid", "-f", "bash", str(HERE / "picom-run.sh")],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # KOYU / AÇIK / ŞEFFAF — xfwm4 yerleşik compositor + resim arka plan (picom YOK)
        css_set_window_bg("transparent")   # arka plan resimlerden gelsin
        run_bg(["pkill", "-x", "picom"])
        run(["xfconf-query", "-c", "xfwm4", "-p", "/general/use_compositing", "-s", "true"])
        regen_images()
        apply_images()
    reload_panel()


# ---- picom blur ----
def picom_get(key: str, default):
    m = re.search(rf"^\s*{key}\s*=\s*\"?([0-9a-z_.]+)\"?\s*;", PICOM.read_text(), re.M)
    return m.group(1) if m else default


def picom_set(key: str, value) -> None:
    txt = PICOM.read_text()
    v = str(value)
    if not re.fullmatch(r"[0-9.]+", v):   # sayı değilse string → picom tırnak ister
        v = f'"{v}"'
    txt = re.sub(rf'(^\s*{key}\s*=\s*)"?[0-9a-z_.]+"?(\s*;)', rf"\g<1>{v}\g<2>", txt, flags=re.M)
    PICOM.write_text(txt)


def blur_strength_get() -> int:
    try:
        return int(float(picom_get("blur-strength", 4)))
    except Exception:
        return 4


def blur_on_get() -> bool:
    return picom_get("blur-method", "dual_kawase") != "none"


def corner_get() -> int:
    return int(state_get("radius", 22))


def corner_set(r: int) -> None:
    txt = PICOM.read_text()
    txt = re.sub(r'(^\s*corner-radius\s*=\s*)\d+', rf'\g<1>{r}', txt, flags=re.M, count=1)
    PICOM.write_text(txt)


# ---- xfconf ----
def xfq_get(path: str, default: float = 0) -> float:
    out = run(["xfconf-query", "-c", "xfce4-panel", "-p", path])
    try:
        return float(out.replace(",", "."))
    except Exception:
        return default


def xfq_set_uint(path: str, val: int) -> None:
    run_bg(["xfconf-query", "-c", "xfce4-panel", "-p", path, "-t", "uint", "-s", str(val)])


def dock_alpha_get() -> int:
    return int(state_get("dock_op", 75))


def dock_alpha_set(pct: int) -> None:
    """Dock opaklığı: resim modunda dock-bg.png'yi tazele; picom modunda rgba."""
    state_set("dock_op", pct)
    if theme_is_image():
        refresh_dock_bg()
    else:
        run_bg(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-2/background-rgba",
                "-t", "double", "-s", "0.13", "-t", "double", "-s", "0.13",
                "-t", "double", "-s", "0.16", "-t", "double", "-s", f"{pct/100:.2f}"])


# ---- docklike rc ----
def dl_read() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    cp.optionxform = str
    if DOCKLIKE_RC.exists():
        cp.read(DOCKLIKE_RC)
    if not cp.has_section("user"):
        cp.add_section("user")
    return cp


def dl_get(key: str, default: str) -> str:
    return dl_read().get("user", key, fallback=default)


def dl_set(key: str, value: str) -> None:
    cp = dl_read()
    cp.set("user", key, value)
    with open(DOCKLIKE_RC, "w") as f:
        cp.write(f, space_around_delimiters=False)


# ---- Profil (kilit ekranı isim + foto) — AccountsService, kendi verin = sudo'suz ----
def account_name() -> str:
    try:
        return run(["getent", "passwd", str(os.getuid())]).split(":")[4].split(",")[0]
    except Exception:
        return ""


def acc_call(method: str, arg: str) -> None:
    run(["gdbus", "call", "--system", "--dest", "org.freedesktop.Accounts",
         "--object-path", f"/org/freedesktop/Accounts/User{os.getuid()}",
         "--method", f"org.freedesktop.Accounts.User.{method}", arg])


def set_avatar(src: str) -> None:
    """Seçilen resmi kare kırp + 256px → kaydet, AccountsService ikonu yap (greeter okur)."""
    dst = os.path.expanduser("~/.config/cupertino/avatar.png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        from PIL import Image
        im = Image.open(src).convert("RGB")
        s = min(im.size); x = (im.width - s) // 2; y = (im.height - s) // 2
        im.crop((x, y, x + s, y + s)).resize((256, 256), Image.LANCZOS).save(dst, "PNG")
    except Exception:
        shutil.copy(src, dst)
    try:
        shutil.copy(dst, os.path.expanduser("~/.face"))
    except Exception:
        pass
    acc_call("SetIconFile", dst)


# ----------------------------- UI -----------------------------
class Card(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(16, 12, 16, 14)
        self.v.setSpacing(10)
        cap = QLabel(title)
        cap.setObjectName("cardCap")
        self.v.addWidget(cap)

    def add(self, w):
        self.v.addWidget(w)


class SliderRow(QWidget):
    released = Signal(int)

    def __init__(self, label: str, lo: int, hi: int, val: int, suffix="%", parent=None):
        super().__init__(parent)
        self._suffix = suffix
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        self.lab = QLabel(label)
        self.lab.setObjectName("rowLab")
        self.lab.setFixedWidth(130)
        self.sl = QSlider(Qt.Horizontal)
        self.sl.setRange(lo, hi)
        self.sl.setValue(val)
        self.val = QLabel(f"{val}{suffix}")
        self.val.setObjectName("rowVal")
        self.val.setFixedWidth(48)
        self.val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sl.valueChanged.connect(lambda v: self.val.setText(f"{v}{self._suffix}"))
        self.sl.sliderReleased.connect(lambda: self.released.emit(self.sl.value()))
        lay.addWidget(self.lab)
        lay.addWidget(self.sl, 1)
        lay.addWidget(self.val)


class SwitchRow(QWidget):
    toggled = Signal(bool)

    def __init__(self, label: str, state: bool, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.lab = QLabel(label)
        self.lab.setObjectName("rowLab")
        self.cb = QCheckBox()
        self.cb.setChecked(state)
        self.cb.toggled.connect(self.toggled.emit)
        lay.addWidget(self.lab)
        lay.addStretch(1)
        lay.addWidget(self.cb)


class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app_title"))
        self.setMinimumWidth(440)
        self.setMinimumHeight(620)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 12)

        self.shell = QFrame()
        self.shell.setObjectName("shell")
        sv = QVBoxLayout(self.shell)
        sv.setContentsMargins(16, 16, 16, 16)
        sv.setSpacing(12)

        head = QLabel("  " + t("app_title"))
        head.setObjectName("head")
        sv.addWidget(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        col = QVBoxLayout(body)
        col.setContentsMargins(0, 0, 6, 0)
        col.setSpacing(12)

        # ---- Üst panel ----
        c1 = Card(t("sec_top"))
        # Stil seçici: Frosted / Dark / Light / Transparent (blur'suz = donma yok)
        style_row = QWidget()
        srl = QHBoxLayout(style_row)
        srl.setContentsMargins(0, 0, 0, 0)
        srl.setSpacing(6)
        lab = QLabel(t("style"))
        lab.setObjectName("rowLab")
        lab.setFixedWidth(48)
        srl.addWidget(lab)
        for key, lbl in (("frosted", t("st_frosted")), ("dark", t("st_dark")),
                         ("light", t("st_light")), ("transparent", t("st_transp"))):
            btn = QPushButton(lbl)
            btn.setObjectName("styleBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self._style(k))
            srl.addWidget(btn, 1)
        c1.add(style_row)
        r = SliderRow(t("transparency"), 0, 100, int(state_get("bar_alpha", 100)))
        r.released.connect(self._top_alpha)
        c1.add(r)
        r = SliderRow(t("height"), 20, 44, int(xfq_get("/panels/panel-1/size", 26)), "px")
        r.released.connect(lambda v: (xfq_set_uint("/panels/panel-1/size", v),))
        c1.add(r)
        col.addWidget(c1)

        # ---- Dock ----
        c2 = Card(t("sec_dock"))
        r = SliderRow(t("dock_bg"), 0, 100, dock_alpha_get())
        r.released.connect(lambda v: dock_alpha_set(v))
        c2.add(r)
        r = SliderRow(t("dock_size"), 40, 96, int(xfq_get("/panels/panel-2/size", 64)), "px")
        r.released.connect(self._dock_size)
        c2.add(r)
        r = SliderRow(t("corner"), 0, 40, corner_get(), "px")
        r.released.connect(self._corner)
        c2.add(r)
        sw = SwitchRow(t("preview"), dl_get("showPreviews", "true") == "true")
        sw.toggled.connect(self._preview_on)
        c2.add(sw)
        r = SliderRow(t("preview_size"), 5, 40, int(float(dl_get("previewScale", "0.18")) * 100))
        r.released.connect(self._preview_scale)
        c2.add(r)
        sw2 = SwitchRow(t("autohide"), int(xfq_get("/panels/panel-2/autohide-behavior", 0)) != 0)
        sw2.toggled.connect(self._autohide)
        c2.add(sw2)
        col.addWidget(c2)

        # ---- Blur ----
        c3 = Card(t("sec_blur"))
        sw = SwitchRow(t("blur_on"), blur_on_get())
        sw.toggled.connect(self._blur_on)
        c3.add(sw)
        r = SliderRow(t("blur_strength"), 1, 12, blur_strength_get(), "")
        r.released.connect(self._blur_strength)
        c3.add(r)
        col.addWidget(c3)

        # ---- Kilit Ekranı / Profil (isim + foto — sudo'suz, anında greeter'a yansır) ----
        c4 = Card(t("sec_lock"))
        nrow = QWidget()
        nl = QHBoxLayout(nrow); nl.setContentsMargins(0, 0, 0, 0); nl.setSpacing(10)
        nlab = QLabel(t("profile_name")); nlab.setObjectName("rowLab"); nlab.setFixedWidth(130)
        self.name_edit = QLineEdit(account_name()); self.name_edit.setObjectName("nameEdit")
        self.name_edit.editingFinished.connect(self._set_name)
        nl.addWidget(nlab); nl.addWidget(self.name_edit, 1)
        c4.add(nrow)
        prow = QWidget()
        pl = QHBoxLayout(prow); pl.setContentsMargins(0, 0, 0, 0); pl.setSpacing(10)
        plab = QLabel(t("profile_photo")); plab.setObjectName("rowLab"); plab.setFixedWidth(130)
        pbtn = QPushButton(t("choose")); pbtn.setObjectName("styleBtn")
        pbtn.setCursor(Qt.PointingHandCursor)
        pbtn.clicked.connect(self._set_photo)
        pl.addWidget(plab); pl.addWidget(pbtn, 1)
        c4.add(prow)
        col.addWidget(c4)

        col.addStretch(1)
        scroll.setWidget(body)
        sv.addWidget(scroll, 1)

        self.status = QLabel(t("ready"))
        self.status.setObjectName("status")
        sv.addWidget(self.status)

        outer.addWidget(self.shell)
        sh = QGraphicsDropShadowEffect(self.shell)
        sh.setBlurRadius(40); sh.setOffset(0, 10); sh.setColor(QColor(0, 0, 0, 140))
        self.shell.setGraphicsEffect(sh)
        self.setStyleSheet(STYLE)

    def _flash(self, msg: str):
        self.status.setText("✓ " + msg)

    def _autohide(self, on):
        # autohide + panel reload → dock konumu temiz okunur ((0,0) glitch'ini hafifletir)
        xfq_set_uint("/panels/panel-2/autohide-behavior", 1 if on else 0)
        reload_panel()
        self._flash(f"{t('autohide')}: {t('on') if on else t('off')}")

    def _style(self, name):
        menubar_style_set(name)
        self._flash(f"{t('style')}: {t('st_' + {'frosted':'frosted','dark':'dark','light':'light','transparent':'transp'}[name])}")

    # --- uygulayıcılar ---
    def _picom_live(self) -> bool:
        return bool(run(["pgrep", "-x", "picom"]))

    def _flash_picom(self, msg: str):
        # picom (blur compositor) çalışıyorsa uygula; değilse "Buzlu modunda geçerli" de
        if self._picom_live():
            reload_picom(); self._flash(msg)
        else:
            self._flash(f"{msg} — {t('needs_frosted')}")

    def _top_alpha(self, v):
        # üst çubuk saydamlığı: resim modunda bar-bg.png alfasını tazele; picom'da CSS
        state_set("bar_alpha", v)
        if theme_is_image():
            refresh_dock_bg()
        else:
            s = STYLES[state_get("theme", "frosted")]
            r, g, b = s["bg"]
            css_set_window_bg(f"rgba({r}, {g}, {b}, {v/100:.2f})"); reload_panel()
        self._flash(f"{t('transparency')} %{v}")

    def _corner(self, v):
        # köşe yuvarlaklığı: resim modunda dock-bg.png yarıçapını tazele; picom'da corner-radius
        state_set("radius", v)
        if theme_is_image():
            refresh_dock_bg(); self._flash(f"{t('corner')} {v}px")
        else:
            corner_set(v); self._flash_picom(f"{t('corner')} {v}px")

    def _dock_size(self, v):
        # dock yüksekliği değişti → resmi yeni boyutta yeniden üret (panel oturunca)
        xfq_set_uint("/panels/panel-2/size", v); reload_panel()
        if theme_is_image():
            QTimer.singleShot(900, refresh_dock_bg)
        self._flash(f"{t('dock_size')} {v}px")

    def _preview_on(self, on):
        dl_set("showPreviews", "true" if on else "false"); reload_panel()
        self._flash(f"{t('preview')}: {t('on') if on else t('off')}")

    def _preview_scale(self, v):
        dl_set("previewScale", f"{v/100:.2f}"); reload_panel(); self._flash(f"{t('preview_size')} {v}")

    def _blur_on(self, on):
        picom_set("blur-method", "dual_kawase" if on else "none")
        self._flash_picom(f"{t('blur_on')}: {t('on') if on else t('off')}")

    def _blur_strength(self, v):
        picom_set("blur-strength", v); self._flash_picom(f"{t('blur_strength')} {v}")

    def _set_name(self):
        n = self.name_edit.text().strip()
        if n:
            acc_call("SetRealName", n)
            self._flash(f"{t('profile_name')}: {n} ✓")

    def _set_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("profile_photo"), os.path.expanduser("~"),
            "Resimler (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            set_avatar(path)
            self._flash(f"{t('profile_photo')} ✓")


STYLE = f"""
QWidget {{ background: transparent; color: #f0f0f2;
           font-family: "SF Pro Text","Inter","Noto Sans",sans-serif; }}
#shell {{ background: rgba(32,32,37,0.97);
          border: 1px solid rgba(255,255,255,0.10); border-radius: 18px; }}
#head {{ font-size: 16px; font-weight: 700; padding: 2px 0 4px 0; }}
#card {{ background: rgba(255,255,255,0.05);
         border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; }}
#cardCap {{ font-size: 12px; font-weight: 700; color: rgba(255,255,255,0.85); }}
#rowLab {{ font-size: 12px; color: rgba(255,255,255,0.9); }}
#styleBtn {{ font-size: 11px; color: #f0f0f2; padding: 5px 4px;
             background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.10);
             border-radius: 8px; }}
#styleBtn:hover {{ background: rgba(10,122,255,0.85); }}
#nameEdit {{ background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.12);
             border-radius: 8px; padding: 5px 10px; color: #f0f0f2; font-size: 12px; }}
#nameEdit:focus {{ border: 1px solid rgba(10,122,255,0.85); }}
#rowVal {{ font-size: 11px; color: {ACCENT}; font-weight: 600; }}
#status {{ font-size: 11px; color: rgba(255,255,255,0.55); padding-top: 4px; }}
QScrollArea {{ background: transparent; border: none; }}
QSlider::groove:horizontal {{ height: 6px; border-radius: 3px; background: rgba(255,255,255,0.15); }}
QSlider::sub-page:horizontal {{ height: 6px; border-radius: 3px; background: {ACCENT}; }}
QSlider::handle:horizontal {{ width: 16px; height: 16px; margin: -6px 0; border-radius: 8px;
                              background: white; }}
QCheckBox::indicator {{ width: 40px; height: 22px; }}
QCheckBox::indicator:unchecked {{ image: none; border-radius: 11px;
    background: rgba(255,255,255,0.18); }}
QCheckBox::indicator:checked {{ border-radius: 11px; background: {ACCENT}; }}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: rgba(255,255,255,0.18); border-radius: 4px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""


def main():
    app = QApplication([])
    app.setFont(QFont("SF Pro Text", 10))
    w = ControlPanel()
    w.show()
    app.exec()


if __name__ == "__main__":
    main()
