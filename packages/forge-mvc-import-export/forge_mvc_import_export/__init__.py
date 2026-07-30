# pyright: strict
"""forge-mvc-import-export — échange CSV opt-in (IMPORT-OPTIN-SCAFFOLD-001).

Deux briques génériques et explicites :

- **import** : lire un CSV (`parse_csv`), valider chaque ligne par champ et
  produire un rapport d'erreurs (`import_rows`, `FieldSpec`, `ImportReport`),
  puis insérer les lignes valides via une fonction fournie par l'application ;
- **export programmatique** : rendre des lignes en CSV (`to_csv`), inverse de
  `parse_csv`, pour un script, un rapport ou des données hors entité CRUD.

Frontière (principe 11) : pour télécharger une entité depuis une page web, la
route d'export générée par le CRUD du cœur reste la voie officielle ; `to_csv`
sert l'export programmatique. Le SQL d'insertion vit dans le modèle de
l'application. La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
"""
from forge_mvc_import_export.csv_reader import parse_csv
from forge_mvc_import_export.csv_writer import to_csv
from forge_mvc_import_export.engine import (
    FieldSpec,
    ImportReport,
    RowError,
    coerce_bool,
    coerce_float,
    coerce_int,
    import_rows,
)
from forge_mvc_import_export.errors import CsvImportError

__version__ = "1.0.0rc3"

__all__ = [
    "CsvImportError",
    "FieldSpec",
    "RowError",
    "ImportReport",
    "parse_csv",
    "to_csv",
    "import_rows",
    "coerce_int",
    "coerce_float",
    "coerce_bool",
]
