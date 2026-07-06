# Forge Import/Export

`forge-mvc-import-export` est l'opt-in d'échange CSV de Forge.

Il fait deux choses : **importer** un CSV (lire, valider chaque ligne par champ, produire un rapport d'erreurs, insérer les lignes valides via une fonction de l'application) et **exporter** programmatiquement des lignes en CSV (`to_csv`, l'inverse de `parse_csv`).

## La frontière avec l'export du CRUD

L'export d'une **entité** dans une page web est déjà couvert par la route d'export générée par le CRUD du cœur : c'est la voie officielle, elle reste inchangée (principe 11).

`to_csv` ne la remplace pas : il sert l'export **programmatique**, pour un script, un rapport, une agrégation, ou des données qui ne viennent pas d'une entité CRUD.
Deux outils pour deux contextes, pas deux façons de faire la même chose.

## Le style Forge

Les briques sont génériques et explicites.
À l'import, l'application décrit ses colonnes par des `FieldSpec` et fournit la fonction d'insertion : le SQL reste dans le modèle de l'application, ce paquet n'apporte que la validation et le rapport.
Le cœur de Forge et les entités ne sont pas touchés (principe 8).

## Mise en route

```bash
pip install --pre forge-mvc-import-export
```

## Premier usage

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec, coerce_int
from mvc.models.eleve_model import add_eleve

rows = parse_csv(open("eleves.csv", encoding="utf-8").read())
specs = [FieldSpec("nom"), FieldSpec("classe"), FieldSpec("age", required=False, coerce=coerce_int)]

report = import_rows(rows, specs, add_eleve)
print(f"{report.imported} ligne(s) importée(s)")
for err in report.errors:
    print(f"  ligne {err.row}, champ {err.field} : {err.message}")
```

## Comportement

Par défaut « tout ou rien »
au niveau validation : une seule ligne invalide et rien n'est inséré, le rapport liste toutes les erreurs.
L'option `partial=True` insère les lignes valides malgré des lignes en erreur.

## Pour aller plus loin

- [La lecture CSV](references/csv.md) : `parse_csv`.
- [Le moteur d'import](references/engine.md) : `FieldSpec`, `import_rows`, `ImportReport`.
- [L'export programmatique](references/export.md) : `to_csv`.
- [Les erreurs](references/errors.md) : `CsvImportError`.
