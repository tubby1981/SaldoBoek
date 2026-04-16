"""CategoryService - Service layer voor categorie operaties."""

import logging

logger = logging.getLogger(__name__)


class CategoryService:
    """Service voor categorie-gerelateerde operaties."""

    def __init__(self, db_manager, categorizer):
        """
        Initialiseer CategoryService.

        Args:
            db_manager: DatabaseManager instantie
            categorizer: Categorizer instantie
        """
        self._db = db_manager
        self._categorizer = categorizer

    def get_all_categories(self, gebruiker_id):
        """
        Haal alle categorieën op voor een gebruiker.

        Args:
            gebruiker_id: Gebruiker ID

        Returns:
            List van categorie tuples (naam, type, beschrijving)
        """
        return self._db.get_categories(gebruiker_id)

    def get_categories_by_type(self, gebruiker_id, cat_type):
        """
        Haal categorieën op gefilterd op type.

        Args:
            gebruiker_id: Gebruiker ID
            cat_type: 'inkomsten' of 'uitgaven'

        Returns:
            List van categorie tuples (naam, type, beschrijving)
        """
        categorieën = self._db.get_categories(gebruiker_id)
        return [c for c in categorieën if c[1] == cat_type]

    def create_category(self, naam, cat_type, beschrijving="", gebruiker_id=None):
        """
        Maak een nieuwe categorie aan.

        Args:
            naam: Naam van de categorie
            cat_type: 'inkomsten' of 'uitgaven'
            beschrijving: Optionele beschrijving
            gebruiker_id: Gebruiker ID (optioneel, gebruikt intern)

        Returns:
            Naam van toegevoegde categorie, of None bij fout
        """
        return self._categorizer.create_new_category(naam, cat_type, beschrijving)

    def get_categorization_rules(self, gebruiker_id):
        """
        Haal alle categorisatie regels op.

        Args:
            gebruiker_id: Gebruiker ID

        Returns:
            List van regels tuples (zoekterm, categorie)
        """
        query = """
            SELECT zoekterm, categorie
            FROM categorisatie_regels
            WHERE actief = 1 AND (gebruiker_id = ? OR gebruiker_id IS NULL)
            ORDER BY categorie, zoekterm
        """
        return self._db.execute(query, (gebruiker_id,), fetch=True)

    def add_categorization_rule(self, zoekterm, categorie, gebruiker_id):
        """
        Voeg een categorisatie regel toe.

        Args:
            zoekterm: Zoekterm voor automatische categorisatie
            categorie: Naam van de categorie
            gebruiker_id: Gebruiker ID
        """
        self._categorizer.add_categorization_rule(zoekterm, categorie)

    def recategorize_transactions(self, keuze, categorie, gebruiker_id):
        """
        Hercategoriseer transacties op basis van keuze.

        Args:
            keuze: '1' voor ongecategoriseerd, '2' voor alle, '3' voor specifieke categorie
            categorie: Naam van categorie (alleen bij keuze '3')
            gebruiker_id: Gebruiker ID

        Returns:
            Aantal hercategoriseerde transacties
        """
        if keuze == "1":
            query = "SELECT * FROM transacties WHERE categorie = 'Ongecategoriseerd' AND gebruiker_id = ?"
            params = (gebruiker_id,)
        elif keuze == "2":
            query = "SELECT * FROM transacties WHERE gebruiker_id = ?"
            params = (gebruiker_id,)
        elif keuze == "3":
            query = "SELECT * FROM transacties WHERE categorie = ? AND gebruiker_id = ?"
            params = (categorie, gebruiker_id)
        else:
            return 0

        df = self._db.query_df(query, params)

        if df.empty:
            return 0

        hercategoriseerd = 0
        for _, row in df.iterrows():
            oude_categorie = row["categorie"]
            omschrijving = str(row["omschrijving"]) if row["omschrijving"] else ""
            nieuwe_categorie = self._categorizer.categorize(row["naam"], omschrijving)

            if nieuwe_categorie and nieuwe_categorie != oude_categorie:
                self._categorizer.update_transaction_category(
                    {
                        "datum": row["datum"],
                        "omschrijving": row["omschrijving"],
                        "bedrag": row["bedrag"],
                    },
                    nieuwe_categorie,
                )
                hercategoriseerd += 1

        logger.info("%d transacties hercategoriseerd", hercategoriseerd)
        return hercategoriseerd

    def get_category_stats(self, gebruiker_id):
        """
        Haal statistieken op over categorieën.

        Args:
            gebruiker_id: Gebruiker ID

        Returns:
            Dict met statistieken per categorie
        """
        query = """
            SELECT
                categorie,
                COUNT(*) as aantal,
                SUM(ABS(bedrag)) as totaal_bedrag
            FROM transacties
            WHERE gebruiker_id = ? AND categorie != 'Ongecategoriseerd'
            GROUP BY categorie
            ORDER BY totaal_bedrag DESC
        """
        result = self._db.execute(query, (gebruiker_id,), fetch=True)

        stats = {}
        for row in result:
            stats[row[0]] = {"aantal": row[1], "totaal_bedrag": row[2] or 0}
        return stats
