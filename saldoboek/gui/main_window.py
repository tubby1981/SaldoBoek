"""SaldoBoek MainWindow - Hoofdvenster met menu navigatie."""

import logging
import os
import shutil
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QToolBar,
    QWidget,
)

from saldoboek.core.categorization import Categorizer
from saldoboek.core.database import DatabaseManager
from saldoboek.core.importer import TransactionImporter
from saldoboek.services.category_service import CategoryService
from saldoboek.services.report_service import ReportService
from saldoboek.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Hoofdvenster van SaldoBoek met menu navigatie."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SaldoBoek")
        self.setMinimumSize(1200, 800)

        self._init_services()
        self._setup_ui()
        self._create_menu_bar()
        self._create_toolbar()
        self._connect_signals()

        # Toon gebruikersselectie dialoog
        self._show_user_selection()

        logger.info("MainWindow initialized")

    def _init_services(self):
        """Initialiseer services voor de GUI."""
        self._db = DatabaseManager()
        self._gebruiker_id = None

        self._categorizer = None
        self._importer = None
        self._transaction_service = None
        self._category_service = None
        self._report_service = None

        # ViewModels
        self._viewmodels = {}

        # View instances
        self._views = {}

        # Current view index for navigation
        self._current_nav_index = 0

    def _create_viewmodels(self):
        """Creëer ViewModels voor alle views."""
        from saldoboek.gui.viewmodels import (
            CategoriesViewModel,
            ImportViewModel,
            ReportsViewModel,
            StatisticsViewModel,
            TransactionsViewModel,
            UncategorizedViewModel,
        )

        self._viewmodels["transacties"] = TransactionsViewModel(
            self._transaction_service
        )
        self._viewmodels["transacties"].set_gebruiker_id(self._gebruiker_id)
        self._viewmodels["import"] = ImportViewModel(self._transaction_service)
        self._viewmodels["import"].set_gebruiker_id(self._gebruiker_id)
        self._viewmodels["categorieën"] = CategoriesViewModel(self._category_service)
        self._viewmodels["categorieën"].set_gebruiker_id(self._gebruiker_id)
        self._viewmodels["rapportages"] = ReportsViewModel(self._transaction_service)
        self._viewmodels["rapportages"].set_report_service(self._report_service)
        self._viewmodels["rapportages"].set_gebruiker_id(self._gebruiker_id)
        self._viewmodels["statistieken"] = StatisticsViewModel(
            self._transaction_service
        )
        self._viewmodels["statistieken"].set_gebruiker_id(self._gebruiker_id)
        self._viewmodels["ongecategoriseerd"] = UncategorizedViewModel(
            self._transaction_service, self._category_service
        )
        self._viewmodels["ongecategoriseerd"].set_gebruiker_id(self._gebruiker_id)

    def _show_user_selection(self, wissel=False):
        """
        Toon de gebruikersselectie dialoog.

        Args:
            wissel: Als True, sluit de app niet bij annuleren (voor gebruiker wisselen)
        """
        from .dialogs.user_selection_dialog import UserSelectionDialog

        dialog = UserSelectionDialog(self._db, self)
        dialog.user_selected.connect(self._on_user_selected)

        if dialog.exec() != dialog.accepted:
            if not wissel:
                # Bij eerste keer starten: geen gebruiker geselecteerd, sluit app
                logger.info("Geen gebruiker geselecteerd, sluit applicatie")
                self.close()
            return

    def _on_user_selected(self, gebruiker_id, gebruiker_naam):
        """Handle gebruiker selectie."""
        self.set_gebruiker(gebruiker_id, gebruiker_naam)
        self._update_views()
        logger.info(
            "Gebruiker %s (ID: %d) succesvol geselecteerd", gebruiker_naam, gebruiker_id
        )

    def _update_views(self):
        """Update views met huidige gebruiker services en ViewModels."""
        from .views.categories_view import CategoriesView
        from .views.import_view import ImportView
        from .views.reports_view import ReportsView
        from .views.statistics_view import StatisticsView
        from .views.transactions_view import TransactionsView
        from .views.uncategorized_view import UncategorizedView

        if self._gebruiker_id is None:
            return

        # Clear existing views
        while self._content_stack.count() > 0:
            self._content_stack.removeWidget(self._content_stack.widget(0))

        # Create ViewModels
        self._create_viewmodels()

        # Create new views with ViewModels
        self._views["transacties"] = TransactionsView(self._viewmodels["transacties"])
        self._views["import"] = ImportView(self._viewmodels["import"])
        self._views["import"].import_completed.connect(self._on_import_completed)
        self._views["categorieën"] = CategoriesView(self._viewmodels["categorieën"])
        self._views["rapportages"] = ReportsView(self._viewmodels["rapportages"])
        self._views["statistieken"] = StatisticsView(self._viewmodels["statistieken"])
        self._views["ongecategoriseerd"] = UncategorizedView(
            self._viewmodels["ongecategoriseerd"]
        )

        # Add to stack
        for view in self._views.values():
            self._content_stack.addWidget(view)

        # Show first view
        self._content_stack.setCurrentIndex(0)
        self._update_toolbar_buttons()

        # Laad data na UI rendering (voorkom freeze)
        QTimer.singleShot(0, lambda: self._views["transacties"].load_transactions())
        QTimer.singleShot(0, lambda: self._views["categorieën"].load_categories())
        QTimer.singleShot(0, lambda: self._views["statistieken"].load_statistics())
        QTimer.singleShot(
            0, lambda: self._views["rapportages"].set_gebruiker_id(self._gebruiker_id)
        )

    def _on_import_completed(self, aantal):
        """Handle import voltooid - refresh transacties."""
        if "transacties" in self._views:
            self._views["transacties"].refresh()
        if "categorieën" in self._views:
            self._views["categorieën"].refresh()

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
        self._report_service = ReportService(self._db, self._transaction_service)

        # Update window title with user name
        self.setWindowTitle(f"SaldoBoek - {gebruiker_naam}")

        logger.info("Gebruiker ingesteld: %s (ID: %d)", gebruiker_naam, gebruiker_id)

    def _setup_ui(self):
        """Bouwt de UI op met sidebar navigatie."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Content area
        self._content_stack = QStackedWidget()
        main_layout.addWidget(self._content_stack, 1)

        # Status bar
        self.statusBar().showMessage("Klaar")

    def _create_menu_bar(self):
        """Creëer de menu bar."""
        menubar = self.menuBar()

        # === Bestand Menu ===
        menu_bestand = menubar.addMenu("&Bestand")

        # Importeren
        импорт_act = QAction("&Importeren...", self)
        импорт_act.setShortcut("Ctrl+I")
        импорт_act.setStatusTip("Importeer transacties uit CSV bestanden")
        импорт_act.triggered.connect(self._on_menu_import)
        menu_bestand.addAction(импорт_act)

        menu_bestand.addSeparator()

        # Exporteren submenu
        menu_exporteren = menu_bestand.addMenu("&Exporteren")

        exp_transacties = QAction("Transacties (CSV)", self)
        exp_transacties.setStatusTip("Exporteer transacties naar CSV")
        exp_transacties.triggered.connect(self._on_export_transactions)
        menu_exporteren.addAction(exp_transacties)

        exp_rapport = QAction("Rapportage (Excel)", self)
        exp_rapport.setStatusTip("Genereer een jaaroverzicht rapport")
        exp_rapport.triggered.connect(self._on_menu_reports)
        menu_exporteren.addAction(exp_rapport)

        menu_bestand.addSeparator()

        # Backup maken
        backup_act = QAction("&Backup maken...", self)
        backup_act.setShortcut("Ctrl+B")
        backup_act.setStatusTip("Maak een backup van de database")
        backup_act.triggered.connect(self._on_backup_database)
        menu_bestand.addAction(backup_act)

        # Herstellen
        restore_act = QAction("&Herstellen...", self)
        restore_act.setShortcut("Ctrl+R")
        restore_act.setStatusTip("Herstel database vanuit backup")
        restore_act.triggered.connect(self._on_restore_database)
        menu_bestand.addAction(restore_act)

        menu_bestand.addSeparator()

        # Afsluiten
        afsluit_act = QAction("&Afsluiten", self)
        afsluit_act.setShortcut("Ctrl+Q")
        afsluit_act.setStatusTip("Sluit SaldoBoek af")
        afsluit_act.triggered.connect(self.close)
        menu_bestand.addAction(afsluit_act)

        # === Opties Menu ===
        menu_opties = menubar.addMenu("&Opties")

        # Gebruiker wisselen
        gebruiker_act = QAction("&Gebruiker wisselen...", self)
        gebruiker_act.setStatusTip("Wissel naar een andere gebruiker")
        gebruiker_act.triggered.connect(self._on_wissel_gebruiker)
        menu_opties.addAction(gebruiker_act)

        menu_opties.addSeparator()

        # Categorieën beheren
        categorieën_act = QAction("&Categorieën...", self)
        categorieën_act.setStatusTip("Beheer categorieën")
        categorieën_act.triggered.connect(self._show_categories)
        menu_opties.addAction(categorieën_act)

        # Ongecategoriseerde transacties
        ongecat_act = QAction("&Ongecategoriseerde transacties...", self)
        ongecat_act.setStatusTip("Categoriseer ongecategoriseerde transacties")
        ongecat_act.triggered.connect(self._show_uncategorized)
        menu_opties.addAction(ongecat_act)

        menu_opties.addSeparator()

        # Thema submenu
        theme_submenu = menu_opties.addMenu("&Thema")

        from .app import ThemeManager

        self._theme_actions = {}
        for theme, label in [
            (ThemeManager.THEME_AUTO, "&Automatisch (systeem)"),
            (ThemeManager.THEME_LIGHT, "&Licht"),
            (ThemeManager.THEME_DARK, "&Donker"),
        ]:
            act = QAction(label, self)
            act.setCheckable(True)
            act.setData(theme)
            act.triggered.connect(self._on_theme_changed)
            theme_submenu.addAction(act)
            self._theme_actions[theme] = act

        # Update checkmark voor huidige thema
        self._update_theme_checkmarks()

        # === Help Menu ===
        menu_help = menubar.addMenu("&Help")

        over_act = QAction("&Over SaldoBoek", self)
        over_act.setStatusTip("Informatie over SaldoBoek")
        over_act.triggered.connect(self._on_show_about)
        menu_help.addAction(over_act)

    def _create_toolbar(self):
        """Creëer de toolbar met sneltoegangsknoppen."""
        toolbar = QToolBar("Hoofdwerkbalk")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Navigation buttons
        self._nav_buttons = {}

        # Transacties
        self._nav_buttons["transacties"] = toolbar.addAction("📋 Transacties")
        self._nav_buttons["transacties"].triggered.connect(self._show_transactions)

        # Importeren
        self._nav_buttons["import"] = toolbar.addAction("📥 Importeren")
        self._nav_buttons["import"].triggered.connect(self._on_menu_import)

        # Categorieën
        self._nav_buttons["categorieën"] = toolbar.addAction("🏷️ Categorieën")
        self._nav_buttons["categorieën"].triggered.connect(self._show_categories)

        toolbar.addSeparator()

        # Rapportages
        self._nav_buttons["rapportages"] = toolbar.addAction("📊 Rapportages")
        self._nav_buttons["rapportages"].triggered.connect(self._show_reports)

        # Statistieken
        self._nav_buttons["statistieken"] = toolbar.addAction("📈 Statistieken")
        self._nav_buttons["statistieken"].triggered.connect(self._show_statistics)

        toolbar.addSeparator()

        # Backup
        backup_act = toolbar.addAction("💾 Backup")
        backup_act.triggered.connect(self._on_backup_database)

    def _update_toolbar_buttons(self):
        """Update toolbar button states based on current view."""
        pass  # Future: highlight current nav button

    def _update_theme_checkmarks(self):
        """Update de checkmarks in het thema menu."""
        from .app import ThemeManager

        current_theme = ThemeManager.get_theme()
        for theme, action in self._theme_actions.items():
            action.setChecked(theme == current_theme)

    def _on_theme_changed(self):
        """Handle thema wijziging vanuit menu."""
        from PySide6.QtWidgets import QApplication

        from .app import ThemeManager

        # Vind welke action getriggerd werd
        action = self.sender()
        if not action:
            return

        new_theme = action.data()
        if not new_theme:
            return

        # Pas thema toe (gebruik QApplication instance)
        app = QApplication.instance()
        ThemeManager.set_theme(new_theme, app)

        # Update checkmarks
        self._update_theme_checkmarks()

        logger.info("Thema gewijzigd naar: %s", new_theme)

    def _connect_signals(self):
        """Verbind signal/slot connecties."""
        pass

    # === Navigation ===

    def _show_transactions(self):
        """Toon transacties view."""
        logger.debug("Navigeer naar transacties")
        if "transacties" in self._views:
            self._content_stack.setCurrentWidget(self._views["transacties"])
            QTimer.singleShot(0, lambda: self._views["transacties"].refresh())
        self.statusBar().showMessage("Transacties")

    def _show_import(self):
        """Toon import view."""
        logger.debug("Navigeer naar importeren")
        if "import" in self._views:
            self._content_stack.setCurrentWidget(self._views["import"])
        self.statusBar().showMessage("Importeren")

    def _show_categories(self):
        """Toon categorieën view."""
        logger.debug("Navigeer naar categorieën")
        if "categorieën" in self._views:
            self._content_stack.setCurrentWidget(self._views["categorieën"])
        self.statusBar().showMessage("Categorieën")

    def _show_uncategorized(self):
        """Toon ongecategoriseerde transacties view."""
        logger.debug("Navigeer naar ongecategoriseerde transacties")
        if "ongecategoriseerd" in self._views:
            self._views["ongecategoriseerd"].load_uncategorized()
            self._content_stack.setCurrentWidget(self._views["ongecategoriseerd"])
        self.statusBar().showMessage("Ongecategoriseerde Transacties")

    def _show_reports(self):
        """Toon rapportages view."""
        logger.debug("Navigeer naar rapportages")
        if "rapportages" in self._views:
            self._content_stack.setCurrentWidget(self._views["rapportages"])
        self.statusBar().showMessage("Rapportages")

    def _show_statistics(self):
        """Toon statistieken view."""
        logger.debug("Navigeer naar statistieken")
        if "statistieken" in self._views:
            self._content_stack.setCurrentWidget(self._views["statistieken"])
        self.statusBar().showMessage("Statistieken")

    # === Menu Actions ===

    def _on_menu_import(self):
        """Handle importeren menu actie."""
        self._show_import()

    def _on_menu_reports(self):
        """Handle rapportages menu actie."""
        self._show_reports()

    def _on_export_transactions(self):
        """Exporteer transacties naar CSV."""
        if "transacties" not in self._views:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Exporteer Transacties",
            os.path.expanduser("~/Documents/SaldoBoek/transacties.csv"),
            "CSV Files (*.csv)",
        )

        if not filepath:
            return

        try:
            # Haal transacties op via service
            df = self._transaction_service.get_transactions(
                filters={}, gebruiker_id=self._gebruiker_id
            )
            df.to_csv(filepath, index=False)
            self.statusBar().showMessage(f"Transacties geëxporteerd naar {filepath}")
            QMessageBox.information(
                self,
                "Export gelukt",
                f"Transacties zijn geëxporteerd naar:\n{filepath}",
            )
        except Exception as e:
            logger.error("Export fout: %s", e)
            QMessageBox.warning(
                self, "Export fout", f"Kon transacties niet exporteren:\n{e}"
            )

    def _on_backup_database(self):
        """Maak een backup van de database."""
        timestamp = datetime.now().strftime("%Y%m%d")
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Backup Maken",
            os.path.expanduser(
                f"~/Documents/SaldoBoek/backup_{self._gebruiker_naam}_{timestamp}.db"
            ),
            "Database Files (*.db)",
        )

        if not filepath:
            return

        try:
            shutil.copy2(self._db.db_path, filepath)
            self.statusBar().showMessage(f"Backup gemaakt: {filepath}")
            QMessageBox.information(
                self, "Backup gelukt", f"Backup is opgeslagen als:\n{filepath}"
            )
        except Exception as e:
            logger.error("Backup fout: %s", e)
            QMessageBox.warning(self, "Backup fout", f"Kon backup niet maken:\n{e}")

    def _on_restore_database(self):
        """Herstel database vanuit backup."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Backup Herstellen",
            os.path.expanduser("~/Documents/SaldoBoek/"),
            "Database Files (*.db)",
        )

        if not filepath:
            return

        reply = QMessageBox.question(
            self,
            "Bevestig Herstellen",
            f"Wil je de database herstellen vanuit:\n{filepath}\n\n"
            "WAARSCHUWING: De huidige data gaat verloren!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            shutil.copy2(filepath, self._db.db_path)
            QMessageBox.information(
                self,
                "Herstellen gelukt",
                "Database is hersteld. Herstart de applicatie om de wijzigingen te zien.",
            )
        except Exception as e:
            logger.error("Herstellen fout: %s", e)
            QMessageBox.warning(
                self, "Herstellen fout", f"Kon database niet herstellen:\n{e}"
            )

    def _on_wissel_gebruiker(self):
        """Wissel naar een andere gebruiker."""
        self._show_user_selection(wissel=True)

    def _on_show_about(self):
        """Toon over dialoog."""
        QMessageBox.about(
            self,
            "Over SaldoBoek",
            "<h3>SaldoBoek</h3>"
            "<p>Versie 1.0.0</p>"
            "<p>Een applicatie voor het beheren van persoonlijke financiën.</p>"
            "<p><small>© 2024 SaldoBoek</small></p>",
        )
