"""
nova/panel.py — Top panel bar for NovaBSD Desktop Environment.

Layout (left → right):
  [Logo]  [Active-app title]        [Wi-Fi] [Battery] [Clock]  [⊞ Launcher]
"""

import subprocess
import time

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

PANEL_HEIGHT = 36
CLOCK_INTERVAL_MS = 1000   # update every second
STATUS_INTERVAL_MS = 15000  # battery / wifi every 15 s


class NovaPanel(Gtk.Window):
    """Horizontal top panel (DOCK window hint)."""

    def __init__(self, launcher, notifier):
        super().__init__()
        self._launcher = launcher
        self._notifier = notifier

        screen = Gdk.Screen.get_default()
        sw = screen.get_width()

        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_default_size(sw, PANEL_HEIGHT)
        self.move(0, 0)
        self.set_name("nova-panel")

        # ── Root container ────────────────────────────────────────────
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.set_name("nova-panel")
        root.set_size_request(sw, PANEL_HEIGHT)

        # Left: logo + active-app label
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        logo = Gtk.Label(label="🌊 NovaBSD")
        logo.set_name("nova-panel-logo")
        left.pack_start(logo, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_top(6)
        sep.set_margin_bottom(6)
        left.pack_start(sep, False, False, 4)

        self._app_title = Gtk.Label(label="Desktop")
        self._app_title.set_name("nova-panel-apptitle")
        left.pack_start(self._app_title, False, False, 0)

        # Center: spacer
        center = Gtk.Box()
        center.set_hexpand(True)

        # Right: status + clock + launcher button
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        right.set_halign(Gtk.Align.END)

        self._wifi_lbl = Gtk.Label(label="")
        self._wifi_lbl.set_name("nova-panel-status")
        right.pack_start(self._wifi_lbl, False, False, 0)

        self._bat_lbl = Gtk.Label(label="")
        self._bat_lbl.set_name("nova-panel-status")
        right.pack_start(self._bat_lbl, False, False, 0)

        self._clock_lbl = Gtk.Label(label="")
        self._clock_lbl.set_name("nova-panel-clock")
        right.pack_start(self._clock_lbl, False, False, 0)

        launcher_btn = Gtk.Button(label="⊞")
        launcher_btn.set_name("nova-dock-btn")
        launcher_btn.set_tooltip_text("Open launcher  (Super)")
        launcher_btn.connect("clicked", self._on_launcher_clicked)
        right.pack_start(launcher_btn, False, False, 4)

        root.pack_start(left,   False, False, 8)
        root.pack_start(center, True,  True,  0)
        root.pack_start(right,  False, False, 8)

        self.add(root)

        # ── Timers ────────────────────────────────────────────────────
        self._update_clock()
        self._update_status()
        GLib.timeout_add(CLOCK_INTERVAL_MS, self._update_clock)
        GLib.timeout_add(STATUS_INTERVAL_MS, self._update_status)

        # Watch for active-window changes
        screen.connect("notify::active-window", self._on_active_window_changed)

    # ------------------------------------------------------------------
    def reserve_strut(self):
        """Use xprop to tell WMs we occupy the top PANEL_HEIGHT pixels."""
        try:
            win_id = self.get_window().get_xid()
            sw = Gdk.Screen.get_default().get_width()
            sh = Gdk.Screen.get_default().get_height()
            # _NET_WM_STRUT_PARTIAL: left right top bottom
            #   left_start left_end right_start right_end
            #   top_start top_end bottom_start bottom_end
            subprocess.Popen(  # noqa: S603
                [
                    "xprop", "-id", str(win_id),
                    "-f", "_NET_WM_STRUT_PARTIAL", "32c",
                    "-set", "_NET_WM_STRUT_PARTIAL",
                    f"0, 0, {PANEL_HEIGHT}, 0, "
                    f"0, 0, 0, 0, "
                    f"0, {sw - 1}, 0, 0",
                ],
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass  # xprop not installed — strut skipped

    # ------------------------------------------------------------------
    def _update_clock(self) -> bool:
        now = time.strftime("%H:%M:%S")
        self._clock_lbl.set_text(now)
        return GLib.SOURCE_CONTINUE

    def _update_status(self) -> bool:
        self._wifi_lbl.set_text(_read_wifi())
        self._bat_lbl.set_text(_read_battery())
        return GLib.SOURCE_CONTINUE

    def _on_active_window_changed(self, screen, _param):
        win = screen.get_active_window()
        if win:
            try:
                title = win.get_utf8_property("_NET_WM_NAME", "UTF8_STRING")
            except Exception:
                title = None
            if title:
                short = (title[:28] + "…") if len(title) > 28 else title
                self._app_title.set_text(short)
                return
        self._app_title.set_text("Desktop")

    def _on_launcher_clicked(self, _btn):
        self._launcher.toggle()


# ---------------------------------------------------------------------------
# Status helpers (best-effort; graceful fallback on failure)
# ---------------------------------------------------------------------------

def _read_battery() -> str:
    """Read battery level from FreeBSD ACPI sysctl."""
    try:
        out = subprocess.check_output(
            ["sysctl", "-n", "hw.acpi.battery.life"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode().strip()
        pct = int(out)
        icon = "🔋" if pct > 20 else "🪫"
        return f"{icon} {pct}%"
    except Exception:
        return ""


def _read_wifi() -> str:
    """Return the active Wi-Fi SSID or a wired icon."""
    try:
        out = subprocess.check_output(
            ["ifconfig"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode()
        if "ssid" in out.lower():
            for line in out.splitlines():
                line_s = line.strip()
                if line_s.lower().startswith("ssid"):
                    ssid = line_s.split()[1]
                    return f"📶 {ssid}"
        if "status: active" in out.lower():
            return "🔌 Wired"
    except Exception:
        pass
    return ""
