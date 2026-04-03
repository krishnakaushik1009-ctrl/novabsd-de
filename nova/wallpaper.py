"""
nova/wallpaper.py — Animated Cairo desktop wallpaper window.

Uses Gdk.WindowTypeHint.DESKTOP and keep_below() so it sits behind
every other window.  A GLib timer redraws slowly-rotating arcs to
give the desktop a subtle live feel.
"""

import math
import time

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

# (cx%, cy%, radius%, start_deg, end_deg, R, G, B, alpha, linewidth)
ARCS = [
    (0.50, 0.50, 0.42, 0,   220, 0.20, 0.25, 0.60, 0.18, 140),
    (0.50, 0.50, 0.32, 40,  260, 0.10, 0.35, 0.70, 0.14, 90),
    (0.20, 0.80, 0.28, 180, 360, 0.30, 0.20, 0.55, 0.12, 70),
    (0.80, 0.20, 0.25, 0,   200, 0.15, 0.40, 0.65, 0.10, 60),
    (0.50, 0.50, 0.18, 0,   360, 0.40, 0.45, 0.80, 0.08, 200),
]

# Degrees per second each arc rotates
ARC_SPEEDS = [1.5, -1.0, 2.0, -0.7, 0.5]

# Refresh interval in milliseconds
REDRAW_INTERVAL_MS = 40  # ~25 fps


class NovaWallpaper(Gtk.Window):
    """Full-screen Cairo animated wallpaper."""

    def __init__(self):
        super().__init__()
        self._start = time.monotonic()

        screen = Gdk.Screen.get_default()
        self.set_default_size(screen.get_width(), screen.get_height())
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.keep_below(True)
        self.set_visual(screen.get_rgba_visual() or screen.get_system_visual())

        self.connect("draw", self._on_draw)
        self.connect("destroy", Gtk.main_quit)

        GLib.timeout_add(REDRAW_INTERVAL_MS, self._tick)

    # ------------------------------------------------------------------
    def _tick(self) -> bool:
        self.queue_draw()
        return GLib.SOURCE_CONTINUE

    def _on_draw(self, _widget, cr) -> bool:
        w = self.get_allocated_width()
        h = self.get_allocated_height()
        elapsed = time.monotonic() - self._start

        # Deep-space background gradient
        grad = _linear_gradient(0, 0, 0, h,
                                (0.0, 0.05, 0.05, 0.12),
                                (1.0, 0.08, 0.07, 0.18))
        cr.set_source(grad)
        cr.paint()

        # Animated arcs
        for i, (cx_pct, cy_pct, r_pct, s_deg, e_deg, R, G, B, alpha, lw) in enumerate(ARCS):
            cx = cx_pct * w
            cy = cy_pct * h
            radius = r_pct * min(w, h)
            offset = math.radians(ARC_SPEEDS[i] * elapsed)
            s_rad = math.radians(s_deg) + offset
            e_rad = math.radians(e_deg) + offset

            cr.set_source_rgba(R, G, B, alpha)
            cr.set_line_width(lw)
            cr.arc(cx, cy, radius, s_rad, e_rad)
            cr.stroke()

        # Subtle star field (static, drawn from a deterministic seed)
        _draw_stars(cr, w, h)
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _linear_gradient(x0, y0, x1, y1, *stops):
    import cairo
    pat = cairo.LinearGradient(x0, y0, x1, y1)
    for stop in stops:
        offset, r, g, b = stop
        pat.add_color_stop_rgb(offset, r, g, b)
    return pat


def _draw_stars(cr, w, h):
    """Draw a fixed star field using a simple LCG so it's deterministic."""
    cr.set_line_width(0)
    a, c, m, seed = 1664525, 1013904223, 2**32, 0x4A3F2B1C
    for _ in range(180):
        seed = (a * seed + c) % m
        sx = (seed % w)
        seed = (a * seed + c) % m
        sy = (seed % h)
        seed = (a * seed + c) % m
        brightness = 0.3 + 0.5 * (seed / m)
        cr.set_source_rgba(brightness, brightness, brightness + 0.1, 0.7)
        cr.arc(sx, sy, 0.8, 0, 2 * math.pi)
        cr.fill()
