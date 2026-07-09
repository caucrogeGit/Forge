# pyright: strict
"""forge_mvc_entities/service.py — Service de persistance pour tables pivot avec attributs (opt-in extrait du core, ADR-021).

Permet de gérer les associations many_to_many enrichies (pivot.fields[]) sans
modifier make:crud. Utilise le même pattern d'injection que MariaDbSessionStore :
fetch_one, fetch_all et execute sont injectables pour les tests.

Décision : PIVOT-ADVANCED-001 / PIVOT-ADVANCED-003.
Contraintes : PIVOT-ADVANCED-006.
UX erreurs : PIVOT-ADVANCED-007.
UX future : PIVOT-ADVANCED-004 (commande/générateur dédié).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field as dc_field
from typing import Any

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Frontière base : les accesseurs DB injectables partagent la signature des
# helpers de ``core.database.db`` (paramètres positionnels SQL + tuple).
_Params = tuple[Any, ...]
_FetchOne = Callable[[str, _Params], "dict[str, Any] | None"]
_FetchAll = Callable[[str, _Params], "list[dict[str, Any]]"]
_Execute = Callable[[str, _Params], int]


def _safe_identifier(name: str, label: str) -> str:
    """Valide qu'un nom de table ou de colonne ne contient pas de caractères dangereux."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(
            f"{label} invalide : {name!r}. "
            "Seuls les caractères [A-Za-z0-9_] sont autorisés, le premier doit être une lettre ou _."
        )
    return name


# ── Résultat ──────────────────────────────────────────────────────────────────

@dataclass
class PivotRow:
    """Représente une ligne de table pivot avec ses attributs."""
    source_id: int | str
    target_id: int | str
    pivot_data: dict[str, Any] = dc_field(default_factory=dict[str, Any])


# ── Erreur UX ─────────────────────────────────────────────────────────────────

@dataclass
class PivotFormError:
    """Erreur pivot normalisée — affichable dans un formulaire de sous-CRUD pivot.

    code    : identifiant stable du type d'erreur
    message : message humain à afficher dans le formulaire
    field   : champ concerné si applicable, None sinon
    """
    code: str
    message: str
    field: str | None = None


class PivotConstraintError(ValueError):
    """Levée quand une contrainte pivot est violée (required, nullable, unique_pair).

    Porte un code stable et éventuellement le champ concerné pour
    permettre un affichage structuré dans les formulaires pivot.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "invalid_pivot_data",
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field


# ── Contraintes ───────────────────────────────────────────────────────────────

@dataclass
class PivotFieldConstraint:
    """Contrainte déclarative sur un champ pivot.

    required=True  → le champ doit être présent dans pivot_data lors d'un attach.
    nullable=False → la valeur None est refusée lors d'un attach ou update.
    """
    name: str
    required: bool = False
    nullable: bool = True


# ── Helper UX ─────────────────────────────────────────────────────────────────

def pivot_error_to_form_error(error: Exception) -> PivotFormError:
    """Convertit une exception de PivotAdvancedService en PivotFormError affichable.

    - PivotConstraintError → PivotFormError avec le code et le champ structurés.
    - ValueError (hors PivotConstraintError) → code unknown_pivot_field.
    - Autre exception → code invalid_pivot_data, message générique (pas de détail SQL).
    """
    if isinstance(error, PivotConstraintError):
        return PivotFormError(
            code=error.code,
            message=str(error),
            field=error.field,
        )
    if isinstance(error, ValueError):
        return PivotFormError(
            code="unknown_pivot_field",
            message=str(error),
        )
    return PivotFormError(
        code="invalid_pivot_data",
        message="Une erreur est survenue lors de l'enregistrement.",
    )


# ── Accesseurs DB par défaut (lazy — pas de connexion à l'import) ─────────────

def _default_fetch_one(sql: str, params: _Params) -> dict[str, Any] | None:
    from core.database.db import fetch_one
    return fetch_one(sql, params)


def _default_fetch_all(sql: str, params: _Params) -> list[dict[str, Any]]:
    from core.database.db import fetch_all
    return fetch_all(sql, params) or []


def _default_execute(sql: str, params: _Params) -> int:
    from core.database.db import execute
    return execute(sql, params)


def _default_insert(sql: str, params: _Params) -> int:
    from core.database.db import insert
    return insert(sql, params)


# ── Service ───────────────────────────────────────────────────────────────────

class PivotAdvancedService:
    """Service générique pour lire et modifier des associations pivot avec attributs.

    Paramètres :
        table             — nom de la table pivot (ex: "article_tag")
        source_key        — colonne de clé source (ex: "article_id")
        target_key        — colonne de clé cible (ex: "tag_id")
        pivot_fields      — liste des noms de colonnes métier autorisés (ex: ["position", "note"])
        pivot_constraints — liste de PivotFieldConstraint pour les contraintes avancées
        unique_pair       — si True, vérifie l'unicité avant INSERT (default False)
        id_field          — nom de la colonne id technique (ex: "id"), active get_by_id etc.

    Les callables fetch_one, fetch_all, execute et insert_fn sont injectables pour les tests.
    En production ils délèguent aux helpers core.database.db.

    API pivot_fields (ancienne) et pivot_constraints (nouvelle) sont mutuellement exclusives.
    Si pivot_constraints est fourni, il prend la priorité et définit la liste des champs autorisés.
    """

    def __init__(
        self,
        table: str,
        source_key: str,
        target_key: str,
        pivot_fields: list[str] | None = None,
        *,
        pivot_constraints: list[PivotFieldConstraint] | None = None,
        unique_pair: bool = False,
        id_field: str | None = None,
        fetch_one: _FetchOne | None = None,
        fetch_all: _FetchAll | None = None,
        execute: _Execute | None = None,
        insert_fn: _Execute | None = None,
    ) -> None:
        self._table = _safe_identifier(table, "table")
        self._source_key = _safe_identifier(source_key, "source_key")
        self._target_key = _safe_identifier(target_key, "target_key")
        self._unique_pair = unique_pair
        self._id_field = _safe_identifier(id_field, "id_field") if id_field else None

        if pivot_constraints is not None:
            for c in pivot_constraints:
                _safe_identifier(c.name, f"pivot_constraints[{c.name}].name")
            self._pivot_fields: tuple[str, ...] = tuple(c.name for c in pivot_constraints)
            self._constraints: dict[str, PivotFieldConstraint] = {c.name: c for c in pivot_constraints}
        else:
            self._pivot_fields = tuple(
                _safe_identifier(f, f"pivot_fields[{i}]")
                for i, f in enumerate(pivot_fields or [])
            )
            self._constraints = {}

        self._fetch_one = fetch_one or _default_fetch_one
        self._fetch_all = fetch_all or _default_fetch_all
        self._execute = execute or _default_execute
        self._insert_fn = insert_fn or _default_insert

    # ── helpers internes ──────────────────────────────────────────────────────

    def _check_pivot_data(self, pivot_data: dict[str, Any]) -> None:
        """Lève ValueError si pivot_data contient des clés inconnues."""
        unknown = set(pivot_data) - set(self._pivot_fields)
        if unknown:
            raise ValueError(
                f"Champs pivot inconnus : {sorted(unknown)}. "
                f"Champs autorisés : {sorted(self._pivot_fields)}."
            )

    def _enforce_attach_constraints(self, pivot_data: dict[str, Any]) -> None:
        """Vérifie required et nullable lors d'un attach."""
        for field_name, constraint in self._constraints.items():
            if constraint.required and field_name not in pivot_data:
                raise PivotConstraintError(
                    f"Champ pivot requis absent : {field_name!r}.",
                    code="required_field_missing",
                    field=field_name,
                )
            if not constraint.nullable and field_name in pivot_data and pivot_data[field_name] is None:
                raise PivotConstraintError(
                    f"Champ pivot non nullable reçoit None : {field_name!r}.",
                    code="nullable_field_rejected",
                    field=field_name,
                )

    def _enforce_update_constraints(self, pivot_data: dict[str, Any]) -> None:
        """Vérifie nullable lors d'un update (required non vérifié — mise à jour partielle)."""
        for field_name, constraint in self._constraints.items():
            if not constraint.nullable and field_name in pivot_data and pivot_data[field_name] is None:
                raise PivotConstraintError(
                    f"Champ pivot non nullable reçoit None : {field_name!r}.",
                    code="nullable_field_rejected",
                    field=field_name,
                )

    def _row_to_pivot_row(self, row: dict[str, Any]) -> PivotRow:
        pivot_data = {k: v for k, v in row.items()
                      if k not in (self._source_key, self._target_key)}
        return PivotRow(
            source_id=row[self._source_key],
            target_id=row[self._target_key],
            pivot_data=pivot_data,
        )

    # ── API publique ──────────────────────────────────────────────────────────

    def list_for_source(self, source_id: int | str) -> list[PivotRow]:
        """Retourne toutes les associations liées à source_id."""
        sql = f"SELECT * FROM {self._table} WHERE {self._source_key} = ?"
        rows = self._fetch_all(sql, (source_id,))
        return [self._row_to_pivot_row(r) for r in rows]

    def get(self, source_id: int | str, target_id: int | str) -> PivotRow | None:
        """Retourne l'association (source_id, target_id), ou None si absente."""
        sql = (
            f"SELECT * FROM {self._table} "
            f"WHERE {self._source_key} = ? AND {self._target_key} = ?"
        )
        row = self._fetch_one(sql, (source_id, target_id))
        return self._row_to_pivot_row(row) if row else None

    def attach(
        self,
        source_id: int | str,
        target_id: int | str,
        pivot_data: dict[str, Any] | None = None,
    ) -> int:
        """Crée une association. Retourne le lastrowid.

        Seuls les champs déclarés dans pivot_fields / pivot_constraints sont acceptés.
        Si unique_pair=True, lève PivotConstraintError si l'association existe déjà.
        """
        pivot_data = pivot_data or {}
        self._check_pivot_data(pivot_data)
        self._enforce_attach_constraints(pivot_data)

        if self._unique_pair and self.get(source_id, target_id) is not None:
            raise PivotConstraintError(
                f"Association ({source_id}, {target_id}) déjà existante dans {self._table}.",
                code="duplicate_pair",
            )

        columns = [self._source_key, self._target_key] + [
            f for f in self._pivot_fields if f in pivot_data
        ]
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(columns)
        values = (source_id, target_id) + tuple(
            pivot_data[f] for f in self._pivot_fields if f in pivot_data
        )

        sql = f"INSERT INTO {self._table} ({col_list}) VALUES ({placeholders})"
        return self._insert_fn(sql, values)

    def update(
        self,
        source_id: int | str,
        target_id: int | str,
        pivot_data: dict[str, Any],
    ) -> int:
        """Modifie les attributs pivot d'une association existante. Retourne rowcount.

        Ne modifie pas source_key ni target_key.
        Seuls les champs déclarés dans pivot_fields / pivot_constraints sont acceptés.
        required n'est pas vérifié (mise à jour partielle autorisée).
        """
        self._check_pivot_data(pivot_data)
        self._enforce_update_constraints(pivot_data)
        if not pivot_data:
            return 0

        set_clause = ", ".join(f"{f} = ?" for f in pivot_data)
        values = tuple(pivot_data[f] for f in pivot_data) + (source_id, target_id)
        sql = (
            f"UPDATE {self._table} SET {set_clause} "
            f"WHERE {self._source_key} = ? AND {self._target_key} = ?"
        )
        return self._execute(sql, values)

    def detach(self, source_id: int | str, target_id: int | str) -> int:
        """Supprime l'association (source_id, target_id). Retourne rowcount."""
        sql = (
            f"DELETE FROM {self._table} "
            f"WHERE {self._source_key} = ? AND {self._target_key} = ?"
        )
        return self._execute(sql, (source_id, target_id))

    # ── Méthodes par id technique (requiert id_field) ─────────────────────────

    def get_by_id(self, pivot_id: int | str) -> PivotRow | None:
        """Retourne la ligne pivot par son id technique. Requiert id_field."""
        if not self._id_field:
            raise PivotConstraintError(
                "get_by_id requiert id_field sur PivotAdvancedService.",
                code="missing_id_field",
            )
        sql = f"SELECT * FROM {self._table} WHERE {self._id_field} = ?"
        row = self._fetch_one(sql, (pivot_id,))
        return self._row_to_pivot_row(row) if row else None

    def update_by_id(self, pivot_id: int | str, pivot_data: dict[str, Any]) -> int:
        """Modifie les attributs d'une ligne pivot par son id technique. Requiert id_field."""
        if not self._id_field:
            raise PivotConstraintError(
                "update_by_id requiert id_field sur PivotAdvancedService.",
                code="missing_id_field",
            )
        self._check_pivot_data(pivot_data)
        self._enforce_update_constraints(pivot_data)
        if not pivot_data:
            return 0
        set_clause = ", ".join(f"{f} = ?" for f in pivot_data)
        values = tuple(pivot_data[f] for f in pivot_data) + (pivot_id,)
        sql = f"UPDATE {self._table} SET {set_clause} WHERE {self._id_field} = ?"
        return self._execute(sql, values)

    def delete_by_id(self, pivot_id: int | str) -> int:
        """Supprime une ligne pivot par son id technique. Requiert id_field."""
        if not self._id_field:
            raise PivotConstraintError(
                "delete_by_id requiert id_field sur PivotAdvancedService.",
                code="missing_id_field",
            )
        sql = f"DELETE FROM {self._table} WHERE {self._id_field} = ?"
        return self._execute(sql, (pivot_id,))
