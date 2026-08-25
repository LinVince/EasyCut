import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Video Edit Suite")
    apply_theme(app)
    win = MainWindow()
    win.resize(1240, 800)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
