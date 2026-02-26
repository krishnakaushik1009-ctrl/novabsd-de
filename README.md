# NovaBSD Desktop Shell — Build & Run Guide

## What This Is
A real GTK3-based desktop environment shell for FreeBSD.
Components: animated wallpaper, top panel, bottom dock, app launcher, notifications.

---

## Install Dependencies (FreeBSD)

```sh
# Core DE runtime
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

# Optional (apps the dock will launch)
pkg install thunar firefox thunderbird vlc xfce4-settings-manager
```

---

## Run the Shell

```sh
# Start an X session first (or add to ~/.xinitrc)
startx

# In your X session:
cd /path/to/novabsd-de
python3 nova_shell.py
```

### Or set as default session in ~/.xinitrc:
```sh
#!/bin/sh
exec python3 /path/to/novabsd-de/nova_shell.py
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
│   ├── dock.py            ← Bottom dock (icons, date/time, running indicators)
│   ├── wallpaper.py       ← Animated Cairo arc wallpaper
│   ├── launcher.py        ← App launcher grid overlay
│   └── notifier.py        ← Toast notifications (top-right stack)
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
