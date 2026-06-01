"""SaldoBoek GUI Application Entry Point"""

import os
import sys

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class ThemeManager:
    """
    Beheert het thema (licht/donker/auto) van de applicatie.

    Klassenmethodes:
    - set_theme(theme): 'light', 'dark', of 'auto'
    - get_theme(): huidig thema
    - is_dark_mode(): True als donkere modus actief is
    """

    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_AUTO = "auto"

    SETTINGS_KEY = "SaldoBoek/theme"

    # Kleuren voor licht thema
    LIGHT_PALETTE = None
    # Kleuren voor donker thema
    DARK_PALETTE = None

    @classmethod
    def _create_palettes(cls):
        """Creëer de kleurenpalettes voor licht en donker thema."""
        # Licht thema
        light = QPalette()
        light.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        light.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        light.setColor(QPalette.ColorRole.Base, QColor(245, 245, 245))
        light.setColor(QPalette.ColorRole.AlternateBase, QColor(235, 235, 235))
        light.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        light.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        light.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        light.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        light.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        light.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        light.setColor(QPalette.ColorRole.Link, QColor(0, 0, 200))
        light.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        light.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        cls.LIGHT_PALETTE = light

        # Donker thema
        dark = QPalette()
        dark.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        dark.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        dark.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        dark.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        dark.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        dark.setColor(QPalette.ColorRole.Button, QColor(60, 60, 60))
        dark.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        dark.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        dark.setColor(QPalette.ColorRole.Link, QColor(100, 180, 255))
        dark.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        dark.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        cls.DARK_PALETTE = dark

    @classmethod
    def get_theme(cls):
        """Haal het huidige thema op uit settings."""
        settings = QSettings()
        return settings.value(cls.SETTINGS_KEY, cls.THEME_AUTO, type=str)

    @classmethod
    def set_theme(cls, theme, app=None):
        """
        Stel het thema in.

        Args:
            theme: 'light', 'dark', of 'auto'
            app: QApplication instantie (optioneel, voor direct toepassen)
        """
        if theme not in (cls.THEME_LIGHT, cls.THEME_DARK, cls.THEME_AUTO):
            theme = cls.THEME_AUTO

        settings = QSettings()
        settings.setValue(cls.SETTINGS_KEY, theme)

        if app:
            cls._apply_theme(app, theme)

    @classmethod
    def _is_system_dark_mode(cls):
        """
        Check of het besturingssysteem in dark mode staat.

        Retourneert True als dark mode, False als light mode.
        """
        # Op Linux (GTK/QT) check de GTK settings
        if sys.platform == "linux":
            try:
                # Probeer via gsettings
                import subprocess

                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if "dark" in result.stdout.lower():
                    return True
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        # Op macOS en Windows kunnen we Qt's platform plugin gebruiken
        # maar voor nu nemen we aan dat het systeem light is als we het niet weten
        return False

    @classmethod
    def is_dark_mode(cls):
        """
        Check of donkere modus actief moet zijn.

        Respecteert de gebruikersvoorkeur en 'auto' instelling.
        """
        theme = cls.get_theme()
        if theme == cls.THEME_DARK:
            return True
        elif theme == cls.THEME_LIGHT:
            return False
        else:  # auto
            return cls._is_system_dark_mode()

    @classmethod
    def _apply_theme(cls, app, theme=None):
        """
        Pas het thema toe op de applicatie.

        Args:
            app: QApplication instantie
            theme: Optioneel thema override ('light', 'dark', 'auto')
        """
        if cls.LIGHT_PALETTE is None:
            cls._create_palettes()

        if theme is None:
            theme = cls.get_theme()

        # Bepaal of we dark of light nodig hebben
        if theme == cls.THEME_DARK:
            palette = cls.DARK_PALETTE
        elif theme == cls.THEME_LIGHT:
            palette = cls.LIGHT_PALETTE
        else:  # auto
            if cls._is_system_dark_mode():
                palette = cls.DARK_PALETTE
            else:
                palette = cls.LIGHT_PALETTE

        app.setPalette(palette)


from saldoboek import __version__


def create_app():
    """Create and configure the QApplication instance."""
    QApplication.setApplicationName("SaldoBoek")
    QApplication.setApplicationVersion(__version__)
    # Enable High DPI scaling via environment variables (Qt 6.3+ prefered way)
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "RoundPreferFloor")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Creëer palettes eenmalig
    ThemeManager._create_palettes()

    # Pas opgeslagen thema toe
    ThemeManager._apply_theme(app)

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
