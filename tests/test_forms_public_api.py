import datetime


from core.forms import (
    BooleanField,
    ChoiceField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    Field,
    FileField,
    ImageField,
    IntegerField,
    PhoneField,
    RelatedIdsField,
    RelationField,
    SlugField,
    StringField,
    TextAreaField,
    UrlField,
    ValidationError,
)


# ---------------------------------------------------------------------------
# API publique — imports
# ---------------------------------------------------------------------------

class TestImportsPublics:

    def test_field_importable(self):
        assert Field is not None

    def test_string_field_importable(self):
        assert StringField is not None

    def test_integer_field_importable(self):
        assert IntegerField is not None

    def test_decimal_field_importable(self):
        assert DecimalField is not None

    def test_boolean_field_importable(self):
        assert BooleanField is not None

    def test_choice_field_importable(self):
        assert ChoiceField is not None

    def test_related_ids_field_importable(self):
        assert RelatedIdsField is not None

    def test_email_field_importable(self):
        assert EmailField is not None

    def test_phone_field_importable(self):
        assert PhoneField is not None

    def test_url_field_importable(self):
        assert UrlField is not None

    def test_date_field_importable(self):
        assert DateField is not None

    def test_datetime_field_importable(self):
        assert DateTimeField is not None

    def test_textarea_field_importable(self):
        assert TextAreaField is not None

    def test_relation_field_importable(self):
        assert RelationField is not None

    def test_slug_field_importable(self):
        assert SlugField is not None

    def test_file_field_importable(self):
        assert FileField is not None

    def test_image_field_importable(self):
        assert ImageField is not None

    def test_validation_error_importable(self):
        assert ValidationError is not None


# ---------------------------------------------------------------------------
# Héritage
# ---------------------------------------------------------------------------

class TestHeritage:

    def test_string_field_herite_field(self):
        assert issubclass(StringField, Field)

    def test_email_field_herite_string_field(self):
        assert issubclass(EmailField, StringField)

    def test_phone_field_herite_string_field(self):
        assert issubclass(PhoneField, StringField)

    def test_url_field_herite_string_field(self):
        assert issubclass(UrlField, StringField)

    def test_slug_field_herite_string_field(self):
        assert issubclass(SlugField, StringField)

    def test_textarea_field_herite_string_field(self):
        assert issubclass(TextAreaField, StringField)

    def test_relation_field_herite_choice_field(self):
        assert issubclass(RelationField, ChoiceField)

    def test_file_field_herite_field(self):
        assert issubclass(FileField, Field)

    def test_image_field_herite_file_field(self):
        assert issubclass(ImageField, FileField)

    def test_date_field_herite_field(self):
        assert issubclass(DateField, Field)

    def test_datetime_field_herite_field(self):
        assert issubclass(DateTimeField, Field)


# ---------------------------------------------------------------------------
# Valeurs retournées
# ---------------------------------------------------------------------------

class TestValeursRetournees:

    def test_string_field_retourne_str(self):
        assert isinstance(StringField().clean("hello"), str)

    def test_email_field_retourne_str(self):
        assert isinstance(EmailField().clean("a@b.com"), str)

    def test_phone_field_retourne_str(self):
        assert isinstance(PhoneField().clean("0612345678"), str)

    def test_url_field_retourne_str(self):
        assert isinstance(UrlField().clean("https://example.com"), str)

    def test_slug_field_retourne_str(self):
        assert isinstance(SlugField().clean("mon-slug"), str)

    def test_textarea_field_retourne_str(self):
        assert isinstance(TextAreaField().clean("texte long"), str)

    def test_date_field_retourne_date(self):
        result = DateField().clean("2026-05-01")
        assert isinstance(result, datetime.date)
        assert not isinstance(result, datetime.datetime)

    def test_datetime_field_retourne_datetime(self):
        result = DateTimeField().clean("2026-05-01T10:30")
        assert isinstance(result, datetime.datetime)

    def test_date_field_valeur_correcte(self):
        result = DateField().clean("2026-05-01")
        assert result == datetime.date(2026, 5, 1)

    def test_datetime_field_valeur_correcte(self):
        result = DateTimeField().clean("2026-05-01T10:30")
        assert result == datetime.datetime(2026, 5, 1, 10, 30)


# ---------------------------------------------------------------------------
# FileField / ImageField — pas de sauvegarde
# ---------------------------------------------------------------------------

class _FakeUpload:
    def __init__(self, filename="photo.jpg", size=100, content_type="image/jpeg"):
        self.filename = filename
        self.size = size
        self.content_type = content_type


class TestFileImagePasDeSauvegarde:

    def test_file_field_retourne_objet_original(self):
        upload = _FakeUpload("doc.pdf", content_type="application/octet-stream")
        result = FileField().clean(upload)
        assert result is upload

    def test_image_field_retourne_objet_original(self):
        upload = _FakeUpload("photo.jpg", content_type="image/jpeg")
        result = ImageField().clean(upload)
        assert result is upload

    def test_file_field_pas_dattribut_save(self):
        assert not hasattr(FileField, "save")

    def test_image_field_pas_dattribut_save(self):
        assert not hasattr(ImageField, "save")
