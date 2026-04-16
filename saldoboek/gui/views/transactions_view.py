"""TransactionsView - Toon en beheer transacties met paginering"""

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Aantal transacties per pagina
PAGE_SIZE = 100


class TransactionsLoader(QThread):
    """Thread voor laden van transacties uit database."""

    finished = Signal(object)  # DataFrame met transacties
    error = Signal(str)  # Error message
    count_updated = Signal(int)  # Totaal aantal

    def __init__(self, transaction_service, filters=None):
        super().__init__()
        self._service = transaction_service
        self._filters = filters or {}

    def run(self):
        """Voer de query uit in de achtergrondthread."""
        try:
            # Haal alleen het totaal op voor de paginering
            df = self._service.get_transactions(filters=self._filters)
            self.count_updated.emit(len(df) if df is not None else 0)
            self.finished.emit(df)
        except Exception as e:
            self.error.emit(str(e))


class TransactionsView(QWidget):
    """View voor het tonen en beheren van transacties met paginering."""

    transaction_selected = Signal(int)
    category_change_requested = Signal(int, str)

    def __init__(self, transaction_service, parent=None):
        super().__init__(parent)
        self._transaction_service = transaction_service
        self._current_filters = {}
        self._all_transactions = []  # Alle transacties (gefilt)
        self._current_page = 0
        self._total_count = 0
        self._loader = None
        self._setup_ui()
        self._setup_table()

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
        self._refresh_btn.clicked.connect(self.refresh)
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
        self._prev_btn.clicked.connect(self._prev_page)
        pagination_layout.addWidget(self._prev_btn)

        # Page indicator
        self._page_label = QLabel("Geen data")
        self._page_label.setObjectName("page_label")
        self._page_label.setAlignment(Qt.AlignCenter)
        pagination_layout.addWidget(self._page_label)

        # Next button
        self._next_btn = QPushButton("Volgende ▶")
        self._next_btn.setObjectName("next_button")
        self._next_btn.clicked.connect(self._next_page)
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
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            [
                "Datum",
                "Rekening",
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
        layout.addWidget(self._table)

        # Initial state
        self._update_pagination_buttons()

    def _setup_table(self):
        """Configureer de tabel eigenschappen."""
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

    def load_transactions(self, filters=None):
        """Laad alle transacties (filtered) - paginering wordt daarna toegepast."""
        if filters:
            self._current_filters.update(filters)

        # Annuleer vorige loader als die nog draait
        if self._loader is not None and self._loader.isRunning():
            self._loader.quit()

        # Disable refresh button tijdens laden
        self._refresh_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(30)
        self._stats_label.setText("Laden...")

        # Start nieuwe loader thread
        self._loader = TransactionsLoader(
            self._transaction_service, self._current_filters
        )
        self._loader.finished.connect(self._on_load_finished)
        self._loader.error.connect(self._on_load_error)
        self._loader.count_updated.connect(self._on_count_updated)
        self._loader.start()

    def _on_count_updated(self, total_count):
        """Update totaal aantal na laden."""
        self._total_count = total_count
        self._current_page = 0

    def _on_load_finished(self, df):
        """Handle load finished callback."""
        self._progress_bar.setVisible(False)
        self._refresh_btn.setEnabled(True)

        if df is None or df.empty:
            self._all_transactions = []
            self._current_page = 0
            self._total_count = 0
        else:
            self._all_transactions = df.to_dict("records")
            self._current_page = 0

        # Toon eerste pagina
        self._show_page()

    def _on_load_error(self, error_msg):
        """Handle load error callback."""
        self._progress_bar.setVisible(False)
        self._refresh_btn.setEnabled(True)
        self._stats_label.setText(f"Fout bij laden: {error_msg}")

    def _show_page(self):
        """Toon de huidige pagina van transacties."""
        total_pages = max(1, (len(self._all_transactions) + PAGE_SIZE - 1) // PAGE_SIZE)

        # Clamp current page
        if self._current_page >= total_pages:
            self._current_page = total_pages - 1
        if self._current_page < 0:
            self._current_page = 0

        # Bereken start en end indices
        start_idx = self._current_page * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, len(self._all_transactions))

        # Get page data
        page_data = self._all_transactions[start_idx:end_idx]

        # Populate table
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(len(page_data))

        for row, trans in enumerate(page_data):
            # Datum
            datum_item = QTableWidgetItem(str(trans.get("datum", "")))
            datum_item.setData(Qt.UserRole, trans.get("id"))
            self._table.setItem(row, 0, datum_item)

            # Rekening
            rekening = str(trans.get("rekening", ""))
            self._table.setItem(row, 1, QTableWidgetItem(rekening))

            # Naam
            self._table.setItem(row, 2, QTableWidgetItem(str(trans.get("naam", ""))))

            # Omschrijving
            self._table.setItem(
                row, 3, QTableWidgetItem(str(trans.get("omschrijving", "")))
            )

            # Bedrag
            bedrag = trans.get("bedrag", 0)
            bedrag_item = QTableWidgetItem(f"€{bedrag:,.2f}")
            if bedrag < 0:
                bedrag_item.setForeground(Qt.red)
            else:
                bedrag_item.setForeground(Qt.darkGreen)
            self._table.setItem(row, 4, bedrag_item)

            # Saldo
            saldo = trans.get("saldo_voor", 0)
            self._table.setItem(row, 5, QTableWidgetItem(f"€{saldo:,.2f}"))

            # Categorie
            categorie = str(trans.get("categorie", "Ongecategoriseerd"))
            categorie_item = QTableWidgetItem(categorie)
            if categorie == "Ongecategoriseerd":
                categorie_item.setForeground(Qt.gray)
            self._table.setItem(row, 6, categorie_item)

        self._table.setUpdatesEnabled(True)

        # Update pagination controls
        self._update_pagination_controls(total_pages)

        # Update stats
        self._update_stats()

    def _update_pagination_controls(self, total_pages):
        """Update paginering controls."""
        if not self._all_transactions:
            self._page_label.setText("Geen transacties")
            self._prev_btn.setEnabled(False)
            self._next_btn.setEnabled(False)
            return

        start_idx = self._current_page * PAGE_SIZE + 1
        end_idx = min((self._current_page + 1) * PAGE_SIZE, len(self._all_transactions))

        self._page_label.setText(
            f"Transacties {start_idx}-{end_idx} van {len(self._all_transactions)} (Pagina {self._current_page + 1} van {total_pages})"
        )

        self._prev_btn.setEnabled(self._current_page > 0)
        self._next_btn.setEnabled(self._current_page < total_pages - 1)

    def _update_pagination_buttons(self):
        """Initiele pagination button state."""
        self._prev_btn.setEnabled(False)
        self._next_btn.setEnabled(False)
        self._page_label.setText("Geen data")

    def _prev_page(self):
        """Ga naar vorige pagina."""
        if self._current_page > 0:
            self._current_page -= 1
            self._show_page()

    def _next_page(self):
        """Ga naar volgende pagina."""
        total_pages = (len(self._all_transactions) + PAGE_SIZE - 1) // PAGE_SIZE
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._show_page()

    def _update_stats(self):
        """Update de statistieken balk."""
        if not self._all_transactions:
            return

        # Bereken stats voor huidige pagina
        start_idx = self._current_page * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, len(self._all_transactions))
        page_data = self._all_transactions[start_idx:end_idx]

        total_in = sum(t.get("bedrag", 0) for t in page_data if t.get("bedrag", 0) > 0)
        total_out = sum(t.get("bedrag", 0) for t in page_data if t.get("bedrag", 0) < 0)

        self._stats_label.setText(
            f"Pagina: €{total_in:,.2f} in | €{abs(total_out):,.2f} uit"
        )

    def refresh(self):
        """Vernieuw de transacties (herlaad alles)."""
        self._stats_label.setText("Laden...")
        self.load_transactions()

    def _on_filter_changed(self):
        """Handle filter wijzigingen."""
        self._current_filters = {}

        # Year
        year_text = self._year_combo.currentText()
        if year_text and year_text != "Alle":
            self._current_filters["jaar"] = int(year_text)

        # Month
        month_index = self._month_combo.currentIndex()
        if month_index > 0:
            self._current_filters["maand"] = month_index

        # Category
        category_text = self._category_combo.currentText()
        if category_text and category_text != "Alle":
            self._current_filters["categorie"] = category_text

        # Search
        search_text = self._search_input.text().strip()
        if search_text:
            self._current_filters["zoek"] = search_text

        self.load_transactions()

    def populate_filter_options(self, years, categories):
        """Vul de filter opties met beschikbare waarden."""
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
