# Changelog

Alle opmerkelijke wijzigingen aan SaldoBoek worden in dit bestand gedocumenteerd.

Het formaat is gebaseerd op [Keep a Changelog](https://keepachangelog.com/nl-NL/1.0.0/).

## [1.0.0] - 2024-XX-XX

### Toegevoegd
- **GUI Applicatie** - Moderne PySide6 grafische interface
  - Transactie overzicht met zoeken en filteren
  - Ongecategoriseerde transacties bekijken en categoriseren
  - Categoriebeheer (toevoegen, bewerken, verwijderen)
  - Statistieken dashboard met grafieken
  - Transactie import van SNS Bank en Rabobank
  - Thema ondersteuning (licht/donker/auto)
- **GitHub Actions** - Automatische builds voor Windows en Linux
- **pyproject.toml** - Python package configuratie

### Verbeteringen
- Column resizing in alle tabellen
- Rekeningtype selectie (betaalrekening/spaarrekening) bij import
- Bug fixes voor categorisatie

### Bekende beperkingen
- macOS niet officieel ondersteund (wel te gebruiken via Python installatie)
- CLI interface nog aanwezig maar focus ligt op GUI

---

## [0.x.x] - Voor GUI

Voor versies vóór 1.0.0 was SaldoBoek een CLI-only applicatie. Zie de GitHub history voor details.