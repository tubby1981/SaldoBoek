"""CategoryComboBox - ComboBox voor categorie selectie."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox


class CategoryComboBox(QComboBox):
    """
    ComboBox voor categorie selectie met ondersteuning voor 'Alle'.

    Signal:
        category_changed(str): Emitted wanneer een andere categorie wordt geselecteerd
    """

    category_changed = Signal(str)

    def __init__(self, parent=None, include_alle=True):
        """
        Initialiseer CategoryComboBox.

        Args:
            parent: Parent widget
            include_alle: Toon "Alle" optie als eerste item
        """
        super().__init__(parent)
        self._include_alle = include_alle
        self._categorieën = []

        if include_alle:
            self.addItem("Alle")

        self.currentTextChanged.connect(self._on_text_changed)

    def set_categories(self, categories):
        """
        Stel de beschikbare categorieën in.

        Args:
            categories: List van categorie namen of list van tuples (naam, type)
        """
        self._categorieën = categories

        # Block signals tijdens update
        self.blockSignals(True)

        # Bewaar huidige selectie
        current = self.currentText()

        # Clear en vul opnieuw
        self.clear()

        if self._include_alle:
            self.addItem("Alle")

        if categories:
            # Als het tuples zijn, pak alleen de naam
            if isinstance(categories[0], tuple):
                for cat in categories:
                    self.addItem(cat[0])
            else:
                self.addItems(categories)

        # Herstel selectie als diese nog bestaat
        index = self.findText(current)
        if index >= 0:
            self.setCurrentIndex(index)
        elif self._include_alle:
            self.setCurrentIndex(0)  # Standaard "Alle"

        self.blockSignals(False)

    def get_selected_category(self):
        """
        Geef de geselecteerde categorie terug.

        Returns:
            str: Naam van geselecteerde categorie, of "Alle" / None als geen selectie
        """
        text = self.currentText()
        if text == "Alle":
            return None
        return text if text else None

    def set_selected_category(self, category_name):
        """
        Stel de geselecteerde categorie in.

        Args:
            category_name: Naam van de categorie om te selecteren
        """
        if category_name is None or category_name == "":
            self.setCurrentIndex(0 if self._include_alle else -1)
            return

        index = self.findText(category_name)
        if index >= 0:
            self.setCurrentIndex(index)

    def _on_text_changed(self, text):
        """Interne handler voor text wijziging."""
        if text == "Alle":
            self.category_changed.emit(None)
        else:
            self.category_changed.emit(text)

    @property
    def categories(self):
        """Geef de lijst van categorieën terug."""
        return self._categorieën
