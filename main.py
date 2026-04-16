import sys
import traceback

from saldoboek.cli import SaldoBoekCLI


def main():
    """Main entry point - start CLI of GUI."""
    if "--gui" in sys.argv:
        from saldoboek.gui.app import run_app

        run_app()
    else:
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
