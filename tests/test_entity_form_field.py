"""Tests pour la métadonnée form.field dans les JSON d'entité et make:crud."""
import pytest

from forge_cli.entities.validation import (
    EntityDefinitionError,
    validate_entity_definition,
)
from forge_cli.entities.make_crud import (
    CrudManyToOneRelation,
    _form_field_code,
    _form_imports,
    _html_input_type,
    _is_textarea,
    build_form,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_entity(extra_field=None):
    fields = [
        {
            "name": "id",
            "sql_type": "INT",
            "python_type": "int",
            "nullable": False,
            "primary_key": True,
            "auto_increment": True,
            "constraints": {},
        },
        extra_field or {
            "name": "nom",
            "sql_type": "VARCHAR(100)",
            "python_type": "str",
            "nullable": False,
            "primary_key": False,
            "auto_increment": False,
            "constraints": {},
        },
    ]
    return {
        "entity": "Contact",
        "table": "contact",
        "description": "",
        "fields": fields,
    }


def _field_with_form(name, sql_type, python_type, form_field, nullable=False, constraints=None):
    return {
        "name": name,
        "sql_type": sql_type,
        "python_type": python_type,
        "nullable": nullable,
        "primary_key": False,
        "auto_increment": False,
        "constraints": constraints or {},
        "form": {"field": form_field},
    }


def _crud_entity(form_field, python_type="str", sql_type="VARCHAR(100)", nullable=False, constraints=None):
    return {
        "entity": "Contact",
        "table": "contact",
        "description": "",
        "fields": [
            {"name": "id", "sql_type": "INT", "python_type": "int",
             "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
            _field_with_form("valeur", sql_type, python_type, form_field,
                             nullable=nullable, constraints=constraints),
        ],
    }


# ---------------------------------------------------------------------------
# Validation JSON — form absent
# ---------------------------------------------------------------------------

class TestFormAbsent:

    def test_form_absent_accepte(self):
        validate_entity_definition(_base_entity(), source="test.json")

    def test_champ_sans_form_accepte(self):
        entity = _base_entity()
        validate_entity_definition(entity, source="test.json")


# ---------------------------------------------------------------------------
# Validation JSON — form présent — structure
# ---------------------------------------------------------------------------

class TestFormStructure:

    def _entity_with_form(self, form_value):
        entity = _base_entity()
        entity["fields"][1]["form"] = form_value
        return entity

    def test_form_objet_valide_accepte(self):
        validate_entity_definition(
            self._entity_with_form({"field": "email"}), source="test.json"
        )

    def test_form_chaine_refuse(self):
        with pytest.raises(EntityDefinitionError, match="doit etre un objet"):
            validate_entity_definition(self._entity_with_form("email"), source="test.json")

    def test_form_entier_refuse(self):
        with pytest.raises(EntityDefinitionError, match="doit etre un objet"):
            validate_entity_definition(self._entity_with_form(42), source="test.json")

    def test_form_liste_refuse(self):
        with pytest.raises(EntityDefinitionError, match="doit etre un objet"):
            validate_entity_definition(self._entity_with_form(["email"]), source="test.json")

    def test_form_cle_inconnue_refuse(self):
        with pytest.raises(EntityDefinitionError, match="cle form non supportee"):
            validate_entity_definition(
                self._entity_with_form({"field": "email", "inconnu": True}),
                source="test.json",
            )

    def test_form_field_non_chaine_refuse(self):
        with pytest.raises(EntityDefinitionError, match="doit etre une chaine"):
            validate_entity_definition(
                self._entity_with_form({"field": 42}), source="test.json"
            )


# ---------------------------------------------------------------------------
# Validation JSON — form.field valeurs supportées
# ---------------------------------------------------------------------------

class TestFormFieldValeurs:

    def _entity_with_field(self, form_field_value):
        entity = _base_entity()
        entity["fields"][1]["form"] = {"field": form_field_value}
        return entity

    def test_form_field_string_accepte(self):
        validate_entity_definition(self._entity_with_field("string"), source="test.json")

    def test_form_field_email_accepte(self):
        validate_entity_definition(self._entity_with_field("email"), source="test.json")

    def test_form_field_phone_accepte(self):
        validate_entity_definition(self._entity_with_field("phone"), source="test.json")

    def test_form_field_url_accepte(self):
        validate_entity_definition(self._entity_with_field("url"), source="test.json")

    def test_form_field_textarea_accepte(self):
        validate_entity_definition(self._entity_with_field("textarea"), source="test.json")

    def test_form_field_slug_accepte(self):
        validate_entity_definition(self._entity_with_field("slug"), source="test.json")

    def test_form_field_inconnu_refuse(self):
        with pytest.raises(EntityDefinitionError, match="valeur non reconnue"):
            validate_entity_definition(
                self._entity_with_field("richtext"), source="test.json"
            )

    def test_form_field_file_refuse_avec_message_upload(self):
        with pytest.raises(EntityDefinitionError, match="upload/media"):
            validate_entity_definition(
                self._entity_with_field("file"), source="test.json"
            )

    def test_form_field_image_refuse_avec_message_upload(self):
        with pytest.raises(EntityDefinitionError, match="upload/media"):
            validate_entity_definition(
                self._entity_with_field("image"), source="test.json"
            )

    def test_form_field_date_avec_DATE_accepte(self):
        entity = _base_entity(
            _field_with_form("debut", "DATE", "date", "date")
        )
        validate_entity_definition(entity, source="test.json")

    def test_form_field_datetime_avec_DATETIME_accepte(self):
        entity = _base_entity(
            _field_with_form("cree_le", "DATETIME", "datetime", "datetime")
        )
        validate_entity_definition(entity, source="test.json")

    def test_form_field_datetime_avec_TIMESTAMP_accepte(self):
        entity = _base_entity(
            _field_with_form("mis_a_jour", "TIMESTAMP", "datetime", "datetime")
        )
        validate_entity_definition(entity, source="test.json")

    @pytest.mark.parametrize("form_field", ["email", "phone", "url", "slug", "textarea"])
    def test_form_field_textuel_avec_INT_refuse(self, form_field):
        entity = _base_entity(
            _field_with_form("valeur", "INT", "str", form_field)
        )
        with pytest.raises(EntityDefinitionError, match="sql_type textuel"):
            validate_entity_definition(entity, source="test.json")

    def test_form_field_date_avec_VARCHAR_refuse(self):
        entity = _base_entity(
            _field_with_form("debut", "VARCHAR(10)", "date", "date")
        )
        with pytest.raises(EntityDefinitionError, match="requiert sql_type='DATE'"):
            validate_entity_definition(entity, source="test.json")

    def test_form_field_datetime_avec_DATE_refuse(self):
        entity = _base_entity(
            _field_with_form("cree_le", "DATE", "datetime", "datetime")
        )
        with pytest.raises(EntityDefinitionError, match="DATETIME"):
            validate_entity_definition(entity, source="test.json")

    def test_form_field_datetime_avec_VARCHAR_refuse(self):
        entity = _base_entity(
            _field_with_form("cree_le", "VARCHAR(30)", "datetime", "datetime")
        )
        with pytest.raises(EntityDefinitionError, match="DATETIME"):
            validate_entity_definition(entity, source="test.json")


# ---------------------------------------------------------------------------
# Normalisation — form passé dans le champ normalisé
# ---------------------------------------------------------------------------

class TestNormalisation:

    def test_form_present_dans_champ_normalise(self):
        from forge_cli.entities.validation import normalize_entity_definition
        entity = _base_entity()
        entity["fields"][1]["form"] = {"field": "email"}
        result = normalize_entity_definition(entity, source="test.json")
        assert result["fields"][1].get("form") == {"field": "email"}

    def test_form_absent_pas_dans_champ_normalise(self):
        from forge_cli.entities.validation import normalize_entity_definition
        result = normalize_entity_definition(_base_entity(), source="test.json")
        assert "form" not in result["fields"][1]


# ---------------------------------------------------------------------------
# make:crud — génération des champs de formulaire
# ---------------------------------------------------------------------------

class TestMakeCrudFormField:

    def test_form_field_email_genere_emailfield(self):
        code, _ = build_form(_crud_entity("email"))
        assert "EmailField" in code

    def test_form_field_phone_genere_phonefield(self):
        code, _ = build_form(_crud_entity("phone"))
        assert "PhoneField" in code

    def test_form_field_url_genere_urlfield(self):
        code, _ = build_form(_crud_entity("url"))
        assert "UrlField" in code

    def test_form_field_textarea_genere_textareafield(self):
        code, _ = build_form(_crud_entity("textarea"))
        assert "TextAreaField" in code

    def test_form_field_slug_genere_slugfield(self):
        code, _ = build_form(_crud_entity("slug"))
        assert "SlugField" in code

    def test_form_field_date_genere_datefield(self):
        code, _ = build_form(_crud_entity("date", python_type="date", sql_type="DATE"))
        assert "DateField" in code

    def test_form_field_datetime_genere_datetimefield(self):
        code, _ = build_form(_crud_entity("datetime", python_type="datetime", sql_type="DATETIME"))
        assert "DateTimeField" in code

    def test_form_field_string_genere_stringfield(self):
        code, _ = build_form(_crud_entity("string"))
        assert "StringField" in code

    def test_form_field_email_pas_de_warn(self):
        _, warnings = build_form(_crud_entity("email"))
        assert warnings == []

    def test_form_field_phone_pas_de_warn(self):
        _, warnings = build_form(_crud_entity("phone"))
        assert warnings == []

    def test_sans_form_field_comportement_actuel_preserve(self):
        entity = {
            "entity": "Contact", "table": "contact", "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                {"name": "nom", "sql_type": "VARCHAR(100)", "python_type": "str",
                 "nullable": False, "primary_key": False, "auto_increment": False, "constraints": {}},
            ],
        }
        code, warnings = build_form(entity)
        assert "StringField" in code
        assert warnings == []

    def test_max_length_transmis_pour_email(self):
        code, _ = build_form(_crud_entity("email", constraints={"max_length": 100}))
        assert "max_length=100" in code

    def test_max_length_transmis_pour_slug(self):
        code, _ = build_form(_crud_entity("slug", constraints={"max_length": 80}))
        assert "max_length=80" in code

    def test_max_length_transmis_pour_textarea(self):
        code, _ = build_form(_crud_entity("textarea", constraints={"max_length": 500}))
        assert "max_length=500" in code

    def test_phone_sans_constraints_dans_code(self):
        code, _ = build_form(_crud_entity("phone"))
        assert "PhoneField" in code

    def test_max_length_transmis_pour_phone(self):
        code, _ = build_form(_crud_entity("phone", constraints={"max_length": 20}))
        assert "max_length=20" in code

    def test_form_field_inconnu_ne_fallback_pas_silencieusement(self):
        field = _field_with_form("valeur", "VARCHAR(100)", "str", "richtext")
        with pytest.raises(KeyError):
            _form_field_code(field)

    def test_relation_field_prioritaire_sur_form_field(self):
        relation = CrudManyToOneRelation(
            field_name="ville_id",
            field_column="VilleId",
            target_entity="Ville",
            target_table="ville",
            target_pk_column="Id",
            target_label_column="Nom",
            choices_function="get_ville_choices",
            choices_key="ville_id_choices",
        )
        f = {
            "name": "ville_id", "sql_type": "INT", "python_type": "int",
            "nullable": False, "primary_key": False, "auto_increment": False,
            "constraints": {}, "form": {"field": "string"},
        }
        code, _ = _form_field_code(f, {"ville_id": relation})
        assert "RelationField" in code
        assert "StringField" not in code


# ---------------------------------------------------------------------------
# _form_imports() avec form.field
# ---------------------------------------------------------------------------

class TestFormImports:

    def test_email_dans_imports(self):
        fields = [_field_with_form("courriel", "VARCHAR(254)", "str", "email")]
        assert "EmailField" in _form_imports(fields)

    def test_phone_dans_imports(self):
        fields = [_field_with_form("tel", "VARCHAR(20)", "str", "phone")]
        assert "PhoneField" in _form_imports(fields)

    def test_url_dans_imports(self):
        fields = [_field_with_form("site", "VARCHAR(2048)", "str", "url")]
        assert "UrlField" in _form_imports(fields)

    def test_textarea_dans_imports(self):
        fields = [_field_with_form("bio", "VARCHAR(500)", "str", "textarea")]
        assert "TextAreaField" in _form_imports(fields)

    def test_slug_dans_imports(self):
        fields = [_field_with_form("slug", "VARCHAR(120)", "str", "slug")]
        assert "SlugField" in _form_imports(fields)

    def test_import_inutile_absent_pour_email(self):
        fields = [_field_with_form("courriel", "VARCHAR(254)", "str", "email")]
        imports = _form_imports(fields)
        assert "StringField" not in imports
        assert "IntegerField" not in imports

    def test_import_inutile_absent_pour_phone(self):
        fields = [_field_with_form("tel", "VARCHAR(20)", "str", "phone")]
        imports = _form_imports(fields)
        assert "StringField" not in imports

    def test_form_field_inconnu_ne_fallback_pas_dans_imports(self):
        fields = [_field_with_form("valeur", "VARCHAR(100)", "str", "richtext")]
        with pytest.raises(KeyError):
            _form_imports(fields)


# ---------------------------------------------------------------------------
# _is_textarea() avec form.field
# ---------------------------------------------------------------------------

class TestIsTextarea:

    def test_form_field_textarea_sur_varchar_detecte(self):
        f = {"name": "bio", "sql_type": "VARCHAR(500)", "python_type": "str",
             "form": {"field": "textarea"}}
        assert _is_textarea(f) is True

    def test_sql_text_detecte_sans_form_field(self):
        f = {"name": "bio", "sql_type": "TEXT", "python_type": "str"}
        assert _is_textarea(f) is True

    def test_varchar_sans_form_field_non_textarea(self):
        f = {"name": "nom", "sql_type": "VARCHAR(100)", "python_type": "str"}
        assert _is_textarea(f) is False

    def test_form_field_email_non_textarea(self):
        f = {"name": "email", "sql_type": "VARCHAR(254)", "python_type": "str",
             "form": {"field": "email"}}
        assert _is_textarea(f) is False


# ---------------------------------------------------------------------------
# _html_input_type() avec form.field
# ---------------------------------------------------------------------------

class TestHtmlInputType:

    def test_form_field_email_produit_type_email(self):
        f = {"name": "courriel", "sql_type": "VARCHAR(254)", "python_type": "str",
             "form": {"field": "email"}}
        assert _html_input_type(f) == "email"

    def test_form_field_phone_produit_type_tel(self):
        f = {"name": "contact", "sql_type": "VARCHAR(20)", "python_type": "str",
             "form": {"field": "phone"}}
        assert _html_input_type(f) == "tel"

    def test_form_field_url_produit_type_url(self):
        f = {"name": "lien", "sql_type": "VARCHAR(2048)", "python_type": "str",
             "form": {"field": "url"}}
        assert _html_input_type(f) == "url"

    def test_form_field_date_produit_type_date(self):
        f = {"name": "debut", "sql_type": "VARCHAR(10)", "python_type": "str",
             "form": {"field": "date"}}
        assert _html_input_type(f) == "date"

    def test_form_field_datetime_produit_type_datetime_local(self):
        f = {"name": "cree_le", "sql_type": "VARCHAR(20)", "python_type": "str",
             "form": {"field": "datetime"}}
        assert _html_input_type(f) == "datetime-local"

    def test_sans_form_field_heuristique_email_preservee(self):
        f = {"name": "email", "sql_type": "VARCHAR(254)", "python_type": "str"}
        assert _html_input_type(f) == "email"

    def test_sans_form_field_heuristique_tel_preservee(self):
        f = {"name": "telephone", "sql_type": "VARCHAR(20)", "python_type": "str"}
        assert _html_input_type(f) == "tel"
