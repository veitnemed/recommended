"""Desktop shell: bootstrap and main window."""

from desktop.shell.bootstrap import main
from desktop.shell.main_window import WatchedMoviesWindow
from desktop.shell.tabs import MainTabRegistry, ShellTabSpec

__all__ = ["MainTabRegistry", "ShellTabSpec", "WatchedMoviesWindow", "main"]
