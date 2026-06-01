"""TransactionsView - Toon en beheer transacties met paginering."""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .uncategorized_view import EditCategoryDialog

logger = logging.getLogger(__name__)


class TransactionsView(QWidget):
    """
    View voor het tonen en beheren van transacties met paginering.

    Deze view ontvangt data via de ViewModel en stuurt gebruikersacties
    door naar de ViewModel. Alle business logic zit in TransactionsViewModel.
    """

    def __init__(self, viewmodel, parent=None):
        """
        Initialiseer TransactionsView.

        Args:
            viewmodel: TransactionsViewModel instantie
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._setup_ui()
        self._setup_table()
        self._connect_signals()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)

        title = QLabel("Transacties")
        title.setObjectName("view_title")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Progress bar (hidden by default)
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("progress_bar")
        self._progress_bar.setVisible(False)
        self._progress_bar.setMaximumWidth(150)
        header_layout.addWidget(self._progress_bar)

        # Refresh button
        self._refresh_btn = QPushButton("🔄 Verversen")
        self._refresh_btn.setObjectName("refresh_button")
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self._refresh_btn)

        layout.addWidget(header)

        # Filters
        filters_frame = QFrame()
        filters_frame.setObjectName("filters_frame")
        filters_layout = QHBoxLayout(filters_frame)

        # Year filter
        year_label = QLabel("Jaar:")
        filters_layout.addWidget(year_label)
        self._year_combo = QComboBox()
        self._year_combo.setObjectName("year_combo")
        self._year_combo.currentTextChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self._year_combo)

        # Month filter
        month_label = QLabel("Maand:")
        filters_layout.addWidget(month_label)
        self._month_combo = QComboBox()
        self._month_combo.setObjectName("month_combo")
        self._month_combo.addItems(
            [
                "Alle",
                "Januari",
                "Februari",
                "Maart",
                "April",
                "Mei",
                "Juni",
                "Juli",
                "Augustus",
                "September",
                "Oktober",
                "November",
                "December",
            ]
        )
        self._month_combo.currentTextChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self._month_combo)

        # Category filter
        category_label = QLabel("Categorie:")
        filters_layout.addWidget(category_label)
        self._category_combo = QComboBox()
        self._category_combo.setObjectName("category_combo")
        self._category_combo.currentTextChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self._category_combo)

        # Search
        search_label = QLabel("Zoeken:")
        filters_layout.addWidget(search_label)
        self._search_input = QLineEdit()
        self._search_input.setObjectName("search_input")
        self._search_input.setPlaceholderText("Zoek...")
        self._search_input.textChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self._search_input)

        layout.addWidget(filters_frame)

        # Paginering controls
        pagination_frame = QFrame()
        pagination_layout = QHBoxLayout(pagination_frame)

        # Previous button
        self._prev_btn = QPushButton("◀ Vorige")
        self._prev_btn.setObjectName("prev_button")
        self._prev_btn.clicked.connect(self._on_prev_page)
        pagination_layout.addWidget(self._prev_btn)

        # Page indicator
        self._page_label = QLabel("Geen data")
        self._page_label.setObjectName("page_label")
        self._page_label.setAlignment(Qt.AlignCenter)
        pagination_layout.addWidget(self._page_label)

        # Next button
        self._next_btn = QPushButton("Volgende ▶")
        self._next_btn.setObjectName("next_button")
        self._next_btn.clicked.connect(self._on_next_page)
        pagination_layout.addWidget(self._next_btn)

        pagination_layout.addStretch()

        # Stats label
        self._stats_label = QLabel("")
        self._stats_label.setObjectName("stats_label")
        pagination_layout.addWidget(self._stats_label)

        layout.addWidget(pagination_frame)

        # Table
        self._table = QTableWidget()
        self._table.setObjectName("transactions_table")
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            [
                "Datum",
                "Rekening",
                "Tegenrekening",
                "Naam",
                "Omschrijving",
                "Bedrag",
                "Saldo",
                "Categorie",
            ]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

        # Initial state
        self._prev_btn.setEnabled(False)
        self._next_btn.setEnabled(False)
        self._page_label.setText("Geen data")

    def _setup_table(self):
        """Configureer de tabel eigenschappen."""
        header = self._table.horizontalHeader()
        # Interactive allows user to resize columns with mouse
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        header.setSectionResizeMode(6, QHeaderView.Interactive)
        header.setSectionResizeMode(7, QHeaderView.Interactive)
        # Set initial reasonable widths
        self._table.setColumnWidth(0, 100)  # Datum
        self._table.setColumnWidth(1, 130)  # Rekening
        self._table.setColumnWidth(2, 130)  # Tegenrekening
        self._table.setColumnWidth(3, 150)  # Naam
        self._table.setColumnWidth(4, 220)  # Omschrijving
        self._table.setColumnWidth(5, 100)  # Bedrag
        self._table.setColumnWidth(6, 100)  # Saldo
        self._table.setColumnWidth(7, 120)  # Categorie

    def _connect_signals(self):
        """Verbind signals van de ViewModel met slots in de View."""
        # Data signals
        self._viewmodel.transactions_loaded.connect(self._on_transactions_loaded)
        self._viewmodel.count_updated.connect(self._on_count_updated)

        # Loading signals
        self._viewmodel.loading_started.connect(self._on_loading_started)
        self._viewmodel.loading_finished.connect(self._on_loading_finished)
        self._viewmodel.error_occurred.connect(self._on_error)

        # Stats signal
        self._viewmodel.stats_updated.connect(self._on_stats_updated)

        # Filter options signal
        self._viewmodel.filter_options_updated.connect(self._on_filter_options_updated)

    # ViewModel signal handlers

    def _on_transactions_loaded(self, page_data):
        """Handle nieuwe transacties geladen van ViewModel."""
        self._render_page(page_data)

    def _on_count_updated(self, total_count):
        """Handle totaal aantal update van ViewModel."""
        self._update_pagination_controls()

    def _on_loading_started(self):
        """Handle laden gestart."""
        self._refresh_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._stats_label.setText("Laden...")

    def _on_loading_finished(self):
        """Handle laden voltooid."""
        self._progress_bar.setVisible(False)
        self._refresh_btn.setEnabled(True)

    def _on_error(self, error_msg):
        """Handle error van ViewModel."""
        self._progress_bar.setVisible(False)
        self._refresh_btn.setEnabled(True)
        self._stats_label.setText(f"Fout bij laden: {error_msg}")

    def _on_stats_updated(self, stats):
        """Handle stats update van ViewModel."""
        inkomsten = stats.get("inkomsten", 0)
        uitgaven = stats.get("uitgaven", 0)
        self._stats_label.setText(
            f"Pagina: €{inkomsten:,.2f} in | €{abs(uitgaven):,.2f} uit"
        )

    def _on_filter_options_updated(self, years, categories):
        """Handle filter opties update van ViewModel."""
        # Years
        self._year_combo.blockSignals(True)
        self._year_combo.clear()
        self._year_combo.addItems(["Alle"] + [str(y) for y in years])
        self._year_combo.blockSignals(False)

        # Categories
        self._category_combo.blockSignals(True)
        self._category_combo.clear()
        self._category_combo.addItems(["Alle"] + categories)
        self._category_combo.blockSignals(False)

    # User action handlers (forward to ViewModel)

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self._stats_label.setText("Laden...")
        self._viewmodel.refresh()

    def _on_filter_changed(self):
        """Handle filter wijzigingen."""
        filters = {}

        # Year
        year_text = self._year_combo.currentText()
        if year_text and year_text != "Alle":
            filters["jaar"] = int(year_text)

        # Month
        month_index = self._month_combo.currentIndex()
        if month_index > 0:
            filters["maand"] = month_index

        # Category
        category_text = self._category_combo.currentText()
        if category_text and category_text != "Alle":
            filters["categorie"] = category_text

        # Search
        search_text = self._search_input.text().strip()
        if search_text:
            filters["zoek"] = search_text

        self._viewmodel.apply_filters(filters)

    def _on_prev_page(self):
        """Ga naar vorige pagina."""
        self._viewmodel.previous_page()

    def _on_next_page(self):
        """Ga naar volgende pagina."""
        self._viewmodel.next_page()

    # Rendering helpers

    def _render_page(self, page_data):
        """Render de huidige pagina met transacties."""
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(len(page_data))

        for row, trans in enumerate(page_data):
            # Datum
            datum_item = QTableWidgetItem(str(trans.get("datum", "")))
            datum_item.setData(Qt.UserRole, trans.get("id"))
            self._table.setItem(row, 0, datum_item)

            # Rekening (eigen rekening)
            rekening = str(trans.get("rekening", ""))
            self._table.setItem(row, 1, QTableWidgetItem(rekening))

            # Tegenrekening
            tegenrekening = str(trans.get("tegenrekening", ""))
            if tegenrekening and tegenrekening not in ("", "nan", "None"):
                display_tegen = tegenrekening
            else:
                display_tegen = "-"
            self._table.setItem(row, 2, QTableWidgetItem(display_tegen))

            # Naam
            self._table.setItem(row, 3, QTableWidgetItem(str(trans.get("naam", ""))))

            # Omschrijving
            self._table.setItem(
                row, 4, QTableWidgetItem(str(trans.get("omschrijving", "")))
            )

            # Bedrag
            bedrag = trans.get("bedrag", 0)
            bedrag_item = QTableWidgetItem(f"€{bedrag:,.2f}")
            if bedrag < 0:
                bedrag_item.setForeground(Qt.red)
            else:
                bedrag_item.setForeground(Qt.darkGreen)
            self._table.setItem(row, 5, bedrag_item)

            # Saldo
            saldo = trans.get("saldo_voor", 0)
            self._table.setItem(row, 6, QTableWidgetItem(f"€{saldo:,.2f}"))

            # Categorie
            categorie = str(trans.get("categorie", "Ongecategoriseerd"))
            categorie_item = QTableWidgetItem(categorie)
            if categorie == "Ongecategoriseerd":
                categorie_item.setForeground(Qt.gray)
            self._table.setItem(row, 7, categorie_item)

        self._table.setUpdatesEnabled(True)
        self._update_pagination_controls()

    def _update_pagination_controls(self):
        """Update paginering controls."""
        if self._viewmodel.get_total_count() == 0:
            self._page_label.setText("Geen transacties")
            self._prev_btn.setEnabled(False)
            self._next_btn.setEnabled(False)
            return

        current_page = self._viewmodel.get_current_page()
        total_pages = self._viewmodel.get_total_pages()
        total_count = self._viewmodel.get_total_count()
        page_size = self._viewmodel.page_size

        start_idx = current_page * page_size + 1
        end_idx = min((current_page + 1) * page_size, total_count)

        self._page_label.setText(
            f"Transacties {start_idx}-{end_idx} van {total_count} "
            f"(Pagina {current_page + 1} van {total_pages})"
        )

        self._prev_btn.setEnabled(current_page > 0)
        self._next_btn.setEnabled(current_page < total_pages - 1)

    # Public methods called by MainWindow

    def load_transactions(self, filters=None):
        """Laad transacties via de ViewModel."""
        self._viewmodel.load_transactions(filters)

    def refresh(self):
        """Vernieuw de transacties via de ViewModel."""
        self._viewmodel.refresh()

    def _on_double_click(self, index):
        """Handle double-click op een transactie."""
        row = index.row()
        transaction = self._get_transaction_at_row(row)
        if transaction:
            self._open_edit_category_dialog(transaction)

    def _on_context_menu(self, position):
        """Toon context menu bij rechtermuisklik."""
        row = self._table.rowAt(position.y())
        if row < 0:
            return

        transaction = self._get_transaction_at_row(row)
        if not transaction:
            return

        menu = QMenu(self)

        # Categorie bewerken action
        edit_action = menu.addAction("Categorie bewerken...")
        edit_action.triggered.connect(
            lambda: self._open_edit_category_dialog(transaction)
        )

        menu.exec(self._table.viewport().mapToGlobal(position))

    def _get_transaction_at_row(self, row):
        """
        Haal transactie data op uit een tabelrij.

        Args:
            row: Rij index

        Returns:
            Dict met transactie data of None
        """
        if row < 0 or row >= self._table.rowCount():
            return None

        # Haal transactie ID uit de datum kolom (UserRole data)
        datum_item = self._table.item(row, 0)
        if not datum_item:
            return None

        transaction_id = datum_item.data(Qt.UserRole)
        if not transaction_id:
            return None

        # Haal alle transacties van huidige pagina uit de ViewModel
        # We moeten de data opslaan bij het renderen van de pagina
        # Helaas moeten we dit via de viewmodel doen
        page_data = self._viewmodel.get_page_data()

        # Zoek de transactie met dit ID in de huidige pagina
        for trans in page_data:
            if trans.get("id") == transaction_id:
                return trans

        return None

    def _open_edit_category_dialog(self, transaction):
        """
        Open de dialoog voor het bewerken van de categorie.

        Args:
            transaction: Dict met transactie data
        """
        try:
            categories = self._viewmodel.get_all_categories()
            similar_df = self._viewmodel.find_similar_transactions(transaction)
        except Exception as e:
            QMessageBox.warning(self, "Fout", f"Kon categorieën niet laden: {e}")
            return

        if not categories:
            QMessageBox.warning(
                self, "Geen Categorieën", "Er zijn geen categorieën beschikbaar."
            )
            return

        dialog = EditCategoryDialog(transaction, categories, similar_df, self)
        dialog.saved.connect(self._on_category_saved)
        dialog.exec()

    def _on_category_saved(
        self, transaction_id, new_category, similar_ids=None, rule_zoekterm=None
    ):
        """
        Handle category saved van de dialog.

        Args:
            transaction_id: ID van de transactie
            new_category: Nieuwe categorie naam
            similar_ids: List van vergelijkbare transactie IDs of None
            rule_zoekterm: Zoekterm voor nieuwe regel of None
        """
        success = self._viewmodel.update_category(transaction_id, new_category)
        if success:
            logger.info(
                "Categorie bijgewerkt: transactie %d -> %s",
                transaction_id,
                new_category,
            )

            # Update ook vergelijkbare transacties indien aangevinkt
            if similar_ids:
                updated_count = self._viewmodel.update_similar_categories(
                    similar_ids, new_category
                )
                if updated_count > 0:
                    logger.info(
                        "Ook %d vergelijkbare transacties bijgewerkt",
                        updated_count,
                    )
                    QMessageBox.information(
                        self,
                        "Bijgewerkt",
                        f"{updated_count + 1} transacties zijn bijgewerkt naar '{new_category}'.",
                    )

            # Voeg regel toe indien aangevinkt
            if rule_zoekterm:
                rule_success = self._viewmodel.add_categorization_rule(
                    rule_zoekterm, new_category
                )
                if rule_success:
                    logger.info(
                        "Regel toegevoegd: '%s' -> %s",
                        rule_zoekterm,
                        new_category,
                    )
        else:
            QMessageBox.warning(self, "Fout", "Kon de categorie niet opslaan.")
