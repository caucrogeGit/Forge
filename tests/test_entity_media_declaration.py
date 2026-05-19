"""Tests pour la métadonnée top-level 'media' dans les JSON d'entité (MEDIA-012)."""
import pytest

from forge_cli.entities.make_entity import build_entity_base, build_entity_sql
from forge_cli.entities.validation import (
    EntityDefinitionError,
    normalize_entity_definition,
    validate_entity_definition,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_entity(**extra):
    d = {
        "entity": "Hebergement",
        "table": "hebergement",
        "description": "",
        "fields": [
            {
                "name": "id",
                "sql_type": "INT",
                "primary_key": True,
                "auto_increment": True,
            },
            {
                "name": "nom",
                "sql_type": "VARCHAR(120)",
                "constraints": {"not_empty": True},
            },
        ],
    }
    d.update(extra)
    return d


def _media_entry(**kwargs):
    base = {"name": "cover", "field": "image", "role": "cover"}
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Entité sans media
# ---------------------------------------------------------------------------

class TestMediaAbsent:

    def test_entite_sans_media_acceptee(self):
        validate_entity_definition(_base_entity(), source="test.json")

    def test_media_absent_pas_dans_normalise(self):
        result = normalize_entity_definition(_base_entity(), source="test.json")
        assert "media" not in result


# ---------------------------------------------------------------------------
# Validation structure — media présent
# ---------------------------------------------------------------------------

class TestMediaStructure:

    def test_media_liste_valide_acceptee(self):
        entity = _base_entity(media=[_media_entry()])
        validate_entity_definition(entity, source="test.json")

    def test_media_liste_vide_acceptee(self):
        entity = _base_entity(media=[])
        validate_entity_definition(entity, source="test.json")

    def test_media_non_liste_refuse(self):
        entity = _base_entity(media={"name": "cover"})
        with pytest.raises(EntityDefinitionError, match="doit etre une liste"):
            validate_entity_definition(entity, source="test.json")

    def test_media_chaine_refuse(self):
        entity = _base_entity(media="cover")
        with pytest.raises(EntityDefinitionError, match="doit etre une liste"):
            validate_entity_definition(entity, source="test.json")

    def test_entree_non_objet_refusee(self):
        entity = _base_entity(media=["cover"])
        with pytest.raises(EntityDefinitionError, match="doit etre un objet"):
            validate_entity_definition(entity, source="test.json")

    def test_cle_inconnue_refusee(self):
        entity = _base_entity(media=[_media_entry(extra_key="valeur")])
        with pytest.raises(EntityDefinitionError, match="cle media non supportee"):
            validate_entity_definition(entity, source="test.json")


# ---------------------------------------------------------------------------
# Validation — clés obligatoires
# ---------------------------------------------------------------------------

class TestMediaClesObligatoires:

    def test_name_absent_refuse(self):
        entity = _base_entity(media=[{"field": "image", "role": "cover"}])
        with pytest.raises(EntityDefinitionError, match="cle obligatoire manquante"):
            validate_entity_definition(entity, source="test.json")

    def test_name_vide_refuse(self):
        entity = _base_entity(media=[_media_entry(name="")])
        with pytest.raises(EntityDefinitionError, match="chaine non vide"):
            validate_entity_definition(entity, source="test.json")

    def test_name_non_chaine_refuse(self):
        entity = _base_entity(media=[_media_entry(name=42)])
        with pytest.raises(EntityDefinitionError, match="chaine non vide"):
            validate_entity_definition(entity, source="test.json")

    def test_field_absent_refuse(self):
        entity = _base_entity(media=[{"name": "cover", "role": "cover"}])
        with pytest.raises(EntityDefinitionError, match="cle obligatoire manquante"):
            validate_entity_definition(entity, source="test.json")

    def test_field_inconnu_refuse(self):
        entity = _base_entity(media=[_media_entry(field="video")])
        with pytest.raises(EntityDefinitionError, match="valeur non reconnue"):
            validate_entity_definition(entity, source="test.json")

    def test_role_absent_refuse(self):
        entity = _base_entity(media=[{"name": "cover", "field": "image"}])
        with pytest.raises(EntityDefinitionError, match="cle obligatoire manquante"):
            validate_entity_definition(entity, source="test.json")

    def test_role_vide_refuse(self):
        entity = _base_entity(media=[_media_entry(role="")])
        with pytest.raises(EntityDefinitionError, match="chaine non vide"):
            validate_entity_definition(entity, source="test.json")


# ---------------------------------------------------------------------------
# Validation — valeurs field
# ---------------------------------------------------------------------------

class TestMediaFieldValeurs:

    def test_field_image_accepte(self):
        entity = _base_entity(media=[_media_entry(field="image")])
        validate_entity_definition(entity, source="test.json")

    def test_field_file_accepte(self):
        entity = _base_entity(media=[_media_entry(field="file", role="brochure")])
        validate_entity_definition(entity, source="test.json")


# ---------------------------------------------------------------------------
# Validation — booléens
# ---------------------------------------------------------------------------

class TestMediaBooleans:

    def test_variants_true_image_accepte(self):
        entity = _base_entity(media=[_media_entry(variants=True)])
        validate_entity_definition(entity, source="test.json")

    def test_variants_true_file_refuse(self):
        entity = _base_entity(media=[_media_entry(field="file", role="doc", variants=True)])
        with pytest.raises(EntityDefinitionError, match="variants=true n'est autorise"):
            validate_entity_definition(entity, source="test.json")

    def test_variants_non_booleen_refuse(self):
        entity = _base_entity(media=[_media_entry(variants=1)])
        with pytest.raises(EntityDefinitionError, match="doit etre un booleen"):
            validate_entity_definition(entity, source="test.json")

    def test_multiple_non_booleen_refuse(self):
        entity = _base_entity(media=[_media_entry(multiple="true")])
        with pytest.raises(EntityDefinitionError, match="doit etre un booleen"):
            validate_entity_definition(entity, source="test.json")

    def test_required_non_booleen_refuse(self):
        entity = _base_entity(media=[_media_entry(required=1)])
        with pytest.raises(EntityDefinitionError, match="doit etre un booleen"):
            validate_entity_definition(entity, source="test.json")

    def test_variants_false_file_accepte(self):
        entity = _base_entity(media=[_media_entry(field="file", role="doc", variants=False)])
        validate_entity_definition(entity, source="test.json")


# ---------------------------------------------------------------------------
# Validation — doublons
# ---------------------------------------------------------------------------

class TestMediaDoublons:

    def test_doublon_name_refuse(self):
        entity = _base_entity(media=[
            _media_entry(name="cover", role="cover"),
            _media_entry(name="cover", field="file", role="brochure"),
        ])
        with pytest.raises(EntityDefinitionError, match="doit etre unique"):
            validate_entity_definition(entity, source="test.json")

    def test_doublon_role_refuse(self):
        entity = _base_entity(media=[
            _media_entry(name="cover1", role="cover"),
            _media_entry(name="cover2", role="cover"),
        ])
        with pytest.raises(EntityDefinitionError, match="doit etre unique"):
            validate_entity_definition(entity, source="test.json")

    def test_deux_medias_distincts_acceptes(self):
        entity = _base_entity(media=[
            _media_entry(name="cover", role="cover", field="image", variants=True),
            {"name": "brochure", "field": "file", "role": "brochure"},
        ])
        validate_entity_definition(entity, source="test.json")


# ---------------------------------------------------------------------------
# Normalisation — defaults
# ---------------------------------------------------------------------------

class TestMediaNormalisation:

    def test_defaults_normalises(self):
        entity = _base_entity(media=[{"name": "cover", "field": "image", "role": "cover"}])
        result = normalize_entity_definition(entity, source="test.json")
        m = result["media"][0]
        assert m["variants"] is False
        assert m["multiple"] is False
        assert m["required"] is False

    def test_label_present_dans_normalise(self):
        entity = _base_entity(media=[_media_entry(label="Image principale")])
        result = normalize_entity_definition(entity, source="test.json")
        assert result["media"][0]["label"] == "Image principale"

    def test_label_absent_pas_dans_normalise(self):
        entity = _base_entity(media=[_media_entry()])
        result = normalize_entity_definition(entity, source="test.json")
        assert "label" not in result["media"][0]

    def test_media_liste_vide_normalisee(self):
        entity = _base_entity(media=[])
        result = normalize_entity_definition(entity, source="test.json")
        assert result["media"] == []

    def test_media_absent_pas_dans_normalise(self):
        result = normalize_entity_definition(_base_entity(), source="test.json")
        assert "media" not in result

    def test_deux_entrees_normalisees(self):
        entity = _base_entity(media=[
            {"name": "cover", "field": "image", "role": "cover", "variants": True},
            {"name": "brochure", "field": "file", "role": "brochure", "label": "PDF"},
        ])
        result = normalize_entity_definition(entity, source="test.json")
        assert len(result["media"]) == 2
        assert result["media"][0]["variants"] is True
        assert result["media"][1]["label"] == "PDF"


# ---------------------------------------------------------------------------
# SQL et _base.py — media n'y apparaît pas
# ---------------------------------------------------------------------------

class TestMediaIgnoreParSQL:

    def _entity_with_media(self):
        return _base_entity(media=[
            {"name": "cover", "field": "image", "role": "cover", "variants": True},
            {"name": "brochure", "field": "file", "role": "brochure"},
        ])

    def test_sql_ne_contient_pas_media(self):
        sql = build_entity_sql(self._entity_with_media())
        assert "cover" not in sql
        assert "brochure" not in sql
        assert "media" not in sql.lower()
        assert "variant" not in sql.lower()

    def test_sql_contient_colonnes_metier(self):
        sql = build_entity_sql(self._entity_with_media())
        assert "Id" in sql
        assert "Nom" in sql

    def test_base_ne_contient_pas_media(self):
        base = build_entity_base(self._entity_with_media())
        assert "cover" not in base
        assert "brochure" not in base
        assert "variants" not in base

    def test_base_contient_champs_metier(self):
        base = build_entity_base(self._entity_with_media())
        assert "self.nom" in base
        assert "self.id" in base


# ---------------------------------------------------------------------------
# Non-régression form.field
# ---------------------------------------------------------------------------

class TestNonRegressionFormField:

    def test_form_field_email_toujours_valide(self):
        entity = {
            "entity": "Contact", "table": "contact", "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True},
                {"name": "email", "sql_type": "VARCHAR(254)", "form": {"field": "email"}},
            ],
        }
        validate_entity_definition(entity, source="test.json")

    def test_form_field_image_toujours_refuse(self):
        entity = {
            "entity": "Contact", "table": "contact", "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True},
                {"name": "photo", "sql_type": "VARCHAR(255)", "form": {"field": "image"}},
            ],
        }
        with pytest.raises(EntityDefinitionError, match="upload/media"):
            validate_entity_definition(entity, source="test.json")

    def test_entite_avec_media_et_form_field_simultanes(self):
        entity = {
            "entity": "Article", "table": "article", "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True},
                {"name": "titre", "sql_type": "VARCHAR(200)", "form": {"field": "string"}},
            ],
            "media": [{"name": "cover", "field": "image", "role": "cover"}],
        }
        validate_entity_definition(entity, source="test.json")
