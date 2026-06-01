#!/usr/bin/env python3
"""
Genereer demo database met fake data voor screenshots.
Gebruik: python generate_demo_data.py
"""

import random
import sqlite3
from datetime import date, timedelta

DEMO_DB_PATH = "docs/screenshots/demo.db"

# Fake data
VOORNAMEN = ["Jan", "Pieter", "Marie", "Emma", "Kees", "Anna", "Bart", "Lisa"]
ACHTERNAMEN = [
    "Jansen",
    "de Vries",
    "van der Berg",
    "Bakker",
    "Visser",
    "Smit",
    "Dekker",
    "Mulder",
]
BEDRIJVEN = [
    "Albert Heijn",
    "Jumbo",
    "Lidl",
    "AH Bio",
    "Gall & Gall",
    "Etos",
    "Kruidvat",
    "MediaMarkt",
]
TEGENREKENINGEN = [
    "NL20ABNA0123456789",
    "NL91ABNA0417164300",
    "NL85INGB0001234567",
    "NL33RABO0123456789",
    "NL28SNSB0123456789",
]

CATEGORIEEN = {
    "Boodschappen": ["albert heijn", "jumbo", "lidl", "plus", "dirk"],
    "Tankstation": ["shell", "bp", "essobook", "total"],
    "Abonnementen": ["netflix", "spotify", "kpn", "vodafone", "t-mobile"],
    "Salaris": ["loon", "salaris", "werkgever"],
    "Verzekering": ["zorgverzekering", "aegon", "centraal beheer"],
}


def create_demo_database():
    """Maak een demo database met fake transacties."""

    # Verwijder oude demo database
    import os

    if os.path.exists(DEMO_DB_PATH):
        os.remove(DEMO_DB_PATH)

    conn = sqlite3.connect(DEMO_DB_PATH)
    cursor = conn.cursor()

    # Maak tabellen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gebruikers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_id INTEGER,
            datum DATE,
            rekening TEXT,
            tegenrekening TEXT,
            naam TEXT,
            omschrijving TEXT,
            bedrag REAL,
            saldo_voor REAL,
            valuta TEXT DEFAULT 'EUR',
            categorie TEXT,
            rekeningtype TEXT,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorieen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            type TEXT,
            beschrijving TEXT,
            gebruiker_id INTEGER NOT NULL,
            is_standaard BOOLEAN DEFAULT 0,
            UNIQUE(naam, gebruiker_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorisatie_regels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_id INTEGER,
            zoekterm TEXT,
            categorie TEXT,
            actief BOOLEAN DEFAULT 1,
            is_standaard BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(zoekterm, gebruiker_id)
        )
    """)

    # Demo gebruiker
    cursor.execute("INSERT INTO gebruikers (naam) VALUES (?)", ("Demo Gebruiker",))
    gebruiker_id = 1

    # Categorieën
    for cat_naam in CATEGORIEEN.keys():
        cursor.execute(
            "INSERT OR IGNORE INTO categorieen (naam, type, beschrijving, gebruiker_id) VALUES (?, ?, ?, ?)",
            (cat_naam, "uitgaven", f"{cat_naam} transacties", gebruiker_id),
        )
    # Extra inkomsten categorie
    cursor.execute(
        "INSERT OR IGNORE INTO categorieen (naam, type, beschrijving, gebruiker_id) VALUES (?, ?, ?, ?)",
        ("Salaris", "inkomsten", "Inkomen uit werk", gebruiker_id),
    )

    # Categorisatie regels
    for categorie, zoektermen in CATEGORIEEN.items():
        for zoekterm in zoektermen:
            cursor.execute(
                "INSERT INTO categorisatie_regels (gebruiker_id, zoekterm, categorie) VALUES (?, ?, ?)",
                (gebruiker_id, zoekterm, categorie),
            )

    # Transacties (laatste 6 maanden)
    vandaag = date.today()
    rek = "NL12ABNA0123456789"
    saldo = 5000.00

    transacties = []

    # Maandelijkse inkomsten (salaris)
    for maand in range(5, -1, -1):
        salaris_datum = vandaag.replace(day=25) - timedelta(days=maand * 30)
        saldo += 3500.00
        transacties.append(
            (
                gebruiker_id,
                salaris_datum.isoformat(),
                rek,
                "NL00ABNA0000000001",
                "Werkgever BV",
                f"SALARIS BETALING 2024",
                3500.00,
                saldo,
                "EUR",
                "Salaris",
                "betaalrekening",
            )
        )

    # Wekelijkse boodschappen
    for week in range(24):
        datum = vandaag - timedelta(days=week * 7)
        bedrijf = random.choice(BEDRIJVEN)
        bedrag = round(random.uniform(25, 85), 2)
        saldo -= bedrag
        categorie = "Boodschappen"
        transacties.append(
            (
                gebruiker_id,
                datum.isoformat(),
                rek,
                random.choice(TEGENREKENINGEN),
                f"{bedrijf}",
                f"BETAALAUTOMAAT {bedrijf}",
                -bedrag,
                saldo,
                "EUR",
                categorie,
                "betaalrekening",
            )
        )

    # Tankbeurten (2x per maand)
    for maand in range(6):
        for week in [0, 2]:
            datum = vandaag.replace(day=1) - timedelta(days=maand * 30 + week * 7)
            if datum <= vandaag:
                bedrag = round(random.uniform(45, 80), 2)
                saldo -= bedrag
                transacties.append(
                    (
                        gebruiker_id,
                        datum.isoformat(),
                        rek,
                        random.choice(TEGENREKENINGEN),
                        "Shell Tankstation",
                        "PIN BETALING SHELL",
                        -bedrag,
                        saldo,
                        "EUR",
                        "Tankstation",
                        "betaalrekening",
                    )
                )

    # Abonnementen (maandelijks)
    for maand in range(6):
        datum = vandaag.replace(day=1) - timedelta(days=maand * 30)
        for abo in [("Netflix", 15.99), ("Spotify", 9.99), ("KPN Internet", 40.00)]:
            saldo -= abo[1]
            transacties.append(
                (
                    gebruiker_id,
                    datum.isoformat(),
                    rek,
                    random.choice(TEGENREKENINGEN),
                    abo[0],
                    f"MAANDELIJKSE ABONNEMENT {abo[0].upper()}",
                    -abo[1],
                    saldo,
                    "EUR",
                    "Abonnementen",
                    "betaalrekening",
                )
            )

    # Verzekering (jaarlijks - zorgverzekering)
    saldo -= 150.00
    transacties.append(
        (
            gebruiker_id,
            vandaag.replace(month=1, day=1).isoformat(),
            rek,
            random.choice(TEGENREKENINGEN),
            "Zorgverzekeraar CZ",
            "ZORGVERZEKERING 2024",
            -150.00,
            saldo,
            "EUR",
            "Verzekering",
            "betaalrekening",
        )
    )

    # Huishuur (maandelijks)
    for maand in range(6):
        datum = vandaag.replace(day=15) - timedelta(days=maand * 30)
        saldo -= 850.00
        transacties.append(
            (
                gebruiker_id,
                datum.isoformat(),
                rek,
                random.choice(TEGENREKENINGEN),
                "Woonstichting",
                f"HUUR {datum.strftime('%B')}",
                -850.00,
                saldo,
                "EUR",
                None,  # Ongecategoriseerd voor demo
                "betaalrekening",
            )
        )

    # Sorteer op datum (nieuwste eerst)
    transacties.sort(key=lambda x: x[1], reverse=True)

    # Insert transacties
    cursor.executemany(
        """
        INSERT INTO transacties
        (gebruiker_id, datum, rekening, tegenrekening, naam, omschrijving, bedrag, saldo_voor, valuta, categorie, rekeningtype)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        transacties,
    )

    conn.commit()
    conn.close()

    print(f"Demo database aangemaakt: {DEMO_DB_PATH}")
    print(f"- 1 demo gebruiker")
    print(f"- {len(CATEGORIEEN)} categorieën")
    print(f"- {len(transacties)} transacties")
    print(f"- {len(transacties) // 6} ongecategoriseerd (huur)")


if __name__ == "__main__":
    create_demo_database()
