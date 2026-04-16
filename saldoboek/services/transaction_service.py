"""TransactionService - Service layer voor transactie operaties."""

import logging

logger = logging.getLogger(__name__)


class TransactionService:
    """Service voor transactie-gerelateerde operaties."""

    def __init__(self, db_manager, categorizer, importer):
        """
        Initialiseer TransactionService.

        Args:
            db_manager: DatabaseManager instantie
            categorizer: Categorizer instantie
            importer: TransactionImporter instantie
        """
        self._db = db_manager
        self._categorizer = categorizer
        self._importer = importer

    def get_transactions(self, filters=None, gebruiker_id=None):
        """
        Haal transacties op met optionele filters.

        Args:
            filters: Optioneel dict met filteropties:
                - jaar: int (filter op jaar)
                - maand: int (filter op maand, 1-12)
                - categorie: str (filter op categorie)
                - rekening: str (filter op rekeningnummer)
                - limit: int (aantal resultaten)
            gebruiker_id: Gebruiker ID voor isolatie

        Returns:
            DataFrame met transacties
        """
        query = "SELECT * FROM transacties WHERE 1=1"
        params = []

        if gebruiker_id is not None:
            query += " AND gebruiker_id = ?"
            params.append(gebruiker_id)

        if filters:
            if "jaar" in filters and filters["jaar"]:
                query += " AND strftime('%Y', datum) = ?"
                params.append(str(filters["jaar"]))

            if "maand" in filters and filters["maand"]:
                query += " AND strftime('%m', datum) = ?"
                params.append(f"{filters['maand']:02d}")

            if "categorie" in filters and filters["categorie"]:
                query += " AND categorie = ?"
                params.append(filters["categorie"])

            if "rekening" in filters and filters["rekening"]:
                query += " AND rekening = ?"
                params.append(filters["rekening"])

        query += " ORDER BY datum DESC"

        if filters and "limit" in filters and filters["limit"]:
            query += f" LIMIT {filters['limit']}"

        return self._db.query_df(query, tuple(params))

    def get_uncategorized_transactions(self, gebruiker_id):
        """
        Haal ongecategoriseerde transacties op.

        Args:
            gebruiker_id: Gebruiker ID

        Returns:
            DataFrame met ongecategoriseerde transacties
        """
        query = """
            SELECT * FROM transacties
            WHERE categorie = 'Ongecategoriseerd' AND gebruiker_id = ?
            ORDER BY datum DESC
        """
        return self._db.query_df(query, (gebruiker_id,))

    def get_categories_for_transaction(self, bedrag):
        """
        Haal relevante categorieën op basis van bedrag.

        Args:
            bedrag: Transactie bedrag (positief = inkomsten, negatief = uitgaven)

        Returns:
            List van categorie tuples (naam, type, beschrijving)
        """
        categorieën = self._db.get_categories(self._db.gebruiker_id)

        if bedrag > 0:
            return [c for c in categorieën if c[1] == "inkomsten"]
        else:
            return [c for c in categorieën if c[1] == "uitgaven"]

    def import_files(self, file_paths, gebruiker_id):
        """
        Importeer transacties uit bestanden.

        Args:
            file_paths: List van file paths
            gebruiker_id: Gebruiker ID

        Returns:
            Tuple (total_imported, uncategorized_transactions)
        """
        return self._importer.import_transactions_with_categorization(
            file_paths, gebruiker_id
        )

    def categorize_transaction(self, item, categorie, gebruiker_id):
        """
        Categoriseer een transactie.

        Args:
            item: Transactie dict met datum, omschrijving, bedrag
            categorie: Naam van de categorie
            gebruiker_id: Gebruiker ID
        """
        self._categorizer.update_transaction_category(item, categorie)

    def add_categorization_rule(self, zoekterm, categorie, gebruiker_id):
        """
        Voeg een categorisatie regel toe.

        Args:
            zoekterm: Zoekterm voor automatische categorisatie
            categorie: Naam van de categorie
            gebruiker_id: Gebruiker ID
        """
        self._categorizer.add_categorization_rule(zoekterm, categorie)

    def get_transaction_stats(self, gebruiker_id):
        """
        Haal statistieken op over transacties.

        Args:
            gebruiker_id: Gebruiker ID

        Returns:
            Dict met statistieken
        """
        query = """
            SELECT
                COUNT(*) as totaal,
                SUM(CASE WHEN categorie = 'Ongecategoriseerd' THEN 1 ELSE 0 END) as ongecategoriseerd,
                SUM(CASE WHEN bedrag > 0 THEN 1 ELSE 0 END) as inkomsten,
                SUM(CASE WHEN bedrag < 0 THEN 1 ELSE 0 END) as uitgaven
            FROM transacties
            WHERE gebruiker_id = ?
        """
        result = self._db.execute(query, (gebruiker_id,), fetch=True)

        if result:
            row = result[0]
            return {
                "totaal": row[0] or 0,
                "ongecategoriseerd": row[1] or 0,
                "inkomsten": row[2] or 0,
                "uitgaven": row[3] or 0,
            }
        return {"totaal": 0, "ongecategoriseerd": 0, "inkomsten": 0, "uitgaven": 0}
