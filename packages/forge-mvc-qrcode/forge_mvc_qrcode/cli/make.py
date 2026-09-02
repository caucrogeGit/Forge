# pyright: strict
"""Commande ``forge qrcode:make`` (`QRCODE-CLI-001`).

Le paquet savait produire un QR Code depuis du code Python et le servir en
HTTP. Produire un fichier, pour une affiche, une étiquette ou une
documentation, demandait d'écrire un script à usage unique.

La commande n'ouvre aucune connexion et ne lit aucune base : le paquet est sans
état.

## Ce qu'elle refuse

**Elle n'écrase jamais un fichier existant** (charte §9). Un QR Code régénéré
avec un autre contenu sous le même nom est indétectable à l'œil : deux carrés
noirs et blancs se ressemblent tous, et l'ancien serait perdu sans que rien ne
le signale.

**Elle refuse un format qui contredit l'extension.** `--format svg --out
code.png` produirait un fichier SVG nommé `.png`, que le navigateur servirait
avec le mauvais type et que l'imprimeur refuserait.
"""
from __future__ import annotations

from pathlib import Path

from forge_mvc_qrcode.errors import QrCodeError
from forge_mvc_qrcode.generator import ERROR_LEVELS, QrCode

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

__all__ = ["STATUS_OK", "STATUS_INFO", "STATUS_ERROR", "parse_options", "main"]

_FORMATS = ("png", "svg")
_EXTENSIONS = {".png": "png", ".svg": "svg"}


class _Options:
    def __init__(self) -> None:
        self.text: "str | None" = None
        self.out: "Path | None" = None
        self.fmt: "str | None" = None
        self.scale = 4
        self.border = 4
        self.error = "m"
        self.error_explicite = False
        self.err: "str | None" = None


def _valeur(argv: list[str], index: int, argument: str) -> "tuple[str | None, int]":
    if "=" in argument:
        return argument.partition("=")[2], index
    if index + 1 >= len(argv):
        return None, index
    return argv[index + 1], index + 1


def _entier(brut: str, nom: str, minimum: int) -> "int | str":
    try:
        valeur = int(brut)
    except ValueError:
        return f"L'option {nom} attend un entier. Reçu : {brut!r}."
    if valeur < minimum:
        return f"L'option {nom} doit valoir au moins {minimum}. Reçu : {valeur}."
    return valeur


def parse_options(argv: list[str]) -> _Options:
    """Lit les arguments. Un argument inconnu est une erreur, jamais un silence."""
    options = _Options()
    positionnels: list[str] = []
    index = 0
    while index < len(argv):
        argument = argv[index]
        nom = argument.partition("=")[0]
        if nom in {"--out", "--format", "--scale", "--border", "--error"}:
            brut, index = _valeur(argv, index, argument)
            if brut is None or not brut.strip():
                options.err = f"L'option {nom} attend une valeur."
                return options
            brut = brut.strip()
            if nom == "--out":
                options.out = Path(brut)
            elif nom == "--format":
                if brut.lower() not in _FORMATS:
                    options.err = (
                        f"Format inconnu : {brut!r}. Attendu "
                        f"{' ou '.join(_FORMATS)}."
                    )
                    return options
                options.fmt = brut.lower()
            elif nom == "--error":
                if brut.lower() not in ERROR_LEVELS:
                    options.err = (
                        f"Niveau de correction inconnu : {brut!r}. Attendu "
                        f"{', '.join(sorted(ERROR_LEVELS))}."
                    )
                    return options
                options.error = brut.lower()
                options.error_explicite = True
            else:
                lu = _entier(brut, nom, 1)
                if isinstance(lu, str):
                    options.err = lu
                    return options
                if nom == "--scale":
                    options.scale = lu
                else:
                    options.border = lu
        elif argument.startswith("-"):
            options.err = f"Option inconnue : {argument!r}."
            return options
        else:
            positionnels.append(argument)
        index += 1

    if len(positionnels) != 1:
        options.err = (
            'Usage : forge qrcode:make "TEXTE" [--out FICHIER] [--format png|svg] '
            "[--error l|m|q|h] [--scale N] [--border N]"
        )
        return options
    options.text = positionnels[0]

    # L'extension et le format doivent s'accorder : un SVG nommé `.png` serait
    # servi avec le mauvais type et refusé par un imprimeur.
    if options.out is not None:
        extension = options.out.suffix.lower()
        deduit = _EXTENSIONS.get(extension)
        if options.fmt is None:
            if deduit is None:
                options.err = (
                    f"Extension inconnue : {extension or '<aucune>'}. "
                    "Nommez le fichier .png ou .svg, ou passez --format."
                )
                return options
            options.fmt = deduit
        elif deduit is not None and deduit != options.fmt:
            options.err = (
                f"L'extension {extension} contredit --format {options.fmt}. "
                "Un fichier au mauvais type est servi et imprimé de travers."
            )
            return options
    elif options.fmt is None:
        options.fmt = "png"
    return options


def main(args: "list[str] | None" = None) -> int:
    options = parse_options(list(args or []))
    if options.err:
        print(f"{STATUS_ERROR} {options.err}")
        return 1

    assert options.text is not None and options.fmt is not None
    try:
        qr = QrCode.from_text(options.text, error=options.error)
        # `to_png` rend des octets, `to_svg` une chaîne : les deux formats
        # n'ont pas la même nature, et écrire l'un comme l'autre lève.
        if options.fmt == "png":
            contenu = qr.to_png(scale=options.scale, border=options.border)
        else:
            rendu = qr.to_svg(scale=options.scale, border=options.border)
            contenu = rendu if isinstance(rendu, bytes) else rendu.encode("utf-8")
    except QrCodeError as exc:
        print(f"{STATUS_ERROR} {exc}")
        return 1

    if options.out is None:
        print(
            f"{STATUS_INFO} QR Code de {len(contenu)} octets, format "
            f"{options.fmt}, correction {options.error}."
        )
        print(
            f"{STATUS_INFO} Aucun fichier écrit. Ajoutez --out fichier."
            f"{options.fmt} pour l'enregistrer (charte §7)."
        )
        return 0

    if options.out.exists():
        print(
            f"{STATUS_ERROR} Le fichier existe déjà : {options.out}. "
            "Deux QR Codes se ressemblent à l'œil : écraser perdrait "
            "l'ancien sans que rien ne le signale."
        )
        return 1

    options.out.parent.mkdir(parents=True, exist_ok=True)
    options.out.write_bytes(contenu)
    print(f"{STATUS_OK} Écrit : {options.out} ({len(contenu)} octets)")
    if not options.error_explicite:
        print(
            f"{STATUS_INFO} Correction d'erreur « m », qui tolère 15 % de "
            "perte. Pour une étiquette ou une affiche, --error h en tolère 30 %."
        )
    return 0
