<div align="center">

# 🍎 Cupertino

### Turn your Linux Mint / Ubuntu **XFCE** desktop into **macOS** — with one command.
### XFCE masaüstünü tek komutla **macOS**'a çevir.

![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![Desktop](https://img.shields.io/badge/desktop-XFCE-orange)
![Made for](https://img.shields.io/badge/for-Linux%20Mint%20%2F%20Ubuntu-green)

*A free & open-source alternative to MyDockFinder, built for XFCE.*

</div>

> 📸 _Add a screenshot here:_ `docs/screenshot.png`

---

## ✨ Features / Özellikler

- 🍎 **macOS menu bar** — Apple logo + global app menu (File/Edit/View)
- 🧊 **Frosted-glass blur** — real backdrop blur via picom (top bar + dock)
- 🚀 **macOS dock** — window previews, running indicators, **hover magnification**
- 🎚️ **Control Center** — Wi-Fi / Bluetooth / Dark Mode toggles + brightness/volume sliders + Now Playing
- ⚙️ **Settings GUI** — tune transparency, blur, corner radius, dock size, previews… live
- 🗑️ **Trash** in the dock (right-click → Empty Trash), macOS icon
- 🔍 **Spotlight** launcher
- 🌍 **8 languages** — EN, TR, ES, DE, FR, RU, PT, ZH (auto-detected)

## 📦 Requirements / Gereksinimler
- **XFCE** desktop (Linux Mint XFCE, Xubuntu, or Ubuntu + XFCE session)
- Internet connection (the installer fetches packages & builds the dock plugin)

> ⚠️ Won't work on GNOME (stock Ubuntu). XFCE only.

## 🚀 Install / Kurulum

```bash
git clone https://github.com/ahmeteminarn2013-cell/Cupertino.git
cd Cupertino
./install.sh
```

Then **log out and back in** so the global menu activates. That's it! 🎉

The installer (idempotent — safe to re-run) sets up: packages → WhiteSur icons →
docklike dock (compiled with magnification patch) → menu bar → blur → Control
Center → Settings GUI.

## 🎛️ Usage / Kullanım
- **Settings:** click the ⚙️ icon in the dock (*Cupertino Settings*) — change everything live
- **Control Center:** click the 🎚️ icon in the top bar
- **Spotlight:** 🔍 in the top bar

## 🗑️ Uninstall / Kaldırma
```bash
./uninstall.sh   # restores your previous desktop (brings Plank back, etc.)
```

## 🧠 How it works / Nasıl çalışıyor
100% userspace — no kernel, no system files touched. Everything lives in
`~/.config` and this folder:
- XFCE panels (top menu bar + bottom dock) configured via `xfconf`
- GTK CSS (`gtk-panel.css`) + `picom` for the glass look
- `xfce4-docklike-plugin` 0.4.2 compiled from source with `docklike-cupertino.patch`
- PySide6 apps for the Control Center & Settings

## ⚠️ Known limitations / Bilinen sınırlar
- **Drag-to-open** (dropping a file onto a dock icon to open it) is **not supported** —
  xfce4-panel intercepts external drops before they reach the dock. Drag files onto
  the app **window** instead.
- Tested mainly on Linux Mint XFCE (Ubuntu noble base). Other XFCE versions may vary.

## 🙏 Credits / Krediler
Built on [xfce4-docklike-plugin](https://gitlab.xfce.org/panel-plugins/xfce4-docklike-plugin),
[WhiteSur-icon-theme](https://github.com/vinceliuice/WhiteSur-icon-theme),
[picom](https://github.com/yshui/picom), and more — see [CREDITS.md](CREDITS.md).

## 📄 License / Lisans
**GPL-3.0** — see [LICENSE](LICENSE). (Required: Cupertino builds on GPL components.)

---
<div align="center">
Made with 🍎 for the Linux community · İyi kodlamalar!
</div>
