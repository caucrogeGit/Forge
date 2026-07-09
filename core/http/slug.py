# pyright: strict
"""Module URL-slug canonique de Forge.

Ticket : SLUG-CORE-001 (ADR-017).

Une **URL slug** est un identifiant URL-safe en kebab-case (`[a-z0-9-]`),
destiné aux routes publiques (`/articles/premier-contact`). Ce module est la
**seule** implémentation officielle (charte §11) :

- :func:`slugify` *transforme* un texte quelconque en slug ;
- :func:`is_valid_slug` *valide* un slug existant (path-safe).

Dépendances **stdlib uniquement** (`unicodedata`, `re`) — runtime minimal de
Forge ; pas de `python-slugify`/`unidecode`.

À ne pas confondre avec ``forge_mvc_entities.migrations.slugify_migration_name``,
qui produit des **noms de fichiers de migration** en snake_case (`_`), pas des
URLs (ADR-017 D1).
"""
from __future__ import annotations

import re
import unicodedata

DEFAULT_MAX_LENGTH = 180

# Frontières camelCase : « MaPage » → « Ma-Page », « HTTPServer » → « HTTP-Server ».
_CAMEL_BOUNDARY_1 = re.compile(r"([a-z0-9])([A-Z])")
_CAMEL_BOUNDARY_2 = re.compile(r"([A-Z]+)([A-Z][a-z])")
_NON_SLUG_RUN = re.compile(r"[^a-z0-9]+")
_VALID_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _strip_accents(text: str) -> str:
    """Translittère les accents via décomposition NFKD (« Écrire » → « Ecrire »)."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def slugify(text: str, *, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """Transforme ``text`` en URL slug kebab-case.

    Étapes : translittération des accents (NFKD), insertion d'un tiret aux
    frontières camelCase, minuscules, remplacement de toute suite de caractères
    hors `[a-z0-9]` par un tiret, compactage et retrait des tirets de bordure,
    bornage de la longueur.

    Le résultat est toujours **path-safe** (`../admin` → `admin`).

    :raises ValueError: uniquement si le résultat est vide (aucun caractère
        exploitable).
    """
    value = _strip_accents(text.strip())
    value = _CAMEL_BOUNDARY_2.sub(r"\1-\2", value)
    value = _CAMEL_BOUNDARY_1.sub(r"\1-\2", value)
    value = value.lower()
    value = _NON_SLUG_RUN.sub("-", value).strip("-")
    if max_length > 0 and len(value) > max_length:
        value = value[:max_length].rstrip("-")
    if not value:
        raise ValueError(f"Texte non transformable en slug : {text!r}")
    return value


def is_valid_slug(value: str, *, max_length: "int | None" = DEFAULT_MAX_LENGTH) -> bool:
    """Vrai si ``value`` est une URL slug valide et **path-safe**.

    Rejette : vide, longueur > ``max_length`` (si défini), présence de `/`, `\\`
    ou `..`, et tout ce qui n'est pas du kebab-case strict
    `[a-z0-9]+(?:-[a-z0-9]+)*` (majuscules, accents, espaces, tirets de bordure
    ou doublés → invalides). ``max_length=None`` lève la borne de longueur.
    """
    if not value or (max_length is not None and len(value) > max_length):
        return False
    if any(part in value for part in ("/", "\\", "..")):
        return False
    return _VALID_SLUG.fullmatch(value) is not None
