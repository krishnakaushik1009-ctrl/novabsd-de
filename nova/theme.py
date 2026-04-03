"""
nova/theme.py — GTK3 CSS theming for NovaBSD Desktop Environment.

All visual style is defined here so other modules stay logic-only.
Call apply_theme() once at startup before any widgets are created.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

# ---------------------------------------------------------------------------
# CSS — edit colors/fonts here to retheme the whole DE
# ---------------------------------------------------------------------------
NOVA_CSS = """
/* ── Global reset ─────────────────────────────────────────────────────── */
* {
    font-family: "Inter", "Cantarell", "DejaVu Sans", sans-serif;
    font-size: 13px;
    color: #e8eaf6;
}

/* ── Panel (top bar) ──────────────────────────────────────────────────── */
#nova-panel {
    background-color: rgba(18, 18, 30, 0.92);
    border-bottom: 1px solid rgba(100, 100, 180, 0.35);
    padding: 0 12px;
}

#nova-panel-logo {
    font-size: 16px;
    font-weight: bold;
    color: #82b1ff;
    padding-right: 12px;
}

#nova-panel-apptitle {
    color: #b0bec5;
    font-size: 12px;
}

#nova-panel-clock {
    color: #e8eaf6;
    font-weight: 600;
    font-size: 13px;
    padding-left: 8px;
}

#nova-panel-status {
    color: #80cbc4;
    font-size: 12px;
    padding-left: 6px;
}

/* ── Dock (bottom bar) ────────────────────────────────────────────────── */
#nova-dock {
    background-color: rgba(18, 18, 30, 0.88);
    border-top: 1px solid rgba(100, 100, 180, 0.30);
    padding: 4px 0;
}

#nova-dock-btn {
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 4px 8px;
    min-width: 52px;
    min-height: 52px;
}

#nova-dock-btn:hover {
    background-color: rgba(130, 177, 255, 0.18);
}

#nova-dock-btn:active {
    background-color: rgba(130, 177, 255, 0.32);
}

#nova-dock-label {
    color: #90a4ae;
    font-size: 10px;
}

#nova-dock-clock {
    color: #e8eaf6;
    font-weight: 600;
    font-size: 14px;
    padding: 0 16px;
}

#nova-dock-date {
    color: #80cbc4;
    font-size: 11px;
    padding: 0 16px;
}

/* ── Launcher overlay ─────────────────────────────────────────────────── */
#nova-launcher {
    background-color: rgba(12, 12, 22, 0.94);
}

#nova-launcher-search {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(130, 177, 255, 0.40);
    border-radius: 20px;
    padding: 6px 16px;
    color: #e8eaf6;
    font-size: 14px;
    caret-color: #82b1ff;
}

#nova-launcher-search:focus {
    border-color: #82b1ff;
}

#nova-launcher-app-btn {
    background: transparent;
    border: none;
    border-radius: 12px;
    padding: 12px;
    min-width: 90px;
    min-height: 90px;
}

#nova-launcher-app-btn:hover {
    background-color: rgba(130, 177, 255, 0.15);
}

#nova-launcher-app-label {
    color: #cfd8dc;
    font-size: 11px;
}

/* ── Notifications ────────────────────────────────────────────────────── */
#nova-notification {
    background-color: rgba(30, 30, 50, 0.95);
    border: 1px solid rgba(130, 177, 255, 0.35);
    border-radius: 10px;
    padding: 10px 14px;
}

#nova-notification-title {
    font-weight: bold;
    color: #82b1ff;
    font-size: 13px;
}

#nova-notification-body {
    color: #cfd8dc;
    font-size: 12px;
}
"""


def apply_theme() -> None:
    """Load NOVA_CSS into the default GTK screen provider."""
    provider = Gtk.CssProvider()
    provider.load_from_data(NOVA_CSS.encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
