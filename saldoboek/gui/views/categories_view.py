"""CategoriesView - Beheer categorieën en regels"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CategoriesView(QWidget):
    """View voor het beheren van categorieën."""

    def __init__(self, category_service, parent=None):
        super().__init__(parent)
        self._category_service = category_service
        self._setup_ui()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)

        title = QLabel("Categorieën")
        title.setObjectName("view_title")
        layout.addWidget(title)

        placeholder = QLabel("Categories view - wordt nog geïmplementeerd")
        placeholder.setObjectName("placeholder")
        layout.addWidget(placeholder)

    def load_categories(self):
        """Laad categorieën."""
        pass

    def refresh(self):
        """Vernieuw de categorieën."""
        pass
