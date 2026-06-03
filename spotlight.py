#!/usr/bin/env python3
"""Cupertino — macOS Spotlight (⌘+Space arama çubuğu).

Ortada frosted yuvarlak panel: üstte arama girişi, altta sonuçlar
(uygulamalar + hesap makinesi + web araması). RAM'de daemon olarak bekler
(Control Center / Elma menüsü gibi), SIGUSR1 ile ANINDA açılır. picom YOK
(xfwm4 compositoru saydamlığı sağlar). Tema-uyumlu (açık/koyu).

Kullanım:  spotlight.py --daemon
Tetik:     Super+Space → spotlight-toggle.sh → SIGUSR1
"""
import os
import re
import sys
import ast
import shlex
import signal
import operator
import subprocess
import configparser
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QFrame, QListWidget, QListWidgetItem,
)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    from i18n import t
except Exception:
    def t(k):
        return k

PIDFILE = Path.home() / ".cache" / "cupertino-spotlight.pid"
STATE = Path.home() / ".config" / "cupertino" / "state.ini"
DEVNULL = subprocess.DEVNULL
MAX_RESULTS = 8
SEARCH_H = 62        # arama satırı yüksekliği
ROW_H = 52           # sonuç satırı yüksekliği


# ----------------------------- yardımcılar -----------------------------
def is_dark() -> bool:
    try:
        c = configparser.ConfigParser(); c.optionxform = str
        c.read(STATE)
        return c.get("ui", "theme", fallback="dark") != "light"
    except Exception:
        return True


def scan_apps():
    """Tüm .desktop uygulamalarını tara (Name, Exec, Icon)."""
    dirs = ["/usr/share/applications",
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/flatpak/exports/share/applications",
            os.path.expanduser("~/.local/share/flatpak/exports/share/applications")]
    apps, seen = [], set()
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".desktop") or f in seen:
                continue
            seen.add(f)
            cp = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                cp.read(os.path.join(d, f), encoding="utf-8")
            except Exception:
                continue
            if not cp.has_section("Desktop Entry"):
                continue
            e = cp["Desktop Entry"]
            if e.get("NoDisplay", "false").lower() == "true":
                continue
            if e.get("Type", "") != "Application":
                continue
            name = e.get("Name", "").strip()
            exec_ = e.get("Exec", "").strip()
            if not name or not exec_:
                continue
            apps.append({
                "name": name, "exec": exec_, "icon": e.get("Icon", "").strip(),
                "comment": e.get("Comment", "").strip(),
                "kw": (name + " " + e.get("Keywords", "") + " " + e.get("Comment", "")).lower(),
            })
    return apps


def app_rank(app, q):
    """Sorguya göre eşleşme puanı (düşük = daha iyi); eşleşme yoksa None."""
    name = app["name"].lower()
    if name == q:
        return 0
    if name.startswith(q):
        return 1
    if any(w.startswith(q) for w in name.split()):
        return 2
    if q in name:
        return 3
    if q in app["kw"]:
        return 4
    return None


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv, ast.USub: operator.neg, ast.UAdd: operator.pos}


def _ev(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_ev(node.left), _ev(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_ev(node.operand))
    raise ValueError


def calc(expr):
    """Güvenli aritmetik (sadece sayı+operatör); değilse None."""
    expr = expr.strip()
    if not re.fullmatch(r"[\d\s+\-*/().%^]+", expr) or not re.search(r"[+\-*/%^]", expr):
        return None
    try:
        r = _ev(ast.parse(expr.replace("^", "**"), mode="eval").body)
        return round(r, 6) if isinstance(r, float) else r
    except Exception:
        return None


def launch_exec(exec_):
    cmd = re.sub(r"%[fFuUdDnNickvm]", "", exec_).strip()
    try:
        subprocess.Popen(shlex.split(cmd), start_new_session=True,
                         stdout=DEVNULL, stderr=DEVNULL)
    except Exception:
        pass


def open_uri(uri):
    try:
        subprocess.Popen(["xdg-open", uri], start_new_session=True,
                         stdout=DEVNULL, stderr=DEVNULL)
    except Exception:
        pass


# ----------------------------- arama girişi -----------------------------
class SearchEdit(QLineEdit):
    nav = Signal(int)       # -1 yukarı, +1 aşağı
    accept = Signal()
    dismiss = Signal()

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key_Down:
            self.nav.emit(1); return
        if k == Qt.Key_Up:
            self.nav.emit(-1); return
        if k in (Qt.Key_Return, Qt.Key_Enter):
            self.accept.emit(); return
        if k == Qt.Key_Escape:
            self.dismiss.emit(); return
        super().keyPressEvent(e)


# ----------------------------- Spotlight penceresi -----------------------------
class Spotlight(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.apps = scan_apps()

        self.shell = QFrame(self)
        self.shell.setObjectName("spot")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.shell)

        v = QVBoxLayout(self.shell)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # arama satırı
        row = QHBoxLayout()
        row.setContentsMargins(20, 14, 20, 14)
        row.setSpacing(12)
        self.mag = QLabel("\U0001F50D")          # 🔍
        self.mag.setObjectName("mag")
        self.edit = SearchEdit()
        self.edit.setObjectName("edit")
        self.edit.setPlaceholderText(t("sp_placeholder"))
        self.edit.textChanged.connect(self._search)
        self.edit.nav.connect(self._nav)
        self.edit.accept.connect(self._activate)
        self.edit.dismiss.connect(self.hide)
        row.addWidget(self.mag)
        row.addWidget(self.edit, 1)
        v.addLayout(row)

        # sonuç listesi
        self.list = QListWidget()
        self.list.setObjectName("results")
        self.list.itemActivated.connect(lambda *_: self._activate())
        self.list.itemClicked.connect(lambda *_: self._activate())
        self.list.setFocusPolicy(Qt.NoFocus)
        self.list.hide()
        v.addWidget(self.list)

        self.setFixedWidth(640)
        self.setStyleSheet(self._css(is_dark()))

    # ---- stil ----
    def _css(self, dark):
        if dark:
            bg, fg, sub = "rgba(34,34,38,0.92)", "#f2f2f4", "rgba(255,255,255,0.45)"
            sel, line = "rgba(10,122,255,0.92)", "rgba(255,255,255,0.08)"
        else:
            bg, fg, sub = "rgba(245,245,247,0.95)", "#1d1d1f", "rgba(0,0,0,0.45)"
            sel, line = "rgba(10,122,255,0.92)", "rgba(0,0,0,0.08)"
        return f"""
        #spot {{ background:{bg}; border:1px solid {line}; border-radius:16px; }}
        QWidget {{ color:{fg}; font-family:"SF Pro Text","Inter","Noto Sans",sans-serif; }}
        #mag {{ font-size:20px; color:{sub}; }}
        #edit {{ background:transparent; border:none; font-size:22px; color:{fg}; }}
        #results {{ background:transparent; border:none; border-top:1px solid {line};
                    outline:0; padding:6px; }}
        #results::item {{ border-radius:8px; padding:0; margin:1px 4px; }}
        #results::item:selected {{ background:{sel}; }}
        #r-name {{ font-size:13px; font-weight:600; }}
        #r-sub  {{ font-size:11px; color:{sub}; }}
        #results::item:selected #r-name, #results::item:selected #r-sub {{ color:#fff; }}
        """

    # ---- sonuç satırı widget'ı ----
    def _row_widget(self, icon, name, sub):
        w = QWidget()
        h = QHBoxLayout(w); h.setContentsMargins(10, 7, 10, 7); h.setSpacing(12)
        ic = QLabel(); ic.setFixedSize(34, 34)
        if icon:
            pm = icon.pixmap(34, 34)
            if not pm.isNull():
                ic.setPixmap(pm)
        h.addWidget(ic)
        col = QVBoxLayout(); col.setSpacing(0); col.setContentsMargins(0, 0, 0, 0)
        ln = QLabel(name); ln.setObjectName("r-name")
        ls = QLabel(sub); ls.setObjectName("r-sub")
        col.addWidget(ln); col.addWidget(ls)
        h.addLayout(col, 1)
        return w

    def _add(self, icon, name, sub, action):
        it = QListWidgetItem(self.list)
        it.setData(Qt.UserRole, action)
        it.setSizeHint(QSize(0, 50))
        self.list.addItem(it)
        self.list.setItemWidget(it, self._row_widget(icon, name, sub))

    # ---- arama ----
    def _search(self, text):
        self.list.clear()
        q = text.strip().lower()
        if not q:
            self.list.hide()
            self._fit()
            return

        # 1) hesap makinesi
        c = calc(text)
        if c is not None:
            self._add(QIcon.fromTheme("accessories-calculator"), f"= {c}",
                      t("sp_calc"), ("calc", str(c)))

        # 2) uygulamalar
        ranked = []
        for a in self.apps:
            r = app_rank(a, q)
            if r is not None:
                ranked.append((r, a["name"].lower(), a))
        ranked.sort(key=lambda x: (x[0], x[1]))
        for _, _, a in ranked[:MAX_RESULTS]:
            ic = QIcon(a["icon"]) if a["icon"].startswith("/") else QIcon.fromTheme(a["icon"])
            if ic.isNull():
                ic = QIcon.fromTheme("application-x-executable")
            self._add(ic, a["name"], a["comment"] or t("sp_app"), ("exec", a["exec"]))

        # 3) web araması (her zaman en altta)
        self._add(QIcon.fromTheme("web-browser"), t("sp_web").format(text.strip()),
                  t("sp_web_sub"), ("web", text.strip()))

        if self.list.count():
            self.list.setCurrentRow(0)
            self.list.show()
        else:
            self.list.hide()
        self._fit()

    def _fit(self):
        n = self.list.count()
        if n:
            lh = min(n, MAX_RESULTS + 1) * ROW_H + 10
            self.list.setFixedHeight(lh)
            self.list.show()
        else:
            self.list.hide()
            lh = 0
        self.setFixedHeight(SEARCH_H + lh)   # pencereyi içeriğe TAM oturt
        self._place()

    def _nav(self, d):
        n = self.list.count()
        if not n:
            return
        self.list.setCurrentRow((self.list.currentRow() + d) % n)

    def _activate(self):
        it = self.list.currentItem()
        if not it:
            return
        kind, data = it.data(Qt.UserRole)
        if kind == "exec":
            launch_exec(data)
        elif kind == "web":
            open_uri("https://duckduckgo.com/?q=" + data.replace(" ", "+"))
        elif kind == "calc":
            QApplication.clipboard().setText(data)
        self.hide()

    # ---- konum / göster / gizle ----
    def _place(self):
        scr = QApplication.primaryScreen().availableGeometry()
        x = scr.x() + (scr.width() - self.width()) // 2
        y = scr.y() + int(scr.height() * 0.18)
        self.move(x, y)

    def show_spot(self):
        self.setStyleSheet(self._css(is_dark()))
        self.edit.clear()
        self.list.hide()
        self.setFixedHeight(SEARCH_H)
        self._place()
        self.show()
        self.raise_()
        self.activateWindow()
        self.edit.setFocus()

    def changeEvent(self, e):
        # odak kaybında gizle (dışarı tıklayınca)
        from PySide6.QtCore import QEvent
        if e.type() == QEvent.ActivationChange and not self.isActiveWindow():
            self.hide()
        super().changeEvent(e)


def main():
    daemon = "--daemon" in sys.argv
    if daemon:
        # kopya-guard
        try:
            if PIDFILE.exists():
                old = PIDFILE.read_text().strip()
                if old and Path(f"/proc/{old}").exists() and "spotlight" in \
                        Path(f"/proc/{old}/cmdline").read_text():
                    return
        except Exception:
            pass
        PIDFILE.parent.mkdir(parents=True, exist_ok=True)
        PIDFILE.write_text(str(os.getpid()))

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = Spotlight()

    if daemon:
        pending = {"show": False}
        signal.signal(signal.SIGUSR1, lambda *a: pending.__setitem__("show", True))
        poll = QTimer(); poll.setInterval(60)
        poll.timeout.connect(
            lambda: pending["show"] and (pending.__setitem__("show", False), w.show_spot()))
        poll.start()
    else:
        w.show_spot()
    app.exec()


if __name__ == "__main__":
    main()
