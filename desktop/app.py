"""PyQt6 desktop viewer for watched movies and series."""

from desktop.shell.bootstrap import main
from desktop.shell.main_window import WatchedMoviesWindow

__all__ = ["WatchedMoviesWindow", "main"]

if __name__ == "__main__":
    main()
