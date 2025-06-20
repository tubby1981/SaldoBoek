class SaldoBoekCLI:
    def __init__(self):
        from .database import DatabaseManager

        self.db = DatabaseManager()
        self.huidige_gebruiker_id = None
        self.huidige_gebruiker_naam = None

    def run(self):
        self.select_user()

        from .categorization import Categorizer
        from .importer import TransactionImporter
        from .reports import ReportGenerator

        self.categorizer = Categorizer(self.db, self.huidige_gebruiker_id)
        self.importer = TransactionImporter(self.categorizer, self.db, self.huidige_gebruiker_id)
        self.reports = ReportGenerator(self.db)

        while True:
            print("\n=== SaldoBoek ===")
            print("1. Transacties importeren")
            print("2. Jaaroverzicht genereren")
            print("3. Database status bekijken")
            print("4. Recente transacties bekijken")
            print("5. Categorieën beheren")
            print("6. Ongecategoriseerde transacties categoriseren")            
            print("7. Afsluiten")
            keuze = input("Keuze: ").strip()
            if keuze == '1':
                paths = input("CSV bestand(en) (gescheiden door komma): ").split(',')
                self.importer.import_transactions_with_categorization([p.strip() for p in paths], self.huidige_gebruiker_id)
            elif keuze == '2':
                jaar_input = input("Voor welk jaar wilt u het Excel overzicht (bijv. 2024)? ").strip()
                if not jaar_input.isdigit():
                    print("Ongeldig jaar ingevoerd")
                    continue
                jaar = int(jaar_input)
                default_filename = f"{self.huidige_gebruiker_naam.lower().replace(' ', '_')}_jaaroverzicht_{jaar}.xlsx"
                output_path = input(f"Output bestand (Enter voor '{default_filename}'): ").strip()
                if not output_path:
                    output_path = default_filename
                self.reports.create_excel_yearly_report(jaar, self.huidige_gebruiker_id, self.huidige_gebruiker_naam, output_path)
            elif keuze == '3':
                self.db.get_database_stats(self.huidige_gebruiker_id)
            elif keuze == '4':
                try:
                    aantal = int(input("Hoeveel recente transacties wilt u zien? (standaard 20): ") or "20")
                    self.db.show_recent_transactions(aantal, self.huidige_gebruiker_id)
                except ValueError:
                    self.db.show_recent_transactions(20, self.huidige_gebruiker_id)
            elif keuze == '5':
                self.categorizer.manage_categories(self.huidige_gebruiker_id)
            elif keuze == '6':
                self.categorizer.categoriseer_bestaande_ongecategoriseerde_transacties(self.huidige_gebruiker_id)                
            elif keuze == '7':
                break
            else:
                print("Ongeldige keuze")

    def select_user(self):
        while True:
            print("\n=== Gebruikersbeheer ===")
            print("1. Gebruiker selecteren")
            print("2. Nieuwe gebruiker aanmaken")
            print("3. Gebruiker verwijderen")
            print("4. Afsluiten")
            keuze = input("Keuze: ").strip()
            if keuze == '1':
                gebruiker_id, gebruiker_naam = self.select_existing_user()
                if gebruiker_id:
                    self.huidige_gebruiker_id = gebruiker_id
                    self.huidige_gebruiker_naam = gebruiker_naam
                    break
            elif keuze == '2':
                naam = input("Naam van nieuwe gebruiker: ").strip()
                self.db.create_user(naam)
            elif keuze == '3':
                naam = input("Naam van te verwijderen gebruiker: ").strip()
                self.db.delete_user(naam)
            elif keuze == '4':
                exit()
            else:
                print("Ongeldige keuze")

    def select_existing_user(self):
        users = self.db.get_all_users()
        if not users:
            print("Geen gebruikers gevonden. Maak eerst een nieuwe gebruiker aan.")
            return None, None
        print("\nBeschikbare gebruikers:")
        for i, user in enumerate(users, 1):
            print(f"{i}. {user[1]}")
        keuze = input("Selecteer gebruiker nummer: ").strip()
        try:
            keuze = int(keuze)
            if 1 <= keuze <= len(users):
                gebruiker_id = users[keuze - 1][0]
                gebruiker_naam = users[keuze - 1][1]
                return gebruiker_id, gebruiker_naam  # <-- wijziging            
            else:
                print("Ongeldige keuze")
                return None, None
        except ValueError:
            print("Ongeldige keuze")
            return None, None

