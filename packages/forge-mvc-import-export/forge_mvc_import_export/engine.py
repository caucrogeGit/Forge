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

from forge_mvc_import_export.errors import CsvImportError


@dataclass(frozen=True)
class FieldSpec:
    """Spécification d'une colonne à importer.

    `coerce` convertit la chaîne CSV en valeur typée ; elle lève `ValueError`
    (ou `TypeError`) si la valeur est invalide. `None` conserve la chaîne.

    `source` déclare le ou les **en-têtes CSV** acceptés pour ce champ
    (`IMPEXP-COLUMN-MAPPING-001`). Sans lui, l'en-tête doit s'appeler comme le
    champ, ce qui obligeait à renommer à la main les colonnes d'un export
    tableur avant tout import : « Adresse e-mail » ne pouvait pas alimenter
    `email`.

    Plusieurs en-têtes peuvent être acceptés, essayés dans l'ordre. La
    correspondance reste **déclarée** : Forge ne rapproche jamais deux noms
    parce qu'ils se ressemblent, ce que le principe 3 refuse. Rapprocher
    « Prix HT » de « prix_ttc » parce que les deux contiennent « prix » ferait
    importer la mauvaise colonne sans que rien ne le signale.
    """

    name: str
    required: bool = True
    coerce: "Callable[[str], object] | None" = None
    source: "str | Sequence[str] | None" = None

    @property
    def accepted_headers(self) -> "tuple[str, ...]":
        """En-têtes acceptés, dans l'ordre d'essai. Le nom du champ à défaut."""
        if self.source is None:
            return (self.name,)
        if isinstance(self.source, str):
            return (self.source,)
        return tuple(self.source)


@dataclass(frozen=True)
class HeaderMapping:
    """Ce que les en-têtes d'un fichier ont donné, face aux `FieldSpec`.

    `missing_required` est la raison d'être de cette étape : sans elle, une
    colonne absente n'était pas détectée, et chaque ligne produisait « valeur
    requise manquante ». Un fichier de dix mille lignes rendait dix mille
    erreurs pour un seul en-tête mal orthographié.
    """

    resolved: "dict[str, str]"
    missing_required: "tuple[str, ...]"
    missing_optional: "tuple[str, ...]"
    unused_headers: "tuple[str, ...]"

    @property
    def ok(self) -> bool:
        return not self.missing_required


def resolve_headers(
    headers: Sequence[str], specs: Sequence[FieldSpec]
) -> HeaderMapping:
    """Rapproche les en-têtes d'un fichier et les colonnes attendues.

    Les en-têtes sont comparés **tels quels**, aux espaces de bordure près. Ni
    la casse ni les accents ne sont normalisés : « Email » et « email » sont
    deux en-têtes différents tant qu'un `source` ne dit pas qu'ils désignent le
    même champ.

    Les en-têtes du fichier que personne ne réclame sont rendus dans
    `unused_headers`. Ils ne sont pas une erreur, un export tableur portant
    souvent des colonnes dont l'import n'a que faire, mais les nommer aide à
    repérer une correspondance oubliée.
    """
    disponibles = {h.strip(): h for h in headers}
    resolus: dict[str, str] = {}
    manquants_requis: list[str] = []
    manquants_optionnels: list[str] = []

    for spec in specs:
        trouve = next(
            (disponibles[c] for c in spec.accepted_headers if c in disponibles), None
        )
        if trouve is not None:
            resolus[spec.name] = trouve
        elif spec.required:
            manquants_requis.append(spec.name)
        else:
            manquants_optionnels.append(spec.name)

    reclames = set(resolus.values())
    return HeaderMapping(
        resolved=resolus,
        missing_required=tuple(manquants_requis),
        missing_optional=tuple(manquants_optionnels),
        unused_headers=tuple(h for h in disponibles.values() if h not in reclames),
    )


@dataclass(frozen=True)
class RowError:
    """Une erreur localisée. `row` est l'index 1-based des lignes de données."""

    row: int
    field: str | None
    message: str


@dataclass(frozen=True)
class ImportReport:
    """Résultat d'un import : nombre de lignes insérées et erreurs collectées.

    `header_errors` porte ce qui a été refusé **avant** d'examiner la moindre
    ligne, c'est à dire les colonnes absentes du fichier. Les distinguer
    importe : une colonne manquante se corrige dans l'en-tête, une valeur
    invalide se corrige dans la ligne.
    """

    imported: int
    errors: list[RowError]
    header_errors: "tuple[str, ...]" = ()

    @property
    def ok(self) -> bool:
        return not self.errors and not self.header_errors

    @property
    def rejected_before_reading(self) -> bool:
        """Vrai si le fichier n'a même pas été parcouru.

        L'utilisateur doit alors corriger son en-tête, pas ses données.
        """
        return bool(self.header_errors)


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

    # IMPEXP-COLUMN-MAPPING-001 : les en-têtes sont rapprochés une fois, avant
    # d'examiner les lignes. Sans cette étape, une colonne absente n'était pas
    # détectée et chaque ligne produisait « valeur requise manquante » : un
    # fichier de dix mille lignes rendait dix mille erreurs pour un seul
    # en-tête mal orthographié, et la vraie cause restait introuvable.
    entetes = list(rows[0].keys()) if rows else [s.name for s in specs]
    mapping = resolve_headers(entetes, specs)
    if not mapping.ok:
        manquantes = ", ".join(repr(nom) for nom in mapping.missing_required)
        detail = (
            f"colonne(s) requise(s) absente(s) du fichier : {manquantes}. "
            f"En-têtes lus : {', '.join(repr(h) for h in entetes) or '<aucun>'}."
        )
        return ImportReport(
            imported=0,
            errors=[RowError(0, None, detail)],
            header_errors=mapping.missing_required,
        )

    errors: list[RowError] = []
    validated: list[tuple[int, dict[str, object]]] = []

    for index, row in enumerate(rows, start=1):
        record: dict[str, object] = {}
        row_ok = True
        for spec in specs:
            entete = mapping.resolved.get(spec.name)
            value = (row.get(entete, "") if entete is not None else "").strip()
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
