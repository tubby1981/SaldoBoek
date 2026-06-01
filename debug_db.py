#!/usr/bin/env python3
"""Debug script om database probleem te onderzoeken."""

import sqlite3

conn = sqlite3.connect("saldoboek/data/database.db")
cur = conn.cursor()

print("=== Database Debug Info ===")

# Check total transactions
cur.execute("SELECT COUNT(*) FROM transacties")
total = cur.fetchone()[0]
print(f"Total transactions: {total}")

# Check transactions with NULL datum
cur.execute("SELECT COUNT(*) FROM transacties WHERE datum IS NULL")
null_datum = cur.fetchone()[0]
print(f"Transactions with NULL datum: {null_datum}")

# Check date format
cur.execute("SELECT typeof(datum) FROM transacties LIMIT 5")
print(f"Data type of datum column: {cur.fetchall()}")

# Sample dates
cur.execute("SELECT datum FROM transacties LIMIT 10")
print(f"Sample dates: {cur.fetchall()}")

# Years available
cur.execute("""
    SELECT DISTINCT strftime('%Y', datum) as jaar
    FROM transacties
    WHERE datum IS NOT NULL
    ORDER BY jaar DESC
""")
print(f"Available years (not NULL): {cur.fetchall()}")

# Years per user
cur.execute("""
    SELECT gebruiker_id, strftime('%Y', datum) as jaar, COUNT(*)
    FROM transacties
    WHERE datum IS NOT NULL
    GROUP BY gebruiker_id, jaar
""")
print(f"Years per user: {cur.fetchall()}")

conn.close()
