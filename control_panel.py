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
import re
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QFrame,
    QGraphicsDropShadowEffect, QCheckBox, QScrollArea, QPushButton,
)

from i18n import t

HERE = Path(__file__).resolve().parent
CSS = HERE / "gtk-panel.css"
PICOM = HERE / "picom.conf"
DOCKLIKE_RC = Path.home() / ".config" / "xfce4" / "panel" / "docklike-30.rc"
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


# ---- GTK CSS (üst panel: transparanlık + stil) ----
def css_alpha_get() -> int:
    # ilk background-color rgba = #XfcePanelWindow (RGB ne olursa olsun)
    m = re.search(r"background-color:\s*rgba\([^,]+,[^,]+,[^,]+,\s*([0-9.]+)\)", CSS.read_text())
    return int(float(m.group(1)) * 100) if m else 15


def css_alpha_set(pct: int) -> None:
    txt = CSS.read_text()
    txt = re.sub(r"(background-color:\s*rgba\([^,]+,[^,]+,[^,]+,\s*)[0-9.]+(\s*\))",
                 rf"\g<1>{pct/100:.2f}\g<2>", txt, count=1)
    CSS.write_text(txt)


# Menü çubuğu stil presetleri: arka plan + metin + blur + ikon teması
STYLES = {
    "frosted":     dict(bg=(28, 28, 32),    a=0.15, fg="rgba(255,255,255,0.92)", blur=True,  icon="WhiteSur-dark"),
    "dark":        dict(bg=(22, 22, 24),    a=1.00, fg="rgba(255,255,255,0.92)", blur=False, icon="WhiteSur-dark"),
    "light":       dict(bg=(246, 246, 248), a=1.00, fg="rgba(20,20,22,0.95)",    blur=False, icon="WhiteSur-light"),
    "transparent": dict(bg=(28, 28, 32),    a=0.06, fg="rgba(255,255,255,0.92)", blur=False, icon="WhiteSur-dark"),
}


def menubar_style_set(name: str) -> None:
    s = STYLES[name]
    txt = CSS.read_text()
    r, g, b = s["bg"]
    # arka plan (ilk = #XfcePanelWindow)
    txt = re.sub(r"background-color:\s*rgba\([^)]*\)",
                 f"background-color: rgba({r}, {g}, {b}, {s['a']:.2f})", txt, count=1)
    # metin rengi (ilk bağımsız color: = .label kuralı)
    txt = re.sub(r"(\n\s+color:\s*)rgba\([^)]*\)", rf"\g<1>{s['fg']}", txt, count=1)
    CSS.write_text(txt)
    # Panel hover'da saydamlaşmasın (enter/leave opaklığı = 100)
    for prop in ("enter-opacity", "leave-opacity"):
        run_bg(["xfconf-query", "-c", "xfce4-panel", "-p", f"/panels/panel-1/{prop}",
                "-t", "uint", "-s", "100"])
    picom_set("blur-method", "dual_kawase" if s["blur"] else "none")
    run_bg(["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", s["icon"]])
    reload_picom()
    reload_panel()


# ---- picom blur ----
def picom_get(key: str, default):
    m = re.search(rf"^\s*{key}\s*=\s*\"?([0-9a-z_.]+)\"?\s*;", PICOM.read_text(), re.M)
    return m.group(1) if m else default


def picom_set(key: str, value) -> None:
    txt = PICOM.read_text()
    txt = re.sub(rf"(^\s*{key}\s*=\s*)\"?[0-9a-z_.]+\"?(\s*;)", rf"\g<1>{value}\g<2>", txt, flags=re.M)
    PICOM.write_text(txt)


def blur_strength_get() -> int:
    try:
        return int(float(picom_get("blur-strength", 4)))
    except Exception:
        return 4


def blur_on_get() -> bool:
    return picom_get("blur-method", "dual_kawase") != "none"


def corner_get() -> int:
    m = re.search(r'^\s*corner-radius\s*=\s*(\d+)', PICOM.read_text(), re.M)
    return int(m.group(1)) if m else 22


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
    out = run(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-2/background-rgba"])
    vals = [v for v in out.splitlines() if v.strip()]
    try:
        return int(float(vals[-1].replace(",", ".")) * 100)
    except Exception:
        return 58


def dock_alpha_set(pct: int) -> None:
    a = pct / 100
    run_bg(["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-2/background-rgba",
            "-t", "double", "-s", "0.13", "-t", "double", "-s", "0.13",
            "-t", "double", "-s", "0.16", "-t", "double", "-s", f"{a:.2f}"])


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
        r = SliderRow(t("transparency"), 0, 100, css_alpha_get())
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
        r.released.connect(lambda v: xfq_set_uint("/panels/panel-2/size", v))
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
        sw2.toggled.connect(lambda on: (xfq_set_uint("/panels/panel-2/autohide-behavior", 1 if on else 0),))
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

    def _style(self, name):
        menubar_style_set(name)
        self._flash(f"{t('style')}: {t('st_' + {'frosted':'frosted','dark':'dark','light':'light','transparent':'transp'}[name])}")

    # --- uygulayıcılar ---
    def _top_alpha(self, v):
        css_alpha_set(v); reload_panel(); self._flash(f"{t('transparency')} %{v}")

    def _corner(self, v):
        corner_set(v); reload_picom(); self._flash(f"{t('corner')} {v}px")

    def _preview_on(self, on):
        dl_set("showPreviews", "true" if on else "false"); reload_panel()
        self._flash(f"{t('preview')}: {t('on') if on else t('off')}")

    def _preview_scale(self, v):
        dl_set("previewScale", f"{v/100:.2f}"); reload_panel(); self._flash(f"{t('preview_size')} {v}")

    def _blur_on(self, on):
        picom_set("blur-method", "dual_kawase" if on else "none"); reload_picom()
        self._flash(f"{t('blur_on')}: {t('on') if on else t('off')}")

    def _blur_strength(self, v):
        picom_set("blur-strength", v); reload_picom(); self._flash(f"{t('blur_strength')} {v}")


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
