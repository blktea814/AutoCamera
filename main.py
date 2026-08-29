import sys
import os

# PyInstaller configures import paths for a frozen application. Injecting the
# bundle's Resources directory here can make cv2's native loader resolve its
# package recursively on macOS. Source checkouts still need this path.
if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()

    background = "--background" in sys.argv
    if background:
        window.hide()
        window.auto_start_monitor()
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
