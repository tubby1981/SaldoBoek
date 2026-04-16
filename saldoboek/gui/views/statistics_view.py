"""StatisticsView - Toon statistieken en overzichten"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StatisticsView(QWidget):
    """View voor het tonen van statistieken."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)

        title = QLabel("Statistieken")
        title.setObjectName("view_title")
        layout.addWidget(title)

        placeholder = QLabel("Statistics view - wordt nog geïmplementeerd")
        placeholder.setObjectName("placeholder")
        layout.addWidget(placeholder)

    def load_statistics(self):
        """Laad statistieken."""
        pass

    def refresh(self):
        """Vernieuw de statistieken."""
        pass
