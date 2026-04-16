"""UserSelectionDialog - Dialoog voor gebruiker selecteren of aanmaken"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class UserSelectionDialog(QDialog):
    """Dialoogvenster voor gebruiker selecteren of aanmaken."""

    user_selected = Signal(int, str)  # gebruiker_id, gebruiker_naam

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self._db = db_manager
        self.setWindowTitle("Gebruiker Selecteren")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        self._setup_ui()
        self._load_users()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)

        # Titel
        title = QLabel("Selecteer een gebruiker of maak een nieuwe aan")
        title.setObjectName("dialog_title")
        layout.addWidget(title)

        # Gebruikerslijst
        self._user_list = QListWidget()
        self._user_list.setObjectName("user_list")
        self._user_list.itemDoubleClicked.connect(self._on_user_double_clicked)
        layout.addWidget(self._user_list)

        # Nieuwe gebruiker sectie
        new_user_frame = QFrame()
        new_user_frame.setObjectName("new_user_frame")
        new_user_layout = QHBoxLayout(new_user_frame)

        self._new_user_input = QLineEdit()
        self._new_user_input.setPlaceholderText("Naam nieuwe gebruiker")
        self._new_user_input.setObjectName("new_user_input")
        new_user_layout.addWidget(self._new_user_input)

        add_btn = QPushButton("➕ Toevoegen")
        add_btn.setObjectName("add_user_button")
        add_btn.clicked.connect(self._on_add_user)
        new_user_layout.addWidget(add_btn)

        layout.addWidget(new_user_frame)

        # Actie knoppen
        button_layout = QHBoxLayout()

        select_btn = QPushButton("✓ Selecteer")
        select_btn.setObjectName("select_button")
        select_btn.clicked.connect(self._on_select_user)
        button_layout.addWidget(select_btn)

        cancel_btn = QPushButton("✕ Annuleren")
        cancel_btn.setObjectName("cancel_button")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_users(self):
        """Laad alle gebruikers in de lijst."""
        self._user_list.clear()
        users = self._db.get_all_users()

        for user_id, naam in users:
            self._user_list.addItem(f"{naam} ({user_id})")

        if users:
            self._user_list.setCurrentRow(0)

    def _on_user_double_clicked(self, item):
        """Handle double-click op gebruiker."""
        self._select_current_user()

    def _on_select_user(self):
        """Handle selecteer knop."""
        self._select_current_user()

    def _select_current_user(self):
        """Selecteer de huidige gebruiker en sluit dialoog."""
        current_item = self._user_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Geen gebruiker", "Selecteer een gebruiker.")
            return

        text = current_item.text()
        # Parse: "Naam (id)"
        parts = text.rstrip(")").split(" (")
        if len(parts) == 2:
            gebruiker_naam = parts[0]
            gebruiker_id = int(parts[1])
            self.user_selected.emit(gebruiker_id, gebruiker_naam)
            self.accept()

    def _on_add_user(self):
        """Handle nieuwe gebruiker toevoegen."""
        naam = self._new_user_input.text().strip()

        if not naam:
            QMessageBox.warning(self, "Lege naam", "Voer een naam in.")
            return

        self._db.create_user(naam)
        self._new_user_input.clear()
        self._load_users()

        # Selecteer de nieuwe gebruiker
        for i in range(self._user_list.count()):
            item = self._user_list.item(i)
            if item.text().startswith(f"{naam} ("):
                self._user_list.setCurrentRow(i)
                break

        QMessageBox.information(
            self, "Gebruiker toegevoegd", f"Gebruiker '{naam}' is toegevoegd."
        )
