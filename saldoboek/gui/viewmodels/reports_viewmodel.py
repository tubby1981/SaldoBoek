"""ReportsViewModel - ViewModel voor rapportage generatie."""

import logging
import os
from datetime import datetime

from PySide6.QtCore import QObject, QThread, Signal, Slot

logger = logging.getLogger(__name__)


class ReportWorker(QThread):
    """Worker thread voor het genereren van rapporten."""

    progress = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, report_service, report_type, jaar, gebruiker_id):
        """
        Initialiseer ReportWorker.

        Args:
            report_service: ReportService instantie
            report_type: Type rapport
            jaar: Jaar voor rapport
            gebruiker_id: Gebruiker ID
        """
        super().__init__()
        self._report_service = report_service
        self._report_type = report_type
        self._jaar = jaar
        self._gebruiker_id = gebruiker_id

    def run(self):
        """Genereer rapport in achtergrond thread."""
        try:
            self.progress.emit("Transacties ophalen...")

            # Gebruik ReportService voor daadwerkijke generatie
            success, result = self._report_service.generate_report(
                self._report_type, self._jaar, self._gebruiker_id
            )

            if success:
                self.progress.emit("Voltooid!")
                self.finished.emit(result)
            else:
                self.error.emit(result)  # result bevat foutmelding

        except Exception as e:
            logger.error("Fout bij genereren rapport: %s", e)
            self.error.emit(str(e))


class ReportsViewModel(QObject):
    """
    ViewModel voor rapportage generatie.

    Verantwoordelijk voor:
    - Laden van beschikbare jaren
    - Starten van rapport generatie (via ReportService)
    - Bijhouden van voortgang
    - Resultaat teruggeven

    Signal/slot communicatie met de View.
    """

    # Signals voor communicatie met View
    years_loaded = Signal(list)  # Beschikbare jaren
    generation_started = Signal()
    generation_progress = Signal(str)  # Status bericht
    generation_finished = Signal(str)  # filepath
    generation_error = Signal(str)  # Error bericht
    output_folder_requested = Signal(str)  # Folder pad

    def __init__(self, transaction_service, parent=None):
        """
        Initialiseer ReportsViewModel.

        Args:
            transaction_service: TransactionService instantie (for getting years)
            parent: Parent QObject
        """
        super().__init__(parent)
        self._transaction_service = transaction_service
        self._report_service = None  # Wordt ingeschakeld via set_report_service
        self._gebruiker_id = None
        self._worker = None
        self._last_filepath = None

        # Beschikbare rapport types
        self._report_types = [
            ("overzicht", "Jaar Overzicht"),
            ("maandelijks", "Maandelijks Rapport"),
            ("inkomsten", "Inkomsten Overzicht"),
            ("uitgaven", "Uitgaven Overzicht"),
            ("categorie", "Categorie Overzicht"),
            ("saldi", "Saldi Overzicht"),
            ("alles", "Alles (Volledig Rapport)"),
        ]

    def set_gebruiker_id(self, gebruiker_id: int) -> None:
        """Stel de gebruiker ID in en laad beschikbare jaren."""
        self._gebruiker_id = gebruiker_id
        self._load_available_years()

    def set_report_service(self, report_service) -> None:
        """
        Stel de ReportService in.

        Args:
            report_service: ReportService instantie
        """
        self._report_service = report_service

    def set_transaction_service(self, service) -> None:
        """Stel de transaction service in (voor jaren laden)."""
        self._transaction_service = service
        if self._gebruiker_id:
            self._load_available_years()

    def get_report_types(self) -> list:
        """
        Geef de beschikbare rapport types.

        Returns:
            List van (key, display_name) tuples
        """
        return self._report_types.copy()

    def _load_available_years(self) -> None:
        """Laad beschikbare jaren voor rapportage."""
        if not self._transaction_service or not self._gebruiker_id:
            return

        try:
            years = self._transaction_service.get_available_years(self._gebruiker_id)
            if not years:
                # Fallback naar huidige jaar
                years = [datetime.now().year]
            self.years_loaded.emit(years)
        except Exception as e:
            logger.error("Fout bij laden jaren: %s", e)

    def generate_report(self, jaar: int, report_type: str) -> None:
        """
        Start rapport generatie.

        Args:
            jaar: Jaar voor het rapport
            report_type: Type rapport (key uit _report_types)
        """
        if not self._report_service:
            self.generation_error.emit("ReportService niet beschikbaar")
            return

        if not self._gebruiker_id:
            self.generation_error.emit("Geen gebruiker ingesteld")
            return

        # Stop vorige worker als die nog draait
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()

        self.generation_started.emit()

        self._worker = ReportWorker(
            self._report_service, report_type, jaar, self._gebruiker_id
        )
        self._worker.progress.connect(self.generation_progress)
        self._worker.finished.connect(self._on_generation_finished)
        self._worker.error.connect(self.generation_error)
        self._worker.start()

    def _on_generation_finished(self, filepath: str) -> None:
        """Handle successful generation."""
        self._last_filepath = filepath
        self.generation_finished.emit(filepath)

    def get_last_filepath(self) -> str:
        """Geef het pad naar het laatst gegenereerde rapport."""
        return self._last_filepath

    def get_output_folder(self) -> str:
        """
        Geef het output folder pad.

        Returns:
            Pad naar de SaldoBoek output folder
        """
        if self._report_service:
            return self._report_service.get_output_folder()
        return os.path.expanduser("~/Documents/SaldoBoek")

    @Slot()
    def open_output_folder(self) -> None:
        """Open de output folder in de file explorer."""
        folder = self.get_output_folder()
        if os.path.exists(folder):
            self.output_folder_requested.emit(folder)

    def cancel_generation(self) -> None:
        """Annuleer lopende rapport generatie."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()
            logger.info("Rapport generatie geannuleerd")
