# pyright: strict
"""Moteur d'import : validation par champ, rapport d'erreurs, insertion.

Le moteur est générique et explicite : l'application décrit ses colonnes par des
:class:`FieldSpec` (nom, requis, fonction de conversion) et fournit une fonction
`insert` qui écrit une ligne validée. Le SQL reste donc dans le modèle de
l'application ; ce paquet ne connaît ni la base ni les entités.

Par défaut, l'import est « tout ou rien » au niveau validation : si une seule
ligne est invalide, **rien n'est inséré** et le rapport liste toutes les
erreurs (on corrige le CSV puis on relance). L'option `partial=True` insère les
lignes valides malgré des lignes en erreur.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from forge_mvc_import.errors import CsvImportError


@dataclass(frozen=True)
class FieldSpec:
    """Spécification d'une colonne à importer.

    `coerce` convertit la chaîne CSV en valeur typée ; elle lève `ValueError`
    (ou `TypeError`) si la valeur est invalide. `None` conserve la chaîne.
    """

    name: str
    required: bool = True
    coerce: "Callable[[str], object] | None" = None


@dataclass(frozen=True)
class RowError:
    """Une erreur localisée. `row` est l'index 1-based des lignes de données."""

    row: int
    field: str | None
    message: str


@dataclass(frozen=True)
class ImportReport:
    """Résultat d'un import : nombre de lignes insérées et erreurs collectées."""

    imported: int
    errors: list[RowError]

    @property
    def ok(self) -> bool:
        return not self.errors


def _try_coerce(coerce: "Callable[[str], object]", value: str) -> tuple[object, bool]:
    try:
        return coerce(value), True
    except (ValueError, TypeError):
        return None, False


def import_rows(
    rows: Sequence[dict[str, str]],
    specs: Sequence[FieldSpec],
    insert: "Callable[[dict[str, object]], object]",
    *,
    partial: bool = False,
) -> ImportReport:
    """Valide `rows` selon `specs`, puis insère les lignes valides via `insert`.

    Renvoie un :class:`ImportReport` (lignes insérées + erreurs). Lève
    :class:`CsvImportError` si `specs` est vide.
    """
    if not specs:
        raise CsvImportError("Aucune colonne à importer (specs vide).")

    errors: list[RowError] = []
    validated: list[tuple[int, dict[str, object]]] = []

    for index, row in enumerate(rows, start=1):
        record: dict[str, object] = {}
        row_ok = True
        for spec in specs:
            value = row.get(spec.name, "").strip()
            if value == "":
                if spec.required:
                    errors.append(RowError(index, spec.name, "valeur requise manquante"))
                    row_ok = False
                else:
                    record[spec.name] = None
                continue
            if spec.coerce is None:
                record[spec.name] = value
                continue
            coerced, success = _try_coerce(spec.coerce, value)
            if success:
                record[spec.name] = coerced
            else:
                errors.append(RowError(index, spec.name, f"valeur invalide : {value!r}"))
                row_ok = False
        if row_ok:
            validated.append((index, record))

    # Validation « tout ou rien » par défaut : aucune insertion si erreurs.
    if errors and not partial:
        return ImportReport(imported=0, errors=errors)

    imported = 0
    for index, record in validated:
        try:
            insert(record)
            imported += 1
        except Exception as exc:  # noqa: BLE001 — toute erreur d'insertion est rapportée
            errors.append(RowError(index, None, f"insertion échouée : {exc}"))
    return ImportReport(imported=imported, errors=errors)


def coerce_int(value: str) -> int:
    """Convertit en entier ; lève `ValueError` si invalide."""
    return int(value)


def coerce_float(value: str) -> float:
    """Convertit en flottant ; lève `ValueError` si invalide."""
    return float(value)


_TRUE = frozenset({"1", "true", "vrai", "oui", "yes", "on"})
_FALSE = frozenset({"0", "false", "faux", "non", "no", "off"})


def coerce_bool(value: str) -> bool:
    """Convertit en booléen (accepte 1/0, true/false, oui/non...) ; lève `ValueError`."""
    lowered = value.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    raise ValueError(f"booléen invalide : {value!r}")
