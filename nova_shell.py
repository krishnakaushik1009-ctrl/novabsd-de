#!/usr/bin/env python3
"""
NovaBSD Shell — Main Entry Point
FreeBSD Desktop Environment Prototype

Run: python3 nova_shell.py
Deps (FreeBSD): pkg install py311-gobject3 gtk3 py311-cairo xwininfo
"""

import sys
import os
import signal
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")

from gi.repository import Gtk, Gdk, GLib

from nova.panel    import NovaPanel
from nova.dock     import NovaDock
from nova.wallpaper import NovaWallpaper
from nova.launcher  import NovaLauncher
from nova.notifier  import NovaNotifier
from nova.theme     import apply_theme


class NovaShell:
    """Top-level DE shell: owns all surface windows."""

    def __init__(self):
        self.display = Gdk.Display.get_default()
        self.screen  = self.display.get_default_screen()

        apply_theme()

        # Core components
        self.wallpaper = NovaWallpaper()
        self.notifier  = NovaNotifier()
        self.launcher  = NovaLauncher(self.notifier)
        self.panel     = NovaPanel(self.launcher, self.notifier)
        self.dock      = NovaDock(self.launcher, self.notifier)

        # Show everything
        self.wallpaper.show_all()
        self.panel.show_all()
        self.dock.show_all()

        # Reserve screen real-estate (EWMH struts)
        self.panel.reserve_strut()
        self.dock.reserve_strut()

        # Handle SIGTERM / SIGINT gracefully
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self._quit)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT,  self._quit)

        print("[NovaBSD Shell] started.")

    def _quit(self, *_):
        print("[NovaBSD Shell] shutting down.")
        Gtk.main_quit()
        return GLib.SOURCE_REMOVE

    def run(self):
        Gtk.main()


def main():
    if os.environ.get("DISPLAY") is None and os.environ.get("WAYLAND_DISPLAY") is None:
        print("ERROR: No display found. Set DISPLAY or WAYLAND_DISPLAY.", file=sys.stderr)
        sys.exit(1)

    shell = NovaShell()
    shell.run()


if __name__ == "__main__":
    main()
