"""StatCard - Statistiek kaartje widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    """
    Statistiek kaartje voor het tonen van een metric met titel en waarde.

    Args:
        title: Titel van de metric
        value: Initiële waarde
        is_positive: None (neutraal), True (groen), False (rood)
    """

    def __init__(self, title="", value="0", is_positive=None, parent=None):
        """
        Initialiseer StatCard.

        Args:
            title: Titel van de kaart
            value: Initiële waarde
            is_positive: Kleurindicatie (None=neutraal, True=positief/groen, False=negatief/rood)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self._setup_ui(title, value, is_positive)

    def _setup_ui(self, title, value, is_positive):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # Titel
        self._title_label = QLabel(title)
        self._title_label.setObjectName("card_title")
        self._title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title_label)

        # Waarde
        self._value_label = QLabel(value)
        self._value_label.setObjectName("card_value")
        self._value_label.setAlignment(Qt.AlignCenter)
        self._apply_style(is_positive)
        layout.addWidget(self._value_label)

    def _apply_style(self, is_positive):
        """Pas kleurstijl toe op basis van is_positive."""
        if is_positive is True:
            self._value_label.setStyleSheet("color: darkgreen; font-weight: bold;")
        elif is_positive is False:
            self._value_label.setStyleSheet("color: darkred; font-weight: bold;")
        else:
            self._value_label.setStyleSheet("font-weight: bold;")

    def set_title(self, title):
        """
        Stel de titel in.

        Args:
            title: Nieuwe titel
        """
        self._title_label.setText(title)

    def set_value(self, value, is_positive=None):
        """
        Stel de waarde in.

        Args:
            value: Nieuwe waarde (string of numeriek)
            is_positive: Optionele kleurindicatie override
        """
        if isinstance(value, (int, float)):
            self._value_label.setText(str(value))
        else:
            self._value_label.setText(value)

        if is_positive is not None:
            self._apply_style(is_positive)

    def get_value(self):
        """
        Geef de huidige waarde terug.

        Returns:
            str: Huidige waarde als string
        """
        return self._value_label.text()

    @property
    def title(self):
        """Geef de titel terug."""
        return self._title_label.text()

    @property
    def value(self):
        """Property alias voor get_value()."""
        return self.get_value()
