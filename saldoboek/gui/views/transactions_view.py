"""TransactionsView - Toon en beheer transacties"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TransactionsView(QWidget):
    """View voor het tonen en beheren van transacties."""

    def __init__(self, transaction_service, parent=None):
        super().__init__(parent)
        self._transaction_service = transaction_service
        self._setup_ui()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)

        title = QLabel("Transacties")
        title.setObjectName("view_title")
        layout.addWidget(title)

        placeholder = QLabel("Transacties view - wordt nog geïmplementeerd")
        placeholder.setObjectName("placeholder")
        layout.addWidget(placeholder)

    def load_transactions(self, filters=None):
        """Laad transacties met optionele filters."""
        pass

    def refresh(self):
        """Vernieuw de transacties."""
        pass
