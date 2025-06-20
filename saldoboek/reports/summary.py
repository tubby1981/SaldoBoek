def print_report_summary(df, jaar):
    inkomsten = df[df['bedrag'] > 0]['bedrag'].sum()
    uitgaven = abs(df[df['bedrag'] < 0]['bedrag'].sum())
    netto = inkomsten - uitgaven

    def format_euro_bedrag(bedrag):
        return f"€{bedrag:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    print(f"\n=== RAPPORT SAMENVATTING {jaar} ===")
    print(f"Totale inkomsten: {format_euro_bedrag(inkomsten)}")
    print(f"Totale uitgaven: {format_euro_bedrag(uitgaven)}")
    print(f"Netto resultaat: {format_euro_bedrag(netto)}")
    print(f"Aantal transacties: {len(df):,}")
    print(f"Aantal categorieën: {df['categorie'].nunique()}")
    print(f"Aantal rekeningen: {df['rekening'].nunique()}")
