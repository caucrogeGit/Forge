# pyright: strict
"""Commande ``forge fixtures:make-factory`` — scaffold d'une factory (ADR-076).

Lit le contrat d'entité ``mvc/entities/<entity>/<entity>.json`` et génère une
factory **riche** sous ``mvc/fixtures/factories/<entity>_factory.py`` : chaque
champ reçoit un provider Faker plausible, deviné par type et par nom. L'utilisateur
part d'une factory qui fonctionne, puis ajuste (boucles, conditions, providers).

Mode « Forge génère » (charte §9) : write-if-new, jamais d'écrasement sans
``--force``. Ne lit que le contrat, n'ouvre aucune connexion (pas de ``config``).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

__all__ = ["provider_for_field", "render_factory", "make_factory", "main"]


class MakeFactoryError(Exception):
    """Contrat d'entité introuvable ou invalide."""


# Provider Faker par défaut selon le type Forge.
_PROVIDER_BY_TYPE: dict[str, str] = {
    "string": "self.faker.word()",
    "text": "self.faker.paragraph()",
    "integer": "self.faker.random_int(min=0, max=1000)",
    "big_integer": "self.faker.random_int(min=0, max=1_000_000)",
    "float": "self.faker.pyfloat(left_digits=3, right_digits=2, positive=True)",
    "decimal": "self.faker.pydecimal(left_digits=6, right_digits=2, positive=True)",
    "boolean": "self.faker.boolean()",
    "date": "self.faker.date_object()",
    "datetime": "self.faker.date_time()",
    "email": "self.faker.email()",
    "password": "self.faker.password()",
    "slug": "self.faker.slug()",
    "json": '"{}"',
}

# Heuristiques par nom (appliquées aux champs textuels) ; premier motif contenu
# dans le nom gagne. `prenom` avant `nom`, `email` en tête.
_PROVIDER_BY_NAME: list[tuple[tuple[str, ...], str]] = [
    (("email",), "self.faker.email()"),
    (("prenom", "first_name", "firstname"), "self.faker.first_name()"),
    (("nom", "name", "lastname"), "self.faker.last_name()"),
    (("ville", "city"), "self.faker.city()"),
    (("adresse", "address"), "self.faker.address()"),
    (("telephone", "phone", "tel"), "self.faker.phone_number()"),
    (("code_postal", "postal", "zip"), "self.faker.postcode()"),
    (("pays", "country"), "self.faker.country()"),
    (("titre", "title"), "self.faker.sentence(nb_words=4)"),
    (("description", "contenu", "content", "resume"), "self.faker.paragraph()"),
    (("url", "lien", "link", "site"), "self.faker.url()"),
    (("slug",), "self.faker.slug()"),
]

_TEXTUAL_TYPES = {"string", "text", "slug"}


def provider_for_field(field: dict[str, Any]) -> tuple[str, str]:
    """Expression de valeur + commentaire éventuel, pour un champ.

    Renvoie ``(expression, comment)`` où ``comment`` commence par ``  #`` ou est vide.
    """
    name = str(field.get("name", "")).lower()
    ftype = str(field.get("type", "string"))

    if ftype == "foreign_key":
        return "1", "  # TODO: id d'une ligne existante (clé étrangère)"

    if ftype in _TEXTUAL_TYPES:
        for tokens, provider in _PROVIDER_BY_NAME:
            if any(token in name for token in tokens):
                return provider, ""

    return _PROVIDER_BY_TYPE.get(ftype, "self.faker.word()"), ""


def _read_contract(root: Path, entity: str) -> dict[str, Any]:
    path = root / "mvc" / "entities" / entity / f"{entity}.json"
    if not path.is_file():
        raise MakeFactoryError(
            f"Contrat d'entité introuvable : {path.as_posix()}. "
            f"Créez l'entité d'abord (forge make:entity {entity})."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MakeFactoryError(f"Contrat JSON invalide ({path.name}) : {exc}") from None
    if not isinstance(data, dict):
        raise MakeFactoryError(f"Contrat JSON invalide ({path.name}) : objet attendu.")
    return cast("dict[str, Any]", data)


def render_factory(contract: dict[str, Any]) -> str:
    """Rend le code Python d'une factory riche depuis un contrat d'entité."""
    class_name = str(contract.get("name") or "Entity").replace(" ", "")
    table = str(contract.get("table") or "table")
    fields: Any = contract.get("fields") or []

    field_lines: list[str] = []
    for field_obj in fields:
        if not isinstance(field_obj, dict):
            continue
        field = cast("dict[str, Any]", field_obj)
        column = str(field.get("name", ""))
        if not column:
            continue
        expr, comment = provider_for_field(field)
        field_lines.append(f'            "{column}": {expr},{comment}')

    body = "\n".join(field_lines) if field_lines else "            # Ajoutez vos colonnes ici."

    return (
        f'"""Factory de fixtures pour {class_name} '
        "(générée par forge fixtures:make-factory).\n"
        "\n"
        "Ajustez les providers Faker, ajoutez des boucles ou des conditions selon\n"
        "vos besoins. Providers disponibles : https://faker.readthedocs.io/\n"
        '"""\n'
        "from forge_mvc_fixtures import Factory\n"
        "\n"
        "\n"
        f"class {class_name}Factory(Factory):\n"
        f'    table = "{table}"\n'
        "\n"
        "    def definition(self) -> dict:\n"
        "        return {\n"
        f"{body}\n"
        "        }\n"
    )


def make_factory(root: Path, entity: str, *, force: bool) -> int:
    """Génère la factory de l'entité. Codes : 0 écrit, 2 erreur, 1 fichier existant."""
    try:
        contract = _read_contract(root, entity)
    except MakeFactoryError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2

    source = render_factory(contract)
    print(source)

    target = root / "mvc" / "fixtures" / "factories" / f"{entity}_factory.py"
    if target.exists() and not force:
        print(
            f"Fichier déjà présent, non écrit : {target.as_posix()}. "
            "Ajoutez --force pour le remplacer (charte §9).",
            file=sys.stderr,
        )
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    print(f"[OK] Factory écrite dans {target.as_posix()}.")
    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge fixtures:make-factory``."""
    argv = list(args or [])
    force = "--force" in argv
    positionals = [a for a in argv if not a.startswith("-")]
    if len(positionals) != 1:
        print(
            "Erreur : usage forge fixtures:make-factory <entity> [--force].",
            file=sys.stderr,
        )
        return 2
    return make_factory(Path.cwd(), positionals[0], force=force)
