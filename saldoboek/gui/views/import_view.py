"""ImportView - Importeer transacties uit CSV bestanden"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ImportView(QWidget):
    """View voor het importeren van transacties."""

    import_completed = Signal(int)  # aantal_geimporteerd

    def __init__(self, transaction_service, parent=None):
        super().__init__(parent)
        self._transaction_service = transaction_service
        self._setup_ui()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)

        title = QLabel("Transacties Importeren")
        title.setObjectName("view_title")
        layout.addWidget(title)

        placeholder = QLabel("Import view - wordt nog geïmplementeerd")
        placeholder.setObjectName("placeholder")
        layout.addWidget(placeholder)

    def load_transactions(self):
        """Laad transacties na import."""
        pass
