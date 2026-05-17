import json
import shutil
from pathlib import Path

from core.uploads.storage import normalize_media_path
from forge_cli.entities.canonical_model_normalizer import normalize_canonical_entity_for_model_build
from forge_cli.entities.make_entity import build_entity_base, build_entity_sql
from forge_cli.entities.model import build_model
from forge_cli.entities.validation import validate_entity_definition


MEDIA_JSON = Path("mvc/entities/media/media.json")


def _media_definition() -> dict:
    return json.loads(MEDIA_JSON.read_text(encoding="utf-8"))


def _normalized_definition() -> dict:
    """Traduit media.json canonique en dict legacy validé pour les générateurs."""
    raw = _media_definition()
    legacy = normalize_canonical_entity_for_model_build(raw)
    return validate_entity_definition(legacy, source=str(MEDIA_JSON))


def test_media_entity_json_is_valid():
    definition = _normalized_definition()

    assert definition["entity"] == "Media"
    assert definition["table"] == "media"
    assert [field["name"] for field in definition["fields"]] == [
        "id",
        "entity_name",
        "entity_id",
        "path",
        "original_name",
        "mime_type",
        "size",
        "role",
        "position",
        "alt_text",
        "created_at",
    ]


def test_media_path_field_is_for_normalized_relative_upload_path():
    definition = _normalized_definition()
    path_field = next(field for field in definition["fields"] if field["name"] == "path")

    assert path_field["sql_type"] == "VARCHAR(500)"
    assert normalize_media_path("storage/uploads/images/photo.jpg") == "images/photo.jpg"


def test_media_entity_sql_matches_generated_projection():
    definition = _normalized_definition()
    expected = build_entity_sql(definition)
    actual = Path("mvc/entities/media/media.sql").read_text(encoding="utf-8")

    assert actual == expected
    assert "CREATE TABLE IF NOT EXISTS media" in actual
    assert "EntityName VARCHAR(100) NOT NULL" in actual
    assert "EntityId INT NOT NULL" in actual
    assert "Path VARCHAR(500) NOT NULL" in actual
    assert "OriginalName VARCHAR(255) NOT NULL" in actual
    assert "MimeType VARCHAR(120) NOT NULL" in actual
    assert "Size INT NOT NULL" in actual
    assert "Role VARCHAR(50) NOT NULL DEFAULT 'default'" in actual
    assert "Position INT NOT NULL DEFAULT 0" in actual
    assert "AltText VARCHAR(255) NULL" in actual
    assert "CreatedAt DATETIME NOT NULL" in actual
    assert "PRIMARY KEY (Id)" in actual


def test_media_entity_base_matches_generated_projection():
    definition = _normalized_definition()
    expected = build_entity_base(definition)
    actual = Path("mvc/entities/media/media_base.py").read_text(encoding="utf-8")

    assert actual == expected
    assert "class MediaBase" in actual
    assert "@min_value(0)" in actual
    assert "datetime.fromisoformat" in actual


def test_media_entity_build_model_writes_standard_files(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    shutil.copytree(Path("mvc/entities"), entities_root)

    result = build_model(entities_root)

    assert entities_root / "media" / "media.sql" in result.written
    assert entities_root / "media" / "media_base.py" in result.written
    assert entities_root / "relations.sql" in result.written
    assert (entities_root / "media" / "media.py").exists()
    assert (entities_root / "media" / "__init__.py").exists()
