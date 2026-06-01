"""TransactionService - Service layer voor transactie operaties."""

import logging

logger = logging.getLogger(__name__)


class TransactionService:
    """Service voor transactie-gerelateerde operaties."""

    def __init__(self, db_manager, categorizer, importer, gebruiker_id=None):
        """Initialiseer TransactionService."""
        self._db = db_manager
        self._categorizer = categorizer
        self._importer = importer
        self._gebruiker_id = gebruiker_id

    def get_available_years(self, gebruiker_id=None):
        """Haal alle beschikbare jaren uit transacties."""
        effective_gebruiker_id = (
            gebruiker_id if gebruiker_id is not None else self._gebruiker_id
        )
        if effective_gebruiker_id is None:
            return []

        query = """
            SELECT DISTINCT strftime('%Y', datum) as jaar
            FROM transacties
            WHERE gebruiker_id = ? AND datum IS NOT NULL
            ORDER BY jaar DESC
        """
        result = self._db.execute(query, (effective_gebruiker_id,), fetch=True)
        return [int(row[0]) for row in result if row[0]]

    def get_available_categories(self, gebruiker_id=None):
        """Haal alle categorieën die gebruikt worden in transacties."""
        effective_gebruiker_id = (
            gebruiker_id if gebruiker_id is not None else self._gebruiker_id
        )
        if effective_gebruiker_id is None:
            return []

        query = """
            SELECT DISTINCT categorie
            FROM transacties
            WHERE gebruiker_id = ? AND categorie IS NOT NULL AND categorie != ''
            ORDER BY categorie
        """
        result = self._db.execute(query, (effective_gebruiker_id,), fetch=True)
        return [row[0] for row in result if row[0]]

    def get_transactions(self, filters=None, gebruiker_id=None):
        """Haal transacties op met optionele filters."""
        query = "SELECT * FROM transacties WHERE 1=1"
        params = []

        effective_gebruiker_id = (
            gebruiker_id if gebruiker_id is not None else self._gebruiker_id
        )
        if effective_gebruiker_id is not None:
            query += " AND gebruiker_id = ?"
            params.append(effective_gebruiker_id)

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

            if "zoek" in filters and filters["zoek"]:
                query += " AND (omschrijving LIKE ? OR naam LIKE ?)"
                zoek = f"%{filters['zoek']}%"
                params.extend([zoek, zoek])

        query += " ORDER BY datum DESC"

        if filters and "limit" in filters and filters["limit"]:
            query += f" LIMIT {filters['limit']}"

        return self._db.query_df(query, tuple(params))

    def get_uncategorized_transactions(self, gebruiker_id):
        """Haal ongecategoriseerde transacties op."""
        query = """
            SELECT * FROM transacties
            WHERE categorie = 'Ongecategoriseerd' AND gebruiker_id = ?
            ORDER BY datum DESC
        """
        return self._db.query_df(query, (gebruiker_id,))

    def get_categories_for_transaction(self, bedrag):
        """Haal relevante categorieën op basis van bedrag."""
        categorieën = self._db.get_categories(self._db.gebruiker_id)

        if bedrag > 0:
            return [c for c in categorieën if c[1] == "inkomsten"]
        else:
            return [c for c in categorieën if c[1] == "uitgaven"]

    def get_all_categories(self, gebruiker_id=None):
        """
        Haal alle categorieën op voor een gebruiker.

        Args:
            gebruiker_id: Gebruiker ID (optioneel)

        Returns:
            List van categorie tuples (naam, type, beschrijving)
        """
        effective_gebruiker_id = (
            gebruiker_id if gebruiker_id is not None else self._gebruiker_id
        )
        if effective_gebruiker_id is None:
            return []
        return self._db.get_categories(effective_gebruiker_id)

    def import_files(self, file_paths, gebruiker_id, account_type="betaalrekening"):
        """Importeer transacties uit bestanden.

        Args:
            file_paths: Lijst van bestandspaden
            gebruiker_id: Gebruiker ID
            account_type: 'betaalrekening' of 'spaarrekening'
        """
        return self._importer.import_transactions_with_categorization(
            file_paths, gebruiker_id, account_type
        )

    def categorize_transaction(self, transaction_id, categorie, gebruiker_id):
        """Categoriseer een transactie op basis van ID."""
        return self._db.update_transaction_category_by_id(
            transaction_id, categorie, gebruiker_id
        )

    def update_transaction_category(self, transaction_id, new_category, gebruiker_id):
        """
        Werk de categorie van een transactie bij.

        Args:
            transaction_id: ID van de transactie
            new_category: Nieuwe categorie naam
            gebruiker_id: Gebruiker ID

        Returns:
            True als successful, False anders
        """
        return self._db.update_transaction_category_by_id(
            transaction_id, new_category, gebruiker_id
        )

    def add_categorization_rule(self, zoekterm, categorie, gebruiker_id):
        """Voeg een categorisatie regel toe."""
        self._categorizer.add_categorization_rule(zoekterm, categorie)

    def find_similar_transactions(self, transaction, gebruiker_id, limit=50):
        """
        Vind transacties die vergelijkbaar zijn met de gegeven transactie.

        Vergelijking is gebaseerd op:
        - Naam (exacte of gedeeltelijke match)
        - Dezelfde bedrag kant (positief/negatief)

        Args:
            transaction: Dict met transactie data
            gebruiker_id: Gebruiker ID
            limit: Maximum aantal resultaten

        Returns:
            DataFrame met vergelijkbare transacties
        """
        naam = transaction.get("naam", "") or ""
        bedrag = transaction.get("bedrag", 0)
        transaction_id = transaction.get("id")

        # Ensure naam is a string
        if not isinstance(naam, str):
            naam = str(naam) if naam else ""

        if not naam or naam.lower() in ("nan", "none", ""):
            return None

        # Bepaal of het inkomsten (positief) of uitgaven (negatief) is
        bedrag_sign = "bedrag > 0" if bedrag > 0 else "bedrag < 0"

        # Zoek transacties met vergelijkbare naam
        # We nemen een deel van de naam (minimaal 3 karakters) voor gedeeltelijke match
        zoektermen = []
        if len(naam) >= 3:
            # Neem eerste 3 karakters en laatste 3 karakters
            zoektermen.append(naam[:3])
            if len(naam) > 6:
                zoektermen.append(naam[-3:])

        # Als naam veel spaties bevat, neem ook elk woord van 3+ karakters
        words = naam.split()
        for word in words:
            if len(word) >= 4 and word not in zoektermen:
                zoektermen.append(word[:4])

        if not zoektermen:
            return None

        # Bouw query voor vergelijkbare transacties
        conditions = [f"gebruiker_id = ?", f"id != ?", bedrag_sign]
        params = [gebruiker_id, transaction_id if transaction_id else 0]

        for term in zoektermen:
            conditions.append("(naam LIKE ? OR omschrijving LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])

        # Unieke transacties (geen duplicaten per ID)
        query = f"""
            SELECT DISTINCT id, datum, naam, omschrijving, bedrag, categorie
            FROM transacties
            WHERE {" AND ".join(conditions)}
            ORDER BY ABS(bedrag) DESC
            LIMIT ?
        """
        params.append(limit)

        return self._db.query_df(query, tuple(params))

    def update_multiple_categories(self, transaction_ids, new_category, gebruiker_id):
        """
        Werk de categorie bij van meerdere transacties.

        Args:
            transaction_ids: List van transactie IDs
            new_category: Nieuwe categorie naam
            gebruiker_id: Gebruiker ID

        Returns:
            Aantal succesvol bijgewerkte transacties
        """
        if not transaction_ids:
            return 0

        count = 0
        for trans_id in transaction_ids:
            success = self._db.update_transaction_category_by_id(
                trans_id, new_category, gebruiker_id
            )
            if success:
                count += 1

        return count

    def get_transaction_stats(self, gebruiker_id):
        """Haal statistieken op over transacties."""
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
