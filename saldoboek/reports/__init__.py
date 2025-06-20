from .sheet_income import create_income_sheet
from .sheet_expenses import create_expenses_sheet
from .sheet_overview import create_overview_sheet
from .sheet_monthly import create_monthly_sheet
from .sheet_monthly_category import create_monthly_category_sheet
from .sheet_transactions import create_transactions_sheet
from .sheet_balances import create_balance_sheet
from .summary import print_report_summary

import pandas as pd
from openpyxl import Workbook
from datetime import datetime

class ReportGenerator:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_excel_yearly_report(self, jaar, gebruiker_id, gebruiker_naam, output_path=None, split_per_rekening=True):
        if not output_path:
            output_path = f"{gebruiker_id}_jaaroverzicht_{jaar}.xlsx"

        query = """
            SELECT datum, rekening, tegenrekening, naam, omschrijving, bedrag, saldo_voor, categorie, rekeningtype
            FROM transacties
            WHERE strftime('%Y', datum) = ? AND gebruiker_id = ?
            ORDER BY datum
        """
        rows = self.db.execute(query, (str(jaar), gebruiker_id), fetch=True)

        if not rows:
            print(f"Geen transacties gevonden voor {jaar}")
            return

        columns = ['datum', 'rekening', 'tegenrekening', 'naam', 'omschrijving', 'bedrag', 'saldo_voor', 'categorie', 'rekeningtype']
        df = pd.DataFrame(rows, columns=columns)

        wb = Workbook()
        wb.remove(wb.active)

        # Sheets voor alle rekeningen samen
        create_overview_sheet(wb, df, jaar)
        create_monthly_sheet(wb, df, jaar)
        create_transactions_sheet(wb, df, jaar)
        create_balance_sheet(wb, df, jaar)

        # Sheets die optioneel per rekening worden gesplitst
        if split_per_rekening:
            for rekening in df['rekening'].unique():
                df_rekening = df[df['rekening'] == rekening]

                # Eerste 4 + laatste 4 tekens van de rekening
                rekening_kort = rekening[4:8] + rekening[-4:] if rekening else ""
                suffix = f" {rekening_kort}" if rekening else ""
                create_income_sheet(wb, df_rekening, jaar, suffix)
                create_expenses_sheet(wb, df_rekening, jaar, suffix)
                create_monthly_category_sheet(wb, df_rekening, jaar, suffix)
        else:
            create_income_sheet(wb, df, jaar)
            create_expenses_sheet(wb, df, jaar)
            create_monthly_category_sheet(wb, df, jaar)

        wb.save(output_path)
        print(f"✓ Excel rapport opgeslagen: {output_path}")
        print_report_summary(df, jaar)
