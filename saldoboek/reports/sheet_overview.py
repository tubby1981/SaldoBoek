def create_overview_sheet(wb, df, jaar, suffix=""):
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter
    from datetime import datetime

    ws = wb.create_sheet(f"Overzicht{suffix}")

    ws['A1'] = f"Jaaroverzicht {jaar}{suffix}"
    ws['A1'].font = Font(bold=True, size=16)
    ws.merge_cells('A1:D1')

    ws['A3'] = "Rapportage periode:"
    ws['B3'] = f"01-01-{jaar} t/m 31-12-{jaar}"
    ws['A4'] = "Gegenereerd op:"
    ws['B4'] = datetime.now().strftime("%d-%m-%Y %H:%M")

    inkomsten = df[df['bedrag'] > 0]['bedrag'].sum()
    uitgaven = abs(df[df['bedrag'] < 0]['bedrag'].sum())
    netto = inkomsten - uitgaven

    ws.append(["", ""])
    ws.append(["FINANCIEEL OVERZICHT"])
    ws.append(["Totale inkomsten:", inkomsten])
    ws.append(["Totale uitgaven:", uitgaven])
    ws.append(["Netto resultaat:", netto])

    ws.append(["", ""])
    ws.append(["STATISTIEKEN"])
    ws.append(["Aantal transacties:", len(df)])
    ws.append(["Aantal rekeningen:", df['rekening'].nunique()])
    ws.append(["Aantal categorieën:", df['categorie'].nunique()])

    for col in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_length + 2, 50)
