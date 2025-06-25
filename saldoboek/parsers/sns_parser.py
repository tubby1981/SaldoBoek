import pandas as pd
import os

class SNSParser:
    """Parser voor SNS Bank CSV bestanden"""
    
    def __init__(self):
        self.kolom_mapping = {
            0: 'datum', 1: 'rekening', 2: 'tegenrekening', 3: 'naam',
            7: 'valuta', 8: 'saldo_voor', 10: 'bedrag', 17: 'omschrijving'
        }
        self.relevante_kolommen = [0, 1, 2, 3, 7, 8, 10, 17]

    def parse_csv(self, filepath):
        """Parse SNS Bank CSV bestanden met correcte kolomindeling"""
        try:
            df = pd.read_csv(filepath, header=None, encoding='utf-8')
            if df.empty:
                print(f"Waarschuwing: {filepath} is leeg")
                return pd.DataFrame()

            rekeningtype = self._ask_account_type(filepath)
            
            # Controleer beschikbare kolommen
            beschikbare_kolommen = [col for col in self.relevante_kolommen if col < len(df.columns)]

            if len(beschikbare_kolommen) < 6:
                print(f"Waarschuwing: {filepath} heeft niet genoeg kolommen ({len(df.columns)} gevonden)")
                return pd.DataFrame()

            # Maak nieuwe DataFrame met juiste kolomnamen
            nieuwe_df = pd.DataFrame()
            for col_idx in beschikbare_kolommen:
                if col_idx in self.kolom_mapping:
                    nieuwe_df[self.kolom_mapping[col_idx]] = df[col_idx]

            # Vul ontbrekende omschrijving
            if 'omschrijving' not in nieuwe_df.columns:
                nieuwe_df['omschrijving'] = nieuwe_df.get('naam', 'Geen omschrijving')
            nieuwe_df['omschrijving'] = nieuwe_df['omschrijving'].fillna('').astype(str)

            # Voeg rekeningtype toe
            nieuwe_df['rekeningtype'] = rekeningtype
            
            # Converteer datatypes
            nieuwe_df = self._convert_datatypes(nieuwe_df)
            
            # Verwijder rijen met ontbrekende essentiële data
            nieuwe_df.dropna(subset=['datum', 'bedrag'], inplace=True)

            self._print_import_summary(filepath, nieuwe_df, rekeningtype)
            return nieuwe_df

        except Exception as e:
            print(f"Fout bij lezen van {filepath}: {e}")
            return pd.DataFrame()

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
                print("Ongeldige invoer. Kies 'b' voor betaalrekening of 's' voor spaarrekening.")

    def _convert_datatypes(self, df):
        """Converteer kolommen naar juiste datatypes"""
        df['datum'] = pd.to_datetime(df['datum'], format='%d-%m-%Y', errors='coerce')
        df['bedrag'] = pd.to_numeric(df['bedrag'], errors='coerce')
        df['saldo_voor'] = pd.to_numeric(df['saldo_voor'], errors='coerce')
        return df

    def _print_import_summary(self, filepath, df, rekeningtype):
        """Print samenvatting van geïmporteerde data"""
        print(f"✓ {os.path.basename(filepath)} succesvol gelezen: {len(df)} transacties")
        print(f"  Rekeningtype: {rekeningtype}")
        if not df.empty:
            print(f"  Periode: {df['datum'].min().strftime('%d-%m-%Y')} tot {df['datum'].max().strftime('%d-%m-%Y')}")
