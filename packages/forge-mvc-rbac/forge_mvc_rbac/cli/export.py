# pyright: strict
"""Commande ``forge rbac:export`` (`RBAC-CONTRACT-EXPORT-001`).

Rend le contrat RBAC en Markdown ou en CSV. Lecture seule : aucune connexion,
aucun fichier écrit sans `--out`.
"""
from __future__ import annotations

from pathlib import Path

from forge_mvc_rbac.contract import load_rbac_contract
from forge_mvc_rbac.export import to_csv, to_markdown

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

__all__ = ["STATUS_OK", "STATUS_INFO", "STATUS_ERROR", "parse_options", "main"]

_FORMATS = ("markdown", "csv")


class _Options:
    def __init__(self) -> None:
        self.fmt = "markdown"
        self.out: "Path | None" = None
        self.error: "str | None" = None


def parse_options(argv: list[str]) -> _Options:
    """Lit les arguments. Un argument inconnu est une erreur, jamais un silence."""
    options = _Options()
    index = 0
    while index < len(argv):
        argument = argv[index]
        nom = argument.partition("=")[0]
        if nom in {"--format", "--out"}:
            if "=" in argument:
                valeur = argument.partition("=")[2]
            else:
                index += 1
                if index >= len(argv):
                    options.error = f"L'option {nom} attend une valeur."
                    return options
                valeur = argv[index]
            valeur = valeur.strip()
            if not valeur:
                options.error = f"L'option {nom} attend une valeur non vide."
                return options
            if nom == "--format":
                if valeur.lower() not in _FORMATS:
                    options.error = (
                        f"Format inconnu : {valeur!r}. Attendu "
                        f"{' ou '.join(_FORMATS)}."
                    )
                    return options
                options.fmt = valeur.lower()
            else:
                options.out = Path(valeur)
        elif argument.startswith("-"):
            options.error = f"Option inconnue : {argument!r}."
            return options
        else:
            options.error = f"Argument inattendu : {argument!r}."
            return options
        index += 1
    return options


def main(args: "list[str] | None" = None) -> int:
    options = parse_options(list(args or []))
    if options.error:
        print(f"{STATUS_ERROR} {options.error}")
        return 1

    resultat = load_rbac_contract(Path.cwd())
    if not resultat.exists:
        print(
            f"{STATUS_INFO} Aucun contrat RBAC dans {resultat.path}. "
            "Rien à exporter."
        )
        return 0
    if not resultat.valid:
        # Exporter un contrat invalide donnerait un tableau qui ne correspond à
        # rien d'applicable, et le lecteur le prendrait pour la vérité.
        print(
            f"{STATUS_ERROR} Le contrat {resultat.path} est invalide : "
            "l'exporter donnerait un tableau qui ne s'applique pas. "
            "Corrigez-le d'abord, forge rbac:validate le détaille."
        )
        return 1

    rendu = (
        to_csv(resultat.data) if options.fmt == "csv" else to_markdown(resultat.data)
    )

    if options.out is None:
        print(rendu)
        return 0

    if options.out.exists():
        print(
            f"{STATUS_ERROR} Le fichier existe déjà : {options.out}. "
            "Forge n'écrase jamais un fichier applicatif (charte §9)."
        )
        return 1

    options.out.parent.mkdir(parents=True, exist_ok=True)
    options.out.write_text(rendu, encoding="utf-8")
    print(f"{STATUS_OK} Écrit : {options.out}")
    print(
        f"{STATUS_INFO} Ce tableau rend le contrat, pas l'état de la base. "
        "forge rbac:audit compare les deux."
    )
    return 0
