# pyright: strict
"""Classe de base des factories de fixtures (ADR-076).

Une factory décrit comment produire des lignes pour une table. L'utilisateur en
écrit une sous-classe par entité, sous ``mvc/fixtures/factories/``, et code sa
génération dans ``rows(count)`` (boucles, conditions, tableaux) ou, pour le cas
simple, dans ``definition()`` (une ligne, répétée ``count`` fois).

``self.faker`` (Faker, locale configurable) est disponible mais **optionnel** :
les données peuvent aussi être écrites à la main ou calculées. La factory ne
touche jamais la base ni ne rend de SQL : elle produit des dicts colonne vers
valeur. Le rendu en ``.sql`` relu est le travail de ``fixtures:generate`` (pas de
magie ni d'auto-persistance, principe 3).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_LOCALE = "fr_FR"


class FactoryError(Exception):
    """Factory mal définie : table manquante ou lignes incohérentes."""


@dataclass(frozen=True)
class FixtureReference:
    """Référence à l'``Id`` d'une ligne d'une autre table, résolue à la charge (ADR-077).

    Produite par ``Factory.reference()`` et posée comme valeur de colonne (une clé
    étrangère, typiquement). ``fixtures:generate`` la rend en **sous-requête SQL**
    ``(SELECT Id FROM <table> WHERE <key_column> = <valeur> LIMIT 1)`` au lieu d'un
    littéral : la résolution se fait donc contre les vrais ``Id`` auto-incrémentés
    au moment de ``fixtures:load``, et le SQL reste visible et relu (principe 5).
    """

    table: str
    key_column: str
    value: Any


class Factory:
    """Base d'une factory de fixtures. À sous-classer par entité."""

    #: Table cible ; à définir dans la sous-classe.
    table: str = ""
    #: Locale Faker ; surchargeable dans la sous-classe.
    locale: str = DEFAULT_LOCALE

    def __init__(self, *, seed: int | None = None) -> None:
        # Import paresseux : le paquet reste importable sans Faker (load/purge).
        from faker import Faker

        self.faker: Any = Faker(self.locale)
        if seed is not None:
            self.faker.seed_instance(seed)

    def reference(self, table: str, key_column: str, value: Any) -> FixtureReference:
        """Référence l'``Id`` d'une ligne d'une autre table par une clé naturelle.

        Rend une valeur de colonne (typiquement une clé étrangère) qui pointe la
        ligne de ``table`` dont ``key_column`` vaut ``value`` : elle relie une
        fixture à une ligne produite par une autre, sans connaître son ``Id``.
        ``fixtures:generate`` l'écrit ``(SELECT Id FROM table WHERE key_column =
        value LIMIT 1)`` ; la résolution a lieu à la charge (ADR-077).
        """
        return FixtureReference(table=table, key_column=key_column, value=value)

    def definition(self) -> dict[str, Any]:
        """Une ligne (colonne vers valeur). À surcharger pour le cas simple."""
        raise NotImplementedError(
            "Définissez definition() (une ligne) ou rows(count) dans la factory."
        )

    def rows(self, count: int) -> list[dict[str, Any]]:
        """Les lignes à produire. Par défaut, ``definition()`` répétée ``count`` fois.

        Surchargez ``rows(count)`` pour coder votre propre génération (boucles,
        conditions, tableaux) ; ``count`` vient de ``--rows``.
        """
        return [self.definition() for _ in range(count)]

    def build(self, count: int) -> list[dict[str, Any]]:
        """Produit et valide les lignes.

        Vérifie que ``table`` est défini, que ``count`` est positif, et que toutes
        les lignes portent les mêmes colonnes dans le même ordre (nécessaire pour
        un ``INSERT`` uniforme). Lève ``FactoryError`` sinon.
        """
        if not self.table:
            raise FactoryError(f"{type(self).__name__} doit définir l'attribut `table`.")
        if count < 0:
            raise FactoryError("Le nombre de lignes ne peut pas être négatif.")

        produced = self.rows(count)
        columns: tuple[str, ...] | None = None
        for row in produced:
            keys = tuple(row.keys())
            if columns is None:
                columns = keys
            elif keys != columns:
                raise FactoryError(
                    "Toutes les lignes doivent porter les mêmes colonnes, dans le "
                    f"même ordre. Attendu {columns}, vu {keys}."
                )
        return produced
