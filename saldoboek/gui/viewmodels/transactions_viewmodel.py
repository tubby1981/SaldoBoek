"""TransactionsViewModel - ViewModel voor transactie overzicht."""

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class TransactionsViewModel(QObject):
    """
    ViewModel voor het transactie overzicht.

    Verantwoordelijk voor:
    - Laden van transacties uit service
    - Filter logica (jaar, maand, categorie, zoekterm)
    - Paginering
    - Statistieken berekening

    Signal/slot communicatie met de View.
    """

    # Signals voor communicatie met View
    transactions_loaded = Signal(list)  # Lijst van transactie dicts
    count_updated = Signal(int)  # Totaal aantal gefilterde transacties
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)
    stats_updated = Signal(dict)  # {inkomsten, uitgaven, saldo}
    filter_options_updated = Signal(list, list)  # years, categories
    category_updated = Signal(int, str)  # transactie_id, nieuwe_categorie
    potential_links_found = Signal(
        list
    )  # [(id, datum, bedrag, naam, omschrijving, already_linked), ...]
    link_completed = Signal(int, int)  # (transaction_id, linked_id)
    unlink_completed = Signal(int)  # transaction_id
    linked_info_loaded = Signal(dict)  # {id, datum, bedrag, naam, info} of None

    def __init__(self, transaction_service, parent=None):
        """
        Initialiseer TransactionsViewModel.

        Args:
            transaction_service: TransactionService instantie
            parent: Parent QObject
        """
        super().__init__(parent)
        self._service = transaction_service
        self._gebruiker_id = None

        # Transactie data
        self._all_transactions = []

        # Paginering
        self._current_page = 0
        self._page_size = 100

        # Filters
        self._filters = {}

        # Beschikbare opties
        self._available_years = []
        self._available_categories = []

    def set_gebruiker_id(self, gebruiker_id: int) -> None:
        """Stel de gebruiker ID in en laad initiële data."""
        self._gebruiker_id = gebruiker_id
        self._load_filter_options()

    def _load_filter_options(self) -> None:
        """Laad beschikbare filter opties (jaren en categorieën)."""
        if not self._service or not self._gebruiker_id:
            return

        try:
            self._available_years = self._service.get_available_years(
                self._gebruiker_id
            )
            self._available_categories = self._service.get_available_categories(
                self._gebruiker_id
            )
            self.filter_options_updated.emit(
                self._available_years, self._available_categories
            )
        except Exception as e:
            logger.error("Fout bij laden filter opties: %s", e)

    def load_transactions(self, filters: Optional[dict] = None) -> None:
        """
        Laad transacties met optionele filters.

        Args:
            filters: Optionele dict met filter criteria
                   {jaar: int, maand: int, categorie: str, zoek: str}
        """
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return

        self.loading_started.emit()

        try:
            if filters:
                self._filters = filters

            df = self._service.get_transactions(
                filters=self._filters, gebruiker_id=self._gebruiker_id
            )

            if df is None or df.empty:
                self._all_transactions = []
            else:
                self._all_transactions = df.to_dict("records")

            self._current_page = 0
            self.count_updated.emit(len(self._all_transactions))
            self.transactions_loaded.emit(self.get_page_data())
            self._update_stats()
            self._load_filter_options()

        except Exception as e:
            logger.error("Fout bij laden transacties: %s", e)
            self.error_occurred.emit(str(e))
        finally:
            self.loading_finished.emit()

    def get_page_data(self) -> list:
        """
        Geef de transacties voor de huidige pagina.

        Returns:
            List van transactie dicts voor huidige pagina
        """
        if not self._all_transactions:
            return []

        total_pages = self._get_total_pages()

        # Clamp current page
        if self._current_page >= total_pages:
            self._current_page = max(0, total_pages - 1)
        if self._current_page < 0:
            self._current_page = 0

        start_idx = self._current_page * self._page_size
        end_idx = min(start_idx + self._page_size, len(self._all_transactions))

        return self._all_transactions[start_idx:end_idx]

    def _get_total_pages(self) -> int:
        """Bereken totaal aantal pagina's."""
        if not self._all_transactions:
            return 1
        return max(
            1, (len(self._all_transactions) + self._page_size - 1) // self._page_size
        )

    @Slot()
    def next_page(self) -> None:
        """Ga naar de volgende pagina."""
        total_pages = self._get_total_pages()
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self.transactions_loaded.emit(self.get_page_data())
            self._update_stats()

    @Slot()
    def previous_page(self) -> None:
        """Ga naar de vorige pagina."""
        if self._current_page > 0:
            self._current_page -= 1
            self.transactions_loaded.emit(self.get_page_data())
            self._update_stats()

    @Slot(int)
    def go_to_page(self, page: int) -> None:
        """Ga naar een specifieke pagina."""
        total_pages = self._get_total_pages()
        if 0 <= page < total_pages:
            self._current_page = page
            self.transactions_loaded.emit(self.get_page_data())
            self._update_stats()

    def set_filter(self, key: str, value) -> None:
        """
        Stel een filter in.

        Args:
            key: Filternaam (jaar, maand, categorie, zoek)
            value: Filterwaarde
        """
        if value is None or value == "" or value == "Alle":
            self._filters.pop(key, None)
        else:
            self._filters[key] = value

    def apply_filters(self, filters: dict) -> None:
        """
        Pas alle filters tegelijk toe en herlaad transacties.

        Args:
            filters: Dict met alle filters
        """
        self._filters = {}

        # Year
        if filters.get("jaar") and filters["jaar"] != "Alle":
            self._filters["jaar"] = int(filters["jaar"])

        # Month
        if filters.get("maand") and filters["maand"] > 0:
            self._filters["maand"] = filters["maand"]

        # Category
        if filters.get("categorie") and filters["categorie"] != "Alle":
            self._filters["categorie"] = filters["categorie"]

        # Search
        if filters.get("zoek"):
            self._filters["zoek"] = filters["zoek"]

        self.load_transactions()

    def get_current_page(self) -> int:
        """Geef huidige pagina nummer (0-based)."""
        return self._current_page

    def get_total_pages(self) -> int:
        """Geef totaal aantal pagina's."""
        return self._get_total_pages()

    def get_total_count(self) -> int:
        """Geef totaal aantal transacties."""
        return len(self._all_transactions)

    def _update_stats(self) -> None:
        """Bereken en emit statistieken voor huidige pagina."""
        page_data = self.get_page_data()

        if not page_data:
            self.stats_updated.emit({"inkomsten": 0.0, "uitgaven": 0.0, "saldo": 0.0})
            return

        inkomsten = sum(t.get("bedrag", 0) for t in page_data if t.get("bedrag", 0) > 0)
        uitgaven = abs(
            sum(t.get("bedrag", 0) for t in page_data if t.get("bedrag", 0) < 0)
        )
        saldo = inkomsten - uitgaven

        self.stats_updated.emit(
            {"inkomsten": inkomsten, "uitgaven": uitgaven, "saldo": saldo}
        )

    def refresh(self) -> None:
        """Vernieuw de transacties met huidige filters."""
        self.load_transactions()

    def update_category(self, transaction_id: int, new_category: str) -> bool:
        """
        Werk de categorie van een transactie bij.

        Args:
            transaction_id: ID van de transactie
            new_category: Nieuwe categorie naam

        Returns:
            True als successful
        """
        if not self._service or not self._gebruiker_id:
            return False

        try:
            success = self._service.update_transaction_category(
                transaction_id, new_category, self._gebruiker_id
            )
            if success:
                self.category_updated.emit(transaction_id, new_category)
                # Update local cache
                for trans in self._all_transactions:
                    if trans.get("id") == transaction_id:
                        trans["categorie"] = new_category
                        break
                # Refresh current page to show updated data
                self.transactions_loaded.emit(self.get_page_data())
            return success
        except Exception as e:
            logger.error("Fout bij updaten categorie: %s", e)
            return False

    def get_all_categories(self) -> list:
        """
        Haal alle beschikbare categorieën op.

        Returns:
            List van categorie tuples (naam, type, beschrijving)
        """
        if not self._service or not self._gebruiker_id:
            return []

        try:
            return self._service.get_all_categories(self._gebruiker_id)
        except Exception as e:
            logger.error("Fout bij laden categorieën: %s", e)
            return []

    def find_similar_transactions(self, transaction):
        """
        Vind transacties die vergelijkbaar zijn met de gegeven transactie.

        Args:
            transaction: Dict met transactie data

        Returns:
            DataFrame met vergelijkbare transacties of None
        """
        if not self._service or not self._gebruiker_id:
            return None

        try:
            return self._service.find_similar_transactions(
                transaction, self._gebruiker_id
            )
        except Exception as e:
            logger.error("Fout bij zoeken naar vergelijkbare transacties: %s", e)
            return None

    def update_similar_categories(self, transaction_ids, new_category):
        """
        Werk de categorie bij van meerdere transacties.

        Args:
            transaction_ids: List van transactie IDs
            new_category: Nieuwe categorie naam

        Returns:
            Aantal succesvol bijgewerkte transacties
        """
        if not self._service or not self._gebruiker_id:
            return 0

        try:
            return self._service.update_multiple_categories(
                transaction_ids, new_category, self._gebruiker_id
            )
        except Exception as e:
            logger.error("Fout bij updaten vergelijkbare transacties: %s", e)
            return 0

    def add_categorization_rule(self, zoekterm, categorie):
        """
        Voeg een categorisatie regel toe.

        Args:
            zoekterm: Zoekterm voor automatische categorisatie
            categorie: Naam van de categorie

        Returns:
            True als gelukt, False bij fout
        """
        if not self._service or not self._gebruiker_id:
            return False

        try:
            self._service.add_categorization_rule(
                zoekterm, categorie, self._gebruiker_id
            )
            logger.info("Regel toegevoegd: '%s' -> %s", zoekterm, categorie)
            return True
        except Exception as e:
            logger.error("Fout bij toevoegen regel: %s", e)
            return False

    def find_potential_links(self, transaction_id, days=90):
        """
        Vind potentiële transacties om te linken aan de gegeven transactie.

        Args:
            transaction_id: ID van de transactie om te matchen
            days: Aantal dagen waarin gezocht wordt (default 90)
        """
        if not self._service:
            self.potential_links_found.emit([])
            return

        try:
            matches = self._service.find_potential_links(transaction_id, days=days)
            self.potential_links_found.emit(matches if matches else [])
        except Exception as e:
            logger.error("Fout bij zoeken naar potentiële links: %s", e)
            self.potential_links_found.emit([])

    def link_transactions(self, transaction_id_1, transaction_id_2):
        """
        Koppel twee transacties aan elkaar.

        Args:
            transaction_id_1: ID van eerste transactie
            transaction_id_2: ID van tweede transactie
        """
        if not self._service:
            return

        try:
            success = self._service.link_transactions(
                transaction_id_1, transaction_id_2
            )
            if success:
                self.link_completed.emit(transaction_id_1, transaction_id_2)
                logger.info(
                    "Transacties gelinkt: %d <-> %d", transaction_id_1, transaction_id_2
                )
        except Exception as e:
            logger.error("Fout bij linken transacties: %s", e)

    def unlink_transaction(self, transaction_id):
        """
        Ontkoppel een transactie van zijn gekoppelde transactie.

        Args:
            transaction_id: ID van de transactie om te ontkoppelen
        """
        if not self._service:
            return

        try:
            success = self._service.unlink_transaction(transaction_id)
            if success:
                self.unlink_completed.emit(transaction_id)
                logger.info("Transactie ontkoppeld: %d", transaction_id)
        except Exception as e:
            logger.error("Fout bij ontkoppelen transactie: %s", e)

    def get_linked_transaction_info(self, transaction_id):
        """
        Haal info op over de gekoppelde transactie en emit via signal.

        Args:
            transaction_id: ID van de transactie
        """
        if not self._service:
            self.linked_info_loaded.emit(None)
            return

        try:
            info = self._service.get_linked_transaction_info(transaction_id)
            self.linked_info_loaded.emit(info)
        except Exception as e:
            logger.error("Fout bij ophalen gekoppelde transactie info: %s", e)
            self.linked_info_loaded.emit(None)

    @property
    def page_size(self) -> int:
        """Geef pagina grootte."""
        return self._page_size
