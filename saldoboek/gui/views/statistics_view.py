"""StatisticsView - Toon statistieken en overzichten."""

import logging

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from saldoboek.gui.widgets import StatCard

logger = logging.getLogger(__name__)


class StatisticsView(QWidget):
    """
    View voor het tonen van statistieken.

    Deze view ontvangt data via de ViewModel en stuurt gebruikersacties
    door naar de ViewModel. Alle business logic zit in StatisticsViewModel.
    """

    def __init__(self, viewmodel, parent=None):
        """
        Initialiseer StatisticsView.

        Args:
            viewmodel: StatisticsViewModel instantie
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

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)

        title = QLabel("Statistieken")
        title.setObjectName("view_title")
        header_layout.addWidget(title)

        # Jaar selector
        year_label = QLabel("Jaar:")
        header_layout.addWidget(year_label)
        self._year_combo = QComboBox()
        self._year_combo.setObjectName("year_combo")
        self._year_combo.addItem("Alle jaren", None)
        self._year_combo.currentIndexChanged.connect(self._on_year_changed)
        header_layout.addWidget(self._year_combo)

        header_layout.addStretch()

        self._refresh_btn = QPushButton("🔄 Verversen")
        self._refresh_btn.setObjectName("refresh_button")
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self._refresh_btn)

        layout.addWidget(header)

        # Stats cards in a grid
        cards_frame = QFrame()
        cards_layout = QGridLayout(cards_frame)

        # Card 1: Totaal transacties
        self._total_card = StatCard("Totaal Transacties", "0")
        cards_layout.addWidget(self._total_card, 0, 0)

        # Card 2: Inkomsten
        self._income_card = StatCard("Inkomsten", "€0,00", is_positive=True)
        cards_layout.addWidget(self._income_card, 0, 1)

        # Card 3: Uitgaven
        self._expense_card = StatCard("Uitgaven", "€0,00", is_positive=False)
        cards_layout.addWidget(self._expense_card, 0, 2)

        # Card 4: Saldo
        self._balance_card = StatCard("Saldo", "€0,00")
        cards_layout.addWidget(self._balance_card, 0, 3)

        layout.addWidget(cards_frame)

        # Second row cards
        cards_frame2 = QFrame()
        cards_layout2 = QGridLayout(cards_frame2)

        # Card 5: Ongecategoriseerd
        self._uncat_card = StatCard("Ongecategoriseerd", "0")
        cards_layout2.addWidget(self._uncat_card, 0, 0)

        # Card 6: Gemiddelde inkomst
        self._avg_income_card = StatCard("Gem. Inkomst", "€0,00", is_positive=True)
        cards_layout2.addWidget(self._avg_income_card, 0, 1)

        # Card 7: Gemiddelde uitgave
        self._avg_expense_card = StatCard("Gem. Uitgave", "€0,00", is_positive=False)
        cards_layout2.addWidget(self._avg_expense_card, 0, 2)

        # Card 8: Populairste categorie
        self._top_cat_card = StatCard("Top Categorie", "-")
        cards_layout2.addWidget(self._top_cat_card, 0, 3)

        layout.addWidget(cards_frame2)

        # Charts row
        charts_frame = QFrame()
        charts_layout = QHBoxLayout(charts_frame)
        charts_layout.setSpacing(20)

        # Maandoverzicht bar chart
        monthly_group = QGroupBox("Maandoverzicht (Laatste 12 maanden)")
        monthly_layout = QVBoxLayout(monthly_group)

        self._monthly_chart_view = QChartView()
        self._monthly_chart_view.setMinimumHeight(200)
        self._monthly_chart_view.setRenderHint(QPainter.Antialiasing)
        monthly_layout.addWidget(self._monthly_chart_view)

        charts_layout.addWidget(monthly_group, 1)

        # Categorieën taartdiagram
        categories_group = QGroupBox("Categoriën Overzicht")
        categories_layout = QVBoxLayout(categories_group)

        self._categories_chart_view = QChartView()
        self._categories_chart_view.setMinimumHeight(200)
        self._categories_chart_view.setRenderHint(QPainter.Antialiasing)
        categories_layout.addWidget(self._categories_chart_view)

        charts_layout.addWidget(categories_group, 1)

        layout.addWidget(charts_frame)

        # Categorie details table
        cat_details_group = QGroupBox("Categoriën Details")
        cat_details_layout = QVBoxLayout(cat_details_group)

        self._category_table = QTableWidget()
        self._category_table.setObjectName("category_table")
        self._category_table.setColumnCount(3)
        self._category_table.setHorizontalHeaderLabels(
            ["Categorie", "Aantal", "Totaal Bedrag"]
        )
        self._category_table.setMaximumHeight(200)
        self._category_table.setAlternatingRowColors(True)
        # Enable column resizing by user
        header = self._category_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        self._category_table.setColumnWidth(0, 150)  # Categorie
        self._category_table.setColumnWidth(1, 80)  # Aantal
        self._category_table.setColumnWidth(2, 120)  # Totaal Bedrag
        cat_details_layout.addWidget(self._category_table)

        layout.addWidget(cat_details_group)

        # Rekening details table
        rek_details_group = QGroupBox("Rekening Overzicht")
        rek_details_layout = QVBoxLayout(rek_details_group)

        self._rekening_table = QTableWidget()
        self._rekening_table.setObjectName("rekening_table")
        self._rekening_table.setColumnCount(4)
        self._rekening_table.setHorizontalHeaderLabels(
            ["Rekening", "Beginstand", "Eindstand", "Totaal Bedrag"]
        )
        self._rekening_table.setMaximumHeight(150)
        self._rekening_table.setAlternatingRowColors(True)
        header = self._rekening_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        self._rekening_table.setColumnWidth(0, 180)  # Rekening
        self._rekening_table.setColumnWidth(1, 110)  # Beginstand
        self._rekening_table.setColumnWidth(2, 110)  # Eindstand
        self._rekening_table.setColumnWidth(3, 110)  # Totaal Bedrag
        rek_details_layout.addWidget(self._rekening_table)

        layout.addWidget(rek_details_group)

        layout.addStretch()

    def _connect_signals(self):
        """Verbind signals van de ViewModel met slots in de View."""
        self._viewmodel.cards_updated.connect(self._on_cards_updated)
        self._viewmodel.monthly_updated.connect(self._on_monthly_updated)
        self._viewmodel.monthly_chart_updated.connect(self._on_monthly_chart_updated)
        self._viewmodel.categories_chart_updated.connect(
            self._on_categories_chart_updated
        )
        self._viewmodel.category_details_updated.connect(
            self._on_category_details_updated
        )
        self._viewmodel.available_years_updated.connect(
            self._on_available_years_updated
        )
        self._viewmodel.rekening_details_updated.connect(
            self._on_rekening_details_updated
        )
        self._viewmodel.loading_started.connect(self._on_loading_started)
        self._viewmodel.loading_finished.connect(self._on_loading_finished)
        self._viewmodel.error_occurred.connect(self._on_error)

    # ViewModel signal handlers

    def _on_cards_updated(self, cards):
        """Handle stat cards update van ViewModel."""
        self._total_card.set_value(cards.get("totaal", "0"))
        self._income_card.set_value(cards.get("inkomsten", "€0,00"), is_positive=True)
        self._expense_card.set_value(cards.get("uitgaven", "€0,00"), is_positive=False)
        self._balance_card.set_value(cards.get("saldo", "€0,00"))
        self._uncat_card.set_value(cards.get("ongecategoriseerd", "0"))
        self._avg_income_card.set_value(
            cards.get("gemiddelde_inkomst", "€0,00"), is_positive=True
        )
        self._avg_expense_card.set_value(
            cards.get("gemiddelde_uitgave", "€0,00"), is_positive=False
        )
        self._top_cat_card.set_value(cards.get("top_categorie", "-"))

    def _on_monthly_updated(self, monthly_text):
        """Handle maandoverzicht text update van ViewModel."""
        # Text is shown in tooltip of chart
        pass

    def _on_monthly_chart_updated(self, maanden, inkomsten, uitgaven):
        """Handle monthly bar chart update van ViewModel."""
        if not maanden:
            # Show placeholder
            chart = QChart()
            chart.setTitle("Geen data beschikbaar")
            self._monthly_chart_view.setChart(chart)
            return

        # Create bar sets
        inkomsten_set = QBarSet("Inkomsten")
        uitgaven_set = QBarSet("Uitgaven")

        for val in inkomsten:
            inkomsten_set.append(val)
        for val in uitgaven:
            uitgaven_set.append(val)

        # Create series and add data
        series = QBarSeries()
        series.append(inkomsten_set)
        series.append(uitgaven_set)

        # Create chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Maandoverzicht (Laatste 12 maanden)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        # Create axes
        axis_x = QBarCategoryAxis()
        axis_x.append(maanden)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("€%.0f")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        self._monthly_chart_view.setChart(chart)

    def _on_categories_chart_updated(self, categorieën, bedragen):
        """Handle categories pie chart update van ViewModel."""
        if not categorieën:
            chart = QChart()
            chart.setTitle("Geen data beschikbaar")
            self._categories_chart_view.setChart(chart)
            return

        # Create pie series
        series = QPieSeries()

        for i, (cat, bedrag) in enumerate(zip(categorieën, bedragen)):
            slice = series.append(cat, bedrag)
            # Set color for first few slices
            if i < 3:
                colors = ["#2ecc71", "#3498db", "#9b59b6"]
                slice.setColor(QColor(colors[i % len(colors)]))

        # Create chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Categoriën Overzicht (Top 8 + Overige)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)

        self._categories_chart_view.setChart(chart)

    def _on_category_details_updated(self, details):
        """Handle category details table update van ViewModel."""
        self._category_table.setUpdatesEnabled(False)
        self._category_table.setRowCount(len(details))

        for row, (naam, aantal, totaal) in enumerate(details):
            self._category_table.setItem(row, 0, QTableWidgetItem(naam))
            self._category_table.setItem(row, 1, QTableWidgetItem(str(aantal)))
            self._category_table.setItem(row, 2, QTableWidgetItem(f"€{totaal:,.2f}"))

        self._category_table.setUpdatesEnabled(True)

    def _on_rekening_details_updated(self, details):
        """Handle rekening details table update van ViewModel."""
        self._rekening_table.setUpdatesEnabled(False)
        self._rekening_table.setRowCount(len(details))

        for row, (rekening, beginstand, eindstand, totaal_bedrag) in enumerate(details):
            self._rekening_table.setItem(row, 0, QTableWidgetItem(rekening))
            self._rekening_table.setItem(
                row, 1, QTableWidgetItem(f"€{beginstand:,.2f}")
            )
            self._rekening_table.setItem(row, 2, QTableWidgetItem(f"€{eindstand:,.2f}"))
            # Totaal bedrag: groen als positief, rood als negatief
            bedrag_item = QTableWidgetItem(f"€{totaal_bedrag:,.2f}")
            if totaal_bedrag < 0:
                bedrag_item.setForeground(QColor("#e74c3c"))  # Rood voor negatief
            elif totaal_bedrag > 0:
                bedrag_item.setForeground(QColor("#2ecc71"))  # Groen voor positief
            self._rekening_table.setItem(row, 3, bedrag_item)

        self._rekening_table.setUpdatesEnabled(True)

    def _on_available_years_updated(self, years):
        """Handle beschikbare jaren update van ViewModel."""
        # Save current selection
        current_data = self._year_combo.currentData()

        # Clear and repopulate
        self._year_combo.blockSignals(True)
        self._year_combo.clear()
        self._year_combo.addItem("Alle jaren", None)
        for year in years:
            self._year_combo.addItem(str(year), year)
        self._year_combo.blockSignals(False)

        # Restore selection if it still exists
        if current_data is not None:
            idx = self._year_combo.findData(current_data)
            if idx >= 0:
                self._year_combo.setCurrentIndex(idx)

    def _on_year_changed(self, index):
        """Handle jaar selectie gewijzigd."""
        year = self._year_combo.currentData()
        self._viewmodel.set_year(year)

    def _on_loading_started(self):
        """Handle laden gestart van ViewModel."""
        self._refresh_btn.setEnabled(False)

    def _on_loading_finished(self):
        """Handle laden voltooid van ViewModel."""
        self._refresh_btn.setEnabled(True)

    def _on_error(self, error_msg):
        """Handle error van ViewModel."""
        logger.error("Statistieken error: %s", error_msg)
        self._monthly_label.setText(f"Fout: {error_msg}")

    # User action handlers

    def _on_refresh_clicked(self):
        """Handle refresh button clicked."""
        self._viewmodel.refresh()

    # Public methods

    def set_gebruiker_id(self, gebruiker_id):
        """Stel de gebruiker ID in via ViewModel."""
        self._viewmodel.set_gebruiker_id(gebruiker_id)

    def set_transaction_service(self, service):
        """Stel de transaction service in via ViewModel."""
        self._viewmodel.set_transaction_service(service)

    def load_statistics(self):
        """Laad statistieken via ViewModel."""
        self._viewmodel.load_statistics()

    def refresh(self):
        """Vernieuw de statistieken via ViewModel."""
        self._viewmodel.refresh()
