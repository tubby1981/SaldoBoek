# 💰 SaldoBoek

**SaldoBoek** is een Nederlandstalige Python-tool voor het beheren, analyseren en rapporteren van persoonlijke financiën. Ideaal voor bijvoorbeeld bewindvoering, budgetbeheer of het maken van jaaroverzichten van banktransacties.

SaldoBoek ondersteunt het importeren van bankafschriften (CSV), het automatisch en handmatig categoriseren van inkomsten/uitgaven, en het genereren van uitgebreide Excel-jaaroverzichten per gebruiker.

---

## 🔧 Functionaliteiten

- ✅ Meerdere gebruikers (zonder wachtwoord, handig bij bewindvoering of gezinsbeheer)
- ✅ Meerdere bankrekeningen per gebruiker
- ✅ **Importeer banktransacties** van SNS, Rabobank en andere banken (mits CSV-structuur ondersteund wordt)
- ✅ **Automatische categorisatie** op basis van herkenbare regels
- ✅ **Handmatige categorisatie en categoriebeheer**
- ✅ **Interactieve CLI-interface** (Command Line Interface)
- ✅ **Jaarlijkse Excel-rapportage**, met o.a.:
  - 📈 Inkomsten en uitgaven per categorie
  - 📊 Maandelijks saldo en balans
  - 📄 Alle transacties met filters
  - 🧾 Rekeningoverzicht en totalen
  - 🔀 Optioneel gesplitst per rekening

---

SaldoBoek is uitbreidbaar en volledig in Python geschreven. Categorieën en regels zijn eenvoudig te beheren via YAML-bestanden. Later kunnen pakketten (.deb, .exe) of een GUI worden toegevoegd.

## 🛠️ Installatie-instructies

### 1. Clone deze repository

```bash
git clone https://github.com/jouw-gebruiker/saldoboek.git
cd saldoboek
```

### 2. Maak een Python virtual environment aan (aanbevolen)

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. Installeer de afhankelijkheden

```bash
pip install -r requirements.txt
```

### 4. Start SaldoBoek

```bash
python main.py
```

## 🧱 Gebruikte database
SaldoBoek gebruikt **SQLite** als lokale opslag. Dit is een lichtgewicht database zonder extra installatie. De data wordt opgeslagen in:

```bash
saldoboek/data/database.db
```

Back-ups maken of synchroniseren is eenvoudig door dit bestand te kopiëren.

## 📁 Structuur

```bash
main.py                      # Startpunt van de CLI
requirements.txt             # Vereiste Python-pakketten
saldoboek/
├── cli.py                   # CLI-menu's en navigatie
├── categorization.py        # Regels en handmatige categorisatie
├── importer.py              # Inlezen en parsen van bank-CSV's
├── database.py              # SQLite-databasebeheer
├── config/
│   ├── bank_parsers.py      # Parser logica per bank
│   ├── categories.yaml      # Categorie-definities
│   └── categorization_rules.yaml # Automatische regels
├── data/database.db         # Transactie-opslag (SQLite)
├── reports/                 # Excel sheet generatie
│   ├── sheet_overview.py    # Jaaroverzicht
│   ├── sheet_income.py      # Inkomsten per categorie
│   ├── sheet_expenses.py    # Uitgaven per categorie
│   ├── sheet_monthly.py     # Maandoverzicht
│   ├── sheet_monthly_category.py # Categorie per maand
│   ├── sheet_balances.py    # Rekeningstanden
│   ├── sheet_transactions.py# Alle transacties
│   └── summary.py           # Samenvatting voor console
```
## 🏦 Ondersteunde banken

* SNS Bank
* Rabobank
* (Andere banken mogelijk door het uitbreiden van bank_parsers.py)

### 📊 Excel rapportage
Bij het genereren van een jaaroverzicht wordt een .xlsx bestand aangemaakt met meerdere tabs, waaronder:

* Jaaroverzicht met inkomsten/uitgavenbalans
* Maandoverzicht
* Categorie-overzichten per maand
* Alle transacties
* Saldo-overzichten per rekening

Deze bestanden zijn compatibel met Excel, LibreOffice en Google Sheets.

## 📄 Licentie

MIT License — Vrij te gebruiken, aan te passen en te verspreiden.

