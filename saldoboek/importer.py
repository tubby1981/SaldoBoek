import pandas as pd
import os
from .config.bank_parsers import BANK_PARSERS

class TransactionImporter:
    def __init__(self, categorizer, db_manager, gebruiker_id):
        self.categorizer = categorizer
        self.db = db_manager
        self.gebruiker_id = gebruiker_id

    def detect_bank_and_parse(self, filepath):
        filename = os.path.basename(filepath).upper()

        for bank_code, parser_method in BANK_PARSERS.items():
            if bank_code in filename:
                return getattr(self, parser_method)(filepath)

        raise ValueError(f"Onbekend bankformaat in bestandsnaam: {filename}")        

    def parse_sns_csv(self, filepath):
        """Parse SNS Bank CSV bestanden met correcte kolomindeling"""
        try:
            df = pd.read_csv(filepath, header=None, encoding='utf-8')
            if df.empty:
                print(f"Waarschuwing: {filepath} is leeg")
                return pd.DataFrame()

            #rekeningtype = detect_account_type(filepath)
            print(f"\nBestand: {filepath}")
            while True:
                keuze = input("Rekeningtype? (b = betaalrekening, s = spaarrekening): ").strip().lower()
                if keuze == 'b':
                    rekeningtype = 'betaalrekening'
                    break
                elif keuze == 's':
                    rekeningtype = 'spaarrekening'
                    break
                else:
                    print("Ongeldige invoer. Kies 'b' voor betaalrekening of 's' voor spaarrekening.")

            kolom_mapping = {
                0: 'datum', 1: 'rekening', 2: 'tegenrekening', 3: 'naam',
                7: 'valuta', 8: 'saldo_voor', 10: 'bedrag', 17: 'omschrijving'
            }
            relevante_kolommen = [0, 1, 2, 3, 7, 8, 10, 17]
            beschikbare_kolommen = [col for col in relevante_kolommen if col < len(df.columns)]

            if len(beschikbare_kolommen) < 6:
                print(f"Waarschuwing: {filepath} heeft niet genoeg kolommen ({len(df.columns)} gevonden)")
                return pd.DataFrame()

            nieuwe_df = pd.DataFrame()
            for col_idx in beschikbare_kolommen:
                if col_idx in kolom_mapping:
                    nieuwe_df[kolom_mapping[col_idx]] = df[col_idx]

            if 'omschrijving' not in nieuwe_df.columns:
                nieuwe_df['omschrijving'] = nieuwe_df.get('naam', 'Geen omschrijving')
            nieuwe_df['omschrijving'] = nieuwe_df['omschrijving'].fillna('').astype(str)

            nieuwe_df['rekeningtype'] = rekeningtype
            nieuwe_df['datum'] = pd.to_datetime(nieuwe_df['datum'], format='%d-%m-%Y', errors='coerce')
            nieuwe_df['bedrag'] = pd.to_numeric(nieuwe_df['bedrag'], errors='coerce')
            nieuwe_df['saldo_voor'] = pd.to_numeric(nieuwe_df['saldo_voor'], errors='coerce')
            nieuwe_df.dropna(subset=['datum', 'bedrag'], inplace=True)

            print(f"✓ {filepath} succesvol gelezen: {len(nieuwe_df)} transacties")
            print(f"  Rekeningtype: {rekeningtype}")
            print(f"  Periode: {nieuwe_df['datum'].min().strftime('%d-%m-%Y')} tot {nieuwe_df['datum'].max().strftime('%d-%m-%Y')}")
            return nieuwe_df

        except Exception as e:
            print(f"Fout bij lezen van {filepath}: {e}")
            return pd.DataFrame()

    def parse_rabo_csv(self, filepath):
        """Parse Rabobank CSV-bestanden (zowel betaal- als spaarrekening)"""
        try:
            #df = pd.read_csv(filepath, encoding='utf-8', sep=',', quotechar='"')
            df = pd.read_csv(filepath, encoding='iso-8859-1', sep=',', quotechar='"')
    
            if df.empty:
                print(f"Waarschuwing: {filepath} is leeg")
                return pd.DataFrame()
    
            print(f"\nBestand: {filepath}")
            while True:
                keuze = input("Rekeningtype? (b = betaalrekening, s = spaarrekening): ").strip().lower()
                if keuze == 'b':
                    rekeningtype = 'betaalrekening'
                    break
                elif keuze == 's':
                    rekeningtype = 'spaarrekening'
                    break
                else:
                    print("Ongeldige invoer. Kies 'b' of 's'.")
            
            # Kolomnamen strippen van spaties
            df.columns = df.columns.str.strip()
    
            df['datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d', errors='coerce')
            df['bedrag'] = df['Bedrag'].str.replace('.', '').str.replace(',', '.').astype(float)
            df['saldo_voor'] = df['Saldo na trn'].str.replace('.', '').str.replace(',', '.').astype(float)
    
            # Omschrijving samenvoegen
            omschrijving = df[['Omschrijving-1', 'Omschrijving-2', 'Omschrijving-3']].fillna('')
            df['omschrijving'] = omschrijving.apply(lambda x: ' '.join(filter(None, x)).strip(), axis=1)
    
            nieuwe_df = pd.DataFrame({
                'datum': df['datum'],
                'rekening': df['IBAN/BBAN'],
                'tegenrekening': df['Tegenrekening IBAN/BBAN'],
                'naam': df['Naam tegenpartij'].fillna(''),
                'valuta': df['Munt'],
                'saldo_voor': df['saldo_voor'],
                'bedrag': df['bedrag'],
                'omschrijving': df['omschrijving'],
                'rekeningtype': rekeningtype
            })
    
            nieuwe_df.dropna(subset=['datum', 'bedrag'], inplace=True)
    
            print(f"✓ {filepath} succesvol gelezen: {len(nieuwe_df)} transacties")
            print(f"  Rekeningtype: {rekeningtype}")
            print(f"  Periode: {nieuwe_df['datum'].min().strftime('%d-%m-%Y')} tot {nieuwe_df['datum'].max().strftime('%d-%m-%Y')}")
            return nieuwe_df
    
        except Exception as e:
            print(f"Fout bij lezen van {filepath}: {e}")
            return pd.DataFrame()
            
    def import_transactions_with_categorization(self, file_paths, gebruiker_id):
        """Importeer transacties met interactieve categorisatie"""
        ongecategoriseerd = []
        total_imported = 0
    
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"Bestand niet gevonden: {file_path}")
                continue
    
            print(f"\nVerwerken: {file_path}")
    
            try:
                df = self.detect_bank_and_parse(file_path)
            except ValueError as e:
                print(f"  ! {e}")
                continue
    
            if df.empty:
                continue
    
            nieuwe_transacties = 0
            duplicaten = 0
    
            for _, row in df.iterrows():
                datum_str = row['datum'].strftime('%Y-%m-%d')
                bestaande = self.db.execute(
                    '''
                    SELECT COUNT(*) FROM transacties 
                    WHERE datum = ? AND rekening = ? AND bedrag = ? AND omschrijving = ? AND gebruiker_id = ?
                    ''',
                    (datum_str, row['rekening'], row['bedrag'], row['omschrijving'], self.gebruiker_id),
                    fetch=True
                )
    
                if bestaande[0][0] == 0:
                    categorie = self.categorizer.categorize(
                        row.get('naam', ''),
                        row['omschrijving']
                    )
    
                    if not categorie:
                        ongecategoriseerd.append({
                            'naam': row.get('naam', ''),
                            'omschrijving': row['omschrijving'],
                            'rekening': row['rekening'],
                            'tegenrekening': row['tegenrekening'],
                            'bedrag': row['bedrag'],
                            'datum': datum_str,
                            'row_data': row
                        })
                        categorie = 'Ongecategoriseerd'
    
                    self.db.execute(
                        '''
                        INSERT INTO transacties 
                        (datum, rekening, tegenrekening, naam, omschrijving, bedrag, saldo_voor, valuta, categorie, rekeningtype, gebruiker_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            datum_str,
                            row['rekening'],
                            row.get('tegenrekening', ''),
                            row.get('naam', ''),
                            row['omschrijving'],
                            row['bedrag'],
                            row.get('saldo_voor', 0),
                            row.get('valuta', 'EUR'),
                            categorie,
                            row['rekeningtype'],
                            self.gebruiker_id
                        )
                    )
                    nieuwe_transacties += 1
                else:
                    duplicaten += 1
    
            print(f"  ✓ {nieuwe_transacties} nieuwe transacties geïmporteerd")
            if duplicaten > 0:
                print(f"  ! {duplicaten} duplicaten overgeslagen")
            total_imported += nieuwe_transacties
    
        if ongecategoriseerd:
            self._handle_uncategorized_transactions(ongecategoriseerd)
    
        print(f"\n=== Import voltooid ===")
        print(f"Totaal nieuwe transacties: {total_imported}")
        if ongecategoriseerd:
            print(f"Ongecategoriseerd: {len([t for t in ongecategoriseerd if t.get('categorie') == 'Ongecategoriseerd'])}")
    
        return total_imported
    
    def _handle_uncategorized_transactions(self, ongecategoriseerd):
        print(f"\n=== HANDMATIGE CATEGORISATIE VEREIST ===")
        print(f"{len(ongecategoriseerd)} transacties vereisen handmatige categorisatie")

        # Toon beschikbare categorieën
        categorieën = self.db.get_categories()
        print("\nBeschikbare categorieën:")
        for i, (cat_naam, cat_type, cat_desc) in enumerate(categorieën, 1):
            print(f"{i:2d}. {cat_naam} ({cat_type})")

        print("\nOpties bij elke transactie:")
        print("- Voer nummer in (1-{}) voor categorie".format(len(categorieën)))
        print("- 'n' voor nieuwe categorie maken")
        print("- 's' om te skippen (blijft ongecategoriseerd)")
        print("- 'q' om te stoppen met categoriseren")

        for item in ongecategoriseerd:
            print(f"\n{'='*60}")
            print(f"Datum:         {item['datum']}")
            print(f"Rekening:      {item['rekening']}")
            print(f"Tegenrekening: {item['tegenrekening']}")
            print(f"Naam:          {item['naam']}")
            print(f"Omschrijving:  {item['omschrijving']}")
            print(f"Bedrag:        €{item['bedrag']:.2f}")            

            while True:
                keuze = input("\nCategorie keuze: ").strip().lower()

                if keuze == 'q':
                    print("Categorisatie gestopt.")
                    return
                elif keuze == 's':
                    break
                elif keuze == 'n':
                    nieuwe_cat = self.db.create_new_category()
                    if nieuwe_cat:
                        self.db.update_transaction_category(item, nieuwe_cat)
                        if input("Wilt u een regel toevoegen voor toekomstige herkenning? (j/n): ").lower() == 'j':
                            zoekterm = input("Zoekterm: ").strip()
                            if zoekterm:
                                self.categorizer.add_categorization_rule(zoekterm, nieuwe_cat)
                    break
                else:
                    try:
                        index = int(keuze) - 1
                        if 0 <= index < len(categorieën):
                            gekozen_categorie = categorieën[index][0]
                            #self.db.update_transaction_category(item, gekozen_categorie)
                            self.categorizer.update_transaction_category(item, gekozen_categorie)
                            if input("Wilt u een regel toevoegen voor toekomstige herkenning? (j/n): ").lower() == 'j':
                                zoekterm = input("Zoekterm: ").strip()
                                if zoekterm:
                                    self.categorizer.add_categorization_rule(zoekterm, gekozen_categorie)
                            break
                        else:
                            print("Ongeldig nummer.")
                    except ValueError:
                        print("Ongeldige invoer.")


