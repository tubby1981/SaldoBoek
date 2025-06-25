class Categorizer:
    def __init__(self, db_manager, gebruiker_id):
        self.db = db_manager
        self.gebruiker_id = gebruiker_id
        self.rules = self._load_rules()

    def _load_rules(self):
        """Laad categorisatie regels uit database"""
        regels = self.db.execute(
            "SELECT zoekterm, categorie FROM categorisatie_regels WHERE actief = 1 AND (gebruiker_id = ? OR gebruiker_id IS NULL)",
            (self.gebruiker_id,),
            fetch=True
        )
        return {term.lower(): cat for term, cat in regels}

    def categorize(self, naam, omschrijving):
        """Bepaal categorie op basis van naam en omschrijving"""
        tekst = f"{naam} {omschrijving}".lower()

        # Zoek naar match in categorisatie regels
        for zoekterm, categorie in self.rules.items():
            if zoekterm in tekst:
                return categorie
        return None

    def create_new_category(self):
        """Maak nieuwe categorie aan"""
        print("\n--- Nieuwe categorie maken ---")
        naam = input("Categorie naam: ").strip()
        if not naam:
            return None
        
        print("Type: 1=inkomsten, 2=uitgaven")
        type_keuze = input("Type (1/2): ").strip()
        cat_type = 'inkomsten' if type_keuze == '1' else 'uitgaven'
        
        beschrijving = input("Beschrijving (optioneel): ").strip()

        try:
            self.db.execute(
                'INSERT INTO categorieen (naam, type, beschrijving, gebruiker_id) VALUES (?, ?, ?, ?)', 
                (naam, cat_type, beschrijving, self.gebruiker_id)
            )
            print(f"✓ Categorie '{naam}' toegevoegd")
            return naam
        except:
            print(f"! Categorie '{naam}' bestaat al")
            return None

    def add_categorization_rule(self, zoekterm, categorie):
        """Voeg categorisatie regel toe als deze nog niet bestaat voor deze gebruiker"""
        zoekterm_lower = zoekterm.lower()
    
        # Controleer of regel al bestaat voor deze gebruiker
        bestaand = self.db.execute(
            '''
            SELECT 1 FROM categorisatie_regels
            WHERE zoekterm = ? AND gebruiker_id = ?
            ''',
            (zoekterm_lower, self.gebruiker_id),
            fetch=True
        )
    
        if bestaand:
            print(f"! Regel bestaat al voor deze gebruiker: '{zoekterm_lower}'")
            return
   
        self.db.execute(
            '''
            INSERT INTO categorisatie_regels (zoekterm, categorie, gebruiker_id)
            VALUES (?, ?, ?)
            ''',
            (zoekterm_lower, categorie, self.gebruiker_id)
        )
        self.rules[zoekterm_lower] = categorie
        print(f"✓ Regel toegevoegd: '{zoekterm_lower}' → '{categorie}'")

    def update_transaction_category(self, item, categorie):
        """Update categorie van transactie"""
 
        self.db.execute('''
            UPDATE transacties
            SET categorie = ?
            WHERE datum = ? AND omschrijving = ? AND bedrag = ? AND gebruiker_id = ?
            ''', (categorie, item['datum'], item['omschrijving'], item['bedrag'], self.gebruiker_id)
        )
        print(f"✓ Transactie gecategoriseerd als '{categorie}'")

    def manage_categories(self, gebruiker_id):
        """Categorieën beheren"""
        while True:
            print("\n=== CATEGORIEËN BEHEER ===")
            print("1. Alle categorieën tonen")
            print("2. Nieuwe categorie toevoegen")
            print("3. Categorisatie regels tonen")
            print("4. Nieuwe categorisatie regel toevoegen")
            print("5. Transacties hercategoriseren")
            print("6. Terug naar hoofdmenu")
            
            keuze = input("\nKeuze (1-6): ").strip()
            
            if keuze == '1':
                self._show_all_categories(gebruiker_id)
            elif keuze == '2':
                self.create_new_category()
            elif keuze == '3':
                self._show_categorization_rules(gebruiker_id)
            elif keuze == '4':
                self._add_new_rule(gebruiker_id)
            elif keuze == '5':
                self._recategorize_transactions(gebruiker_id)
            elif keuze == '6':
                print("Programma afgesloten.")
                break

            #elif keuze == '7':
            #    manager.categoriseer_bestaande_ongecategoriseerde_transacties()
            #    break
            else:
                print("Ongeldige keuze.")

    def _show_all_categories(self, gebruiker_id):
        """Toon alle categorieën"""
        categorieën = self.db.get_categories(self.gebruiker_id)
        
        print(f"\n=== ALLE CATEGORIEËN ({len(categorieën)}) ===")
        inkomsten_cat = [c for c in categorieën if c[1] == 'inkomsten']
        uitgaven_cat = [c for c in categorieën if c[1] == 'uitgaven']
        
        print(f"\nINKOMSTEN CATEGORIEËN ({len(inkomsten_cat)}):")
        for naam, type_cat, beschrijving in inkomsten_cat:
            print(f"  • {naam}: {beschrijving}")
        
        print(f"\nUITGAVEN CATEGORIEËN ({len(uitgaven_cat)}):")
        for naam, type_cat, beschrijving in uitgaven_cat:
            print(f"  • {naam}: {beschrijving}")

    def _show_categorization_rules(self, gebruiker_id):
        """Toon categorisatie regels"""
        regels = self.db.execute(
            'SELECT zoekterm, categorie FROM categorisatie_regels WHERE actief = 1 AND (gebruiker_id = ? OR gebruiker_id IS NULL) ORDER BY categorie, zoekterm',
            (self.gebruiker_id,),
            fetch=True
        )

        print(f"\n=== CATEGORISATIE REGELS ({len(regels)}) ===")
        current_cat = None

        for zoekterm, categorie in regels:
            if categorie != current_cat:
                print(f"\n{categorie}:")
                current_cat = categorie
            print(f"  • '{zoekterm}'")

    def _add_new_rule(self, gebruiker_id):
        """Voeg nieuwe categorisatie regel toe"""
        print("\n--- Nieuwe categorisatie regel ---")
        zoekterm = input("Zoekterm: ").strip()
        if not zoekterm:
            return
        
        categorieën = self.db.get_categories(self.gebruiker_id)
        print("\nBeschikbare categorieën:")
        for i, (cat_naam, cat_type, cat_desc) in enumerate(categorieën, 1):
            print(f"{i:2d}. {cat_naam} ({cat_type})")
        
        try:
            keuze = int(input("Kies categorie (nummer): ")) - 1
            if 0 <= keuze < len(categorieën):
                categorie = categorieën[keuze][0]
                self.add_categorization_rule(zoekterm, categorie)
            else:
                print("Ongeldig nummer.")
        except ValueError:
            print("Ongeldige invoer.")
    
    def _recategorize_transactions(self, gebruiker_id):
        """Hercategoriseer transacties"""
        print("\n--- Transacties hercategoriseren ---")
        print("1. Alle 'Ongecategoriseerd' transacties")
        print("2. Alle transacties")
        print("3. Specifieke categorie")
        
        keuze = input("Keuze (1-3): ").strip()
    
        if keuze == '1':
            query = "SELECT * FROM transacties WHERE categorie = 'Ongecategoriseerd' AND gebruiker_id = ?"
        elif keuze == '2':
            query = "SELECT * FROM transacties WHERE gebruiker_id = ?"
        elif keuze == '3':
            categorie = input("Welke categorie hercategoriseren? ").strip()
            query = f"SELECT * FROM transacties WHERE categorie = '{categorie}' AND gebruiker_id = ?"
        else:
            print("Ongeldige keuze.")
            return
        
        df = self.db.query_df(query, (self.gebruiker_id,))  # Veronderstel dat `db.query_df` een pandas DataFrame retourneert
        
        if df.empty:
            print("Geen transacties gevonden om te hercategoriseren.")
            return
    
        print(f"\n{len(df)} transacties gevonden voor hercategorisatie...")
    
        hercategoriseerd = 0
        for _, row in df.iterrows():
            oude_categorie = row['categorie']
            omschrijving = str(row['omschrijving']) if row['omschrijving'] else ""
            nieuwe_categorie = self.categorize(row['naam'], omschrijving)
    
            if nieuwe_categorie and nieuwe_categorie != oude_categorie:
                self.db.execute(
                    "UPDATE transacties SET categorie = ? WHERE id = ? AND gebruiker_id = ?",
                    (nieuwe_categorie, row['id'], self.gebruiker_id)
                )
                hercategoriseerd += 1
                print(f"  {row['datum']} | {omschrijving[:30]:30} | {oude_categorie} → {nieuwe_categorie}")
    
        print(f"\n✓ {hercategoriseerd} transacties hercategoriseerd")   
   
    def categoriseer_bestaande_ongecategoriseerde_transacties(self, gebruiker_id):

        df = self.db.execute_df("SELECT * FROM transacties WHERE categorie = 'Ongecategoriseerd' AND gebruiker_id = ?", (self.gebruiker_id,))

        if df.empty:
            print("Er zijn geen ongecategoriseerde transacties.")
            return
    
        print(f"\nEr zijn {len(df)} ongecategoriseerde transacties.")
    
        # Haal alle categorieën op
        alle_categorieën = self.db.get_categories(self.gebruiker_id)
    
        print("\nOpties bij elke transactie:")
        print("- Voer nummer in voor categorie")
        print("- 'n' voor nieuwe categorie maken")
        print("- 's' om te skippen (blijft ongecategoriseerd)")
        print("- 'q' om te stoppen met categoriseren")
    
        for _, row in df.iterrows():
            print(f"\n{'='*60}")
            print(f"Datum:         {row['datum']}")
            print(f"Rekening:      {row['rekening']}")
            print(f"Tegenrekening: {row['tegenrekening']}")
            print(f"Naam:          {row['naam']}")
            print(f"Omschrijving:  {row['omschrijving']}")
            print(f"Bedrag:        €{row['bedrag']:.2f}")
            
            # Filter categorieën op basis van bedrag (positief = inkomsten, negatief = uitgaven)
            if row['bedrag'] > 0:
                relevante_categorieën = [c for c in alle_categorieën if c[1] == 'inkomsten']
                print(f"\nBeschikbare INKOMSTEN categorieën:")
            else:
                relevante_categorieën = [c for c in alle_categorieën if c[1] == 'uitgaven']
                print(f"\nBeschikbare UITGAVEN categorieën:")
            
            for i, (cat_naam, cat_type, cat_desc) in enumerate(relevante_categorieën, 1):
                print(f"{i:2d}. {cat_naam} ({cat_type})")
    
            while True:
                keuze = input("Categorie keuze: ").strip().lower()
                if keuze == 'q':
                    print("Categorisatie gestopt.")
                    return
    
                elif keuze == 's':
                    break
    
                elif keuze == 'n':
                    nieuwe_cat = self.create_new_category()
                    if nieuwe_cat:
                        self.db.execute(
                            "UPDATE transacties SET categorie = ? WHERE id = ? AND gebruiker_id = ?",
                            (nieuwe_cat, row['id'], self.gebruiker_id)
                        )
                        if input("Wilt u een regel toevoegen voor toekomstige herkenning? (j/n): ").lower() == 'j':
                            zoekterm = input("Zoekterm: ").strip()
                            if zoekterm:
                                self.add_categorization_rule(zoekterm, nieuwe_cat)
                    break
    
                else:
                    try:
                        index = int(keuze) - 1
                        if 0 <= index < len(relevante_categorieën):
                            gekozen = relevante_categorieën[index][0]
                            self.db.execute(
                                "UPDATE transacties SET categorie = ? WHERE id = ? AND gebruiker_id = ?",
                                (gekozen, row['id'], self.gebruiker_id)
                            )
                            if input("Wilt u een regel toevoegen voor toekomstige herkenning? (j/n): ").lower() == 'j':
                                zoekterm = input("Zoekterm: ").strip()
                                if zoekterm:
                                    self.add_categorization_rule(zoekterm, gekozen)
                            break
                        else:
                            print("Ongeldig nummer. Probeer opnieuw.")
                    except ValueError:
                        print("Ongeldige invoer. Probeer opnieuw.")
    
        print("✓ Categorisatie van alle ongecategoriseerde transacties voltooid.")
