# NovaBSD Desktop Shell — Build & Run Guide

## What This Is
A real GTK3-based desktop environment shell for FreeBSD.
Components: animated wallpaper, top panel, bottom dock, app launcher, notifications.

---

## Install Dependencies (FreeBSD)

> **Note:** `pkg install` requires root. Switch to root first with `su root` (or prefix with `sudo` if configured).

```sh
# Core DE runtime  (run as root)
pkg install \
  python311 \
  py311-gobject3 \
  py311-cairo \
  gtk3 \
  glib \
  pango \
  cairo \
  xorg \
  xterm \
  xwininfo \
  xprop

# Optional — apps the dock will launch (install what you need)
pkg install thunar firefox thunderbird vlc
# NovaBSD has its own settings UI; xfce4 is NOT required
```

---

## Run the Shell

> **Note:** `pkg install python311` installs the binary as `python3.11` on FreeBSD —
> there is no `python3` symlink by default. Use `python3.11` directly as shown below.

```sh
# Start an X session first (or add to ~/.xinitrc)
startx

# In your X session — cd into the project directory first:
cd /path/to/novabsd-de
python3.11 nova_shell.py
```

### Or set as default session in ~/.xinitrc:
```sh
#!/bin/sh
exec python3.11 /path/to/novabsd-de/nova_shell.py
```

---

## Project Structure

```
novabsd-de/
├── nova_shell.py          ← Entry point (run this)
├── nova/
│   ├── __init__.py
│   ├── theme.py           ← GTK CSS (all colors, fonts, styling)
│   ├── panel.py           ← Top bar (logo, app label, clock, battery, wifi)
│   ├── dock.py            ← Bottom dock (pinned apps, date/time)
│   ├── wallpaper.py       ← Animated Cairo arc wallpaper with star field
│   ├── launcher.py        ← Searchable full-screen app launcher overlay
│   └── notifier.py        ← Toast notifications (top-right, auto-dismiss)
└── README.md
```

---

## Customization

### Change dock apps (nova/dock.py)
```python
PINNED_APPS = [
    ("📁", "Files",    ["thunar"],   "Thunar"),
    ("💻", "Terminal", ["xterm"],    "xterm"),
    # Add your apps here...
]
```

### Change colors (nova/theme.py)
All colors are CSS variables in the `NOVA_CSS` string.
Edit `background-color`, `border`, etc. to change the theme.

### Change wallpaper arcs (nova/wallpaper.py)
Edit the `ARCS` list: (cx%, cy%, radius%, start_angle, end_angle, R, G, B, alpha, linewidth)

---

## Architecture Notes

- **NovaPanel** and **NovaDock** use `Gdk.WindowTypeHint.DOCK` so WMs
  automatically avoid overlapping them.
- **EWMH struts** are set via `xprop _NET_WM_STRUT_PARTIAL` so maximized
  windows respect the panel/dock space.
- **NovaWallpaper** uses `Gdk.WindowTypeHint.DESKTOP` and `keep_below(True)`
  to always stay behind other windows.
- Cairo draws directly on the GTK window surface — no Wayland-specific APIs,
  pure X11/Cairo stack for maximum FreeBSD compatibility.

---

## Next Steps (Production)
- Replace `xprop` strut calls with direct libxcb atom setting (no subprocess)
- Add `python-ewmh` for proper window list / taskbar integration
- Add keybinding daemon (sxhkd or custom) for Super key → launcher
- Add VTE widget in launcher for in-shell terminal
- Hook into `devd` for real battery / network status updates
