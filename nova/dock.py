"""
nova/dock.py — Bottom application dock for NovaBSD Desktop Environment.

Layout (left → right):
  [pinned app buttons …]    [spacer]    [date]  [time]
"""

import subprocess
import time

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

DOCK_HEIGHT = 68
CLOCK_INTERVAL_MS = 1000

# (emoji-icon, display-name, argv, tooltip)
PINNED_APPS = [
    ("💻", "Terminal", ["xterm"],                             "Open terminal"),
    ("📁", "Files",    ["thunar"],                            "File manager"),
    ("🌐", "Browser",  ["firefox"],                           "Web browser"),
    ("📧", "Mail",     ["thunderbird"],                       "E-mail client"),
    ("🎬", "Media",    ["vlc"],                               "Media player"),
    ("⚙️",  "Settings", ["xterm", "-title", "NovaBSD Settings",
                           "-e", "sh", "-c",
                           "echo '=== NovaBSD Settings ==='; "
                           "echo 'Edit nova/theme.py  — colors/fonts'; "
                           "echo 'Edit nova/dock.py   — pinned apps'; "
                           "echo 'Edit nova/wallpaper.py — arcs/stars'; "
                           "echo; read -r _"],            "System settings"),
]


class NovaDock(Gtk.Window):
    """Horizontal bottom dock (DOCK window hint)."""

    def __init__(self, launcher, notifier):
        super().__init__()
        self._launcher = launcher
        self._notifier = notifier

        screen = Gdk.Screen.get_default()
        sw = screen.get_width()
        sh = screen.get_height()

        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_default_size(sw, DOCK_HEIGHT)
        self.move(0, sh - DOCK_HEIGHT)
        self.set_name("nova-dock")

        # ── Root container ────────────────────────────────────────────
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.set_name("nova-dock")
        root.set_size_request(sw, DOCK_HEIGHT)

        # Pinned app buttons
        apps_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        apps_box.set_margin_start(8)
        for emoji, name, cmd, tip in PINNED_APPS:
            btn = self._make_dock_btn(emoji, name, cmd, tip)
            apps_box.pack_start(btn, False, False, 0)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)

        # Date / time block
        time_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        time_box.set_valign(Gtk.Align.CENTER)
        time_box.set_margin_end(16)

        self._time_lbl = Gtk.Label(label="")
        self._time_lbl.set_name("nova-dock-clock")

        self._date_lbl = Gtk.Label(label="")
        self._date_lbl.set_name("nova-dock-date")

        time_box.pack_start(self._time_lbl, False, False, 0)
        time_box.pack_start(self._date_lbl, False, False, 0)

        root.pack_start(apps_box, False, False, 0)
        root.pack_start(spacer,   True,  True,  0)
        root.pack_end(time_box,   False, False, 0)

        self.add(root)

        self._update_clock()
        GLib.timeout_add(CLOCK_INTERVAL_MS, self._update_clock)

    # ------------------------------------------------------------------
    def reserve_strut(self):
        """Use xprop to reserve bottom DOCK_HEIGHT pixels for the dock."""
        try:
            win_id = self.get_window().get_xid()
            screen = Gdk.Screen.get_default()
            sw = screen.get_width()
            sh = screen.get_height()
            subprocess.Popen(  # noqa: S603
                [
                    "xprop", "-id", str(win_id),
                    "-f", "_NET_WM_STRUT_PARTIAL", "32c",
                    "-set", "_NET_WM_STRUT_PARTIAL",
                    f"0, 0, 0, {DOCK_HEIGHT}, "
                    f"0, 0, 0, 0, "
                    f"0, 0, 0, {sw - 1}",
                ],
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass

    # ------------------------------------------------------------------
    def _make_dock_btn(self, emoji: str, name: str, cmd: list, tip: str) -> Gtk.Button:
        btn = Gtk.Button()
        btn.set_name("nova-dock-btn")
        btn.set_tooltip_text(tip)
        btn.set_relief(Gtk.ReliefStyle.NONE)

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        inner.set_valign(Gtk.Align.CENTER)
        inner.set_halign(Gtk.Align.CENTER)

        icon = Gtk.Label()
        icon.set_markup(f'<span font="24">{emoji}</span>')

        label = Gtk.Label(label=name)
        label.set_name("nova-dock-label")

        inner.pack_start(icon,  False, False, 0)
        inner.pack_start(label, False, False, 0)
        btn.add(inner)

        btn.connect("clicked", self._on_app_clicked, cmd, name)
        return btn

    def _on_app_clicked(self, _btn, cmd: list, name: str):
        try:
            subprocess.Popen(cmd, start_new_session=True)  # noqa: S603
        except FileNotFoundError:
            self._notifier.send("Not installed", f"'{cmd[0]}' was not found.")

    def _update_clock(self) -> bool:
        self._time_lbl.set_text(time.strftime("%H:%M:%S"))
        self._date_lbl.set_text(time.strftime("%a, %d %b %Y"))
        return GLib.SOURCE_CONTINUE
