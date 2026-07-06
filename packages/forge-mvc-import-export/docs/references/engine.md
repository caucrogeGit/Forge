# Le moteur d'import

Ce document décrit la validation des lignes et leur insertion.

Le fichier de code correspondant est `forge_mvc_import_export/engine.py`.

## 1. Décrire les colonnes (`FieldSpec`)

```python
@dataclass(frozen=True)
class FieldSpec:
    name: str
    required: bool = True
    coerce: Callable[[str], object] | None = None
```

Un `FieldSpec` décrit une colonne : son nom (clé dans la ligne CSV), si elle est requise, et une fonction de conversion optionnelle.
`coerce` transforme la chaîne en valeur typée et lève `ValueError` (ou `TypeError`) si la valeur est invalide.
Trois convertisseurs prêts à l'emploi sont fournis : `coerce_int`, `coerce_float`, `coerce_bool`.

## 2. Importer (`import_rows`)

```python
def import_rows(rows, specs, insert, *, partial=False) -> ImportReport
```

`import_rows` valide chaque ligne selon `specs`, puis insère les lignes valides en appelant `insert(record)`.
`insert` reçoit un dictionnaire validé ; c'est là que l'application écrit en base (par exemple via la fonction `add_<entite>` de son modèle).

```python
from forge_mvc_import_export import import_rows, FieldSpec, coerce_int

specs = [FieldSpec("nom"), FieldSpec("age", coerce=coerce_int)]
report = import_rows(rows, specs, add_eleve)
```

## 3. Tout ou rien, ou partiel

Par défaut, l'import est « tout ou rien »
au niveau validation : si une ligne est invalide, **aucune** ligne n'est insérée et le rapport liste toutes les erreurs.
Avec `partial=True`, les lignes valides sont insérées malgré les lignes en erreur.

Pour une vraie atomicité au niveau base, l'application enveloppe l'appel dans une transaction (le moteur ne gère pas la transaction lui-même : le SQL reste à l'application).

## 4. Le rapport (`ImportReport`)

```python
@dataclass(frozen=True)
class ImportReport:
    imported: int
    errors: list[RowError]

@dataclass(frozen=True)
class RowError:
    row: int          # numéro de ligne de données (1-based)
    field: str | None # nom du champ, ou None pour une erreur de ligne
    message: str
```

`report.ok` vaut `True` quand il n'y a aucune erreur.

## 5. Voir aussi

- [La lecture CSV](csv.md) : produire les `rows`.
- [Les erreurs](errors.md) : `CsvImportError`.
