"""ReportsView - Genereer rapportages en exporteer data"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ReportsView(QWidget):
    """View voor het genereren van rapportages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)

        title = QLabel("Rapportages")
        title.setObjectName("view_title")
        layout.addWidget(title)

        placeholder = QLabel("Reports view - wordt nog geïmplementeerd")
        placeholder.setObjectName("placeholder")
        layout.addWidget(placeholder)

    def generate_report(self, jaar, rapportage_type):
        """Genereer een rapport."""
        pass

    def export_data(self, formaat, bestandspad):
        """Exporteer data naar bestand."""
        pass
