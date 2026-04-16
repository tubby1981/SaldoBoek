"""SaldoBoek MainWindow - Hoofdvenster met navigatie sidebar"""

import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from saldoboek.core.categorization import Categorizer
from saldoboek.core.importer import TransactionImporter
from saldoboek.services.category_service import CategoryService
from saldoboek.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Hoofdvenster van SaldoBoek met navigatie sidebar."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SaldoBoek")
        self.setMinimumSize(1200, 800)

        self._init_services()
        self._setup_ui()
        self._connect_signals()

        # Toon gebruikersselectie dialoog
        self._show_user_selection()

        logger.info("MainWindow initialized")

    def _init_services(self):
        """Initialiseer services voor de GUI."""
        from saldoboek.core.database import DatabaseManager

        self._db = DatabaseManager()
        self._gebruiker_id = None

        self._categorizer = None
        self._importer = None
        self._transaction_service = None
        self._category_service = None

        # Import views hier zodat ze beschikbaar zijn
        self._views = {}

    def _show_user_selection(self):
        """Toon de gebruikersselectie dialoog."""
        from .dialogs.user_selection_dialog import UserSelectionDialog

        dialog = UserSelectionDialog(self._db, self)
        dialog.user_selected.connect(self._on_user_selected)

        if dialog.exec() != dialog.accepted:
            # Gebruiker heeft geannuleerd, sluit applicatie
            logger.info("Geen gebruiker geselecteerd, sluit applicatie")
            self.close()
            return

    def _on_user_selected(self, gebruiker_id, gebruiker_naam):
        """Handle gebruiker selectie."""
        self.set_gebruiker(gebruiker_id, gebruiker_naam)
        self._user_label.setText(gebruiker_naam)
        self._update_views()
        logger.info(
            "Gebruiker %s (ID: %d) succesvol geselecteerd", gebruiker_naam, gebruiker_id
        )

    def _update_views(self):
        """Update views met huidige gebruiker services."""
        from .views.categories_view import CategoriesView
        from .views.import_view import ImportView
        from .views.reports_view import ReportsView
        from .views.statistics_view import StatisticsView
        from .views.transactions_view import TransactionsView

        if self._gebruiker_id is None:
            return

        # Clear existing views
        while self._content_stack.count() > 0:
            self._content_stack.removeWidget(self._content_stack.widget(0))

        # Create new views with services
        self._views["transacties"] = TransactionsView(self._transaction_service)
        self._views["import"] = ImportView(self._transaction_service)
        self._views["categorieën"] = CategoriesView(self._category_service)
        self._views["rapportages"] = ReportsView()
        self._views["statistieken"] = StatisticsView()

        # Add to stack
        for view in self._views.values():
            self._content_stack.addWidget(view)

        # Show first view
        self._content_stack.setCurrentIndex(0)

        # Laad transacties
        self._views["transacties"].load_transactions()

    def set_gebruiker(self, gebruiker_id, gebruiker_naam):
        """Stel de huidige gebruiker in en update services."""
        self._gebruiker_id = gebruiker_id
        self._gebruiker_naam = gebruiker_naam
        self._categorizer = Categorizer(self._db, gebruiker_id)
        self._importer = TransactionImporter(self._categorizer, self._db, gebruiker_id)
        self._transaction_service = TransactionService(
            self._db, self._categorizer, self._importer, gebruiker_id
        )
        self._category_service = CategoryService(self._db, self._categorizer)

        logger.info("Gebruiker ingesteld: %s (ID: %d)", gebruiker_naam, gebruiker_id)

    def _setup_ui(self):
        """Bouwt de UI op met sidebar navigatie."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Content area
        self._content_stack = QStackedWidget()
        main_layout.addWidget(self._content_stack, 1)

    def _create_sidebar(self) -> QFrame:
        """Creëer de navigatie sidebar."""
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setObjectName("sidebar")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)
        title = QLabel("SaldoBoek")
        title.setObjectName("sidebar_title")
        header_layout.addWidget(title)
        self._user_label = QLabel("Niet ingelogd")
        self._user_label.setObjectName("sidebar_user")
        header_layout.addWidget(self._user_label)
        layout.addWidget(header)

        # Navigation buttons
        nav_frame = QFrame()
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(5)

        self._nav_buttons = {}

        nav_items = [
            ("transacties", "Transacties", self._show_transactions),
            ("import", "Importeren", self._show_import),
            ("categorieën", "Categorieën", self._show_categories),
            ("rapportages", "Rapportages", self._show_reports),
            ("statistieken", "Statistieken", self._show_statistics),
        ]

        for key, label, callback in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav_button")
            btn.clicked.connect(callback)
            nav_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        nav_layout.addStretch()
        layout.addWidget(nav_frame)

        # Footer with settings
        footer = QFrame()
        footer.setFixedHeight(50)
        footer_layout = QHBoxLayout(footer)
        settings_btn = QPushButton("⚙️ Instellingen")
        settings_btn.setObjectName("settings_button")
        footer_layout.addWidget(settings_btn)
        layout.addWidget(footer)

        return sidebar

    def _connect_signals(self):
        """Verbind signal/slot connecties."""
        pass

    def _show_transactions(self):
        """Toon transacties view."""
        logger.debug("Navigeer naar transacties")
        if "transacties" in self._views:
            self._content_stack.setCurrentWidget(self._views["transacties"])
            self._views["transacties"].refresh()

    def _show_import(self):
        """Toon import view."""
        logger.debug("Navigeer naar importeren")
        if "import" in self._views:
            self._content_stack.setCurrentWidget(self._views["import"])

    def _show_categories(self):
        """Toon categorieën view."""
        logger.debug("Navigeer naar categorieën")
        if "categorieën" in self._views:
            self._content_stack.setCurrentWidget(self._views["categorieën"])

    def _show_reports(self):
        """Toon rapportages view."""
        logger.debug("Navigeer naar rapportages")
        if "rapportages" in self._views:
            self._content_stack.setCurrentWidget(self._views["rapportages"])

    def _show_statistics(self):
        """Toon statistieken view."""
        logger.debug("Navigeer naar statistieken")
        if "statistieken" in self._views:
            self._content_stack.setCurrentWidget(self._views["statistieken"])
