"""UncategorizedViewModel - ViewModel voor ongecategoriseerde transacties."""

import logging

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class UncategorizedViewModel(QObject):
    """
    ViewModel voor het categoriseren van ongecategoriseerde transacties.

    Signal/slot communicatie met de View.
    """

    # Signals
    transactions_loaded = Signal(
        list
    )  # [{id, datum, naam, omschrijving, bedrag, ...}, ...]
    current_transaction_changed = Signal(dict)  # huidige transactie
    categories_loaded = Signal(list)  # [categorie_namen]
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)
    transaction_categorized = Signal(int)  # transactie id
    rule_added = Signal(str, str)  # zoekterm, categorie

    def __init__(self, transaction_service, category_service, parent=None):
        """
        Initialiseer UncategorizedViewModel.

        Args:
            transaction_service: TransactionService instantie
            category_service: CategoryService instantie
            parent: Parent QObject
        """
        super().__init__(parent)
        self._transaction_service = transaction_service
        self._category_service = category_service
        self._gebruiker_id = None

        self._transactions = []
        self._current_index = -1
        self._categories = []

    def set_gebruiker_id(self, gebruiker_id):
        """Stel de gebruiker ID in en laad data."""
        self._gebruiker_id = gebruiker_id
        self.load_uncategorized()

    def load_uncategorized(self):
        """Laad ongecategoriseerde transacties."""
        if not self._transaction_service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return

        self.loading_started.emit()

        try:
            df = self._transaction_service.get_uncategorized_transactions(
                self._gebruiker_id
            )
            self._transactions = df.to_dict("records")
            self.transactions_loaded.emit(self._transactions)

            # Laad categorieën (als tuples: naam, type, beschrijving)
            self._categories = self._category_service.get_all_categories(
                self._gebruiker_id
            )
            self.categories_loaded.emit(self._categories)

            # Set current index to first if available
            if self._transactions:
                self._current_index = 0
                self.current_transaction_changed.emit(self._transactions[0])
            else:
                self._current_index = -1

        except Exception as e:
            logger.error("Fout bij laden ongecategoriseerde transacties: %s", e)
            self.error_occurred.emit(str(e))
        finally:
            self.loading_finished.emit()

    def get_uncategorized_count(self):
        """Geef het aantal ongecategoriseerde transacties."""
        return len(self._transactions)

    def get_current_transaction(self):
        """Geef de huidige transactie."""
        if 0 <= self._current_index < len(self._transactions):
            return self._transactions[self._current_index]
        return None

    def get_current_index(self):
        """Geef de huidige index."""
        return self._current_index

    def get_categories(self):
        """Geef alle beschikbare categorieën."""
        return self._categories.copy()

    def get_relevant_categories(self, bedrag):
        """Geef categorieën relevant voor een bedrag (inkomsten of uitgaven)."""
        if bedrag > 0:
            cat_type = "inkomsten"
        else:
            cat_type = "uitgaven"

        if not self._categories:
            return []

        # Categories zijn tuples: (naam, type, beschrijving)
        return [c for c in self._categories if len(c) > 1 and c[1] == cat_type]

    def set_current_index(self, index):
        """Stel de huidige index in."""
        if 0 <= index < len(self._transactions):
            self._current_index = index
            self.current_transaction_changed.emit(self._transactions[index])

    def next_transaction(self):
        """Ga naar de volgende transactie."""
        if self._current_index < len(self._transactions) - 1:
            self._current_index += 1
            self.current_transaction_changed.emit(
                self._transactions[self._current_index]
            )

    def previous_transaction(self):
        """Ga naar de vorige transactie."""
        if self._current_index > 0:
            self._current_index -= 1
            self.current_transaction_changed.emit(
                self._transactions[self._current_index]
            )

    def categorize_current(self, categorie):
        """Categoriseer de huidige transactie."""
        if not self._transaction_service or not self._gebruiker_id:
            return False

        trans = self.get_current_transaction()
        if not trans:
            return False

        try:
            success = self._transaction_service.categorize_transaction(
                trans["id"], categorie, self._gebruiker_id
            )
            if success:
                # Verwijder uit lokale lijst
                del self._transactions[self._current_index]

                # Pas index aan
                if self._current_index >= len(self._transactions):
                    self._current_index = max(0, len(self._transactions) - 1)

                # Emit updates
                self.transactions_loaded.emit(self._transactions)
                if self._transactions:
                    self.current_transaction_changed.emit(
                        self._transactions[self._current_index]
                    )
                else:
                    self.current_transaction_changed.emit({})

                self.transaction_categorized.emit(trans["id"])
                logger.info(
                    "Transactie %d gecategoriseerd als %s", trans["id"], categorie
                )
            return success
        except Exception as e:
            logger.error("Fout bij categoriseren: %s", e)
            self.error_occurred.emit(str(e))
            return False

    def add_rule_and_categorize(self, zoekterm, categorie):
        """Voeg een regel toe en categoriseer de huidige transactie."""
        if not self._category_service or not self._gebruiker_id:
            return False

        try:
            self._category_service.add_categorization_rule(
                zoekterm, categorie, self._gebruiker_id
            )
            self.rule_added.emit(zoekterm, categorie)
            return self.categorize_current(categorie)
        except Exception as e:
            logger.error("Fout bij toevoegen regel: %s", e)
            self.error_occurred.emit(str(e))
            return False

    def skip_current(self):
        """Sla de huidige transactie over."""
        self.next_transaction()

    def refresh(self):
        """Vernieuw de lijst."""
        self.load_uncategorized()
