# Credits & Attributions / Krediler ve Atıflar

NexusDock builds on the great work of these open-source projects.
NexusDock şu açık kaynak projelerin emeği üzerine kuruludur.

## Third-party components / Üçüncü taraf bileşenler

| Project | Author | License | Usage in NexusDock |
|---------|--------|---------|--------------------|
| [xfce4-docklike-plugin](https://gitlab.xfce.org/panel-plugins/xfce4-docklike-plugin) | XFCE / Gerhard Schmidt et al. | GPL-3.0 | macOS-style dock (window previews, running indicators). NexusDock applies a small patch (`docklike-nexus.patch`) adding hover magnification. |
| [WhiteSur-icon-theme](https://github.com/vinceliuice/WhiteSur-icon-theme) | vinceliuice | GPL-3.0 | macOS Big Sur icons (battery, wifi, sound, trash, etc.) |
| [picom](https://github.com/yshui/picom) | yshui et al. | MIT/MPL | Compositor for the frosted-glass blur |
| [playerctl](https://github.com/altdesktop/playerctl) | Tony Crisci et al. | LGPL-3.0 | "Now Playing" media controls (MPRIS) |
| [PySide6 / Qt](https://www.qt.io/) | The Qt Company | LGPL-3.0 | Control Center & Settings GUI |
| vala-panel-appmenu / xfce4-appmenu-plugin | XFCE community | GPL | Global menu bar (File/Edit/View) |

## NexusDock's own code / NexusDock'un kendi kodu
- `install.sh`, `uninstall.sh`, `*.sh` — kurulum/yapılandırma scriptleri
- `control_center.py`, `control_panel.py`, `i18n.py` — PySide6 GUI'ler
- `gtk-panel.css`, `picom.conf` — tema/derleyici ayarları
- `docklike-nexus.patch` — docklike için hover-magnification yaması (GPL-3, türev iş)
- `assets/*.svg` — özgün ikonlar (apple, dock simgeleri)

## License / Lisans
NexusDock is released under **GPL-3.0** (see `LICENSE`), consistent with the
GPL-licensed components it builds upon.

NexusDock, üzerine kurulduğu GPL bileşenlerle uyumlu olarak **GPL-3.0** ile yayınlanır.
