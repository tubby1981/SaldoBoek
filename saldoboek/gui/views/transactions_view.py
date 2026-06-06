"""TransactionsView - Toon en beheer transacties met paginering."""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
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
        self._table.cellClicked.connect(self._on_cell_clicked)
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

        # Link signals
        self._viewmodel.potential_links_found.connect(self._on_potential_links_found)
        self._viewmodel.link_completed.connect(self._on_link_completed)
        self._viewmodel.unlink_completed.connect(self._on_unlink_completed)
        self._viewmodel.linked_info_loaded.connect(self._on_linked_info_loaded)
        self._linked_info_pending = None  # Wacht op info voor click actie

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
        # Bewaar huidige selecties
        current_year = self._year_combo.currentText()
        current_month = self._month_combo.currentIndex()
        current_category = self._category_combo.currentText()

        # Years
        self._year_combo.blockSignals(True)
        self._year_combo.clear()
        self._year_combo.addItems(["Alle"] + [str(y) for y in years])
        # Herstel selectie als deze nog bestaat
        if current_year and current_year != "Alle":
            idx = self._year_combo.findText(current_year)
            if idx >= 0:
                self._year_combo.setCurrentIndex(idx)
        self._year_combo.blockSignals(False)

        # Categories
        self._category_combo.blockSignals(True)
        self._category_combo.clear()
        self._category_combo.addItems(["Alle"] + categories)
        # Herstel selectie als deze nog bestaat
        if current_category and current_category != "Alle":
            idx = self._category_combo.findText(current_category)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)
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

            # Naam (met link indicator)
            naam = trans.get("naam", "")
            if naam is None or (isinstance(naam, float) and str(naam) == "nan"):
                naam = "-"
            else:
                naam = str(naam)
            trans_id = trans.get("id")
            linked_id = trans.get("linked_transaction_id")
            # Check voor None EN NaN (pandas leest SQLite NULL als NaN)
            has_link = linked_id is not None and str(linked_id) != "nan"
            if has_link:
                naam = f"🔗 {naam}"
            naam_item = QTableWidgetItem(naam)
            if has_link:
                naam_item.setForeground(Qt.blue)
                naam_item.setToolTip("Klik om gekoppelde transactie te zien")
                # Sla transactie ID op in het item voor click handling
                naam_item.setData(Qt.UserRole, trans_id)
            self._table.setItem(row, 3, naam_item)

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

    def _on_cell_clicked(self, row, col):
        """
        Handle click op een cel. Als het een gekoppelde transactie betreft
        (kolom 3 = Naam) en de gebruiker klikt op de 🔗, toon de gekoppelde transactie.
        """
        if col != 3:  # Alleen kolom "Naam"
            return

        item = self._table.item(row, col)
        if not item:
            return

        # Check of dit een linked transactie is (heeft UserRole data)
        trans_id = item.data(Qt.UserRole)
        if trans_id is None:
            return  # Geen linked transactie

        # Vraag de gekoppelde transactie info op
        self._linked_info_pending = trans_id
        self._viewmodel.get_linked_transaction_info(trans_id)

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

        menu.addSeparator()

        # Link/ unlink actie
        linked_id = transaction.get("linked_transaction_id")
        # Check voor None EN NaN (pandas leest SQLite NULL als NaN)
        has_link = linked_id is not None and str(linked_id) != "nan"
        if has_link:
            # Toon info over gekoppelde transactie
            info_action = menu.addAction("🔗 Gekoppelde transactie bekijken")
            info_action.triggered.connect(
                lambda: self._show_linked_transaction(transaction["id"])
            )
            # Optie om koppeling te verwijderen
            unlink_action = menu.addAction("🔗 Koppeling verwijderen")
            unlink_action.triggered.connect(
                lambda: self._viewmodel.unlink_transaction(transaction["id"])
            )
        else:
            link_action = menu.addAction("🔗 Transacties koppelen...")
            link_action.triggered.connect(lambda: self._open_link_dialog(transaction))

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

    def _open_link_dialog(self, transaction):
        """
        Open de dialoog voor het koppelen van transacties.

        Args:
            transaction: Dict met transactie data
        """
        self._link_dialog = LinkTransactionsDialog(transaction, self._viewmodel, self)
        self._link_dialog.exec()
        self._link_dialog = None  # Cleanup after dialog closes

    def _on_potential_links_found(self, matches):
        """Handle potential links found van ViewModel."""
        if hasattr(self, "_link_dialog") and self._link_dialog:
            self._link_dialog.update_matches(matches)

    def _on_link_completed(self, trans_id_1, trans_id_2):
        """Handle link completed van ViewModel."""
        logger.info("Transacties gekoppeld: %d <-> %d", trans_id_1, trans_id_2)
        if hasattr(self, "_link_dialog") and self._link_dialog:
            self._link_dialog.accept()
        QMessageBox.information(self, "Gekoppeld", f"Transacties zijn nu gekoppeld.")
        self._viewmodel.refresh()

    def _on_unlink_completed(self, transaction_id):
        """Handle unlink completed van ViewModel."""
        logger.info("Transactie ontkoppeld: %d", transaction_id)
        QMessageBox.information(self, "Ontkoppeld", f"De koppeling is verwijderd.")
        self._viewmodel.refresh()

    def _on_linked_info_loaded(self, info):
        """Handle linked info geladen van ViewModel."""
        if self._linked_info_pending is None:
            return

        trans_id = self._linked_info_pending
        self._linked_info_pending = None

        if info is None:
            QMessageBox.information(
                self, "Gekoppeld", "Geen gekoppelde transactie gevonden."
            )
            return

        # Highlight de gekoppelde transactie in de tabel
        self._scroll_to_transaction(info["id"])
        QMessageBox.information(
            self, "Gekoppelde transactie", f"Gekoppeld aan: {info['info']}"
        )

    def _show_linked_transaction(self, transaction_id):
        """Toon de gekoppelde transactie info en scroll ernaar."""
        self._linked_info_pending = transaction_id
        self._viewmodel.get_linked_transaction_info(transaction_id)

    def _scroll_to_transaction(self, transaction_id):
        """Scroll de tabel naar de transactie met het gegeven ID en selecteer deze."""
        # Zoek de rij met dit transaction_id
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.UserRole) == transaction_id:
                self._table.selectRow(row)
                self._table.scrollToItem(item, QAbstractItemView.PositionAtCenter)
                return

        # Niet gevonden in huidige pagina - laad opnieuw met filter
        # (zou eigenlijk de juiste pagina moeten laden)
        logger.info("Transactie %d niet op huidige pagina", transaction_id)


class LinkTransactionsDialog(QDialog):
    """
    Dialoog voor het koppelen van transacties.

    Toont de geselecteerde transactie en zoekt automatisch naar
    potentiële matches (tegenovergesteld bedrag, zelfde rekening, etc.)
    """

    def __init__(self, transaction, viewmodel, parent=None):
        """
        Initialiseer de LinkTransactionsDialog.

        Args:
            transaction: Dict met transactie data van de eerste transactie
            viewmodel: TransactionsViewModel instantie
            parent: Parent widget
        """
        super().__init__(parent)
        self._transaction = transaction
        self._viewmodel = viewmodel
        self._selected_match_id = None
        self._matches = []
        self._setup_ui()
        # Direct connect - signal comes directly to dialog, not via View
        viewmodel.potential_links_found.connect(self.update_matches)
        self._search_matches()

    def _setup_ui(self):
        """Bouw de UI op."""
        self.setWindowTitle("Transacties koppelen")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Originele transactie info
        info_group = QGroupBox("Transactie om te koppelen")
        info_layout = QFormLayout(info_group)

        def safe_str(val, default="-"):
            """Converteer waarde naar string, vervang None/NaN door default."""
            if val is None or (isinstance(val, float) and str(val) == "nan"):
                return default
            return str(val)

        self._orig_datum = QLabel(safe_str(self._transaction.get("datum")))
        self._orig_bedrag = QLabel(f"€{self._transaction.get('bedrag', 0):,.2f}")
        self._orig_naam = QLabel(safe_str(self._transaction.get("naam")))
        self._orig_omschrijving = QLabel(
            safe_str(self._transaction.get("omschrijving"))
        )

        info_layout.addRow("Datum:", self._orig_datum)
        info_layout.addRow("Bedrag:", self._orig_bedrag)
        info_layout.addRow("Naam:", self._orig_naam)
        info_layout.addRow("Omschrijving:", self._orig_omschrijving)

        layout.addWidget(info_group)

        # Zoekopties
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Zoeken binnen (dagen):"))
        self._days_spin = QSpinBox()
        self._days_spin.setMinimum(1)
        self._days_spin.setMaximum(365)
        self._days_spin.setValue(90)
        options_layout.addWidget(self._days_spin)

        self._search_btn = QPushButton("Opnieuw zoeken")
        self._search_btn.clicked.connect(self._search_matches)
        options_layout.addWidget(self._search_btn)
        options_layout.addStretch()

        layout.addLayout(options_layout)

        # Matches tabel
        matches_group = QGroupBox("Gevonden potentiële matches")
        matches_layout = QVBoxLayout(matches_group)

        self._matches_table = QTableWidget()
        self._matches_table.setObjectName("matches_table")
        self._matches_table.setColumnCount(5)
        self._matches_table.setHorizontalHeaderLabels(
            ["Datum", "Bedrag", "Naam", "Omschrijving", "Status"]
        )
        self._matches_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._matches_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._matches_table.setAlternatingRowColors(True)
        header = self._matches_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        self._matches_table.setColumnWidth(0, 90)
        self._matches_table.setColumnWidth(1, 100)
        self._matches_table.setColumnWidth(2, 120)
        self._matches_table.setColumnWidth(4, 100)
        self._matches_table.itemSelectionChanged.connect(self._on_match_selected)
        matches_layout.addWidget(self._matches_table)

        layout.addWidget(matches_group)

        # Status label
        self._status_label = QLabel("Zoeken naar matches...")
        layout.addWidget(self._status_label)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        self._ok_btn = button_box.button(QDialogButtonBox.Ok)
        self._ok_btn.setEnabled(False)
        layout.addWidget(button_box)

    def _search_matches(self):
        """Zoek naar potentiële matches."""
        self._status_label.setText("Zoeken naar matches...")
        self._matches_table.setRowCount(0)
        days = self._days_spin.value()
        self._viewmodel.find_potential_links(self._transaction["id"], days=days)

    def update_matches(self, matches):
        """
        Update de matches tabel met gevonden matches.

        Args:
            matches: List van tuples (id, datum, bedrag, naam, omschrijving, already_linked)
        """
        self._matches = matches
        self._matches_table.setUpdatesEnabled(False)
        self._matches_table.setRowCount(len(matches))

        for row, match in enumerate(matches):
            match_id, datum, bedrag, naam, omschrijving, already_linked = match

            self._matches_table.setItem(row, 0, QTableWidgetItem(str(datum)))
            self._matches_table.setItem(row, 1, QTableWidgetItem(f"€{bedrag:,.2f}"))
            self._matches_table.setItem(row, 2, QTableWidgetItem(str(naam)))
            self._matches_table.setItem(row, 3, QTableWidgetItem(str(omschrijving)))

            status_item = QTableWidgetItem()
            if already_linked:
                status_item.setText("Reeds gekoppeld")
                status_item.setForeground(Qt.gray)
            else:
                status_item.setText("Koppelen")
                status_item.setForeground(Qt.darkGreen)
            self._matches_table.setItem(row, 4, status_item)

        self._matches_table.setUpdatesEnabled(True)

        if matches:
            self._status_label.setText(f"{len(matches)} potentiële match(es) gevonden")
        else:
            self._status_label.setText(
                "Geen matches gevonden. De tegenrekening is mogelijk van een andere rekening."
            )

    def _on_match_selected(self):
        """Handle match geselecteerd in de tabel."""
        selected = self._matches_table.selectedItems()
        if selected:
            row = selected[0].row()
            if row < len(self._matches):
                self._selected_match_id = self._matches[row][0]
                self._ok_btn.setEnabled(True)
                return
        self._selected_match_id = None
        self._ok_btn.setEnabled(False)

    def _on_accept(self):
        """Handle accept - koppel de transacties."""
        if self._selected_match_id:
            self._viewmodel.link_transactions(
                self._transaction["id"], self._selected_match_id
            )
            self.accept()
