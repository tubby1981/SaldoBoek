"""CategoriesView - Beheer categorieën en regels."""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class AddCategoryDialog(QDialog):
    """Dialoog voor het toevoegen van een nieuwe categorie."""

    category_added = Signal(str, str, str)  # naam, type, beschrijving

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nieuwe Categorie")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Naam
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Naam:"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Bijv. Boodschappen")
        name_layout.addWidget(self._name_input)
        layout.addLayout(name_layout)

        # Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(["uitgaven", "inkomsten"])
        type_layout.addWidget(self._type_combo)
        layout.addLayout(type_layout)

        # Beschrijving
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Beschrijving:"))
        self._desc_input = QLineEdit()
        self._desc_input.setPlaceholderText("Optioneel")
        desc_layout.addWidget(self._desc_input)
        layout.addLayout(desc_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Annuleren")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._add_btn = QPushButton("Toevoegen")
        self._add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self._add_btn)

        layout.addLayout(btn_layout)

    def _on_add(self):
        """Handle add button click."""
        naam = self._name_input.text().strip()
        if not naam:
            self._name_input.setFocus()
            return

        cat_type = self._type_combo.currentText()
        beschrijving = self._desc_input.text().strip()

        self.category_added.emit(naam, cat_type, beschrijving)
        self.accept()


class EditCategoryDialog(QDialog):
    """Dialoog voor het bewerken van een categorie."""

    category_updated = Signal(
        str, str, str, str
    )  # oude_naam, nieuwe_naam, type, beschrijving

    def __init__(self, naam, cat_type, beschrijving, parent=None):
        super().__init__(parent)
        self._oude_naam = naam
        self.setWindowTitle(f"Categorie Bewerken: {naam}")
        self.setMinimumWidth(400)
        self._setup_ui(naam, cat_type, beschrijving)

    def _setup_ui(self, naam, cat_type, beschrijving):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Naam
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Naam:"))
        self._name_input = QLineEdit()
        self._name_input.setText(naam)
        name_layout.addWidget(self._name_input)
        layout.addLayout(name_layout)

        # Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(["uitgaven", "inkomsten"])
        self._type_combo.setCurrentText(cat_type)
        type_layout.addWidget(self._type_combo)
        layout.addLayout(type_layout)

        # Beschrijving
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Beschrijving:"))
        self._desc_input = QLineEdit()
        self._desc_input.setText(beschrijving)
        desc_layout.addWidget(self._desc_input)
        layout.addLayout(desc_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Annuleren")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._save_btn = QPushButton("Opslaan")
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _on_save(self):
        """Handle save button click."""
        nieuwe_naam = self._name_input.text().strip()
        if not nieuwe_naam:
            self._name_input.setFocus()
            return

        cat_type = self._type_combo.currentText()
        beschrijving = self._desc_input.text().strip()

        self.category_updated.emit(self._oude_naam, nieuwe_naam, cat_type, beschrijving)
        self.accept()


class EditRuleDialog(QDialog):
    """Dialoog voor het bewerken van een regel."""

    rule_updated = Signal(
        str, str, str
    )  # oude_zoekterm, nieuwe_zoekterm, nieuwe_categorie

    def __init__(self, oude_zoekterm, oude_categorie, categorie_namen, parent=None):
        super().__init__(parent)
        self._oude_zoekterm = oude_zoekterm
        self.setWindowTitle(f"Regel Bewerken: {oude_zoekterm}")
        self.setMinimumWidth(400)
        self._setup_ui(oude_zoekterm, oude_categorie, categorie_namen)

    def _setup_ui(self, oude_zoekterm, oude_categorie, categorie_namen):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Zoekterm
        term_layout = QHBoxLayout()
        term_layout.addWidget(QLabel("Zoekterm:"))
        self._term_input = QLineEdit()
        self._term_input.setText(oude_zoekterm)
        term_layout.addWidget(self._term_input)
        layout.addLayout(term_layout)

        # Categorie
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Categorie:"))
        self._cat_combo = QComboBox()
        self._cat_combo.addItems(categorie_namen)
        if oude_categorie in categorie_namen:
            self._cat_combo.setCurrentText(oude_categorie)
        cat_layout.addWidget(self._cat_combo)
        layout.addLayout(cat_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Annuleren")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._save_btn = QPushButton("Opslaan")
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _on_save(self):
        """Handle save button click."""
        nieuwe_zoekterm = self._term_input.text().strip()
        if not nieuwe_zoekterm:
            self._term_input.setFocus()
            return

        nieuwe_categorie = self._cat_combo.currentText()

        self.rule_updated.emit(self._oude_zoekterm, nieuwe_zoekterm, nieuwe_categorie)
        self.accept()


class CategoriesView(QWidget):
    """
    View voor het beheren van categorieën en regels.

    Deze view ontvangt data via de ViewModel en stuurt gebruikersacties
    door naar de ViewModel. Alle business logic zit in CategoriesViewModel.
    """

    def __init__(self, viewmodel, parent=None):
        """
        Initialiseer CategoriesView.

        Args:
            viewmodel: CategoriesViewModel instantie
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._editable_categories = set()  # set van bewerkbare categorie namen
        self._editable_rules = set()  # set van bewerkbare zoektermen
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)

        title = QLabel("Categorieën")
        title.setObjectName("view_title")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Refresh button
        self._refresh_btn = QPushButton("🔄 Verversen")
        self._refresh_btn.setObjectName("refresh_button")
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self._refresh_btn)

        layout.addWidget(header)

        # Tabs voor categorieën en regels
        self._tabs = QTabWidget()
        self._tabs.setObjectName("categories_tabs")

        # Tab 1: Categorieën
        categories_tab = QWidget()
        categories_layout = QVBoxLayout(categories_tab)
        categories_layout.setSpacing(10)

        # Stats info
        self._stats_label = QLabel("")
        self._stats_label.setObjectName("stats_label")
        categories_layout.addWidget(self._stats_label)

        # Categories table
        self._categories_table = QTableWidget()
        self._categories_table.setObjectName("categories_table")
        self._categories_table.setColumnCount(5)
        self._categories_table.setHorizontalHeaderLabels(
            ["Categorie", "Type", "Aantal", "Totaal Bedrag", "Acties"]
        )
        self._categories_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._categories_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._categories_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._categories_table.verticalHeader().setVisible(False)
        self._categories_table.setAlternatingRowColors(True)
        categories_layout.addWidget(self._categories_table)

        layout.addWidget(categories_tab)

        # Tab 2: Regels
        rules_tab = QWidget()
        rules_layout = QVBoxLayout(rules_tab)
        rules_layout.setSpacing(10)

        rules_header = QFrame()
        rules_header_layout = QHBoxLayout(rules_header)

        rules_header_layout.addWidget(QLabel("Automatische Categorisatie Regels"))
        rules_header_layout.addStretch()

        self._add_rule_btn = QPushButton("➕ Regel Toevoegen")
        self._add_rule_btn.setObjectName("add_rule_button")
        self._add_rule_btn.clicked.connect(self._show_add_rule_dialog)
        rules_header_layout.addWidget(self._add_rule_btn)

        rules_layout.addWidget(rules_header)

        # Rules table
        self._rules_table = QTableWidget()
        self._rules_table.setObjectName("rules_table")
        self._rules_table.setColumnCount(3)
        self._rules_table.setHorizontalHeaderLabels(["Zoekterm", "Categorie", "Acties"])
        self._rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._rules_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._rules_table.verticalHeader().setVisible(False)
        self._rules_table.setAlternatingRowColors(True)
        rules_layout.addWidget(self._rules_table)

        layout.addWidget(rules_tab)

        self._tabs.addTab(categories_tab, "Categorieën")
        self._tabs.addTab(rules_tab, "Regels")

        layout.addWidget(self._tabs)

        # Add category button
        self._add_cat_btn = QPushButton("➕ Nieuwe Categorie")
        self._add_cat_btn.setObjectName("add_category_button")
        self._add_cat_btn.clicked.connect(self._show_add_category_dialog)
        layout.addWidget(self._add_cat_btn)

    def _connect_signals(self):
        """Verbind signals van de ViewModel met slots in de View."""
        self._viewmodel.categories_loaded.connect(self._on_categories_loaded)
        self._viewmodel.rules_loaded.connect(self._on_rules_loaded)
        self._viewmodel.stats_loaded.connect(self._on_stats_loaded)
        self._viewmodel.loading_started.connect(self._on_loading_started)
        self._viewmodel.loading_finished.connect(self._on_loading_finished)
        self._viewmodel.error_occurred.connect(self._on_error)

    def _create_action_buttons(self, table, row, edit_callback, delete_callback):
        """Maak edit/delete buttons voor een tabelrij."""
        container = QFrame()
        container.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(30, 24)
        edit_btn.clicked.connect(edit_callback)
        edit_btn.setToolTip("Bewerken")
        layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 24)
        delete_btn.clicked.connect(delete_callback)
        delete_btn.setToolTip("Verwijderen")
        layout.addWidget(delete_btn)

        table.setCellWidget(row, table.columnCount() - 1, container)
        return container

    # ViewModel signal handlers

    def _on_categories_loaded(self, categorieën):
        """Handle categorieën geladen van ViewModel."""
        self._categories_table.setUpdatesEnabled(False)
        self._categories_table.setRowCount(len(categorieën))

        stats = self._viewmodel.get_stats()
        self._editable_categories.clear()

        for row, (naam, cat_type, beschrijving) in enumerate(categorieën):
            self._categories_table.setItem(row, 0, QTableWidgetItem(naam))

            type_item = QTableWidgetItem(cat_type)
            if cat_type == "inkomsten":
                type_item.setForeground(Qt.darkGreen)
            else:
                type_item.setForeground(Qt.darkRed)
            self._categories_table.setItem(row, 1, type_item)

            cat_stats = stats.get(naam, {"aantal": 0, "totaal_bedrag": 0})
            self._categories_table.setItem(
                row, 2, QTableWidgetItem(str(cat_stats["aantal"]))
            )
            self._categories_table.setItem(
                row, 3, QTableWidgetItem(f"€{cat_stats['totaal_bedrag']:,.2f}")
            )

            # Check of deze categorie bewerkbaar is
            is_editable = self._viewmodel.is_category_editable(naam)
            if is_editable:
                self._editable_categories.add(naam)
                self._create_action_buttons(
                    self._categories_table,
                    row,
                    lambda checked, n=naam, t=cat_type, b=beschrijving: (
                        self._show_edit_category_dialog(n, t, b)
                    ),
                    lambda checked, n=naam: self._on_delete_category(n),
                )
            else:
                # Globale categorie - toon slotje en disable buttons
                self._categories_table.setItem(row, 4, QTableWidgetItem("🔒 Globaal"))
                self._categories_table.item(row, 4).setForeground(Qt.gray)

        header = self._categories_table.horizontalHeader()
        # Interactive allows user to resize columns with mouse
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        # Set initial reasonable widths
        self._categories_table.setColumnWidth(0, 150)  # Categorie
        self._categories_table.setColumnWidth(1, 100)  # Type
        self._categories_table.setColumnWidth(2, 80)  # Aantal
        self._categories_table.setColumnWidth(3, 120)  # Totaal Bedrag
        self._categories_table.setColumnWidth(4, 100)  # Acties

        self._categories_table.setUpdatesEnabled(True)

    def _on_rules_loaded(self, rules):
        """Handle regels geladen van ViewModel."""
        self._rules_table.setUpdatesEnabled(False)
        self._rules_table.setRowCount(len(rules))
        self._editable_rules.clear()

        for row, (zoekterm, categorie) in enumerate(rules):
            self._rules_table.setItem(row, 0, QTableWidgetItem(zoekterm))
            self._rules_table.setItem(row, 1, QTableWidgetItem(categorie))

            # Check of deze regel bewerkbaar is
            is_editable = self._viewmodel.is_rule_editable(zoekterm)
            if is_editable:
                self._editable_rules.add(zoekterm)
                self._create_action_buttons(
                    self._rules_table,
                    row,
                    lambda checked, z=zoekterm, c=categorie: (
                        self._show_edit_rule_dialog(z, c)
                    ),
                    lambda checked, z=zoekterm: self._on_delete_rule(z),
                )
            else:
                # Globale regel - toon slotje en disable buttons
                self._rules_table.setItem(row, 2, QTableWidgetItem("🔒 Globaal"))
                self._rules_table.item(row, 2).setForeground(Qt.gray)

        header = self._rules_table.horizontalHeader()
        # Interactive allows user to resize columns with mouse
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        # Set initial reasonable widths
        self._rules_table.setColumnWidth(0, 200)  # Zoekterm
        self._rules_table.setColumnWidth(1, 150)  # Categorie
        self._rules_table.setColumnWidth(2, 100)  # Acties

        self._rules_table.setUpdatesEnabled(True)

    def _on_stats_loaded(self, stats):
        """Handle stats geladen van ViewModel."""
        total_stats = self._viewmodel.get_total_stats()

        self._stats_label.setText(
            f"{total_stats.get('aantal_categorieën', 0)} categorieën | "
            f"{total_stats.get('totaal_aantal', 0)} getransacteerd | "
            f"€{total_stats.get('totaal_bedrag', 0):,.2f} totaal"
        )

    def _on_loading_started(self):
        """Handle laden gestart van ViewModel."""
        self._refresh_btn.setEnabled(False)

    def _on_loading_finished(self):
        """Handle laden voltooid van ViewModel."""
        self._refresh_btn.setEnabled(True)

    def _on_error(self, error_msg):
        """Handle error van ViewModel."""
        logger.error("Categorieën error: %s", error_msg)
        QMessageBox.warning(self, "Fout", error_msg)

    # User action handlers

    def _on_refresh_clicked(self):
        """Handle refresh button clicked."""
        self._viewmodel.refresh()

    def _show_add_category_dialog(self):
        """Toon dialoog voor nieuwe categorie."""
        dialog = AddCategoryDialog(self)
        dialog.category_added.connect(self._on_category_added)
        dialog.exec()

    def _on_category_added(self, naam, cat_type, beschrijving):
        """Handle new category added via dialog."""
        self._viewmodel.create_category(naam, cat_type, beschrijving)

    def _show_edit_category_dialog(self, naam, cat_type, beschrijving):
        """Toon dialoog voor bewerken categorie."""
        dialog = EditCategoryDialog(naam, cat_type, beschrijving, self)
        dialog.category_updated.connect(self._on_category_updated)
        dialog.exec()

    def _on_category_updated(self, oude_naam, nieuwe_naam, cat_type, beschrijving):
        """Handle category updated via dialog."""
        self._viewmodel.update_category(oude_naam, nieuwe_naam, cat_type, beschrijving)

    def _on_delete_category(self, naam):
        """Handle delete category request."""
        # Check of er transacties aan gekoppeld zijn
        stats = self._viewmodel.get_category_stats(naam)
        aantal = stats.get("aantal", 0)

        if aantal > 0:
            msg = (
                f"De categorie '{naam}' heeft {aantal} gekoppelde transacties.\n\n"
                f"Deze transacties worden verplaatst naar 'Ongecategoriseerd'.\n\n"
                f"Wil je doorgaan?"
            )
        else:
            msg = f"Wil je de categorie '{naam}' verwijderen?"

        reply = QMessageBox.question(
            self,
            "Categorie Verwijderen",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            transacties, success = self._viewmodel.delete_category(naam)
            if success:
                if transacties > 0:
                    QMessageBox.information(
                        self,
                        "Verwijderd",
                        f"Categorie verwijderd. {transacties} transacties verplaatst naar Ongecategoriseerd.",
                    )
                else:
                    QMessageBox.information(self, "Verwijderd", "Categorie verwijderd.")

    def _show_add_rule_dialog(self):
        """Toon dialoog voor nieuwe regel."""
        categorie_namen = self._viewmodel.get_category_names()
        if not categorie_namen:
            logger.warning("Geen categorieën beschikbaar voor regel")
            QMessageBox.warning(
                self, "Geen Categorieën", "Maak eerst een categorie aan."
            )
            return

        zoekterm, ok = QInputDialog.getText(
            self, "Nieuwe Regel", "Zoekterm (bijv. ALBERT HEIN):"
        )
        if not ok or not zoekterm.strip():
            return

        categorie, ok = QInputDialog.getItem(
            self, "Nieuwe Regel", "Categorie:", categorie_namen, 0, False
        )
        if not ok or not categorie:
            return

        self._viewmodel.add_rule(zoekterm.strip(), categorie)

    def _show_edit_rule_dialog(self, zoekterm, categorie):
        """Toon dialoog voor bewerken regel."""
        categorie_namen = self._viewmodel.get_category_names()
        if not categorie_namen:
            logger.warning("Geen categorieën beschikbaar voor regel")
            return

        dialog = EditRuleDialog(zoekterm, categorie, categorie_namen, self)
        dialog.rule_updated.connect(self._on_rule_updated)
        dialog.exec()

    def _on_rule_updated(self, oude_zoekterm, nieuwe_zoekterm, nieuwe_categorie):
        """Handle rule updated via dialog."""
        self._viewmodel.update_rule(oude_zoekterm, nieuwe_zoekterm, nieuwe_categorie)

    def _on_delete_rule(self, zoekterm):
        """Handle delete rule request."""
        msg = f"Wil je de regel '{zoekterm}' verwijderen?"
        reply = QMessageBox.question(
            self,
            "Regel Verwijderen",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            success = self._viewmodel.delete_rule(zoekterm)
            if success:
                QMessageBox.information(self, "Verwijderd", "Regel verwijderd.")

    # Public methods

    def set_gebruiker_id(self, gebruiker_id):
        """Stel de gebruiker ID in via ViewModel."""
        self._viewmodel.set_gebruiker_id(gebruiker_id)

    def load_categories(self):
        """Laad categorieën via ViewModel."""
        self._viewmodel.load_all()

    def refresh(self):
        """Vernieuw de categorieën via ViewModel."""
        self._viewmodel.refresh()

    def is_category_editable(self, naam):
        """Check of een categorie bewerkbaar is."""
        return naam in self._editable_categories

    def is_rule_editable(self, zoekterm):
        """Check of een regel bewerkbaar is."""
        return zoekterm in self._editable_rules
