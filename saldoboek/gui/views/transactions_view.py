"""TransactionsView - Toon en beheer transacties met threading"""

from PySide6.QtCore import QCoreApplication, Qt, QThread, Signal
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


class TransactionsLoader(QThread):
    """Thread voor laden van transacties uit database."""

    finished = Signal(object)  # DataFrame met transacties
    error = Signal(str)  # Error message
    progress = Signal(int)  # Progress percentage

    def __init__(self, transaction_service, filters=None):
        super().__init__()
        self._service = transaction_service
        self._filters = filters or {}

    def run(self):
        """Voer de query uit in de achtergrondthread."""
        try:
            self.progress.emit(10)
            df = self._service.get_transactions(filters=self._filters)
            self.progress.emit(100)
            self.finished.emit(df)
        except Exception as e:
            self.error.emit(str(e))


class TransactionsView(QWidget):
    """View voor het tonen en beheren van transacties."""

    transaction_selected = Signal(int)  # transactie_id
    category_change_requested = Signal(int, str)  # transactie_id, nieuwe_categorie

    def __init__(self, transaction_service, parent=None):
        super().__init__(parent)
        self._transaction_service = transaction_service
        self._current_filters = {}
        self._transactions = []
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
        self._progress_bar.setMaximumWidth(200)
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
        self._search_input.setPlaceholderText("Zoek in omschrijving of naam...")
        self._search_input.textChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self._search_input)

        layout.addWidget(filters_frame)

        # Stats bar
        self._stats_label = QLabel("Geen transacties geladen")
        self._stats_label.setObjectName("stats_label")
        layout.addWidget(self._stats_label)

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

    def _setup_table(self):
        """Configureer de tabel eigenschappen."""
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

    def load_transactions(self, filters=None):
        """Laad transacties met optionele filters (async)."""
        if filters:
            self._current_filters.update(filters)

        # Annuleer vorige loader als die nog draait
        if self._loader is not None and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()

        # Disable refresh button tijdens laden
        self._refresh_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(10)
        self._stats_label.setText("Laden...")

        # Start nieuwe loader thread
        self._loader = TransactionsLoader(
            self._transaction_service, self._current_filters
        )
        self._loader.finished.connect(self._on_load_finished)
        self._loader.error.connect(self._on_load_error)
        self._loader.progress.connect(self._progress_bar.setValue)
        self._loader.start()

    def _on_load_finished(self, df):
        """Handle load finished callback."""
        self._progress_bar.setVisible(False)
        self._refresh_btn.setEnabled(True)

        if df is None or df.empty:
            self._transactions = []
            self._populate_table()
            self._update_stats()
            return

        self._transactions = df.to_dict("records")
        self._populate_table()
        self._update_stats()

    def _on_load_error(self, error_msg):
        """Handle load error callback."""
        self._progress_bar.setVisible(False)
        self._refresh_btn.setEnabled(True)
        self._stats_label.setText(f"Fout bij laden: {error_msg}")

    def refresh(self):
        """Vernieuw de transacties (async)."""
        self.load_transactions()

    def _populate_table(self):
        """Vul de tabel met transacties (in batches voor performance)."""
        total_rows = len(self._transactions)

        # Disable updates tijdens populatie voor betere performance
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(total_rows)

        BATCH_SIZE = 100  # Processeer 100 rijen tegelijk

        for batch_start in range(0, total_rows, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_rows)

            for row in range(batch_start, batch_end):
                trans = self._transactions[row]

                # Datum
                datum_item = QTableWidgetItem(str(trans.get("datum", "")))
                datum_item.setData(Qt.UserRole, trans.get("id"))
                self._table.setItem(row, 0, datum_item)

                # Rekening
                rekening = str(trans.get("rekening", ""))
                self._table.setItem(row, 1, QTableWidgetItem(rekening))

                # Naam
                self._table.setItem(
                    row, 2, QTableWidgetItem(str(trans.get("naam", "")))
                )

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

            # Laat de UI even ademen tussen batches
            QCoreApplication.processEvents()

        # Herinschakelen updates en forceer refresh
        self._table.setUpdatesEnabled(True)

    def _update_stats(self):
        """Update de statistieken balk."""
        count = len(self._transactions)
        if count == 0:
            self._stats_label.setText("Geen transacties gevonden")
            return

        total_in = sum(
            t.get("bedrag", 0) for t in self._transactions if t.get("bedrag", 0) > 0
        )
        total_out = sum(
            t.get("bedrag", 0) for t in self._transactions if t.get("bedrag", 0) < 0
        )

        self._stats_label.setText(
            f"{count} transacties | Totaal in: €{total_in:,.2f} | Totaal uit: €{abs(total_out):,.2f}"
        )

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
