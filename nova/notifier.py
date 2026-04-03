"""
nova/notifier.py — Toast notification stack for NovaBSD.

Notifications slide in from the top-right corner and auto-dismiss
after a configurable timeout.  Other modules obtain a reference to
the single NovaNotifier instance and call .send(title, body).
"""

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

# How long (ms) each toast stays visible before fading away
DEFAULT_TIMEOUT_MS = 4000
FADE_STEPS = 20
FADE_INTERVAL_MS = 30  # total fade ~600 ms

TOAST_WIDTH = 300
TOAST_MARGIN = 12  # gap from screen edge and between toasts
PANEL_HEIGHT = 36  # leave room for the top panel


class _Toast(Gtk.Window):
    """A single notification popup."""

    def __init__(self, title: str, body: str, on_dismissed):
        super().__init__()
        self._on_dismissed = on_dismissed
        self._alpha = 1.0

        screen = Gdk.Screen.get_default()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_app_paintable(True)
        self.set_default_size(TOAST_WIDTH, -1)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        outer.set_name("nova-notification")
        outer.set_margin_top(4)
        outer.set_margin_bottom(4)
        outer.set_margin_start(4)
        outer.set_margin_end(4)

        lbl_title = Gtk.Label(label=title, xalign=0)
        lbl_title.set_name("nova-notification-title")
        lbl_title.set_line_wrap(True)
        lbl_title.set_max_width_chars(30)

        lbl_body = Gtk.Label(label=body, xalign=0)
        lbl_body.set_name("nova-notification-body")
        lbl_body.set_line_wrap(True)
        lbl_body.set_max_width_chars(32)

        outer.pack_start(lbl_title, False, False, 0)
        if body:
            outer.pack_start(lbl_body, False, False, 0)

        self.add(outer)
        self.connect("draw", self._on_draw)
        self.connect("button-press-event", self._dismiss_now)

    def _on_draw(self, _w, cr):
        cr.set_operator(1)  # CAIRO_OPERATOR_SOURCE
        cr.paint_with_alpha(self._alpha)
        return False

    def start_timer(self, timeout_ms: int):
        GLib.timeout_add(timeout_ms, self._begin_fade)

    def _begin_fade(self) -> bool:
        self._step = 0
        GLib.timeout_add(FADE_INTERVAL_MS, self._fade_tick)
        return GLib.SOURCE_REMOVE

    def _fade_tick(self) -> bool:
        self._step += 1
        self._alpha = max(0.0, 1.0 - self._step / FADE_STEPS)
        self.queue_draw()
        if self._step >= FADE_STEPS:
            self._on_dismissed(self)
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    def _dismiss_now(self, *_):
        self._on_dismissed(self)


class NovaNotifier:
    """Manages the vertical stack of toast notifications."""

    def __init__(self):
        self._toasts: list[_Toast] = []

    # ------------------------------------------------------------------
    def send(self, title: str, body: str = "", timeout_ms: int = DEFAULT_TIMEOUT_MS):
        """Display a new toast notification."""
        toast = _Toast(title, body, self._on_dismissed)
        self._toasts.append(toast)
        self._reposition_all()
        toast.show_all()
        toast.start_timer(timeout_ms)

    # ------------------------------------------------------------------
    def _on_dismissed(self, toast: _Toast):
        toast.hide()
        toast.destroy()
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._reposition_all()

    def _reposition_all(self):
        screen = Gdk.Screen.get_default()
        sw = screen.get_width()
        y = PANEL_HEIGHT + TOAST_MARGIN
        for toast in self._toasts:
            # Force the window to compute its natural height
            toast.show_all()
            _w, h = toast.get_size()
            x = sw - TOAST_WIDTH - TOAST_MARGIN
            toast.move(x, y)
            y += h + TOAST_MARGIN
