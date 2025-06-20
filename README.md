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
git clone https://github.com/tubby1981/SaldoBoek.git
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

### 4. Configuratiebestanden

SaldoBoek gebruikt een aantal configureerbare YAML- en Python-bestanden om het categoriseren van transacties en het importeren van bankafschriften te vereenvoudigen en uitbreiden:

#### `config/categories.yaml`

Bevat **standaardcategorieën** die eenmalig worden toegevoegd bij het eerste gebruik van een nieuwe gebruiker. Daarna kunnen categorieën beheerd worden via het programma zelf.

- **Structuur**: per categorie:
  - `naam`: de naam van de categorie
  - `type`: `"inkomsten"` of `"uitgaven"`
  - `beschrijving`: optioneel

**Voorbeeld:**
```yaml
uitgaven:
  - naam: "Zorgverzekering"
    beschrijving: "Premies en eigen bijdragen zorgverzekering"

inkomsten:
  - naam: "Salaris"
    beschrijving: "Maandelijkse loonbetaling"
```

🔁 Je kunt dit bestand uitbreiden vóór het eerste gebruik. Daarna worden wijzigingen in de database bijgehouden.

#### `config/categorization_rules.yaml`

Bevat **zoekregels** voor automatische categorisatie. Als een omschrijving of tegenrekening een van de opgegeven zoekwoorden bevat (niet hoofdlettergevoelig), dan wordt de transactie automatisch toegewezen aan de bijbehorende categorie. Dit wordt eenmalig toegevoegd bij het eerste gebruik van een nieuwe gebruiker. Daarna kunnen categorieën beheerd worden via het programma zelf.

**Voorbeeld**
```yaml
zorgverzekering: "Zorgverzekering"
"albert heijn": "Boodschappen"
jumbo: "Boodschappen"
```

✏️  Je kunt dit bestand uitbreiden vóór het eerste gebruik. Daarna worden wijzigingen in de database bijgehouden.

### `config/bank_parsers.py`

Bevat een mapping van banknamen naar parserfuncties voor CSV-bestanden. Hiermee wordt per bank bepaald welke parser moet worden gebruikt.

**Voorbeeld**
```python
BANK_PARSERS = {
    'RABO': 'parse_rabo_csv',
    'SNS': 'parse_sns_csv',
    # 'ING': 'parse_ing_csv'
}
```

🔄 Je kunt hier eenvoudig extra banken toevoegen door een nieuwe CSV-parserfunctie te schrijven en toe te voegen aan deze mapping. De CSV-parserfuncties staan in `importer.py`


### 5. Start SaldoBoek

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

