"""ReportService - Service layer voor rapportage operaties."""

import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportService:
    """Service voor rapportage-gerelateerde operaties."""

    def __init__(self, db_manager, transaction_service):
        """
        Initialiseer ReportService.

        Args:
            db_manager: DatabaseManager instantie
            transaction_service: TransactionService instantie
        """
        self._db = db_manager
        self._transaction_service = transaction_service

    def get_available_report_types(self) -> list:
        """
        Geef de beschikbare rapport types.

        Returns:
            List van (key, display_name) tuples
        """
        return [
            ("overzicht", "Jaar Overzicht"),
            ("maandelijks", "Maandelijks Rapport"),
            ("inkomsten", "Inkomsten Overzicht"),
            ("uitgaven", "Uitgaven Overzicht"),
            ("categorie", "Categorie Overzicht"),
            ("saldi", "Saldi Overzicht"),
            ("alles", "Alles (Volledig Rapport)"),
        ]

    def generate_report(self, report_type: str, jaar: int, gebruiker_id: int) -> tuple:
        """
        Genereer een rapport en sla het op.

        Args:
            report_type: Type rapport (overzicht, maandelijks, etc.)
            jaar: Jaar voor het rapport
            gebruiker_id: Gebruiker ID

        Returns:
            Tuple van (success: bool, filepath: str of error_message: str)

        Raises:
            ValueError: Als rapport type onbekend is
            RuntimeError: Als rapport generatie mislukt
        """
        logger.info("Start rapport generatie: type=%s, jaar=%d", report_type, jaar)

        # Haal transacties op
        df = self._transaction_service.get_transactions(
            filters={"jaar": jaar}, gebruiker_id=gebruiker_id
        )

        if df is None or df.empty:
            raise ValueError("Geen transacties gevonden voor dit jaar")

        # Genereer rapport
        filepath = self._create_report(report_type, df, jaar)

        logger.info("Rapport gegenereerd: %s", filepath)
        return (True, filepath)

    def _create_report(self, report_type: str, df, jaar: int) -> str:
        """
        Creëer het Excel rapport.

        Args:
            report_type: Type rapport
            df: DataFrame met transacties
            jaar: Jaar voor het rapport

        Returns:
            Pad naar het gegenereerde bestand
        """
        from openpyxl import Workbook

        from saldoboek.reports.sheet_balances import create_balance_sheet
        from saldoboek.reports.sheet_expenses import create_expenses_sheet
        from saldoboek.reports.sheet_income import create_income_sheet
        from saldoboek.reports.sheet_monthly import create_monthly_sheet
        from saldoboek.reports.sheet_monthly_category import (
            create_monthly_category_sheet,
        )
        from saldoboek.reports.sheet_overview import create_overview_sheet
        from saldoboek.reports.sheet_transactions import create_transactions_sheet

        wb = Workbook()
        wb.remove(wb.active)

        # Bepaal welke sheets te maken op basis van rapport type
        if report_type == "overzicht":
            create_overview_sheet(wb, df, jaar)
            create_transactions_sheet(wb, df, jaar)
        elif report_type == "maandelijks":
            create_monthly_sheet(wb, df, jaar)
        elif report_type == "inkomsten":
            create_income_sheet(wb, df, jaar)
        elif report_type == "uitgaven":
            create_expenses_sheet(wb, df, jaar)
        elif report_type == "categorie":
            create_monthly_category_sheet(wb, df, jaar)
        elif report_type == "saldi":
            create_balance_sheet(wb, df, jaar)
        elif report_type == "alles":
            # Overkoepelende sheets
            create_overview_sheet(wb, df, jaar)
            create_transactions_sheet(wb, df, jaar)
            create_monthly_sheet(wb, df, jaar)
            create_income_sheet(wb, df, jaar)
            create_expenses_sheet(wb, df, jaar)
            create_monthly_category_sheet(wb, df, jaar)
            create_balance_sheet(wb, df, jaar)

            # Per-rekening sheets (laatste 4 digits van rekeningnummer)
            for rekening in df["rekening"].unique():
                df_rek = df[df["rekening"] == rekening]
                # Gebruik laatste 4 karakters van rekeningnummer (bijv. SNSB1522)
                rekening_short = rekening[-4:] if len(rekening) >= 4 else rekening
                suffix = f" {rekening_short}"
                create_income_sheet(wb, df_rek, jaar, suffix)
                create_expenses_sheet(wb, df_rek, jaar, suffix)
                create_monthly_category_sheet(wb, df_rek, jaar, suffix)
        else:
            raise ValueError(f"Onbekend rapport type: {report_type}")

        # Bepaal output pad
        output_dir = os.path.expanduser("~/Documents/SaldoBoek")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SaldoBoek_{report_type}_{jaar}_{timestamp}.xlsx"
        filepath = os.path.join(output_dir, filename)

        wb.save(filepath)

        return filepath

    def get_output_folder(self) -> str:
        """
        Geef het output folder pad.

        Returns:
            Pad naar de SaldoBoek output folder
        """
        return os.path.expanduser("~/Documents/SaldoBoek")

    def open_output_folder(self) -> None:
        """Open de output folder in de file explorer."""
        folder = self.get_output_folder()
        if os.path.exists(folder):
            import platform

            system = platform.system()
            if system == "Windows":
                os.startfile(folder)
            elif system == "Darwin":
                os.system(f"open '{folder}'")
            else:
                os.system(f"xdg-open '{folder}'")
