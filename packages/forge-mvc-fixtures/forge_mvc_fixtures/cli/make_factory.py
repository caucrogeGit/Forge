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
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

# Dependance douce a forge-mvc-entities (ADR-077) : producteur des contrats, il
# expose la source unique du mapping champ vers colonne. Absent, on retombe sur
# le nom de champ brut (mode degrade documente).
_entities_column_for_field: Callable[[dict[str, Any]], str] | None
try:
    from forge_mvc_entities import column_for_field as _entities_column_for_field
except ImportError:  # pragma: no cover - depend de l'environnement d'installation
    _entities_column_for_field = None

__all__ = [
    "column_for_field",
    "reference_expr",
    "provider_for_field",
    "fk_targets",
    "render_factory",
    "make_factory",
    "main",
]


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


def column_for_field(field: dict[str, Any]) -> str:
    """Colonne SQL reelle d'un champ de contrat (ADR-077).

    Delegue a ``forge_mvc_entities.column_for_field`` (source unique du mapping
    champ vers colonne : ``Id`` pour la PK, snake conserve pour un
    ``foreign_key``, PascalCase sinon). En son absence (dependance douce), repli
    sur le nom de champ brut, mode degrade documente.
    """
    if _entities_column_for_field is not None:
        return _entities_column_for_field(field)
    return str(field.get("name", ""))


def reference_expr(target_table: str | None) -> tuple[str, str]:
    """Scaffold ``self.reference(...)`` pour une clé étrangère (F43, ADR-077).

    Relie la ligne à une autre table par une clé naturelle, plutôt qu'un
    ``random_int`` sans cible. ``target_table`` vient de ``relations.json`` quand
    il est connu ; la clé naturelle et sa valeur restent des TODO à renseigner.
    """
    table = target_table or "table_cible"
    return (
        f'self.reference("{table}", "cle_naturelle", "valeur")',
        "  # TODO (F43): renseignez la clé naturelle (colonne unique) et sa valeur",
    )


def provider_for_field(field: dict[str, Any]) -> tuple[str, str]:
    """Expression de valeur + commentaire éventuel, pour un champ.

    Renvoie ``(expression, comment)`` où ``comment`` commence par ``  #`` ou est vide.
    """
    name = str(field.get("name", "")).lower()
    ftype = str(field.get("type", "string"))

    if ftype == "foreign_key":
        return reference_expr(None)

    if ftype in _TEXTUAL_TYPES:
        for tokens, provider in _PROVIDER_BY_NAME:
            if any(token in name for token in tokens):
                return provider, ""

    return _PROVIDER_BY_TYPE.get(ftype, "self.faker.word()"), ""


def _snake(name: str) -> str:
    """PascalCase vers snake_case (``AnneeScolaire`` vers ``annee_scolaire``)."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _target_table(root: Path, target_entity: str) -> str:
    """Table de l'entité cible, lue dans son contrat ; repli sur le nom snake."""
    snake = _snake(target_entity)
    path = root / "mvc" / "entities" / snake / f"{snake}.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return snake
        if isinstance(data, dict):
            table = cast("dict[str, Any]", data).get("table")
            if isinstance(table, str) and table:
                return table
    return snake


def fk_targets(root: Path, entity: str) -> dict[str, str]:
    """Colonnes clé étrangère de l'entité vers leur table cible (F43, ADR-077).

    Lit ``mvc/entities/relations.json`` : pour chaque relation ``many_to_one``
    dont l'entité est la source, associe la colonne FK (``foreign_key`` ou
    ``<name>_id`` par défaut) à la table de l'entité cible. Absente ou illisible,
    renvoie un mapping vide (repli sans référence).
    """
    path = root / "mvc" / "entities" / "relations.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    relations = cast("dict[str, Any]", data).get("relations")
    if not isinstance(relations, list):
        return {}
    targets: dict[str, str] = {}
    for rel_obj in cast("list[Any]", relations):
        if not isinstance(rel_obj, dict):
            continue
        rel = cast("dict[str, Any]", rel_obj)
        if rel.get("type") != "many_to_one":
            continue
        if _snake(str(rel.get("from", ""))) != entity:
            continue
        name = str(rel.get("name", ""))
        fk_column = str(rel.get("foreign_key") or f"{name}_id")
        if fk_column:
            targets[fk_column] = _target_table(root, str(rel.get("to", "")))
    return targets


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


def render_factory(
    contract: dict[str, Any], *, fk_map: dict[str, str] | None = None
) -> str:
    """Rend le code Python d'une factory riche depuis un contrat d'entité.

    ``fk_map`` associe une colonne clé étrangère à sa table cible (``relations.json``,
    F43) : un champ ``foreign_key``, ou dont le nom y figure, reçoit un
    ``self.reference(...)`` au lieu d'un provider aléatoire.
    """
    targets = fk_map or {}
    class_name = str(contract.get("name") or "Entity").replace(" ", "")
    table = str(contract.get("table") or "table")
    fields: Any = contract.get("fields") or []

    field_lines: list[str] = []
    for field_obj in fields:
        if not isinstance(field_obj, dict):
            continue
        field = cast("dict[str, Any]", field_obj)
        name = str(field.get("name", ""))
        if not name:
            continue
        column = column_for_field(field)
        if str(field.get("type", "")) == "foreign_key" or name in targets:
            expr, comment = reference_expr(targets.get(name))
        else:
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

    source = render_factory(contract, fk_map=fk_targets(root, entity))
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
