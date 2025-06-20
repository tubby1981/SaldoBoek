from saldoboek.cli import SaldoBoekCLI
import traceback

def main():
    cli = SaldoBoekCLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\nProgramma afgesloten door gebruiker.")
    except Exception as e:
        print(f"Er is een onverwachte fout opgetreden: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

