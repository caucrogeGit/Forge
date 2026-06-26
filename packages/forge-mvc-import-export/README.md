# forge-mvc-import-export

Échange CSV opt-in pour Forge : **import** (lire un CSV, valider chaque ligne par
champ, produire un rapport d'erreurs, insérer les lignes valides) et **export
programmatique** (`to_csv`, l'inverse de `parse_csv`).

Dans le style Forge : explicite, validation visible, SQL laissé à l'application.

**Frontière (principe 11)** : pour télécharger une **entité** depuis une page
web, la route d'export générée par le CRUD du cœur reste la voie officielle.
`to_csv` sert l'export **programmatique** : un script, un rapport, une
agrégation, ou des données qui ne viennent pas d'une entité CRUD.

## Installation

```bash
pip install --pre forge-mvc-import-export
```

En développement : `pip install -e ./packages/forge-mvc-import-export`.

## Utilisation

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec, coerce_int

csv_text = open("eleves.csv", encoding="utf-8").read()
rows = parse_csv(csv_text)

specs = [
    FieldSpec("nom"),                              # requis, chaîne
    FieldSpec("classe"),
    FieldSpec("age", required=False, coerce=coerce_int),
]

# `insert` reçoit une ligne validée ; le SQL reste dans le modèle de l'app.
from mvc.models.eleve_model import add_eleve
report = import_rows(rows, specs, lambda row: add_eleve(row))

print(f"{report.imported} ligne(s) importée(s)")
for err in report.errors:
    print(f"  ligne {err.row}, champ {err.field} : {err.message}")
```

## Export programmatique

```python
from forge_mvc_import_export import to_csv

rows = [{"nom": "Alice", "classe": "6A"}, {"nom": "Bob", "classe": "6B"}]
csv_text = to_csv(rows, ["nom", "classe"])
# "nom,classe\nAlice,6A\nBob,6B\n"
```

## Comportement

- Import : par défaut « tout ou rien » au niveau validation : si une ligne est
  invalide, **rien n'est inséré** et le rapport liste toutes les erreurs.
  L'option `partial=True` insère les lignes valides malgré les lignes en erreur.
- Convertisseurs fournis : `coerce_int`, `coerce_float`, `coerce_bool`.
- Le cœur de Forge et les entités ne sont pas touchés : la dépendance va de
  l'opt-in vers le cœur.

## Périmètre

V1 : import CSV (validation, rapport d'erreurs) et export programmatique
(`to_csv`).
Hors périmètre V1 : Excel, JSON, mapping de colonnes avancé, modèles d'import.

Documentation complète : <https://forgemvc.com/docs/forge/>.
