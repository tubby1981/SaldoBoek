import sqlite3
import pandas as pd
import yaml
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
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

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _load_categories_config(self):
        """Laad categorieën uit YAML configuratie"""
        config_file = self.config_dir / "categories.yaml"
        if not config_file.exists():
            print(f"Warning: Config file {config_file} not found, using empty categories")
            return []
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            categories = []
            # Verwerk uitgaven categorieën
            for cat in config.get('uitgaven', []):
                categories.append((cat['naam'], 'uitgaven', cat['beschrijving']))
            
            # Verwerk inkomsten categorieën  
            for cat in config.get('inkomsten', []):
                categories.append((cat['naam'], 'inkomsten', cat['beschrijving']))
                
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
            with open(config_file, 'r', encoding='utf-8') as f:
                rules_dict = yaml.safe_load(f)
            
            # Converteer dictionary naar list of tuples
            rules = [(zoekterm, categorie) for zoekterm, categorie in rules_dict.items()]
            return rules
        except Exception as e:
            print(f"Error loading rules config: {e}")
            return []

    def _initialize(self):
        """Initialiseer de database met benodigde tabellen"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()
        
            # Transacties tabel
            cursor.execute('''
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
            ''')
            
            # Categorieën tabel
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categorieen (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    naam TEXT UNIQUE,
                    type TEXT, -- 'inkomsten' of 'uitgaven'
                    beschrijving TEXT
                )
            ''')
        
            # Categorisatie regels tabel
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categorisatie_regels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gebruiker_id INTEGER,
                    zoekterm TEXT UNIQUE,
                    categorie TEXT,
                    actief BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Gebruikers tabel
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gebruikers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    naam TEXT NOT NULL UNIQUE
                )
            ''')
        
            # Laad categorieën uit configuratie
            standaard_categorieen = self._load_categories_config()
            for cat in standaard_categorieen:
                cursor.execute('INSERT OR IGNORE INTO categorieen (naam, type, beschrijving) VALUES (?, ?, ?)', cat)
            
            # Laad categorisatie regels uit configuratie
            standaard_regels = self._load_rules_config()
            for regel in standaard_regels:
                cursor.execute('INSERT OR IGNORE INTO categorisatie_regels (zoekterm, categorie) VALUES (?, ?)', regel)
            
            conn.commit()

    def reload_config(self):
        """Herlaad configuratie en update database"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()
            
            # Laad en update categorieën
            standaard_categorieen = self._load_categories_config()
            for cat in standaard_categorieen:
                cursor.execute('INSERT OR IGNORE INTO categorieen (naam, type, beschrijving) VALUES (?, ?, ?)', cat)
            
            # Laad en update regels
            standaard_regels = self._load_rules_config()
            for regel in standaard_regels:
                cursor.execute('INSERT OR IGNORE INTO categorisatie_regels (zoekterm, categorie) VALUES (?, ?)', regel)
            
            conn.commit()
            print("Configuration reloaded successfully")

    def get_categories(self, gebruiker_id=None):
        """Haal alle categorieën op"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT naam, type, beschrijving FROM categorieen ORDER BY type, naam')
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
        
            df = pd.read_sql_query(query, conn, params=[gebruiker_id,aantal])
        
            if df.empty:
                print("Geen transacties gevonden")
                return
        
            print(f"\n=== LAATSTE {aantal} TRANSACTIES voor gebruiker: {gebruikersnaam} ===")
            for _, row in df.iterrows():
                print(f"{row['datum']} | €{row['bedrag']:>8.2f} | "
                    f"{(row['naam'] or '')[:20]:20} | "
                    f"{(row['categorie'] or '')[:15]:15} | "
                    f"{(row['omschrijving'] or '')[:50]}")

    def get_database_stats(self, gebruiker_id=None):
        """Toon database statistieken"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()

            # Gebruikersnaam ophalen
            cursor.execute("SELECT naam FROM gebruikers WHERE id = ?", (gebruiker_id,))
            row = cursor.fetchone()
            gebruikersnaam = row[0] if row else "Onbekend"

            # Totaal aantal transacties
            cursor.execute("SELECT COUNT(*) FROM transacties WHERE gebruiker_id = ?", (gebruiker_id,))
            total_transacties = cursor.fetchone()[0]
 
            # Transacties per rekeningtype
            cursor.execute("""
                SELECT rekeningtype, COUNT(*)
                FROM transacties
                GROUP BY rekeningtype
            """)
            per_type = cursor.fetchall()
 
            # Datumbereik
            cursor.execute("SELECT MIN(datum), MAX(datum) FROM transacties WHERE gebruiker_id = ?", (gebruiker_id,))
            datum_bereik = cursor.fetchone()
 
            # Transacties per rekening
            cursor.execute("""
                SELECT rekening, COUNT(*), MIN(datum), MAX(datum)
                FROM transacties WHERE gebruiker_id = ?
                GROUP BY rekening
                ORDER BY COUNT(*) DESC
            """, (gebruiker_id,))
            per_rekening = cursor.fetchall()
 
            # Categorieën statistieken
            cursor.execute("""
                SELECT categorie, COUNT(*), SUM(bedrag)
                FROM transacties WHERE gebruiker_id = ?
                GROUP BY categorie
                ORDER BY COUNT(*) DESC
            """, (gebruiker_id,))
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
        """Voeg een nieuwe gebruiker toe"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO gebruikers (naam) VALUES (?)', (naam,))
            conn.commit()

    def get_all_users(self):
        """Haal alle gebruikers op"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, naam FROM gebruikers ORDER BY naam')
            gebruikers = cursor.fetchall()
            return gebruikers

    def delete_user(self, naam):
        """Verwijder een gebruiker op naam"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM gebruikers WHERE naam = ?', (naam,))
            conn.commit()

    def get_user_id(self, naam):
        """Haal het ID op van een gebruiker"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM gebruikers WHERE naam = ?', (naam,))
            gebruiker_id = cursor.fetchone()
            return gebruiker_id[0] if gebruiker_id else None

