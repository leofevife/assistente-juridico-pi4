import argparse
import sys

from avaliacao.ground_truth import carregar_artigos_cdc, carregar_ground_truth, validar_ground_truth


def _validar() -> int:
    conjunto = carregar_ground_truth()
    problemas = validar_ground_truth(conjunto, carregar_artigos_cdc())
    if problemas:
        print(f"Ground Truth inválido ({len(problemas)} problema(s)):")
        for problema in problemas:
            print(f" - {problema}")
        return 1
    temas = len({caso.tema for caso in conjunto.casos})
    print(f"Ground Truth v{conjunto.versao} válido: {len(conjunto.casos)} casos em {temas} temas.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m avaliacao", description="Avaliação do assistente jurídico.")
    subcomandos = parser.add_subparsers(dest="comando", required=True)
    subcomandos.add_parser("validar", help="Valida o conjunto Ground Truth contra o texto do CDC.")

    args = parser.parse_args(argv)
    if args.comando == "validar":
        return _validar()
    return 2


if __name__ == "__main__":
    sys.exit(main())
