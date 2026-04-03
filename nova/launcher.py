"""
nova/launcher.py — Full-screen app-launcher overlay for NovaBSD.

Activated by NovaPanel's grid button (or Super key via the shell).
Displays a searchable grid of application shortcuts.
"""

import subprocess
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

# ---------------------------------------------------------------------------
# Application catalogue  (emoji-icon, display-name, argv, desktop-category)
# ---------------------------------------------------------------------------
APP_CATALOGUE = [
    # System tools
    ("💻", "Terminal",    ["xterm"],                    "System"),
    ("📁", "Files",       ["thunar"],                   "System"),
    ("⚙️",  "Settings",   ["xterm", "-title", "NovaBSD Settings",
                              "-e", "sh", "-c",
                              "echo '=== NovaBSD Settings ==='; "
                              "echo 'Edit nova/theme.py to change colors.'; "
                              "echo 'Edit nova/dock.py to change pinned apps.'; "
                              "echo; read -r _"],          "System"),
    ("🖥️",  "Task Mgr",   ["xterm", "-e", "top"],        "System"),
    # Internet
    ("🌐", "Browser",     ["firefox"],                  "Internet"),
    ("📧", "Mail",        ["thunderbird"],               "Internet"),
    # Media
    ("🎬", "Media",       ["vlc"],                       "Media"),
    ("🖼️",  "Images",     ["eog"],                       "Media"),
    # Editors
    ("📝", "Text Edit",   ["mousepad"],                  "Editor"),
    ("💡", "Gedit",       ["gedit"],                     "Editor"),
]

GRID_COLUMNS = 5
ICON_FONT_SIZE = 32  # px — shown as large label


class NovaLauncher(Gtk.Window):
    """Full-screen launcher overlay with search filter."""

    def __init__(self, notifier):
        super().__init__()
        self._notifier = notifier
        self._visible = False

        screen = Gdk.Screen.get_default()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)
        self.set_default_size(screen.get_width(), screen.get_height())
        self.move(0, 0)
        self.set_name("nova-launcher")

        # ── Layout ────────────────────────────────────────────────────
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.set_name("nova-launcher")
        vbox.set_valign(Gtk.Align.FILL)
        vbox.set_halign(Gtk.Align.FILL)

        # Search bar row
        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        search_row.set_halign(Gtk.Align.CENTER)
        search_row.set_margin_top(72)
        search_row.set_margin_bottom(32)

        self._search = Gtk.Entry()
        self._search.set_name("nova-launcher-search")
        self._search.set_placeholder_text("Search apps…")
        self._search.set_size_request(420, 42)
        self._search.connect("changed", self._on_search_changed)
        self._search.connect("activate", self._on_search_activate)
        search_row.pack_start(self._search, False, False, 0)
        vbox.pack_start(search_row, False, False, 0)

        # App grid inside a scrolled window
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._flow = Gtk.FlowBox()
        self._flow.set_max_children_per_line(GRID_COLUMNS)
        self._flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self._flow.set_homogeneous(True)
        self._flow.set_row_spacing(8)
        self._flow.set_column_spacing(8)
        self._flow.set_margin_start(48)
        self._flow.set_margin_end(48)
        self._flow.set_halign(Gtk.Align.CENTER)
        scroll.add(self._flow)
        vbox.pack_start(scroll, True, True, 0)

        # Close hint
        hint = Gtk.Label(label="Press Esc to close")
        hint.set_margin_bottom(18)
        hint.set_opacity(0.4)
        vbox.pack_end(hint, False, False, 0)

        self.add(vbox)

        # Keyboard / focus handling
        self.connect("key-press-event", self._on_key_press)
        self.connect("focus-out-event", lambda *_: self.hide_launcher())

        self._build_grid(APP_CATALOGUE)

    # ------------------------------------------------------------------
    def toggle(self):
        if self._visible:
            self.hide_launcher()
        else:
            self.show_launcher()

    def show_launcher(self):
        self._visible = True
        self._search.set_text("")
        self._build_grid(APP_CATALOGUE)
        self.show_all()
        self._search.grab_focus()

    def hide_launcher(self):
        self._visible = False
        self.hide()

    # ------------------------------------------------------------------
    def _build_grid(self, apps):
        for child in self._flow.get_children():
            self._flow.remove(child)

        for emoji, name, cmd, _cat in apps:
            btn = self._make_app_button(emoji, name, cmd)
            self._flow.add(btn)

        self._flow.show_all()

    def _make_app_button(self, emoji: str, name: str, cmd: list) -> Gtk.Button:
        btn = Gtk.Button()
        btn.set_name("nova-launcher-app-btn")
        btn.set_relief(Gtk.ReliefStyle.NONE)

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        inner.set_halign(Gtk.Align.CENTER)

        icon_lbl = Gtk.Label()
        icon_lbl.set_markup(
            f'<span font="{ICON_FONT_SIZE}">{emoji}</span>'
        )

        name_lbl = Gtk.Label(label=name)
        name_lbl.set_name("nova-launcher-app-label")

        inner.pack_start(icon_lbl, False, False, 0)
        inner.pack_start(name_lbl, False, False, 0)
        btn.add(inner)

        btn.connect("clicked", self._on_app_clicked, cmd, name)
        return btn

    # ------------------------------------------------------------------
    def _on_app_clicked(self, _btn, cmd: list, name: str):
        self.hide_launcher()
        self._launch(cmd, name)

    def _launch(self, cmd: list, name: str):
        try:
            subprocess.Popen(cmd, start_new_session=True)  # noqa: S603
        except FileNotFoundError:
            self._notifier.send("Not installed", f"'{cmd[0]}' was not found.")

    def _on_search_changed(self, entry):
        query = entry.get_text().strip().lower()
        if not query:
            self._build_grid(APP_CATALOGUE)
            return
        filtered = [
            app for app in APP_CATALOGUE
            if query in app[1].lower() or query in app[3].lower()
        ]
        self._build_grid(filtered)

    def _on_search_activate(self, _entry):
        """Launch the first visible result on Enter."""
        children = self._flow.get_children()
        if children:
            btn = children[0].get_child()
            btn.clicked()

    def _on_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.hide_launcher()
            return True
        return False
