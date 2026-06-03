# Changelog

## v2.0
The "fully macOS" release — and it no longer needs picom. 🍎

### ✨ Added
- **Apple menu** — click the Apple logo for a real macOS menu:
  - **About This Mac** — a styled window with a laptop illustration + your real model, chip, memory, disk, kernel
  - System Settings · App Store · Recent Items · Force Quit · Sleep · Restart · Shut Down · Lock · Log Out
  - macOS-style **confirmation dialogs** for Restart / Shut Down / Log Out (no checkbox, blue action button)
- **Spotlight** (`⌘`/Win`+Space`, or the 🔍 button) — searches **apps**, **calculator**, and **web**; instant (RAM-resident daemon)
- **macOS OSD** — volume & brightness keys show a Big-Sur-style centered overlay (icon + segmented bar)
- **macOS notifications** — rounded, translucent, theme-aware (light & dark)
- **Light theme** alongside Dark, switchable from the Settings GUI
- **Dock bottom gap** (`./set-gap.sh <px>`) for the floating-dock look

### 🔧 Changed
- **Dark & Light themes no longer use picom.** The rounded, translucent dock and solid menu bar are now drawn with **XFCE's own compositor + generated PNG backgrounds**. Result: smooth on weak Intel GPUs — no compositor freezes, no menu-bar corruption. picom is now **optional** (Frosted theme only).
- Power actions go through `systemctl` behind the new confirm dialogs (reliable where `xfce4-session-logout --reboot` silently failed).
- 5 lightweight daemons (Control Center, Apple menu, OSD, Spotlight, dock-bg watcher) auto-start at login and stay RAM-resident for instant response.

### 🐞 Fixed
- Dock right-edge "second rounded corner" tiling artifact — the background image now always matches the dock width (live watcher).
- Brightness keys now reliably trigger the OSD (correct keysym binding + power-manager grab released).

---

## v1.1
- First public release: macOS menu bar (Apple logo + global app menu), frosted-glass dock via picom, hover magnification, Control Center, Settings GUI, Trash with Empty Trash, 8 languages.
