"""Core data models - Dataclasses voor SaldoBoek business logic."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Transactie:
    """
    Data model voor een banktransactie.

    Attributen:
        id: Unieke identificatie
        datum: Transactiedatum
        gebruiker_id: ID van de eigenaar
        rekening: IBAN/BBAN van eigen rekening
        tegenrekening: IBAN/BBAN van tegenpartij
        naam: Naam van de tegenpartij
        omschrijving: Transactie omschrijving
        bedrag: Bedrag (positief=inkomsten, negatief=uitgaven)
        saldo_voor: Saldo voor deze transactie
        valuta: ISO valuta code (default EUR)
        categorie: Categorienaam
        rekeningtype: Type rekening (betaalrekening/spaarrekening)
        imported_at: Tijdstip van import
    """

    id: int
    datum: date
    gebruiker_id: int
    rekening: str
    bedrag: Decimal
    naam: str = ""
    omschrijving: str = ""
    tegenrekening: str = ""
    saldo_voor: Decimal = Decimal("0.00")
    valuta: str = "EUR"
    categorie: str = "Ongecategoriseerd"
    rekeningtype: str = "betaalrekening"
    imported_at: Optional[datetime] = None

    @property
    def is_inkomen(self) -> bool:
        """Check of transactie inkomsten zijn."""
        return self.bedrag > 0

    @property
    def is_uitgave(self) -> bool:
        """Check of transactie uitgaven zijn."""
        return self.bedrag < 0

    @property
    def is_ongecategoriseerd(self) -> bool:
        """Check of transactie geen categorie heeft."""
        return self.categorie == "Ongecategoriseerd"

    def to_dict(self) -> dict:
        """Converteer naar dictionary voor GUI/DB operaties."""
        return {
            "id": self.id,
            "datum": self.datum.isoformat()
            if isinstance(self.datum, date)
            else self.datum,
            "gebruiker_id": self.gebruiker_id,
            "rekening": self.rekening,
            "tegenrekening": self.tegenrekening,
            "naam": self.naam,
            "omschrijving": self.omschrijving,
            "bedrag": float(self.bedrag),
            "saldo_voor": float(self.saldo_voor),
            "valuta": self.valuta,
            "categorie": self.categorie,
            "rekeningtype": self.rekeningtype,
            "imported_at": self.imported_at.isoformat() if self.imported_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transactie":
        """Maak Transactie instantie van dictionary."""
        from datetime import date, datetime

        datum = data.get("datum")
        if isinstance(datum, str):
            datum = datetime.fromisoformat(datum).date()
        elif not isinstance(datum, date):
            datum = date.today()

        imported_at = data.get("imported_at")
        if isinstance(imported_at, str):
            imported_at = datetime.fromisoformat(imported_at)

        return cls(
            id=data.get("id", 0),
            datum=datum,
            gebruiker_id=data.get("gebruiker_id", 0),
            rekening=data.get("rekening", ""),
            tegenrekening=data.get("tegenrekening", ""),
            naam=data.get("naam", ""),
            omschrijving=data.get("omschrijving", ""),
            bedrag=Decimal(str(data.get("bedrag", 0))),
            saldo_voor=Decimal(str(data.get("saldo_voor", 0))),
            valuta=data.get("valuta", "EUR"),
            categorie=data.get("categorie", "Ongecategoriseerd"),
            rekeningtype=data.get("rekeningtype", "betaalrekening"),
            imported_at=imported_at,
        )


@dataclass
class Categorie:
    """
    Data model voor een categorie.

    Attributen:
        id: Unieke identificatie
        naam: Naam van de categorie
        type: Type (inkomsten/uitgaven)
        beschrijving: Optionele beschrijving
        gebruiker_id: ID van de eigenaar (None voor globale categorieën)
    """

    id: int
    naam: str
    type: str  # 'inkomsten' of 'uitgaven'
    beschrijving: str = ""
    gebruiker_id: Optional[int] = None

    def is_inkomsten(self) -> bool:
        """Check of categorie voor inkomsten is."""
        return self.type == "inkomsten"

    def is_uitgaven(self) -> bool:
        """Check of categorie voor uitgaven is."""
        return self.type == "uitgaven"

    def to_dict(self) -> dict:
        """Converteer naar dictionary."""
        return {
            "id": self.id,
            "naam": self.naam,
            "type": self.type,
            "beschrijving": self.beschrijving,
            "gebruiker_id": self.gebruiker_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Categorie":
        """Maak Categorie instantie van dictionary."""
        return cls(
            id=data.get("id", 0),
            naam=data.get("naam", ""),
            type=data.get("type", "uitgaven"),
            beschrijving=data.get("beschrijving", ""),
            gebruiker_id=data.get("gebruiker_id"),
        )


@dataclass
class CategorisatieRegel:
    """
    Data model voor een categorisatie regel.

    Attributen:
        id: Unieke identificatie
        zoekterm: Zoekterm (kleine letters)
        categorie: Naam van de categorie
        gebruiker_id: ID van de eigenaar (None voor globale regels)
        actief: Of de regel actief is
    """

    id: int
    zoekterm: str
    categorie: str
    gebruiker_id: Optional[int] = None
    actief: bool = True

    def to_dict(self) -> dict:
        """Converteer naar dictionary."""
        return {
            "id": self.id,
            "zoekterm": self.zoekterm,
            "categorie": self.categorie,
            "gebruiker_id": self.gebruiker_id,
            "actief": self.actief,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CategorisatieRegel":
        """Maak CategorisatieRegel instantie van dictionary."""
        return cls(
            id=data.get("id", 0),
            zoekterm=data.get("zoekterm", ""),
            categorie=data.get("categorie", ""),
            gebruiker_id=data.get("gebruiker_id"),
            actief=data.get("actief", True),
        )


@dataclass
class Gebruiker:
    """
    Data model voor een gebruiker.

    Attributen:
        id: Unieke identificatie
        naam: Naam van de gebruiker
        created_at: Tijdstip van aanmaken
    """

    id: int
    naam: str
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Converteer naar dictionary."""
        return {
            "id": self.id,
            "naam": self.naam,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Gebruiker":
        """Maak Gebruiker instantie van dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            id=data.get("id", 0),
            naam=data.get("naam", ""),
            created_at=created_at,
        )


@dataclass
class ImportResult:
    """
    Data model voor het resultaat van een import.

    Attributen:
        totaal: Totaal aantal geïmporteerde transacties
        ongecategoriseerd: Lijst van ongecategoriseerde transacties
        duplicaten: Aantal overgeslagen duplicaten
        fouten: Aantal fouten tijdens import
    """

    totaal: int = 0
    ongecategoriseerd: list = field(default_factory=list)
    duplicaten: int = 0
    fouten: int = 0

    @property
    def has_errors(self) -> bool:
        """Check of er fouten waren."""
        return self.fouten > 0

    @property
    def has_ongecategoriseerd(self) -> bool:
        """Check of er ongecategoriseerde transacties zijn."""
        return len(self.ongecategoriseerd) > 0

    def to_dict(self) -> dict:
        """Converteer naar dictionary."""
        return {
            "totaal": self.totaal,
            "ongecategoriseerd": self.ongecategoriseerd,
            "duplicaten": self.duplicaten,
            "fouten": self.fouten,
        }


@dataclass
class FilterOpts:
    """
    Data model voor transactie filters.

    Attributen:
        jaar: Filter op jaar
        maand: Filter op maand (1-12)
        categorie: Filter op categorienaam
        rekening: Filter op rekeningnummer
        zoek: Zoekterm voor omschrijving/naam
    """

    jaar: Optional[int] = None
    maand: Optional[int] = None
    categorie: Optional[str] = None
    rekening: Optional[str] = None
    zoek: Optional[str] = None

    def to_dict(self) -> dict:
        """Converteer naar dictionary voor service laag."""
        result = {}
        if self.jaar is not None:
            result["jaar"] = self.jaar
        if self.maand is not None:
            result["maand"] = self.maand
        if self.categorie:
            result["categorie"] = self.categorie
        if self.rekening:
            result["rekening"] = self.rekening
        if self.zoek:
            result["zoek"] = self.zoek
        return result

    def is_empty(self) -> bool:
        """Check of er geen filters ingesteld zijn."""
        return not any(
            [self.jaar, self.maand, self.categorie, self.rekening, self.zoek]
        )
