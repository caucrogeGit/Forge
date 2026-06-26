# pyright: strict
"""forge-mvc-import — import CSV opt-in (IMPORT-OPTIN-SCAFFOLD-001).

Brique générique : lire un CSV, valider chaque ligne par champ, produire un
rapport d'erreurs lisible, puis insérer les lignes valides via une fonction
fournie par l'application. Le cœur de Forge et les entités restent intouchés :
le SQL d'insertion vit dans le modèle de l'application, ce paquet n'apporte que
le moteur de validation et de rapport (l'export CSV, lui, est déjà généré par le
CRUD du cœur).

La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
"""
from forge_mvc_import.csv_reader import parse_csv
from forge_mvc_import.engine import (
    FieldSpec,
    ImportReport,
    RowError,
    coerce_bool,
    coerce_float,
    coerce_int,
    import_rows,
)
from forge_mvc_import.errors import CsvImportError

__version__ = "1.0.0b17"

__all__ = [
    "CsvImportError",
    "FieldSpec",
    "RowError",
    "ImportReport",
    "parse_csv",
    "import_rows",
    "coerce_int",
    "coerce_float",
    "coerce_bool",
]
