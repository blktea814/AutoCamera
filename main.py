import sys
import os

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
