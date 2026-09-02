# pyright: strict
"""Commande ``forge iot:token`` (`IOT-DEVICE-AUTH-001`).

Crée, liste et révoque les jetons de lecture par site ou par équipement.

Le jeton créé est **affiché une seule fois**. Il n'est pas stocké en clair, et
ne pourra pas être retrouvé : c'est le mode « Forge affiche » de la charte, et
la seule façon d'éviter qu'un secret dorme en base.
"""
from __future__ import annotations

from forge_mvc_iot.tokens import IotScope, IotTokenError, IotTokenRepository

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

__all__ = ["STATUS_OK", "STATUS_INFO", "STATUS_ERROR", "parse_options", "main"]

_SOUS_COMMANDES = ("create", "list", "revoke")


class _Options:
    def __init__(self) -> None:
        self.action: "str | None" = None
        self.site: "str | None" = None
        self.device: "str | None" = None
        self.label: "str | None" = None
        self.token_id: "int | None" = None
        self.error: "str | None" = None


def _valeur(argv: list[str], index: int, argument: str) -> "tuple[str | None, int]":
    if "=" in argument:
        return argument.partition("=")[2], index
    if index + 1 >= len(argv):
        return None, index
    return argv[index + 1], index + 1


def parse_options(argv: list[str]) -> _Options:
    """Lit les arguments. Un argument inconnu est une erreur, jamais un silence."""
    options = _Options()
    positionnels: list[str] = []
    index = 0
    while index < len(argv):
        argument = argv[index]
        nom = argument.partition("=")[0]
        if nom in {"--site", "--device", "--label"}:
            valeur, index = _valeur(argv, index, argument)
            if valeur is None or not valeur.strip():
                options.error = f"L'option {nom} attend une valeur."
                return options
            setattr(options, nom.lstrip("-"), valeur.strip())
        elif argument.startswith("-"):
            options.error = f"Option inconnue : {argument!r}."
            return options
        else:
            positionnels.append(argument)
        index += 1

    if not positionnels:
        options.error = (
            "Usage : forge iot:token create [--site SITE] [--device ID] [--label TEXTE]\n"
            "        forge iot:token list\n"
            "        forge iot:token revoke ID"
        )
        return options

    options.action = positionnels[0]
    if options.action not in _SOUS_COMMANDES:
        options.error = (
            f"Sous-commande inconnue : {options.action!r}. "
            f"Attendu {', '.join(_SOUS_COMMANDES)}."
        )
        return options

    if options.action == "revoke":
        if len(positionnels) != 2:
            options.error = "Usage : forge iot:token revoke ID"
            return options
        try:
            options.token_id = int(positionnels[1])
        except ValueError:
            options.error = f"Identifiant de jeton invalide : {positionnels[1]!r}."
            return options
    elif len(positionnels) > 1:
        options.error = f"Argument en trop : {positionnels[1]!r}."
        return options

    if options.action == "create" and options.device and not options.site:
        options.error = (
            "--device exige --site : deux sites peuvent nommer leur capteur "
            "de la même façon."
        )
    return options


def _creer(options: _Options, depot: IotTokenRepository) -> int:
    try:
        brut, identifiant = depot.create(
            site=options.site, device_id=options.device, label=options.label
        )
    except IotTokenError as exc:
        print(f"{STATUS_ERROR} {exc}")
        return 1

    portee = IotScope(site=options.site, device_id=options.device)
    print(f"{STATUS_OK} Jeton {identifiant} créé, portée {portee.describe()}.")
    print()
    print(f"    {brut}")
    print()
    print(
        f"{STATUS_INFO} Ce jeton ne sera plus jamais affiché : seule son "
        "empreinte est stockée. Le perdre oblige à en créer un autre."
    )
    if portee.is_global:
        print(
            f"{STATUS_INFO} Portée globale : ce jeton ouvre TOUS les sites. "
            "Préférez --site pour ne donner que ce qui est nécessaire."
        )
    return 0


def _lister(depot: IotTokenRepository) -> int:
    lignes = depot.list_all()
    if not lignes:
        print(f"{STATUS_INFO} Aucun jeton enregistré.")
        return 0
    print(f"{STATUS_INFO} {len(lignes)} jeton(s) :")
    for ligne in lignes:
        portee = IotScope(
            site=str(ligne["site"]) if ligne.get("site") else None,
            device_id=str(ligne["device_id"]) if ligne.get("device_id") else None,
        )
        etat = "révoqué" if ligne.get("revoked_at") else "actif"
        libelle = f" — {ligne['label']}" if ligne.get("label") else ""
        print(f"    {ligne['id']:>4}  {etat:<8}  {portee.describe()}{libelle}")
    return 0


def main(args: "list[str] | None" = None) -> int:
    options = parse_options(list(args or []))
    if options.error:
        print(f"{STATUS_ERROR} {options.error}")
        return 1

    depot = IotTokenRepository()

    if options.action == "create":
        return _creer(options, depot)
    if options.action == "list":
        return _lister(depot)

    assert options.token_id is not None
    if depot.revoke(options.token_id):
        print(f"{STATUS_OK} Jeton {options.token_id} révoqué.")
        return 0
    print(
        f"{STATUS_ERROR} Aucun jeton actif portant l'identifiant "
        f"{options.token_id}."
    )
    return 1
