# Forge Import

`forge-mvc-import` est l'opt-in d'import CSV de Forge.

Il lit un fichier CSV, valide chaque ligne par champ, produit un rapport
d'erreurs lisible, puis insère les lignes valides via une fonction fournie par
l'application.
L'export CSV est déjà généré par le CRUD du cœur ; ce paquet comble l'autre
sens, l'import.

## Le style Forge

Le moteur est générique et explicite.
L'application décrit ses colonnes par des `FieldSpec` et fournit la fonction
d'insertion : le SQL reste donc dans le modèle de l'application, ce paquet
n'apporte que la validation et le rapport.
Le cœur de Forge et les entités ne sont pas touchés (principe 8).

## Mise en route

```bash
pip install --pre forge-mvc-import
```

## Premier usage

```python
from forge_mvc_import import parse_csv, import_rows, FieldSpec, coerce_int
from mvc.models.eleve_model import add_eleve

rows = parse_csv(open("eleves.csv", encoding="utf-8").read())
specs = [FieldSpec("nom"), FieldSpec("classe"), FieldSpec("age", required=False, coerce=coerce_int)]

report = import_rows(rows, specs, add_eleve)
print(f"{report.imported} ligne(s) importée(s)")
for err in report.errors:
    print(f"  ligne {err.row}, champ {err.field} : {err.message}")
```

## Comportement

Par défaut « tout ou rien » au niveau validation : une seule ligne invalide et
rien n'est inséré, le rapport liste toutes les erreurs.
L'option `partial=True` insère les lignes valides malgré des lignes en erreur.

## Pour aller plus loin

- [La lecture CSV](references/csv.md) : `parse_csv`.
- [Le moteur d'import](references/engine.md) : `FieldSpec`, `import_rows`, `ImportReport`.
- [Les erreurs](references/errors.md) : `CsvImportError`.
