# forge-mvc-import

Import CSV opt-in pour Forge : lire un fichier CSV, valider chaque ligne par
champ, produire un rapport d'erreurs lisible, puis insérer les lignes valides.

L'export CSV est déjà généré par le CRUD du cœur ; ce paquet comble l'autre
sens, l'import, dans le style Forge : explicite, validation visible, SQL laissé
à l'application.

## Installation

```bash
pip install --pre forge-mvc-import
```

En développement : `pip install -e ./packages/forge-mvc-import`.

## Utilisation

```python
from forge_mvc_import import parse_csv, import_rows, FieldSpec, coerce_int

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

## Comportement

- Par défaut « tout ou rien » au niveau validation : si une ligne est invalide,
  **rien n'est inséré** et le rapport liste toutes les erreurs. L'option
  `partial=True` insère les lignes valides malgré les lignes en erreur.
- Convertisseurs fournis : `coerce_int`, `coerce_float`, `coerce_bool`.
- Le cœur de Forge et les entités ne sont pas touchés : la dépendance va de
  l'opt-in vers le cœur.

## Périmètre

V1 : CSV, validation par champ, rapport d'erreurs.
Hors périmètre V1 : Excel, JSON, mapping de colonnes avancé, modèles d'import.

Documentation complète : <https://forgemvc.com/docs/forge/>.
