#!/usr/bin/env python3
"""
Script om datums in de database te repareren.
Dit helpt bij transities waar datums verkeerd zijn geïmporteerd.
"""

import re
import sqlite3
from datetime import datetime

DB_PATH = "saldoboek/data/database.db"


def parse_datum(datum_str):
    """Probeer datum te parsen uit verschillende formaten."""
    if not datum_str:
        return None

    # Al bekend als YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", str(datum_str)):
        try:
            return datetime.strptime(datum_str, "%Y-%m-%d")
        except ValueError:
            pass

    # DD-MM-YYYY
    if re.match(r"^\d{2}-\d{2}-\d{4}$", str(datum_str)):
        try:
            return datetime.strptime(datum_str, "%d-%m-%Y")
        except ValueError:
            pass

    # DD-MM-YY
    if re.match(r"^\d{2}-\d{2}-\d{2}$", str(datum_str)):
        try:
            dt = datetime.strptime(datum_str, "%d-%m-%y")
            # Convert 2-digit year: 00-69 -> 2000s, 70-99 -> 1900s
            if dt.year > 2050:
                dt = dt.replace(year=dt.year - 100)
            return dt
        except ValueError:
            pass

    return None


def fix_dates():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Haal alle transacties met hun huidige datum
    cur.execute("SELECT id, datum FROM transacties WHERE datum IS NOT NULL")
    rows = cur.fetchall()

    fixes = 0
    errors = 0

    for row_id, datum in rows:
        parsed = parse_datum(datum)
        if parsed:
            new_datum = parsed.strftime("%Y-%m-%d")
            if new_datum != datum:
                cur.execute(
                    "UPDATE transacties SET datum = ? WHERE id = ?", (new_datum, row_id)
                )
                fixes += 1
        else:
            errors += 1
            print(f"  Could not parse datum: id={row_id}, datum={datum}")

    conn.commit()

    print(f"\n=== Resultaat ===")
    print(f"Datums gerepareerd: {fixes}")
    print(f"Niet te repareren: {errors}")

    # Toon beschikbare jaren nu
    cur.execute("""
        SELECT DISTINCT strftime('%Y', datum) as jaar, COUNT(*)
        FROM transacties
        WHERE datum IS NOT NULL
        GROUP BY jaar
        ORDER BY jaar DESC
    """)
    print(f"\nBeschikbare jaren in database:")
    for jaar, count in cur.fetchall():
        print(f"  {jaar}: {count} transacties")

    conn.close()


if __name__ == "__main__":
    print("=== Database Datum Reparatie ===\n")
    fix_dates()
