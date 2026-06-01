"""CategoriesViewModel - ViewModel voor categorieën en regels."""

import logging

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class CategoriesViewModel(QObject):
    """
    ViewModel voor categorieën en regels beheer.

    Verantwoordelijk voor:
    - Laden van categorieën
    - Laden van categorisatie regels
    - Aanmaken van nieuwe categorieën
    - Toevoegen van regels
    - Statistieken per categorie

    Signal/slot communicatie met de View.
    """

    # Signals voor communicatie met View
    categories_loaded = Signal(list)  # [(naam, type, beschrijving), ...]
    rules_loaded = Signal(list)  # [(zoekterm, categorie), ...]
    stats_loaded = Signal(dict)  # {categorie: {aantal, totaal_bedrag}}
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)
    category_added = Signal(str)  # naam van nieuwe categorie

    def __init__(self, category_service, parent=None):
        """
        Initialiseer CategoriesViewModel.

        Args:
            category_service: CategoryService instantie
            parent: Parent QObject
        """
        super().__init__(parent)
        self._service = category_service
        self._gebruiker_id = None

        # Cached data
        self._categorieën = []
        self._regels = []
        self._stats = {}

    def set_gebruiker_id(self, gebruiker_id: int) -> None:
        """Stel de gebruiker ID in en laad data."""
        self._gebruiker_id = gebruiker_id
        self.load_all()

    def load_all(self) -> None:
        """Laad alle categorieën, regels en statistieken."""
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return

        self.loading_started.emit()

        try:
            self._load_categories()
            self._load_rules()
            self._load_stats()
        except Exception as e:
            logger.error("Fout bij laden categorieën: %s", e)
            self.error_occurred.emit(str(e))
        finally:
            self.loading_finished.emit()

    def _load_categories(self) -> None:
        """Laad alle categorieën."""
        self._categorieën = self._service.get_all_categories(self._gebruiker_id)
        self.categories_loaded.emit(self._categorieën)

    def _load_rules(self) -> None:
        """Laad alle categorisatie regels."""
        self._regels = self._service.get_categorization_rules(self._gebruiker_id)
        self.rules_loaded.emit(self._regels)

    def _load_stats(self) -> None:
        """Laad statistieken per categorie."""
        self._stats = self._service.get_category_stats(self._gebruiker_id)
        self.stats_loaded.emit(self._stats)

    def create_category(self, naam: str, cat_type: str, beschrijving: str = "") -> bool:
        """
        Maak een nieuwe categorie aan.

        Args:
            naam: Naam van de categorie
            cat_type: 'inkomsten' of 'uitgaven'
            beschrijving: Optionele beschrijving

        Returns:
            True als gelukt, False bij fout
        """
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return False

        try:
            self._service.create_category(
                naam, cat_type, beschrijving, self._gebruiker_id
            )
            self.category_added.emit(naam)
            self.load_all()  # Refresh
            logger.info("Categorie '%s' toegevoegd", naam)
            return True
        except Exception as e:
            logger.error("Fout bij toevoegen categorie: %s", e)
            self.error_occurred.emit(str(e))
            return False

    def add_rule(self, zoekterm: str, categorie: str) -> bool:
        """
        Voeg een categorisatie regel toe.

        Args:
            zoekterm: Zoekterm voor automatische categorisatie
            categorie: Naam van de categorie

        Returns:
            True als gelukt, False bij fout
        """
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return False

        try:
            self._service.add_categorization_rule(
                zoekterm, categorie, self._gebruiker_id
            )
            self.load_all()  # Refresh
            logger.info("Regel toegevoegd: '%s' -> %s", zoekterm, categorie)
            return True
        except Exception as e:
            logger.error("Fout bij toevoegen regel: %s", e)
            self.error_occurred.emit(str(e))
            return False

    def update_category(
        self, oude_naam: str, nieuwe_naam: str, nieuw_type: str, beschrijving: str
    ) -> bool:
        """
        Bewerk een categorie.

        Args:
            oude_naam: Huidige naam
            nieuwe_naam: Nieuwe naam
            nieuw_type: 'inkomsten' of 'uitgaven'
            beschrijving: Beschrijving

        Returns:
            True als gelukt, False bij fout
        """
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return False

        if not self._service.is_category_editable(oude_naam):
            self.error_occurred.emit("Globale categorieën kunnen niet bewerkt worden")
            return False

        try:
            success = self._service.update_category(
                oude_naam, nieuwe_naam, nieuw_type, beschrijving, self._gebruiker_id
            )
            if success:
                self.load_all()  # Refresh
                logger.info("Categorie bijgewerkt: %s", oude_naam)
            return success
        except Exception as e:
            logger.error("Fout bij bewerken categorie: %s", e)
            self.error_occurred.emit(str(e))
            return False

    def delete_category(self, naam: str) -> tuple:
        """
        Verwijder een categorie.

        Args:
            naam: Naam van de categorie

        Returns:
            Tuple (transacties_verplaatst, success)
        """
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return 0, False

        if not self._service.is_category_editable(naam):
            self.error_occurred.emit(
                "Globale categorieën kunnen niet verwijderd worden"
            )
            return 0, False

        try:
            result = self._service.delete_category(naam, self._gebruiker_id)
            if result[1]:
                self.load_all()  # Refresh
                logger.info("Categorie verwijderd: %s", naam)
            return result
        except Exception as e:
            logger.error("Fout bij verwijderen categorie: %s", e)
            self.error_occurred.emit(str(e))
            return 0, False

    def update_rule(
        self, oude_zoekterm: str, nieuwe_zoekterm: str, nieuwe_categorie: str
    ) -> bool:
        """
        Bewerk een categorisatie regel.

        Args:
            oude_zoekterm: Huidige zoekterm
            nieuwe_zoekterm: Nieuwe zoekterm
            nieuwe_categorie: Nieuwe categorie

        Returns:
            True als gelukt, False bij fout
        """
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return False

        if not self._service.is_rule_editable(oude_zoekterm):
            self.error_occurred.emit("Globale regels kunnen niet bewerkt worden")
            return False

        try:
            success = self._service.update_rule(
                oude_zoekterm, nieuwe_zoekterm, nieuwe_categorie, self._gebruiker_id
            )
            if success:
                self.load_all()  # Refresh
                logger.info("Regel bijgewerkt: %s", oude_zoekterm)
            return success
        except Exception as e:
            logger.error("Fout bij bewerken regel: %s", e)
            self.error_occurred.emit(str(e))
            return False

    def delete_rule(self, zoekterm: str) -> bool:
        """
        Verwijder een categorisatie regel.

        Args:
            zoekterm: Zoekterm van de regel

        Returns:
            True als gelukt, False bij fout
        """
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return False

        if not self._service.is_rule_editable(zoekterm):
            self.error_occurred.emit("Globale regels kunnen niet verwijderd worden")
            return False

        try:
            success = self._service.delete_rule(zoekterm, self._gebruiker_id)
            if success:
                self.load_all()  # Refresh
                logger.info("Regel verwijderd: %s", zoekterm)
            return success
        except Exception as e:
            logger.error("Fout bij verwijderen regel: %s", e)
            self.error_occurred.emit(str(e))
            return False

    def is_category_editable(self, naam: str) -> bool:
        """Check of een categorie bewerkbaar is door de gebruiker."""
        if not self._service:
            return False
        return self._service.is_category_editable(naam)

    def is_rule_editable(self, zoekterm: str) -> bool:
        """Check of een regel bewerkbaar is door de gebruiker."""
        if not self._service:
            return False
        return self._service.is_rule_editable(zoekterm)

    def recategorize_transactions(self, keuze: str, categorie: str = None) -> int:
        """
        Hercategoriseer transacties.

        Args:
            keuze: '1' voor ongecategoriseerd, '2' voor alle,
                   '3' voor specifieke categorie
            categorie: Naam van categorie (alleen bij keuze '3')

        Returns:
            Aantal hercategoriseerde transacties
        """
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return 0

        try:
            count = self._service.recategorize_transactions(
                keuze, categorie, self._gebruiker_id
            )
            self.load_all()  # Refresh
            return count
        except Exception as e:
            logger.error("Fout bij hercategoriseren: %s", e)
            self.error_occurred.emit(str(e))
            return 0

    def get_categories(self) -> list:
        """Geef alle categorieën terug."""
        return self._categorieën.copy()

    def get_category_names(self) -> list:
        """Geef alleen de namen van alle categorieën."""
        return [c[0] for c in self._categorieën]

    def get_rules(self) -> list:
        """Geef alle regels terug."""
        return self._regels.copy()

    def get_stats(self) -> dict:
        """Geef de statistieken per categorie terug."""
        return self._stats.copy()

    def get_category_stats(self, naam: str) -> dict:
        """
        Geef statistieken voor een specifieke categorie.

        Args:
            naam: Naam van de categorie

        Returns:
            Dict met aantal en totaal_bedrag, of lege dict
        """
        return self._stats.get(naam, {"aantal": 0, "totaal_bedrag": 0.0})

    def get_total_stats(self) -> dict:
        """
        Geef totaal statistieken over alle categorieën.

        Returns:
            Dict met totaal_aantal en totaal_bedrag
        """
        totaal_aantal = sum(s["aantal"] for s in self._stats.values())
        totaal_bedrag = sum(s["totaal_bedrag"] for s in self._stats.values())
        return {
            "totaal_aantal": totaal_aantal,
            "totaal_bedrag": totaal_bedrag,
            "aantal_categorieën": len(self._categorieën),
        }

    def refresh(self) -> None:
        """Vernieuw alle data."""
        self.load_all()
