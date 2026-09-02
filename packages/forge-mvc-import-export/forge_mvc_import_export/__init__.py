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
from forge_mvc_import_export.jsonl import (
    JSONL_MIME_TYPE,
    JsonlError,
    parse_jsonl,
    to_jsonl,
)
from forge_mvc_import_export.report import (
    REPORT_COLUMNS,
    errors_to_csv,
    errors_to_rows,
    report_filename,
)
from forge_mvc_import_export.engine import (
    FieldSpec,
    HeaderMapping,
    resolve_headers,
    ImportReport,
    RowError,
    coerce_bool,
    coerce_float,
    coerce_int,
    import_rows,
)
from forge_mvc_import_export.errors import CsvImportError
from forge_mvc_import_export.queueing import (
    IMPORT_JOB_TASK,
    ImporterNotFound,
    ImportSourceError,
    RegisteredImporter,
    clear_importers,
    import_payload,
    make_import_job_handler,
    register_importer,
    registered_importers,
)

__version__ = "1.0.0rc7"

__all__ = [
    # Import différé par une file (IMPEXP-ASYNC-JOBS-001)
    "IMPORT_JOB_TASK",
    "register_importer",
    "clear_importers",
    "registered_importers",
    "import_payload",
    "make_import_job_handler",
    "RegisteredImporter",
    "ImporterNotFound",
    "ImportSourceError",
    "CsvImportError",
    "FieldSpec",
    # Correspondance de colonnes déclarée (IMPEXP-COLUMN-MAPPING-001)
    "HeaderMapping",
    "resolve_headers",
    # Rapport d'erreurs téléchargeable (IMPEXP-ERROR-REPORT-001)
    "errors_to_csv",
    "errors_to_rows",
    "report_filename",
    "REPORT_COLUMNS",
    # Format JSONL (IMPEXP-JSONL-001)
    "to_jsonl",
    "parse_jsonl",
    "JsonlError",
    "JSONL_MIME_TYPE",
    "RowError",
    "ImportReport",
    "parse_csv",
    "to_csv",
    "import_rows",
    "coerce_int",
    "coerce_float",
    "coerce_bool",
]
