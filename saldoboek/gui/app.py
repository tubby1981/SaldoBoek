"""SaldoBoek GUI Application Entry Point"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


def create_app():
    """Create and configure the QApplication instance."""
    QApplication.setApplicationName("SaldoBoek")
    QApplication.setApplicationVersion("1.0.0")
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    return app


def run_app():
    """Main entry point for the GUI application."""
    from .main_window import MainWindow

    app = create_app()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
