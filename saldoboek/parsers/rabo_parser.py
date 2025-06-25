import pandas as pd
import os

class RaboParser:
    """Parser voor Rabobank CSV bestanden"""
    
    def __init__(self):
        self.omschrijving_kolommen = ['Omschrijving-1', 'Omschrijving-2', 'Omschrijving-3']

    def parse_csv(self, filepath):
        """Parse Rabobank CSV-bestanden (zowel betaal- als spaarrekening)"""
        try:
            # Probeer verschillende encodings
            df = self._read_csv_with_encoding(filepath)
    
            if df.empty:
                print(f"Waarschuwing: {filepath} is leeg")
                return pd.DataFrame()
    
            rekeningtype = self._ask_account_type(filepath)
            
            # Verwerk de data
            processed_df = self._process_rabobank_data(df, rekeningtype)
            
            self._print_import_summary(filepath, processed_df, rekeningtype)
            return processed_df
    
        except Exception as e:
            print(f"Fout bij lezen van {filepath}: {e}")
            return pd.DataFrame()

    def _read_csv_with_encoding(self, filepath):
        """Probeer CSV te lezen met verschillende encodings"""
        encodings = ['iso-8859-1', 'utf-8', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(filepath, encoding=encoding, sep=',', quotechar='"')
                if not df.empty:
                    print(f"  Bestand gelezen met encoding: {encoding}")
                    return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"  Fout met encoding {encoding}: {e}")
                continue
        
        raise Exception("Kon bestand niet lezen met beschikbare encodings")

    def _ask_account_type(self, filepath):
        """Vraag gebruiker om rekeningtype"""
        print(f"\nBestand: {filepath}")
        while True:
            keuze = input("Rekeningtype? (b = betaalrekening, s = spaarrekening): ").strip().lower()
            if keuze == 'b':
                return 'betaalrekening'
            elif keuze == 's':
                return 'spaarrekening'
            else:
                print("Ongeldige invoer. Kies 'b' of 's'.")

    def _process_rabobank_data(self, df, rekeningtype):
        """Verwerk Rabobank data naar gestandaardiseerd formaat"""
        # Kolomnamen strippen van spaties
        df.columns = df.columns.str.strip()
        
        # Controleer of vereiste kolommen aanwezig zijn
        required_columns = ['Datum', 'Bedrag', 'IBAN/BBAN']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise Exception(f"Ontbrekende kolommen: {missing_columns}")

        # Datum conversie
        df['datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d', errors='coerce')
        
        # Bedrag conversie (van Nederlands formaat naar float)
        df['bedrag'] = self._convert_dutch_currency(df['Bedrag'])
        
        # Saldo conversie
        if 'Saldo na trn' in df.columns:
            df['saldo_voor'] = self._convert_dutch_currency(df['Saldo na trn'])
        else:
            df['saldo_voor'] = 0.0

        # Omschrijving samenvoegen
        df['omschrijving'] = self._merge_descriptions(df)

        # Maak nieuwe DataFrame met gestandaardiseerde kolommen
        nieuwe_df = pd.DataFrame({
            'datum': df['datum'],
            'rekening': df['IBAN/BBAN'],
            'tegenrekening': df.get('Tegenrekening IBAN/BBAN', ''),
            'naam': df.get('Naam tegenpartij', '').fillna(''),
            'valuta': df.get('Munt', 'EUR'),
            'saldo_voor': df['saldo_voor'],
            'bedrag': df['bedrag'],
            'omschrijving': df['omschrijving'],
            'rekeningtype': rekeningtype
        })

        # Verwijder rijen met ontbrekende essentiële data
        nieuwe_df.dropna(subset=['datum', 'bedrag'], inplace=True)
        
        return nieuwe_df

    def _convert_dutch_currency(self, series):
        """Converteer Nederlands valuta formaat (1.234,56) naar float"""
        return series.astype(str).str.replace('.', '').str.replace(',', '.').astype(float)

    def _merge_descriptions(self, df):
        """Voeg omschrijvingskolommen samen tot één kolom"""
        available_desc_cols = [col for col in self.omschrijving_kolommen if col in df.columns]
        
        if not available_desc_cols:
            return df.get('Naam tegenpartij', '').fillna('')
        
        omschrijving_data = df[available_desc_cols].fillna('')
        return omschrijving_data.apply(
            lambda x: ' '.join(filter(None, x)).strip(), axis=1
        )

    def _print_import_summary(self, filepath, df, rekeningtype):
        """Print samenvatting van geïmporteerde data"""
        print(f"✓ {os.path.basename(filepath)} succesvol gelezen: {len(df)} transacties")
        print(f"  Rekeningtype: {rekeningtype}")
        if not df.empty:
            print(f"  Periode: {df['datum'].min().strftime('%d-%m-%Y')} tot {df['datum'].max().strftime('%d-%m-%Y')}")
