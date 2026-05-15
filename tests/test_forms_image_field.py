import pytest

from core.forms import FileField, ImageField, ValidationError


class DummyUpload:
    def __init__(self, filename, size=100, content_type="image/jpeg"):
        self.filename = filename
        self.size = size
        self.content_type = content_type


def _field(**kw):
    return ImageField(**kw)


# ---------------------------------------------------------------------------
# Héritage
# ---------------------------------------------------------------------------

class TestImageFieldHeritage:

    def test_herite_de_filefield(self):
        assert issubclass(ImageField, FileField)

    def test_instance_est_filefield(self):
        assert isinstance(_field(), FileField)


# ---------------------------------------------------------------------------
# Défauts extensions et MIME
# ---------------------------------------------------------------------------

class TestImageFieldDefaults:

    def test_extensions_par_defaut_contiennent_jpg(self):
        f = _field()
        assert "jpg" in f.allowed_extensions

    def test_extensions_par_defaut_contiennent_jpeg(self):
        assert "jpeg" in _field().allowed_extensions

    def test_extensions_par_defaut_contiennent_png(self):
        assert "png" in _field().allowed_extensions

    def test_gif_absent_des_extensions_par_defaut(self):
        assert "gif" not in _field().allowed_extensions

    def test_extensions_par_defaut_contiennent_webp(self):
        assert "webp" in _field().allowed_extensions

    def test_svg_absent_des_extensions_par_defaut(self):
        assert "svg" not in _field().allowed_extensions

    def test_mime_par_defaut_contient_jpeg(self):
        assert "image/jpeg" in _field().allowed_mime_types

    def test_mime_par_defaut_contient_png(self):
        assert "image/png" in _field().allowed_mime_types

    def test_image_gif_absent_des_mime_par_defaut(self):
        assert "image/gif" not in _field().allowed_mime_types

    def test_mime_par_defaut_contient_webp(self):
        assert "image/webp" in _field().allowed_mime_types

    def test_svg_mime_absent_par_defaut(self):
        assert "image/svg+xml" not in _field().allowed_mime_types


# ---------------------------------------------------------------------------
# Fichiers valides
# ---------------------------------------------------------------------------

class TestImageFieldValid:

    @pytest.mark.parametrize("filename,mime", [
        ("photo.jpg",       "image/jpeg"),
        ("photo.jpeg",      "image/jpeg"),
        ("image.PNG",       "image/png"),
        ("photo.webp",      "image/webp"),
    ])
    def test_image_valide(self, filename, mime):
        upload = DummyUpload(filename, content_type=mime)
        result = _field().clean(upload)
        assert result is upload

    def test_extension_majuscule_acceptee(self):
        upload = DummyUpload("PHOTO.JPG", content_type="image/jpeg")
        assert _field().clean(upload) is upload

    def test_retourne_objet_original(self):
        upload = DummyUpload("photo.jpg")
        assert _field().clean(upload) is upload

    def test_sous_max_size_passe(self):
        upload = DummyUpload("photo.jpg", size=500)
        assert _field(max_size=1024).clean(upload) is upload

    def test_egal_max_size_passe(self):
        upload = DummyUpload("photo.jpg", size=1024)
        assert _field(max_size=1024).clean(upload) is upload


# ---------------------------------------------------------------------------
# Fichiers invalides
# ---------------------------------------------------------------------------

class TestImageFieldInvalid:

    def test_refuse_pdf(self):
        with pytest.raises(ValidationError, match="Extension"):
            _field().clean(DummyUpload("document.pdf", content_type="application/pdf"))

    def test_refuse_php(self):
        with pytest.raises(ValidationError, match="Extension"):
            _field().clean(DummyUpload("script.php", content_type="text/plain"))

    def test_refuse_svg_par_defaut(self):
        with pytest.raises(ValidationError, match="Extension"):
            _field().clean(DummyUpload("image.svg", content_type="image/svg+xml"))

    def test_refuse_double_extension_dangereuse(self):
        with pytest.raises(ValidationError, match="Extension"):
            _field().clean(DummyUpload("image.jpg.php"))

    def test_refuse_sans_extension(self):
        with pytest.raises(ValidationError, match="Extension"):
            _field().clean(DummyUpload("imagepasextension"))

    def test_refuse_mime_non_image(self):
        upload = DummyUpload("photo.jpg", content_type="application/pdf")
        with pytest.raises(ValidationError, match="MIME"):
            _field().clean(upload)

    def test_refuse_mime_texte_plain(self):
        upload = DummyUpload("photo.png", content_type="text/plain")
        with pytest.raises(ValidationError, match="MIME"):
            _field().clean(upload)

    def test_refuse_au_dessus_max_size(self):
        upload = DummyUpload("photo.jpg", size=9999)
        with pytest.raises(ValidationError, match="volumineux"):
            _field(max_size=1024).clean(upload)

    def test_refuse_gif_par_defaut(self):
        with pytest.raises(ValidationError, match="Extension"):
            _field().clean(DummyUpload("animation.gif", content_type="image/gif"))


# ---------------------------------------------------------------------------
# Fichier absent / required
# ---------------------------------------------------------------------------

class TestImageFieldEmpty:

    def test_none_accepte_si_non_required(self):
        assert _field(required=False).clean(None) is None

    def test_none_refuse_si_required(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field(required=True).clean(None)

    def test_taille_zero_refuse_si_required(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field(required=True).clean(DummyUpload("photo.jpg", size=0))

    def test_taille_zero_accepte_si_non_required(self):
        assert _field(required=False).clean(DummyUpload("photo.jpg", size=0)) is None


# ---------------------------------------------------------------------------
# Surcharge extensions et MIME
# ---------------------------------------------------------------------------

class TestImageFieldOverride:

    def test_surcharge_allowed_extensions(self):
        f = ImageField(allowed_extensions=["jpg"])
        assert f.allowed_extensions == ["jpg"]

    def test_surcharge_exclut_png_si_absent(self):
        f = ImageField(allowed_extensions=["jpg"])
        with pytest.raises(ValidationError, match="Extension"):
            f.clean(DummyUpload("image.png", content_type="image/png"))

    def test_surcharge_allowed_mime_types(self):
        f = ImageField(allowed_mime_types=["image/jpeg"])
        with pytest.raises(ValidationError, match="MIME"):
            f.clean(DummyUpload("photo.png", content_type="image/png"))

    def test_max_size_surchargeable(self):
        f = ImageField(max_size=512)
        with pytest.raises(ValidationError, match="volumineux"):
            f.clean(DummyUpload("photo.jpg", size=1024))

    def test_max_size_none_par_defaut(self):
        f = ImageField()
        assert f.max_size is None
