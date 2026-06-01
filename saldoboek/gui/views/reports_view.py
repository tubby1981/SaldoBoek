"""ReportsView - Genereer en exporteer rapporten."""

import logging
import os
import platform

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class ReportsView(QWidget):
    """
    View voor het genereren van rapportages.

    Deze view ontvangt data via de ViewModel en stuurt gebruikersacties
    door naar de ViewModel. Alle business logic zit in ReportsViewModel.
    """

    def __init__(self, viewmodel, parent=None):
        """
        Initialiseer ReportsView.

        Args:
            viewmodel: ReportsViewModel instantie
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Bouwt de UI op."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QFrame()
        header_layout = QHBoxLayout(header)

        title = QLabel("Rapportages")
        title.setObjectName("view_title")
        header_layout.addWidget(title)

        layout.addWidget(header)

        options_frame = QFrame()
        options_frame.setObjectName("options_frame")
        options_layout = QVBoxLayout(options_frame)

        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Jaar:"))
        self._year_combo = QComboBox()
        self._year_combo.setObjectName("year_combo")
        year_layout.addWidget(self._year_combo)
        year_layout.addStretch()
        options_layout.addLayout(year_layout)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Rapport type:"))
        self._type_combo = QComboBox()
        self._type_combo.setObjectName("type_combo")

        # Populate with report types from ViewModel
        report_types = self._viewmodel.get_report_types()
        for key, display_name in report_types:
            self._type_combo.addItem(display_name, key)

        type_layout.addWidget(self._type_combo)
        type_layout.addStretch()
        options_layout.addLayout(type_layout)

        layout.addWidget(options_frame)

        self._generate_btn = QPushButton("📊 Rapport Genereren")
        self._generate_btn.setObjectName("generate_button")
        self._generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self._generate_btn)

        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("progress_bar")
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setObjectName("status_label")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        self._open_folder_btn = QPushButton("📂 Open Folder")
        self._open_folder_btn.setObjectName("open_folder_button")
        self._open_folder_btn.clicked.connect(self._on_open_folder_clicked)
        self._open_folder_btn.setVisible(False)
        layout.addWidget(self._open_folder_btn)

        layout.addStretch()

    def _connect_signals(self):
        """Verbind signals van de ViewModel met slots in de View."""
        self._viewmodel.years_loaded.connect(self._on_years_loaded)
        self._viewmodel.generation_started.connect(self._on_generation_started)
        self._viewmodel.generation_progress.connect(self._on_generation_progress)
        self._viewmodel.generation_finished.connect(self._on_generation_finished)
        self._viewmodel.generation_error.connect(self._on_generation_error)

    # ViewModel signal handlers

    def _on_years_loaded(self, years):
        """Handle beschikbare jaren geladen van ViewModel."""
        self._year_combo.blockSignals(True)
        self._year_combo.clear()
        if years:
            self._year_combo.addItems([str(y) for y in years])
        else:
            from datetime import datetime

            self._year_combo.addItem(str(datetime.now().year))
        self._year_combo.blockSignals(False)

    def _on_generation_started(self):
        """Handle generatie gestart van ViewModel."""
        self._generate_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 0)
        self._status_label.setText("Genereren...")
        self._open_folder_btn.setVisible(False)

    def _on_generation_progress(self, message):
        """Handle generatie voortgang van ViewModel."""
        self._status_label.setText(message)

    def _on_generation_finished(self, filepath):
        """Handle generatie voltooid van ViewModel."""
        self._progress_bar.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._status_label.setText(f"✓ Rapport opgeslagen:\n{filepath}")
        self._open_folder_btn.setVisible(True)

    def _on_generation_error(self, error_message):
        """Handle generatie error van ViewModel."""
        self._progress_bar.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._status_label.setText(f"Fout: {error_message}")

    # User action handlers

    def _on_generate_clicked(self):
        """Start rapport generatie via ViewModel."""
        jaar = int(self._year_combo.currentText())
        report_type = self._type_combo.currentData()
        self._viewmodel.generate_report(jaar, report_type)

    def _on_open_folder_clicked(self):
        """Open de output folder via ViewModel."""
        folder = self._viewmodel.get_output_folder()
        if os.path.exists(folder):
            system = platform.system()
            if system == "Windows":
                os.startfile(folder)
            elif system == "Darwin":
                os.system(f"open '{folder}'")
            else:
                os.system(f"xdg-open '{folder}'")

    # Public methods

    def set_gebruiker_id(self, gebruiker_id):
        """Stel de gebruiker ID in via ViewModel."""
        self._viewmodel.set_gebruiker_id(gebruiker_id)

    def set_transaction_service(self, service):
        """Stel de transaction service in via ViewModel."""
        self._viewmodel.set_transaction_service(service)
