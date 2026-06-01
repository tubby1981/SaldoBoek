"""UncategorizedView - View voor het categoriseren van ongecategoriseerde transacties."""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class CategorizeDialog(QDialog):
    """Dialoog voor het categoriseren van een enkele transactie."""

    categorized = Signal(str, str)  # categorie, (optioneel) zoekterm
    skip = Signal()
    previous = Signal()
    next = Signal()

    def __init__(
        self, transaction, categories, current_index, total_count, parent=None
    ):
        """
        Initialiseer CategorizeDialog.

        Args:
            transaction: Dict met transactie data
            categories: List van categorie tuples (naam, type, beschrijving)
            current_index: Huidige index in de lijst
            total_count: Totaal aantal ongecategoriseerde transacties
            parent: Parent widget
        """
        super().__init__(parent)
        self._transaction = transaction
        self._categories = categories
        self._current_index = current_index
        self._total_count = total_count
        self._selected_categories = [
            c
            for c in categories
            if c[1] == ("inkomsten" if transaction.get("bedrag", 0) > 0 else "uitgaven")
        ]
        self._setup_ui()
        self._populate_data()

    def _setup_ui(self):
        """Bouwt de UI op."""
        self.setWindowTitle(
            f"Transactie Categoriseren ({self._current_index + 1}/{self._total_count})"
        )
        self.setMinimumSize(500, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header met navigatie info
        header = QLabel(f"Transactie {self._current_index + 1} van {self._total_count}")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Transactie details frame
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        details_layout.setSpacing(5)

        # Datum
        datum = self._transaction.get("datum", "")
        if datum:
            datum_str = str(datum)[:10]  # YYYY-MM-DD format
        else:
            datum_str = "-"
        details_layout.addWidget(QLabel(f"<b>Datum:</b> {datum_str}"))

        # Rekening
        rekening = self._transaction.get("rekening", "")
        if rekening and str(rekening) not in ("", "nan", "None"):
            rekening_str = str(rekening)
            display_rekening = (
                rekening_str[-4:] if len(rekening_str) >= 4 else rekening_str
            )
            details_layout.addWidget(QLabel(f"<b>Rekening:</b> {display_rekening}"))
        else:
            details_layout.addWidget(QLabel(f"<b>Rekening:</b> -"))

        # Tegenrekening
        tegenrekening = self._transaction.get("tegenrekening", "")
        if tegenrekening and str(tegenrekening) not in ("", "nan", "None"):
            details_layout.addWidget(QLabel(f"<b>Tegenrekening:</b> {tegenrekening}"))

        # Naam (selecteerbaar)
        naam = self._transaction.get("naam", "")
        naam_str = str(naam) if naam and str(naam) not in ("nan", "None", "") else "-"
        details_layout.addWidget(QLabel("<b>Naam:</b>"))
        self._naam_text = QTextEdit(naam_str)
        self._naam_text.setReadOnly(True)
        self._naam_text.setMaximumHeight(40)
        self._naam_text.textChanged.connect(self._on_selection_changed)
        details_layout.addWidget(self._naam_text)

        # Omschrijving (selecteerbaar)
        omschrijving = self._transaction.get("omschrijving", "")
        omschrijving_str = (
            str(omschrijving)
            if omschrijving and str(omschrijving) not in ("nan", "None", "")
            else "-"
        )
        details_layout.addWidget(QLabel("<b>Omschrijving:</b>"))
        self._omschrijving_text = QTextEdit(omschrijving_str)
        self._omschrijving_text.setReadOnly(True)
        self._omschrijving_text.setMaximumHeight(60)
        self._omschrijving_text.textChanged.connect(self._on_selection_changed)
        details_layout.addWidget(self._omschrijving_text)

        # Bedrag
        bedrag = self._transaction.get("bedrag", 0)
        bedrag_label = QLabel(f"<b>Bedrag:</b> €{bedrag:,.2f}")
        if bedrag < 0:
            bedrag_label.setStyleSheet("color: red;")
        else:
            bedrag_label.setStyleSheet("color: darkgreen;")
        details_layout.addWidget(bedrag_label)

        layout.addWidget(details_frame)

        # Categorie dropdown
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("<b>Categorie:</b>"))
        self._cat_combo = QComboBox()
        self._cat_combo.setMinimumWidth(200)
        for cat_naam, cat_type, cat_desc in self._selected_categories:
            display = f"{cat_naam} ({cat_type})"
            self._cat_combo.addItem(display, cat_naam)
        cat_layout.addWidget(self._cat_combo)
        cat_layout.addStretch()
        layout.addLayout(cat_layout)

        # Regel toevoegen optie
        rule_frame = QFrame()
        rule_layout = QHBoxLayout(rule_frame)

        self._add_rule_check = QCheckBox("Regel toevoegen:")
        self._add_rule_check.setChecked(False)
        self._add_rule_check.toggled.connect(self._on_rule_check_toggled)
        rule_layout.addWidget(self._add_rule_check)

        self._rule_input = QLineEdit()
        self._rule_input.setPlaceholderText("zoekterm invoeren...")
        self._rule_input.setEnabled(False)
        self._rule_input.setMinimumWidth(200)
        rule_layout.addWidget(self._rule_input)

        self._use_selection_btn = QPushButton("Selectie gebruiken")
        self._use_selection_btn.setEnabled(False)
        self._use_selection_btn.clicked.connect(self._on_use_selection)
        rule_layout.addWidget(self._use_selection_btn)

        rule_layout.addStretch()
        layout.addWidget(rule_frame)

        layout.addStretch()

        # Navigation buttons
        nav_layout = QHBoxLayout()

        self._prev_btn = QPushButton("◀ Vorige")
        self._prev_btn.clicked.connect(self._on_previous)
        if self._current_index == 0:
            self._prev_btn.setEnabled(False)
        nav_layout.addWidget(self._prev_btn)

        self._skip_btn = QPushButton("Overslaan")
        self._skip_btn.clicked.connect(self._on_skip)
        nav_layout.addWidget(self._skip_btn)

        self._save_btn = QPushButton("Opslaan")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_save)
        nav_layout.addWidget(self._save_btn)

        self._next_btn = QPushButton("Volgende ▶")
        self._next_btn.clicked.connect(self._on_next)
        if self._current_index >= self._total_count - 1:
            self._next_btn.setEnabled(False)
        nav_layout.addWidget(self._next_btn)

        layout.addLayout(nav_layout)

    def _populate_data(self):
        """Vul de UI met data."""
        # Pre-selecteer een categorie als die al bekend is
        pass

    def _on_rule_check_toggled(self, checked):
        """Handle rule checkbox toggle."""
        self._rule_input.setEnabled(checked)
        self._use_selection_btn.setEnabled(checked)
        if checked:
            self._rule_input.setFocus()
            self._on_selection_changed()

    def _on_previous(self):
        """Handle vorige button."""
        self.previous.emit()

    def _on_skip(self):
        """Handle overslaan button."""
        self.skip.emit()

    def _on_save(self):
        """Handle opslaan button."""
        categorie = self._cat_combo.currentData()
        if not categorie:
            QMessageBox.warning(self, "Geen Categorie", "Selecteer een categorie.")
            return

        if self._add_rule_check.isChecked():
            zoekterm = self._rule_input.text().strip()
            if zoekterm:
                self.categorized.emit(categorie, zoekterm)
            else:
                self.categorized.emit(categorie, "")
        else:
            self.categorized.emit(categorie, "")

    def _on_selection_changed(self):
        """Handle text selection in naam/omschrijving velden."""
        if not self._add_rule_check.isChecked():
            self._use_selection_btn.setEnabled(False)
            return

        # Check both fields for selected text
        selected = ""
        if self._naam_text.textCursor().hasSelection():
            selected = self._naam_text.textCursor().selectedText()
        elif self._omschrijving_text.textCursor().hasSelection():
            selected = self._omschrijving_text.textCursor().selectedText()

        self._use_selection_btn.setEnabled(bool(selected))

    def _on_use_selection(self):
        """Use selected text from naam/omschrijving as search term."""
        selected = ""
        if self._naam_text.textCursor().hasSelection():
            selected = self._naam_text.textCursor().selectedText()
        elif self._omschrijving_text.textCursor().hasSelection():
            selected = self._omschrijving_text.textCursor().selectedText()

        if selected:
            self._rule_input.setText(selected)
            self._rule_input.setFocus()

    def _on_next(self):
        """Handle volgende button."""
        self.next.emit()


class EditCategoryDialog(QDialog):
    """
    Dialoog voor het bewerken van de categorie van een bestaande transactie.

    Toont transactie details en een dropdown om de categorie te wijzigen.
    """

    saved = Signal(
        int, str, list, str
    )  # transaction_id, nieuwe_categorie, similar_ids, rule_zoekterm

    def __init__(self, transaction, categories, similar_transactions=None, parent=None):
        """
        Initialiseer EditCategoryDialog.

        Args:
            transaction: Dict met transactie data
            categories: List van categorie tuples (naam, type, beschrijving)
            similar_transactions: DataFrame met vergelijkbare transacties of None
            parent: Parent widget
        """
        super().__init__(parent)
        self._transaction = transaction
        self._categories = categories
        self._transaction_id = transaction.get("id")
        self._current_category = transaction.get("categorie", "")
        self._similar_transactions = similar_transactions
        self._similar_ids = []
        if similar_transactions is not None and not similar_transactions.empty:
            self._similar_ids = similar_transactions["id"].tolist()
        self._setup_ui()
        self._populate_data()

    def _setup_ui(self):
        """Bouwt de UI op."""
        self.setWindowTitle("Bewerk Categorie")
        self.setMinimumSize(450, 350)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Transactie details frame
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        details_layout.setSpacing(5)

        # Datum
        datum = self._transaction.get("datum", "")
        datum_str = str(datum)[:10] if datum else "-"
        details_layout.addWidget(QLabel(f"<b>Datum:</b> {datum_str}"))

        # Naam
        naam = self._transaction.get("naam", "")
        naam_str = str(naam) if naam and str(naam) not in ("nan", "None", "") else "-"
        details_layout.addWidget(QLabel(f"<b>Naam:</b> {naam_str}"))

        # Omschrijving
        omschrijving = self._transaction.get("omschrijving", "")
        omschrijving_str = (
            str(omschrijving)
            if omschrijving and str(omschrijving) not in ("nan", "None", "")
            else "-"
        )
        details_layout.addWidget(QLabel(f"<b>Omschrijving:</b> {omschrijving_str}"))

        # Bedrag
        bedrag = self._transaction.get("bedrag", 0)
        bedrag_label = QLabel(f"<b>Bedrag:</b> €{bedrag:,.2f}")
        if bedrag < 0:
            bedrag_label.setStyleSheet("color: red;")
        else:
            bedrag_label.setStyleSheet("color: darkgreen;")
        details_layout.addWidget(bedrag_label)

        # Huidige categorie
        details_layout.addWidget(
            QLabel(f"<b>Huidige categorie:</b> {self._current_category}")
        )

        layout.addWidget(details_frame)

        # Categorie dropdown - filter op type (inkomsten/uitgaven)
        cat_type = "inkomsten" if bedrag > 0 else "uitgaven"
        self._selected_categories = [c for c in self._categories if c[1] == cat_type]

        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("<b>Nieuwe categorie:</b>"))
        self._cat_combo = QComboBox()
        self._cat_combo.setMinimumWidth(200)
        for cat_naam, cat_type, cat_desc in self._selected_categories:
            display = f"{cat_naam} ({cat_type})"
            self._cat_combo.addItem(display, cat_naam)
        cat_layout.addWidget(self._cat_combo)
        cat_layout.addStretch()
        layout.addLayout(cat_layout)

        # Regel toevoegen optie (voor automatische toekomstige categorisatie)
        rule_frame = QFrame()
        rule_layout = QHBoxLayout(rule_frame)

        self._add_rule_check = QCheckBox("Regel toevoegen:")
        self._add_rule_check.setChecked(False)
        self._add_rule_check.toggled.connect(self._on_rule_check_toggled)
        rule_layout.addWidget(self._add_rule_check)

        self._rule_input = QLineEdit()
        self._rule_input.setPlaceholderText("zoekterm invoeren...")
        self._rule_input.setEnabled(False)
        self._rule_input.setMinimumWidth(200)
        rule_layout.addWidget(self._rule_input)

        self._use_selection_btn = QPushButton("Selectie gebruiken")
        self._use_selection_btn.setEnabled(False)
        self._use_selection_btn.clicked.connect(self._on_use_selection)
        rule_layout.addWidget(self._use_selection_btn)

        rule_layout.addStretch()
        layout.addWidget(rule_frame)

        # Optie voor vergelijkbare transacties
        if self._similar_ids:
            self._apply_similar_check = QCheckBox(
                f"Pas ook toe op {len(self._similar_ids)} vergelijkbare transacties"
            )
            self._apply_similar_check.setChecked(False)
            self._apply_similar_check.toggled.connect(self._on_similar_check_toggled)
            layout.addWidget(self._apply_similar_check)

            # Info over vergelijkbare transacties
            self._similar_info_label = QLabel("")
            self._similar_info_label.setStyleSheet("color: gray; font-size: 10px;")
            self._similar_info_label.setWordWrap(True)
            layout.addWidget(self._similar_info_label)
            self._update_similar_info()
        else:
            self._apply_similar_check = None
            self._similar_info_label = None

        # Info label
        info_label = QLabel("Selecteer een nieuwe categorie en klik Opslaan.")
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Annuleren")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        self._save_btn = QPushButton("Opslaan")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self._save_btn)

        layout.addLayout(button_layout)

    def _populate_data(self):
        """Vul de UI met data."""
        # Pre-selecteer de huidige categorie
        for i in range(self._cat_combo.count()):
            if self._cat_combo.itemData(i) == self._current_category:
                self._cat_combo.setCurrentIndex(i)
                break

    def _on_rule_check_toggled(self, checked):
        """Handle rule checkbox toggle."""
        self._rule_input.setEnabled(checked)
        self._use_selection_btn.setEnabled(checked)
        if checked:
            self._rule_input.setFocus()

    def _on_use_selection(self):
        """Use selected text from naam/omschrijving as search term."""
        # Use de naam als zoekterm (is meestal het meest karakteristieke)
        naam = self._transaction.get("naam", "")
        if naam and str(naam) not in ("nan", "None", ""):
            self._rule_input.setText(str(naam))
            self._rule_input.setFocus()

    def _on_similar_check_toggled(self, checked):
        """Handle similar checkbox toggle."""
        self._update_similar_info()

    def _update_similar_info(self):
        """Update info over geselecteerde vergelijkbare transacties."""
        if not self._similar_info_label:
            return

        if self._apply_similar_check and self._apply_similar_check.isChecked():
            if (
                self._similar_transactions is not None
                and not self._similar_transactions.empty
            ):
                # Toon eerste 3 namen als preview
                names = self._similar_transactions["naam"].head(3).tolist()
                names_str = ", ".join(str(n)[:20] for n in names)
                if len(self._similar_ids) > 3:
                    names_str += f"... (+{len(self._similar_ids) - 3} meer)"
                self._similar_info_label.setText(f"Worden ook bijgewerkt: {names_str}")
            else:
                self._similar_info_label.setText("")
        else:
            self._similar_info_label.setText("")

    def _on_save(self):
        """Handle opslaan button."""
        new_category = self._cat_combo.currentData()
        if not new_category:
            QMessageBox.warning(self, "Geen Categorie", "Selecteer een categorie.")
            return

        # Check of we vergelijkbare transacties ook moeten bijwerken
        apply_to_similar = (
            self._apply_similar_check is not None
            and self._apply_similar_check.isChecked()
            and self._similar_ids
        )

        if apply_to_similar:
            reply = QMessageBox.question(
                self,
                "Bevestig",
                f"Weet je zeker dat je de categorie '{new_category}' wilt toepassen "
                f"op {len(self._similar_ids) + 1} transacties?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        similar_ids_to_update = self._similar_ids if apply_to_similar else []

        # Check of er een regel moet worden toegevoegd
        rule_zoekterm = ""
        if self._add_rule_check.isChecked():
            rule_zoekterm = self._rule_input.text().strip()

        self.saved.emit(
            self._transaction_id, new_category, similar_ids_to_update, rule_zoekterm
        )
        self.accept()


class UncategorizedView(QWidget):
    """
    View voor het tonen en categoriseren van ongecategoriseerde transacties.

    Deze view ontvangt data via de ViewModel en stuurt gebruikersacties
    door naar de ViewModel.
    """

    # Signal for when categorization is complete
    categorization_completed = Signal()

    def __init__(self, viewmodel, parent=None):
        """
        Initialiseer UncategorizedView.

        Args:
            viewmodel: UncategorizedViewModel instantie
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._dialog = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)

        title = QLabel("Ongecategoriseerde Transacties")
        title.setObjectName("view_title")
        header_layout.addWidget(title)

        self._count_label = QLabel("")
        self._count_label.setObjectName("count_label")
        header_layout.addWidget(self._count_label)

        header_layout.addStretch()

        # Refresh button
        self._refresh_btn = QPushButton("🔄 Verversen")
        self._refresh_btn.setObjectName("refresh_button")
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self._refresh_btn)

        layout.addWidget(header)

        # Table
        self._table = QTableWidget()
        self._table.setObjectName("uncategorized_table")
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Datum", "Tegenrekening", "Naam", "Omschrijving", "Bedrag", "Categorie"]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.itemDoubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self._table)

        # Action buttons
        action_layout = QHBoxLayout()

        self._categorize_btn = QPushButton("🔗 Categoriseren")
        self._categorize_btn.setObjectName("categorize_button")
        self._categorize_btn.clicked.connect(self._on_categorize_clicked)
        action_layout.addWidget(self._categorize_btn)

        self._categorize_all_btn = QPushButton("🔄 Alles Hercategoriseren")
        self._categorize_all_btn.setObjectName("categorize_all_button")
        self._categorize_all_btn.clicked.connect(self._on_categorize_all_clicked)
        action_layout.addWidget(self._categorize_all_btn)

        action_layout.addStretch()

        self._status_label = QLabel("")
        self._status_label.setObjectName("status_label")
        action_layout.addWidget(self._status_label)

        layout.addLayout(action_layout)

    def _connect_signals(self):
        """Verbind signals van de ViewModel met slots in de View."""
        self._viewmodel.transactions_loaded.connect(self._on_transactions_loaded)
        self._viewmodel.current_transaction_changed.connect(
            self._on_current_transaction_changed
        )
        self._viewmodel.categories_loaded.connect(self._on_categories_loaded)
        self._viewmodel.loading_started.connect(self._on_loading_started)
        self._viewmodel.loading_finished.connect(self._on_loading_finished)
        self._viewmodel.error_occurred.connect(self._on_error)
        self._viewmodel.transaction_categorized.connect(
            self._on_transaction_categorized
        )

    # ViewModel signal handlers

    def _on_transactions_loaded(self, transactions):
        """Handle transacties geladen van ViewModel."""
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(len(transactions))

        for row, trans in enumerate(transactions):
            # Datum
            self._table.setItem(row, 0, QTableWidgetItem(str(trans.get("datum", ""))))

            # Tegenrekening
            tegenrekening = str(trans.get("tegenrekening", ""))
            if tegenrekening and tegenrekening not in ("", "nan", "None"):
                display_tegen = tegenrekening
            else:
                display_tegen = "-"
            self._table.setItem(row, 1, QTableWidgetItem(display_tegen))

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

            # Categorie (altijd Ongecategoriseerd)
            categorie_item = QTableWidgetItem("Ongecategoriseerd")
            categorie_item.setForeground(Qt.gray)
            self._table.setItem(row, 5, categorie_item)

        # Resize columns - Interactive allows user to resize with mouse
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        # Set initial reasonable widths
        self._table.setColumnWidth(0, 100)  # Datum
        self._table.setColumnWidth(1, 130)  # Tegenrekening
        self._table.setColumnWidth(2, 150)  # Naam
        self._table.setColumnWidth(3, 220)  # Omschrijving
        self._table.setColumnWidth(4, 100)  # Bedrag
        self._table.setColumnWidth(5, 120)  # Categorie

        self._table.setUpdatesEnabled(True)

        # Update count
        self._count_label.setText(f"{len(transactions)} transacties")

        if not transactions:
            self._status_label.setText("Alle transacties zijn gecategoriseerd!")
            self._categorize_btn.setEnabled(False)
        else:
            self._status_label.setText("")
            self._categorize_btn.setEnabled(True)

    def _on_current_transaction_changed(self, transaction):
        """Handle huidige transactie veranderd."""
        pass  # Kan gebruikt worden voor status updates

    def _on_categories_loaded(self, categories):
        """Handle categorieën geladen."""
        self._categories = categories

    def _on_loading_started(self):
        """Handle laden gestart."""
        self._refresh_btn.setEnabled(False)
        self._status_label.setText("Laden...")

    def _on_loading_finished(self):
        """Handle laden voltooid."""
        self._refresh_btn.setEnabled(True)

    def _on_error(self, error_msg):
        """Handle error van ViewModel."""
        self._status_label.setText(f"Fout: {error_msg}")
        QMessageBox.warning(self, "Fout", error_msg)

    def _on_transaction_categorized(self, trans_id):
        """Handle transactie succesvol gecategoriseerd."""
        count = self._viewmodel.get_uncategorized_count()
        self._status_label.setText(f"Nog {count} ongecategoriseerd")
        if count == 0:
            self.categorization_completed.emit()

    # User action handlers

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self._viewmodel.refresh()

    def _on_row_double_clicked(self, item):
        """Handle row double click - open dialog."""
        row = item.row()
        self._open_categorize_dialog(row)

    def _on_categorize_clicked(self):
        """Handle categoriseer button click."""
        selected = self._table.currentRow()
        if selected >= 0:
            self._open_categorize_dialog(selected)
        else:
            QMessageBox.information(
                self,
                "Selecteer Transactie",
                "Selecteer een transactie om te categoriseren.",
            )

    def _on_categorize_all_clicked(self):
        """Handle alles hercategoriseren button click."""
        QMessageBox.information(
            self,
            "Alle Transacties",
            "Gebruik de categoriseer knop (Enter) of dubbelklik op een rij om transacties één voor één te categoriseren.",
        )

    def _open_categorize_dialog(self, row):
        """Open de categoriseer dialoog voor een transactie."""
        transactions = self._viewmodel._transactions
        if row < 0 or row >= len(transactions):
            return

        transaction = transactions[row]
        categories = (
            self._viewmodel._categories
        )  # Already tuples: (naam, type, beschrijving)
        current_index = row
        total_count = len(transactions)

        dialog = CategorizeDialog(
            transaction, categories, current_index, total_count, self
        )
        dialog.categorized.connect(self._on_dialog_categorized)
        dialog.skip.connect(self._on_dialog_skip)
        dialog.previous.connect(self._on_dialog_previous)
        dialog.next.connect(self._on_dialog_next)

        self._dialog = dialog
        dialog.exec()
        self._dialog = None

    def _on_dialog_categorized(self, categorie, zoekterm):
        """Handle dialog categorie gekozen."""
        if zoekterm:
            self._viewmodel.add_rule_and_categorize(zoekterm, categorie)
        else:
            self._viewmodel.categorize_current(categorie)

    def _on_dialog_skip(self):
        """Handle dialog overslaan."""
        self._dialog.accept()
        self._viewmodel.skip_current()
        # Open next dialog
        current_index = self._viewmodel.get_current_index()
        if (
            current_index >= 0
            and current_index < self._viewmodel.get_uncategorized_count()
        ):
            self._open_categorize_dialog(current_index)

    def _on_dialog_previous(self):
        """Handle dialog vorige."""
        self._dialog.accept()
        self._viewmodel.previous_transaction()
        # Open previous dialog
        current_index = self._viewmodel.get_current_index()
        self._open_categorize_dialog(current_index)

    def _on_dialog_next(self):
        """Handle dialog volgende."""
        self._dialog.accept()
        self._viewmodel.next_transaction()
        # Open next dialog
        current_index = self._viewmodel.get_current_index()
        if (
            current_index >= 0
            and current_index < self._viewmodel.get_uncategorized_count()
        ):
            self._open_categorize_dialog(current_index)

    # Public methods

    def set_gebruiker_id(self, gebruiker_id):
        """Stel de gebruiker ID in via ViewModel."""
        self._viewmodel.set_gebruiker_id(gebruiker_id)

    def load_uncategorized(self):
        """Laad ongecategoriseerde transacties."""
        self._viewmodel.load_uncategorized()

    def refresh(self):
        """Vernieuw de transacties."""
        self._viewmodel.refresh()
