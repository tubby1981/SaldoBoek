import sqlite3
from pathlib import Path

import pandas as pd
import yaml

# Get the directory where this script is located (saldoboek/core/)
# Use .parent to get saldoboek/ level
SCRIPT_DIR = Path(__file__).parent.parent
# Create data directory path relative to the script location
DATA_DIR = SCRIPT_DIR / "data"
# Database file path
DB_PATH = DATA_DIR / "database.db"
# Config directory path
CONFIG_DIR = SCRIPT_DIR / "config"


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.config_dir = CONFIG_DIR
        # Ensure the data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        self._ensure_indexes()
        print(f"[DEBUG] Gebruikte database: {self.db_path}")

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _load_categories_config(self):
        """Laad categorieën uit YAML configuratie"""
        config_file = self.config_dir / "categories.yaml"
        if not config_file.exists():
            print(
                f"Warning: Config file {config_file} not found, using empty categories"
            )
            return []

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            categories = []
            # Verwerk uitgaven categorieën
            for cat in config.get("uitgaven", []):
                categories.append((cat["naam"], "uitgaven", cat["beschrijving"]))

            # Verwerk inkomsten categorieën
            for cat in config.get("inkomsten", []):
                categories.append((cat["naam"], "inkomsten", cat["beschrijving"]))

            return categories
        except Exception as e:
            print(f"Error loading categories config: {e}")
            return []

    def _load_rules_config(self):
        """Laad categorisatie regels uit YAML configuratie"""
        config_file = self.config_dir / "categorization_rules.yaml"
        if not config_file.exists():
            print(f"Warning: Config file {config_file} not found, using empty rules")
            return []

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                rules_dict = yaml.safe_load(f)

            # Converteer dictionary naar list of tuples
            rules = [
                (zoekterm, categorie) for zoekterm, categorie in rules_dict.items()
            ]
            return rules
        except Exception as e:
            print(f"Error loading rules config: {e}")
            return []

    def _initialize(self):
        """Initialiseer de database met benodigde tabellen en voer migraties uit"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()

            # Transacties tabel
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transacties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gebruiker_id INTEGER,
                    datum DATE,
                    rekening TEXT,
                    tegenrekening TEXT,
                    naam TEXT,
                    omschrijving TEXT,
                    bedrag REAL,
                    saldo_voor REAL,
                    valuta TEXT,
                    categorie TEXT,
                    rekeningtype TEXT,
                    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Categorieën tabel
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorieen (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    naam TEXT NOT NULL,
                    type TEXT,
                    beschrijving TEXT,
                    gebruiker_id INTEGER NOT NULL,
                    is_standaard BOOLEAN DEFAULT 0,
                    UNIQUE(naam, gebruiker_id)
                )
            """)

            # Categorisatie regels tabel
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorisatie_regels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gebruiker_id INTEGER,
                    zoekterm TEXT,
                    categorie TEXT,
                    actief BOOLEAN DEFAULT 1,
                    is_standaard BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(zoekterm, gebruiker_id)
                )
            """)

            # Gebruikers tabel
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gebruikers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    naam TEXT NOT NULL UNIQUE
                )
            """)

            # Migratie: voeg ontbrekende kolommen toe aan bestaande tabellen
            self._migrate_if_needed(cursor)

            # Laad categorisatie regels uit configuratie (als standaard)
            standaard_regels = self._load_rules_config()
            for regel in standaard_regels:
                cursor.execute(
                    """INSERT OR IGNORE INTO categorisatie_regels (zoekterm, categorie, is_standaard, gebruiker_id)
                       VALUES (?, ?, 1, NULL)""",
                    regel,
                )

            conn.commit()

    def _migrate_if_needed(self, cursor):
        """Voer database migraties uit voor nieuwe kolommen"""
        # Check en voeg rekening kolom toe aan transacties als die ontbreekt
        try:
            cursor.execute("SELECT rekening FROM transacties LIMIT 1")
        except sqlite3.OperationalError:
            # Kolom ontbreekt, voeg toe
            cursor.execute("ALTER TABLE transacties ADD COLUMN rekening TEXT")

        # Check of is_standaard kolom bestaat in categorieen
        try:
            cursor.execute("SELECT is_standaard FROM categorieen LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute(
                "ALTER TABLE categorieen ADD COLUMN is_standaard BOOLEAN DEFAULT 0"
            )

        # Check of is_standaard kolom bestaat in categorisatie_regels
        try:
            cursor.execute("SELECT is_standaard FROM categorisatie_regels LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute(
                "ALTER TABLE categorisatie_regels ADD COLUMN is_standaard BOOLEAN DEFAULT 0"
            )

        # Check of linked_transaction_id kolom bestaat in transacties (voor gekoppelde transacties)
        try:
            cursor.execute("SELECT linked_transaction_id FROM transacties LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute(
                "ALTER TABLE transacties ADD COLUMN linked_transaction_id INTEGER REFERENCES transacties(id)"
            )

    def _ensure_indexes(self):
        """Zorg dat alle benodigde indexen bestaan voor performance"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()

            # Indexen voor transacties tabel
            index_commands = [
                "CREATE INDEX IF NOT EXISTS idx_transacties_gebruiker_id ON transacties(gebruiker_id)",
                "CREATE INDEX IF NOT EXISTS idx_transacties_datum ON transacties(datum)",
                "CREATE INDEX IF NOT EXISTS idx_transacties_categorie ON transacties(categorie)",
                "CREATE INDEX IF NOT EXISTS idx_transacties_rekening ON transacties(rekening)",
                "CREATE INDEX IF NOT EXISTS idx_transacties_gebruiker_datum ON transacties(gebruiker_id, datum)",
            ]

            for cmd in index_commands:
                cursor.execute(cmd)

            conn.commit()
            print("[DEBUG] Database indexen gecontroleerd/aangemaakt")

    def reload_config(self):
        """Herlaad configuratie en update database"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()

            # Laad en update categorieën
            standaard_categorieen = self._load_categories_config()
            for gebruiker in self.get_all_users():
                gebruiker_id = gebruiker[0]
                for cat in standaard_categorieen:
                    cursor.execute(
                        "INSERT OR IGNORE INTO categorieen (naam, type, beschrijving, gebruiker_id) VALUES (?, ?, ?, ?)",
                        (*cat, gebruiker_id),
                    )

            # Laad en update regels (globale regels zonder gebruiker_id)
            standaard_regels = self._load_rules_config()
            for regel in standaard_regels:
                cursor.execute(
                    "INSERT OR IGNORE INTO categorisatie_regels (zoekterm, categorie, gebruiker_id) VALUES (?, ?, NULL)",
                    regel,
                )

            conn.commit()
            print("Configuration reloaded successfully")

    def get_categories(self, gebruiker_id=None):
        """Haal alle categorieën op"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT naam, type, beschrijving FROM categorieen WHERE gebruiker_id = ? ORDER BY type, naam",
                (gebruiker_id,),
            )
            categorieën = cursor.fetchall()
            return categorieën

    def show_recent_transactions(self, aantal=20, gebruiker_id=None):
        """Toon recente transacties"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()

            # Gebruikersnaam ophalen
            cursor.execute("SELECT naam FROM gebruikers WHERE id = ?", (gebruiker_id,))
            row = cursor.fetchone()
            gebruikersnaam = row[0] if row else "Onbekend"

            query = """
                SELECT datum, rekening, naam, omschrijving, bedrag, categorie, rekeningtype
                FROM transacties WHERE gebruiker_id = ?
                ORDER BY datum DESC, imported_at DESC
                LIMIT ?
            """

            df = pd.read_sql_query(query, conn, params=[gebruiker_id, aantal])

            if df.empty:
                print("Geen transacties gevonden")
                return

            print(
                f"\n=== LAATSTE {aantal} TRANSACTIES voor gebruiker: {gebruikersnaam} ==="
            )
            for _, row in df.iterrows():
                print(
                    f"{row['datum']} | €{row['bedrag']:>8.2f} | "
                    f"{(row['naam'] or '')[:20]:20} | "
                    f"{(row['categorie'] or '')[:15]:15} | "
                    f"{(row['omschrijving'] or '')[:50]}"
                )

    def get_database_stats(self, gebruiker_id=None):
        """Toon database statistieken"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()

            # Gebruikersnaam ophalen
            cursor.execute("SELECT naam FROM gebruikers WHERE id = ?", (gebruiker_id,))
            row = cursor.fetchone()
            gebruikersnaam = row[0] if row else "Onbekend"

            # Totaal aantal transacties
            cursor.execute(
                "SELECT COUNT(*) FROM transacties WHERE gebruiker_id = ?",
                (gebruiker_id,),
            )
            total_transacties = cursor.fetchone()[0]

            # Transacties per rekeningtype
            cursor.execute("""
                SELECT rekeningtype, COUNT(*)
                FROM transacties
                GROUP BY rekeningtype
            """)
            per_type = cursor.fetchall()

            # Datumbereik
            cursor.execute(
                "SELECT MIN(datum), MAX(datum) FROM transacties WHERE gebruiker_id = ?",
                (gebruiker_id,),
            )
            datum_bereik = cursor.fetchone()

            # Transacties per rekening
            cursor.execute(
                """
                SELECT rekening, COUNT(*), MIN(datum), MAX(datum)
                FROM transacties WHERE gebruiker_id = ?
                GROUP BY rekening
                ORDER BY COUNT(*) DESC
            """,
                (gebruiker_id,),
            )
            per_rekening = cursor.fetchall()

            # Categorieën statistieken
            cursor.execute(
                """
                SELECT categorie, COUNT(*), SUM(bedrag)
                FROM transacties WHERE gebruiker_id = ?
                GROUP BY categorie
                ORDER BY COUNT(*) DESC
            """,
                (gebruiker_id,),
            )
            per_categorie = cursor.fetchall()

            print(f"\n=== Database Status voor gebruiker: {gebruikersnaam} ===")
            print(f"Totaal transacties: {total_transacties}")

            if datum_bereik[0] and datum_bereik[1]:
                print(f"Periode: {datum_bereik[0]} tot {datum_bereik[1]}")

            print(f"\nTransacties per rekeningtype:")
            for rtype, count in per_type:
                print(f"  {rtype}: {count}")

            print(f"\nTransacties per rekening:")
            for rekening, count, min_datum, max_datum in per_rekening:
                print(f"  {rekening}: {count} transacties ({min_datum} - {max_datum})")

            print(f"\nTop 10 categorieën:")
            for categorie, count, totaal in per_categorie[:10]:
                print(f"  {categorie}: {count} transacties, €{totaal:.2f}")

    def execute(self, query, params=None, fetch=False, many=False):
        with self._connect() as conn:
            cur = conn.cursor()
            if many:
                cur.executemany(query, params)
            else:
                cur.execute(query, params or ())
            if fetch:
                return cur.fetchall()
            conn.commit()

    def execute_df(self, query, params=None):
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def query_df(self, query, params=None):
        """Voer een query uit en retourneer een pandas DataFrame"""
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params or ())

    def create_user(self, naam):
        """Voeg een nieuwe gebruiker toe (of gebruik bestaande) en vul standaardcategorieën"""
        with self._connect() as conn:
            cursor = conn.cursor()

            # Probeer gebruiker toe te voegen
            cursor.execute(
                "INSERT OR IGNORE INTO gebruikers (naam) VALUES (?)", (naam,)
            )

            # Haal het ID op
            cursor.execute("SELECT id FROM gebruikers WHERE naam = ?", (naam,))
            row = cursor.fetchone()
            if not row:
                print(f"Kon geen ID vinden voor gebruiker '{naam}'")
                return
            gebruiker_id = row[0]

            # Voeg standaardcategorieën toe (als standaard)
            standaard_categorieen = self._load_categories_config()
            for cat in standaard_categorieen:
                cursor.execute(
                    "INSERT OR IGNORE INTO categorieen (naam, type, beschrijving, gebruiker_id, is_standaard) VALUES (?, ?, ?, ?, 1)",
                    (*cat, gebruiker_id),
                )

            conn.commit()
            print(
                f"Gebruiker '{naam}' actief met ID {gebruiker_id}, categorieën ingesteld."
            )

    def get_all_users(self):
        """Haal alle gebruikers op"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, naam FROM gebruikers ORDER BY naam")
            gebruikers = cursor.fetchall()
            return gebruikers

    def delete_user(self, naam):
        """Verwijder een gebruiker op naam"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gebruikers WHERE naam = ?", (naam,))
            conn.commit()

    def get_user_id(self, naam):
        """Haal het ID op van een gebruiker"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM gebruikers WHERE naam = ?", (naam,))
            gebruiker_id = cursor.fetchone()
            return gebruiker_id[0] if gebruiker_id else None

    # === CATEGORIEËN BEHEREN ===

    def update_category(
        self, oude_naam, nieuwe_naam, nieuw_type, nieuwe_beschrijving, gebruiker_id
    ):
        """Update een categorie (alleen eigen categorieën)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE categorieen
                SET naam = ?, type = ?, beschrijving = ?
                WHERE naam = ? AND gebruiker_id = ?
                """,
                (nieuwe_naam, nieuw_type, nieuwe_beschrijving, oude_naam, gebruiker_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_category(self, naam, gebruiker_id):
        """Verwijder een categorie (alleen eigen categorieën)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            # Verplaats transacties naar Ongecategoriseerd
            cursor.execute(
                """
                UPDATE transacties
                SET categorie = 'Ongecategoriseerd'
                WHERE categorie = ? AND gebruiker_id = ?
                """,
                (naam, gebruiker_id),
            )
            transacties_aangepast = cursor.rowcount
            # Verwijder de categorie
            cursor.execute(
                "DELETE FROM categorieen WHERE naam = ? AND gebruiker_id = ?",
                (naam, gebruiker_id),
            )
            conn.commit()
            return transacties_aangepast, cursor.rowcount > 0

    def get_user_categories(self, gebruiker_id):
        """Haal alleen de categorieën van een specifieke gebruiker (niet global)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT naam, type, beschrijving
                FROM categorieen
                WHERE gebruiker_id = ?
                ORDER BY type, naam
                """,
                (gebruiker_id,),
            )
            return cursor.fetchall()

    def is_category_global(self, naam):
        """Check of een categorie globaal is (geen gebruiker_id)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM categorieen WHERE naam = ? AND gebruiker_id IS NULL",
                (naam,),
            )
            return cursor.fetchone()[0] > 0

    # === REGELS BEHEREN ===

    def update_rule(
        self, oude_zoekterm, nieuwe_zoekterm, nieuwe_categorie, gebruiker_id
    ):
        """Update een categorisatie regel (alleen eigen regels)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE categorisatie_regels
                SET zoekterm = ?, categorie = ?
                WHERE zoekterm = ? AND gebruiker_id = ?
                """,
                (nieuwe_zoekterm, nieuwe_categorie, oude_zoekterm, gebruiker_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_rule(self, zoekterm, gebruiker_id):
        """Verwijder een categorisatie regel (alleen eigen regels)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM categorisatie_regels WHERE zoekterm = ? AND gebruiker_id = ?",
                (zoekterm, gebruiker_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_user_rules(self, gebruiker_id):
        """Haal alleen de regels van een specifieke gebruiker (niet global)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT zoekterm, categorie
                FROM categorisatie_regels
                WHERE gebruiker_id = ? AND actief = 1
                ORDER BY categorie, zoekterm
                """,
                (gebruiker_id,),
            )
            return cursor.fetchall()

    def is_rule_global(self, zoekterm):
        """Check of een regel globaal is (geen gebruiker_id)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM categorisatie_regels WHERE zoekterm = ? AND gebruiker_id IS NULL",
                (zoekterm,),
            )
            return cursor.fetchone()[0] > 0

    def is_category_standaard(self, naam):
        """Check of een categorie standaard is (uit YAML config)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM categorieen WHERE naam = ? AND is_standaard = 1",
                (naam,),
            )
            return cursor.fetchone()[0] > 0

    def is_rule_standaard(self, zoekterm):
        """Check of een regel standaard is (uit YAML config)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM categorisatie_regels WHERE zoekterm = ? AND is_standaard = 1",
                (zoekterm,),
            )
            return cursor.fetchone()[0] > 0

    def update_transaction_category_by_id(
        self, transaction_id, categorie, gebruiker_id
    ):
        """Update categorie van een transactie op basis van ID."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE transacties SET categorie = ? WHERE id = ? AND gebruiker_id = ?",
                (categorie, transaction_id, gebruiker_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def uncategorize_transaction(self, transaction_id, gebruiker_id):
        """Zet de categorie van een transactie op NULL (ongecategoriseerd)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE transacties SET categorie = NULL WHERE id = ? AND gebruiker_id = ?",
                (transaction_id, gebruiker_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_transaction_by_id(self, transaction_id, gebruiker_id):
        """Haal een enkele transactie op basis van ID."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transacties WHERE id = ? AND gebruiker_id = ?",
                (transaction_id, gebruiker_id),
            )
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
