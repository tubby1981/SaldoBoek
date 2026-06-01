"""StatisticsViewModel - ViewModel voor statistieken dashboard."""

import logging

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class StatisticsViewModel(QObject):
    """
    ViewModel voor het statistieken dashboard.

    Verantwoordelijk voor:
    - Laden van statistieken uit service
    - Berekenen van totalen en gemiddelden
    - Maandoverzicht berekeningen
    - Jaar filtering

    Signal/slot communicatie met de View.
    """

    # Signals voor communicatie met View
    stats_loaded = Signal(
        dict
    )  # {totaal, inkomsten, uitgaven, saldo, ongecategoriseerd}
    cards_updated = Signal(dict)  # Card values dict
    monthly_updated = Signal(str)  # Maandoverzicht als string
    monthly_chart_updated = Signal(list, list, list)  # maanden, inkomsten, uitgaven
    categories_chart_updated = Signal(list, list)  # categorieën, bedragen
    category_details_updated = Signal(list)  # lijst van (naam, aantal, totaal)
    available_years_updated = Signal(list)  # beschikbare jaren
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, transaction_service, parent=None):
        """
        Initialiseer StatisticsViewModel.

        Args:
            transaction_service: TransactionService instantie
            parent: Parent QObject
        """
        super().__init__(parent)
        self._service = transaction_service
        self._gebruiker_id = None
        self._selected_year = None  # None = alle jaren

        # Cached data
        self._stats = {}
        self._df = None
        self._all_df = None  # Alle transacties (voor filtering)

    def set_gebruiker_id(self, gebruiker_id: int) -> None:
        """Stel de gebruiker ID in en laad data."""
        self._gebruiker_id = gebruiker_id
        self.load_statistics()

    def set_transaction_service(self, service) -> None:
        """Stel de transaction service in."""
        self._service = service

    def load_statistics(self) -> None:
        """Laad alle statistieken."""
        if not self._service or not self._gebruiker_id:
            self.error_occurred.emit("Geen service of gebruiker ingesteld")
            return

        self.loading_started.emit()

        try:
            # Haal basis stats uit service
            self._stats = self._service.get_transaction_stats(self._gebruiker_id)

            # Haal alle transacties op voor berekeningen
            self._all_df = self._service.get_transactions(
                filters={}, gebruiker_id=self._gebruiker_id
            )

            # Emit beschikbare jaren
            self._emit_available_years()

            # Pas jaar filter toe
            self._apply_year_filter()

        except Exception as e:
            logger.error("Fout bij laden statistieken: %s", e)
            self.error_occurred.emit(str(e))
        finally:
            self.loading_finished.emit()

    def _emit_available_years(self) -> None:
        """Emit de beschikbare jaren uit de transacties."""
        if self._all_df is None or self._all_df.empty:
            self.available_years_updated.emit([])
            return

        try:
            import pandas as pd

            df = self._all_df.copy()
            df["datum"] = pd.to_datetime(df["datum"])
            years = sorted(df["datum"].dt.year.unique().tolist(), reverse=True)
            self.available_years_updated.emit(years)
        except Exception as e:
            logger.error("Fout bij bepalen beschikbare jaren: %s", e)
            self.available_years_updated.emit([])

    def _apply_year_filter(self) -> None:
        """Pas jaar filter toe op de data."""
        if self._all_df is None or self._all_df.empty:
            self._df = self._all_df
        else:
            if self._selected_year:
                import pandas as pd

                df = self._all_df.copy()
                df["datum"] = pd.to_datetime(df["datum"])
                self._df = df[df["datum"].dt.year == self._selected_year]
            else:
                self._df = self._all_df

        # Emit basis stats (aangepast voor gefilterde data)
        self._emit_stats()

        # Bereken en emit card values
        self._update_cards()

        # Bereken en emit maandoverzicht
        self._update_monthly()

    def _emit_stats(self) -> None:
        """Emit basis statistieken voor gefilterde data."""
        if self._df is None or self._df.empty:
            self._stats = {
                "totaal": 0,
                "ongecategoriseerd": 0,
                "inkomsten": 0,
                "uitgaven": 0,
            }
        else:
            self._stats = {
                "totaal": len(self._df),
                "ongecategoriseerd": len(
                    self._df[self._df["categorie"] == "Ongecategoriseerd"]
                ),
                "inkomsten": int((self._df["bedrag"] > 0).sum()),
                "uitgaven": int((self._df["bedrag"] < 0).sum()),
            }
        self.stats_loaded.emit(self._stats)

    def set_year(self, year: int = None) -> None:
        """
        Stel het geselecteerde jaar in.

        Args:
            year: Jaar om te filteren, of None voor alle jaren
        """
        self._selected_year = year
        self._apply_year_filter()

    def _update_cards(self) -> None:
        """Bereken waarden voor de stat cards."""
        if self._df is None or self._df.empty:
            cards = {
                "totaal": "0",
                "inkomsten": "€0,00",
                "uitgaven": "€0,00",
                "saldo": "€0,00",
                "ongecategoriseerd": "0",
                "gemiddelde_inkomst": "€0,00",
                "gemiddelde_uitgave": "€0,00",
                "top_categorie": "-",
            }
            self.cards_updated.emit(cards)
            return

        # Bereken totalen
        inkomsten = self._df[self._df["bedrag"] > 0]["bedrag"].sum()
        uitgaven = abs(self._df[self._df["bedrag"] < 0]["bedrag"].sum())
        saldo = inkomsten - uitgaven

        # Tel inkomsten/uitgaven
        inkomsten_count = (self._df["bedrag"] > 0).sum()
        uitgaven_count = (self._df["bedrag"] < 0).sum()

        # Gemiddeldes
        avg_income = inkomsten / inkomsten_count if inkomsten_count > 0 else 0
        avg_expense = uitgaven / uitgaven_count if uitgaven_count > 0 else 0

        # Top categorie (meest voorkomende, excl ongecategoriseerd)
        top_cat = "-"
        if not self._df.empty:
            cat_counts = (
                self._df[self._df["categorie"] != "Ongecategoriseerd"]
                .groupby("categorie")
                .size()
            )
            if not cat_counts.empty:
                top_cat = cat_counts.idxmax()

        cards = {
            "totaal": f"{self._stats.get('totaal', 0):,}",
            "inkomsten": f"€{inkomsten:,.2f}",
            "uitgaven": f"€{uitgaven:,.2f}",
            "saldo": f"€{saldo:,.2f}",
            "ongecategoriseerd": f"{self._stats.get('ongecategoriseerd', 0):,}",
            "gemiddelde_inkomst": f"€{avg_income:,.2f}",
            "gemiddelde_uitgave": f"€{avg_expense:,.2f}",
            "top_categorie": top_cat,
        }

        self.cards_updated.emit(cards)

    def _update_monthly(self) -> None:
        """Bereken het maandoverzicht."""
        if self._df is None or self._df.empty:
            self.monthly_updated.emit("Geen transacties beschikbaar")
            self.monthly_chart_updated.emit([], [], [])
            return

        try:
            import pandas as pd

            df = self._df.copy()
            df["datum"] = pd.to_datetime(df["datum"])
            df["jaar_maand"] = df["datum"].dt.to_period("M")

            monthly = (
                df.groupby("jaar_maand")
                .agg(
                    aantal=("id", "count"),
                    inkomsten=("bedrag", lambda x: x[x > 0].sum()),
                    uitgaven=("bedrag", lambda x: abs(x[x < 0].sum())),
                )
                .tail(12)
            )

            # Text overview
            lines = ["Laatste 12 maanden:"]
            maanden = []
            inkomsten_list = []
            uitgaven_list = []

            for idx, row in monthly.iterrows():
                maand_saldo = row["inkomsten"] - row["uitgaven"]
                saldo_str = (
                    f"+€{maand_saldo:,.2f}"
                    if maand_saldo >= 0
                    else f"-€{abs(maand_saldo):,.2f}"
                )
                lines.append(
                    f"{idx}: {int(row['aantal'])} tx | "
                    f"In: €{row['inkomsten']:,.2f} | "
                    f"Uit: €{row['uitgaven']:,.2f} | {saldo_str}"
                )

                # Chart data
                maanden.append(str(idx))
                inkomsten_list.append(float(row["inkomsten"]))
                uitgaven_list.append(float(row["uitgaven"]))

            self.monthly_updated.emit("\n".join(lines))
            self.monthly_chart_updated.emit(maanden, inkomsten_list, uitgaven_list)

            # Update categorie chart
            self._update_categories()

        except Exception as e:
            logger.error("Fout bij maandoverzicht: %s", e)
            self.monthly_updated.emit("Kon maandoverzicht niet laden")
            self.monthly_chart_updated.emit([], [], [])

    def _update_categories(self) -> None:
        """Bereken categorie overzicht voor grafiek."""
        if self._df is None or self._df.empty:
            self.categories_chart_updated.emit([], [])
            self.category_details_updated.emit([])
            return

        try:
            import pandas as pd

            df = self._df.copy()
            # Filter out ongecategoriseerd for the pie chart
            cat_df = df[df["categorie"] != "Ongecategoriseerd"]

            if cat_df.empty:
                self.categories_chart_updated.emit([], [])
                self.category_details_updated.emit([])
                return

            # Group by categorie
            cat_totals = (
                cat_df.groupby("categorie")
                .agg(
                    aantal=("id", "count"),
                    totaal=("bedrag", "sum"),
                )
                .sort_values("totaal", ascending=False)
            )

            # Take top 8 for pie chart, rest combined as "Overige"
            top_cats = cat_totals.head(8)
            rest = cat_totals.iloc[8:]

            if not rest.empty:
                other_total = rest["totaal"].sum()
                other_count = rest["aantal"].sum()
                top_cats.loc["Overige"] = [other_count, other_total]

            categorieën = top_cats.index.tolist()
            bedragen = [float(abs(row.totaal)) for row in top_cats.itertuples()]

            self.categories_chart_updated.emit(categorieën, bedragen)

            # Detailed table data
            details = []
            for idx, row in cat_totals.iterrows():
                details.append((idx, int(row["aantal"]), float(row["totaal"])))

            self.category_details_updated.emit(details)

        except Exception as e:
            logger.error("Fout bij categorie overzicht: %s", e)
            self.categories_chart_updated.emit([], [])
            self.category_details_updated.emit([])

    def refresh(self) -> None:
        """Vernieuw de statistieken."""
        self.load_statistics()

    def get_stats(self) -> dict:
        """Geef de laatste statistieken terug."""
        return self._stats.copy()
