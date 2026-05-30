#!/usr/bin/env python3
"""Cupertino Control Center — macOS Big Sur tarzı açılır kontrol merkezi.

Üst panelden bir düğmeyle açılır. Gerçek sistem kontrolleri:
  - Wi-Fi    (nmcli radio wifi on/off)
  - Bluetooth(rfkill / bluetoothctl)
  - Dark Mode(xfconf GTK teması WhiteSur-Dark <-> WhiteSur)
  - Parlaklık(xrandr --brightness, yazılımsal)
  - Ses      (pactl @DEFAULT_SINK@)

Çalıştırma:  python3 control_center.py
Sağ üstte, panelin altında, cam bir kart olarak açılır. Dışına tıklayınca kapanır.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QGraphicsDropShadowEffect, QFrame,
)

from i18n import t

ASSETS = Path(__file__).resolve().parent / "assets"


def glyph_pixmap(name: str, size: int) -> QPixmap:
    return QIcon(str(ASSETS / name)).pixmap(QSize(size, size))


# ----------------------------- sistem yardımcıları -----------------------------
def run(cmd: list[str], timeout: float = 3.0) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout).stdout.strip()
    except Exception:
        return ""


def run_bg(cmd: list[str]) -> None:
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def wifi_on() -> bool:
    return run(["nmcli", "radio", "wifi"]).lower().startswith("en")


def set_wifi(on: bool) -> None:
    run_bg(["nmcli", "radio", "wifi", "on" if on else "off"])


def bt_on() -> bool:
    out = run(["rfkill", "list", "bluetooth"])
    return "Soft blocked: no" in out


def set_bt(on: bool) -> None:
    run_bg(["rfkill", "unblock" if on else "block", "bluetooth"])


def available_themes() -> set[str]:
    names: set[str] = set()
    for d in (Path.home() / ".themes", Path("/usr/share/themes")):
        if d.exists():
            names.update(p.name for p in d.iterdir())
    return names


def dark_on() -> bool:
    return "Dark" in run(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"])


def set_dark(on: bool) -> None:
    themes = available_themes()
    if on:
        target = "WhiteSur-Dark" if "WhiteSur-Dark" in themes else "WhiteSur"
    else:
        target = next((c for c in ("WhiteSur-Light", "WhiteSur", "Mint-Y-Aqua",
                                    "Mint-Y", "Adwaita") if c in themes), "Adwaita")
    run_bg(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", target])
    run_bg(["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName",
            "-s", "WhiteSur-dark" if on else "WhiteSur-light"])


def primary_output() -> str:
    for line in run(["xrandr"]).splitlines():
        if " connected" in line:
            return line.split()[0]
    return ""


def get_brightness() -> int:
    out = run(["xrandr", "--verbose"])
    m = re.search(r"Brightness:\s*([0-9.]+)", out)
    return int(float(m.group(1)) * 100) if m else 100


def set_brightness(pct: int) -> None:
    out = primary_output()
    if out:
        run_bg(["xrandr", "--output", out, "--brightness", f"{max(10, pct) / 100:.2f}"])


def get_volume() -> int:
    out = run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
    m = re.search(r"(\d+)%", out)
    return int(m.group(1)) if m else 50


def set_volume(pct: int) -> None:
    run_bg(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"])


# ----------------------------- müzik (MPRIS / playerctl) -----------------------------
def player_status() -> str:
    return run(["playerctl", "status"])  # Playing / Paused / boş


def player_track():
    out = run(["playerctl", "metadata", "--format", "{{title}}\t{{artist}}"])
    if not out or "\t" not in out:
        return None
    title, artist = out.split("\t", 1)
    return title.strip(), artist.strip()


def player_action(cmd: str) -> None:  # play-pause / next / previous
    run_bg(["playerctl", cmd])


# ----------------------------- UI bileşenleri -----------------------------
ACCENT = "#0a84ff"


class Card(QFrame):
    """Yuvarlak köşeli yarı saydam macOS kartı."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")


class ToggleTile(QFrame):
    """Yuvarlak ikon + etiket + durum; tıklanınca açılıp kapanır (macOS pill)."""
    toggled = Signal(bool)

    def __init__(self, icon: str, title: str, state: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("tile")
        self._on = state
        self.setCursor(Qt.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 12, 8)
        lay.setSpacing(10)

        self.dot = QLabel()
        self.dot.setPixmap(glyph_pixmap(icon, 17))
        self.dot.setFixedSize(30, 30)
        self.dot.setAlignment(Qt.AlignCenter)
        self.dot.setObjectName("glyph")

        col = QVBoxLayout()
        col.setSpacing(0)
        self.title = QLabel(title)
        self.title.setObjectName("tileTitle")
        self.state = QLabel(t("on") if state else t("off"))
        self.state.setObjectName("tileState")
        col.addWidget(self.title)
        col.addWidget(self.state)

        lay.addWidget(self.dot)
        lay.addLayout(col)
        lay.addStretch(1)
        self._restyle()

    def mousePressEvent(self, e):
        self._on = not self._on
        self.state.setText(t("on") if self._on else t("off"))
        self._restyle()
        self.toggled.emit(self._on)

    def set_state(self, on: bool):
        """Sinyal yaymadan durumu güncelle (arka plan tazelemesi için)."""
        self._on = on
        self.state.setText(t("on") if on else t("off"))
        self._restyle()

    def _restyle(self):
        if self._on:
            self.dot.setStyleSheet(
                f"#glyph{{background:{ACCENT};color:white;border-radius:15px;font-size:15px;}}")
        else:
            self.dot.setStyleSheet(
                "#glyph{background:rgba(255,255,255,0.16);color:rgba(255,255,255,0.85);"
                "border-radius:15px;font-size:15px;}")


class SliderCard(Card):
    """Başlık + ikonlu kaydırıcı (parlaklık / ses)."""
    changed = Signal(int)

    def __init__(self, title: str, icon: str, value: int, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(7)
        cap = QLabel(title)
        cap.setObjectName("cardTitle")
        lay.addWidget(cap)

        row = QHBoxLayout()
        row.setSpacing(10)
        ic = QLabel()
        ic.setPixmap(glyph_pixmap(icon, 16))
        ic.setObjectName("sliderGlyph")
        ic.setFixedWidth(22)
        ic.setAlignment(Qt.AlignCenter)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(value)
        self.slider.valueChanged.connect(self.changed.emit)
        row.addWidget(ic)
        row.addWidget(self.slider, 1)
        lay.addLayout(row)


class IconButton(QLabel):
    """Tıklanabilir SVG ikon (medya kontrolleri)."""
    clicked = Signal()

    def __init__(self, icon: str, size: int = 18, parent=None):
        super().__init__(parent)
        self._name = icon
        self._size = size
        self.setObjectName("mediaBtn")
        self.setFixedSize(size + 14, size + 14)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        self.set_icon(icon)

    def set_icon(self, icon: str):
        self._name = icon
        self.setPixmap(glyph_pixmap(icon, self._size))

    def mousePressEvent(self, e):
        self.clicked.emit()


class NowPlaying(Card):
    """macOS 'Now Playing' kartı — başlık/sanatçı + önceki/oynat/sonraki."""
    action = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 12, 10)
        lay.setSpacing(8)

        col = QVBoxLayout()
        col.setSpacing(1)
        self.title = QLabel(t("not_playing"))
        self.title.setObjectName("nowTitle")
        self.artist = QLabel("—")
        self.artist.setObjectName("nowArtist")
        col.addWidget(self.title)
        col.addWidget(self.artist)
        lay.addLayout(col, 1)

        self.b_prev = IconButton("prev.svg")
        self.b_play = IconButton("play.svg")
        self.b_next = IconButton("next.svg")
        self.b_prev.clicked.connect(lambda: self.action.emit("previous"))
        self.b_play.clicked.connect(lambda: self.action.emit("play-pause"))
        self.b_next.clicked.connect(lambda: self.action.emit("next"))
        for b in (self.b_prev, self.b_play, self.b_next):
            lay.addWidget(b)

    def set_data(self, status: str, track):
        if track and track[0]:
            title, artist = track
            self.title.setText(title[:28])
            self.artist.setText(artist[:30] if artist else "—")
        else:
            self.title.setText(t("not_playing"))
            self.artist.setText("—")
        self.b_play.set_icon("pause.svg" if status == "Playing" else "play.svg")


class ControlCenter(QWidget):
    stateReady = Signal(dict)  # arka plan iş parçacığından gelen güncel değerler

    def __init__(self):
        super().__init__()
        self._test = bool(os.environ.get("NEXUS_CC_TEST"))
        self._last_hidden = 0.0
        # Popup: WM tarafından yok sayılır → Plank/taskbar'da GÖRÜNMEZ,
        # dışarı tıklayınca kendiliğinden kapanır. (Test modunda Tool, ekran için.)
        if self._test:
            self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(330)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)

        self.shell = Card()
        self.shell.setObjectName("shell")
        s = QVBoxLayout(self.shell)
        s.setContentsMargins(12, 12, 12, 12)
        s.setSpacing(10)

        # --- bağlantı kartı (wifi / bluetooth / dark mode) ---
        conn = Card()
        cl = QVBoxLayout(conn)
        cl.setContentsMargins(6, 6, 6, 6)
        cl.setSpacing(2)
        self.t_wifi = ToggleTile("wifi.svg", "Wi-Fi", wifi_on())
        self.t_wifi.toggled.connect(set_wifi)
        self.t_bt = ToggleTile("bluetooth.svg", "Bluetooth", bt_on())
        self.t_bt.toggled.connect(set_bt)
        self.t_dark = ToggleTile("moon.svg", t("darkmode"), dark_on())
        self.t_dark.toggled.connect(set_dark)
        for t in (self.t_wifi, self.t_bt, self.t_dark):
            cl.addWidget(t)
        s.addWidget(conn)

        # --- parlaklık ---
        self.disp = SliderCard(t("display"), "sun.svg", get_brightness())
        self.disp.changed.connect(set_brightness)
        s.addWidget(self.disp)

        # --- ses ---
        self.snd = SliderCard(t("sound"), "speaker.svg", get_volume())
        self.snd.changed.connect(set_volume)
        s.addWidget(self.snd)

        # --- Now Playing (müzik) ---
        self.now = NowPlaying()
        self.now.action.connect(self._music_action)
        s.addWidget(self.now)

        root.addWidget(self.shell)
        self.stateReady.connect(self._apply_state)

        shadow = QGraphicsDropShadowEffect(self.shell)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.shell.setGraphicsEffect(shadow)

        self.setStyleSheet(STYLE)
        self._place_top_right()

    def _place_top_right(self):
        scr = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        x = scr.x() + scr.width() - self.width() - 8
        y = scr.y() + 4
        self.move(x, y)

    # ---------- aç / kapat (daemon, RAM'de sürekli açık) ----------
    def toggle(self):
        if self.isVisible():
            self.hide()
        elif time.monotonic() - self._last_hidden > 0.25:
            self.show_panel()

    def show_panel(self):
        self._place_top_right()
        self.show()
        self.raise_()
        self.activateWindow()
        self._refresh_async()  # değerleri arka planda tazele (pencere donmadan)

    def hideEvent(self, e):
        # Popup dışarı tıklamayla kapandığında da burası çalışır → buton
        # tekrar bastığında anında yeniden açılmasını (0.25s) engeller.
        self._last_hidden = time.monotonic()
        super().hideEvent(e)

    # ---------- arka plan tazeleme ----------
    def _refresh_async(self):
        threading.Thread(target=self._read_state, daemon=True).start()

    def _read_state(self):
        data = {
            "wifi": wifi_on(), "bt": bt_on(), "dark": dark_on(),
            "bright": get_brightness(), "vol": get_volume(),
            "play_status": player_status(), "track": player_track(),
        }
        self.stateReady.emit(data)  # GUI iş parçacığına kuyruklanır

    def _apply_state(self, d: dict):
        self.t_wifi.set_state(d["wifi"])
        self.t_bt.set_state(d["bt"])
        self.t_dark.set_state(d["dark"])
        for sl, key in ((self.disp.slider, "bright"), (self.snd.slider, "vol")):
            sl.blockSignals(True)
            sl.setValue(d[key])
            sl.blockSignals(False)
        self.now.set_data(d["play_status"], d["track"])

    def _music_action(self, cmd: str):
        player_action(cmd)
        # kısa süre sonra durum/başlığı tazele (oynat-duraklat ikonu güncellensin)
        QTimer.singleShot(350, self._refresh_async)


STYLE = f"""
#shell {{
    background: rgba(38, 38, 43, 0.82);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
}}
#card {{
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
}}
#tile {{ background: transparent; border-radius: 10px; }}
#tile:hover {{ background: rgba(255,255,255,0.06); }}
#tileTitle {{ color: white; font-size: 12px; font-weight: 600; }}
#tileState {{ color: rgba(255,255,255,0.5); font-size: 10px; }}
#cardTitle {{ color: rgba(255,255,255,0.85); font-size: 11px; font-weight: 600; }}
#sliderGlyph {{ color: rgba(255,255,255,0.8); font-size: 14px; }}
#nowTitle {{ color: white; font-size: 12px; font-weight: 600; }}
#nowArtist {{ color: rgba(255,255,255,0.55); font-size: 10px; }}
#mediaBtn {{ border-radius: 8px; }}
#mediaBtn:hover {{ background: rgba(255,255,255,0.14); }}
QSlider::groove:horizontal {{
    height: 22px; border-radius: 11px;
    background: rgba(255,255,255,0.14);
}}
QSlider::sub-page:horizontal {{
    height: 22px; border-radius: 11px;
    background: rgba(255,255,255,0.92);
}}
QSlider::handle:horizontal {{
    width: 18px; height: 18px; margin: 2px;
    border-radius: 9px; background: white;
    border: 1px solid rgba(0,0,0,0.15);
}}
"""


PIDFILE = Path.home() / ".cache" / "cupertino-cc.pid"


def main():
    daemon = "--daemon" in sys.argv

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)  # gizlenince çıkma
    app.setFont(QFont("SF Pro Text", 10))
    w = ControlCenter()

    if daemon:
        # PID dosyası yaz (toggle scripti bunu kullanır)
        PIDFILE.parent.mkdir(parents=True, exist_ok=True)
        PIDFILE.write_text(str(os.getpid()))

        # SIGUSR1 = aç/kapat. Qt döngüsü C'de bloke olduğundan, sinyali
        # bir bayrakla yakalayıp periyodik timer'da işliyoruz.
        pending = {"toggle": False}
        signal.signal(signal.SIGUSR1, lambda *a: pending.__setitem__("toggle", True))
        poll = QTimer()
        poll.setInterval(60)
        poll.timeout.connect(
            lambda: pending["toggle"] and (pending.__setitem__("toggle", False), w.toggle()))
        poll.start()
        # RAM'de gizli bekle; ilk sinyalde anında açılır
    else:
        w.show_panel()

    app.exec()


if __name__ == "__main__":
    main()
