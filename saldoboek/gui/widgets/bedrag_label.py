"""BedragLabel - Label voor het tonen van bedragen met kleurcodering."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class BedragLabel(QLabel):
    """
    Label voor het tonen van bedragen met automatische kleurcodering.

    - Negatieve bedragen: rood
    - Positieve bedragen: donkergroen
    - Nul: standaard kleur
    """

    def __init__(self, bedrag=None, parent=None):
        """
        Initialiseer BedragLabel.

        Args:
            bedrag: Optioneel startbedrag om weer te geven
            parent: Parent widget
        """
        super().__init__(parent)
        self._bedrag = 0
        if bedrag is not None:
            self.set_bedrag(bedrag)
        else:
            self.setText("€0,00")

    def set_bedrag(self, bedrag):
        """
        Stel het bedrag in en update de weergave.

        Args:
            bedrag: Numerieke waarde (positief of negatief)
        """
        self._bedrag = float(bedrag)

        if self._bedrag == 0:
            self.setText("€0,00")
            self.setStyleSheet("")
        elif self._bedrag < 0:
            self.setText(f"€{self._bedrag:,.2f}")
            self.setStyleSheet("color: darkred;")
        else:
            self.setText(f"€{self._bedrag:,.2f}")
            self.setStyleSheet("color: darkgreen;")

    def get_bedrag(self):
        """Geef het huidige bedrag terug."""
        return self._bedrag

    @property
    def bedrag(self):
        """Property alias voor get_bedrag()."""
        return self._bedrag
