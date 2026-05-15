import pytest

from core.forms import FileField, ValidationError


class DummyUpload:
    def __init__(self, filename, size=100, content_type="application/octet-stream"):
        self.filename = filename
        self.size = size
        self.content_type = content_type


def _field(**kw):
    return FileField(**kw)


# ---------------------------------------------------------------------------
# Fichier absent / vide
# ---------------------------------------------------------------------------

class TestFileFieldEmpty:

    def test_none_accepte_si_non_required(self):
        assert _field(required=False).clean(None) is None

    def test_none_refuse_si_required(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field(required=True).clean(None)

    def test_chaine_vide_accepte_si_non_required(self):
        assert _field(required=False).clean("") is None

    def test_chaine_vide_refuse_si_required(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field(required=True).clean("")

    def test_filename_vide_refuse_si_required(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field(required=True).clean(DummyUpload(""))

    def test_filename_blancs_refuse_si_required(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field(required=True).clean(DummyUpload("   "))

    def test_filename_vide_accepte_si_non_required(self):
        assert _field(required=False).clean(DummyUpload("")) is None

    def test_taille_zero_refuse_si_required(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field(required=True).clean(DummyUpload("doc.pdf", size=0))

    def test_taille_zero_accepte_si_non_required(self):
        assert _field(required=False).clean(DummyUpload("doc.pdf", size=0)) is None


# ---------------------------------------------------------------------------
# Retour de l'objet original
# ---------------------------------------------------------------------------

class TestFileFieldReturnValue:

    def test_retourne_objet_original(self):
        upload = DummyUpload("doc.pdf", size=100, content_type="application/pdf")
        result = _field().clean(upload)
        assert result is upload

    def test_retourne_objet_original_avec_extension_autorisee(self):
        upload = DummyUpload("rapport.pdf")
        result = _field(allowed_extensions=["pdf"]).clean(upload)
        assert result is upload


# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------

class TestFileFieldExtension:

    def test_extension_autorisee_passe(self):
        upload = DummyUpload("document.pdf")
        assert _field(allowed_extensions=["pdf"]).clean(upload) is upload

    def test_extension_interdite_refuse(self):
        with pytest.raises(ValidationError, match="Extension"):
            _field(allowed_extensions=["pdf"]).clean(DummyUpload("script.php"))

    def test_extension_majuscule_acceptee(self):
        upload = DummyUpload("image.JPG")
        assert _field(allowed_extensions=["jpg", "jpeg"]).clean(upload) is upload

    def test_extension_mixte_casse_acceptee(self):
        upload = DummyUpload("photo.Png")
        assert _field(allowed_extensions=["png"]).clean(upload) is upload

    def test_extension_autorisee_avec_point_dans_liste(self):
        upload = DummyUpload("doc.pdf")
        assert _field(allowed_extensions=[".pdf"]).clean(upload) is upload

    def test_sans_extension_refuse_si_liste_definie(self):
        with pytest.raises(ValidationError, match="Extension"):
            _field(allowed_extensions=["pdf"]).clean(DummyUpload("fichier_sans_extension"))

    def test_double_extension_dangereuse_refusee(self):
        with pytest.raises(ValidationError, match="Extension"):
            _field(allowed_extensions=["jpg"]).clean(DummyUpload("image.jpg.php"))

    def test_sans_contrainte_extension_passe_nimporte_quoi(self):
        upload = DummyUpload("script.php")
        assert _field().clean(upload) is upload

    def test_plusieurs_extensions_autorisees(self):
        for ext in ("doc.pdf", "image.jpg", "photo.png"):
            upload = DummyUpload(ext)
            assert _field(allowed_extensions=["pdf", "jpg", "png"]).clean(upload) is upload


# ---------------------------------------------------------------------------
# Taille maximale
# ---------------------------------------------------------------------------

class TestFileFieldSize:

    def test_sous_max_size_passe(self):
        upload = DummyUpload("doc.pdf", size=500)
        assert _field(max_size=1024).clean(upload) is upload

    def test_egal_max_size_passe(self):
        upload = DummyUpload("doc.pdf", size=1024)
        assert _field(max_size=1024).clean(upload) is upload

    def test_au_dessus_max_size_refuse(self):
        upload = DummyUpload("doc.pdf", size=2000)
        with pytest.raises(ValidationError, match="volumineux"):
            _field(max_size=1024).clean(upload)

    def test_sans_max_size_passe_nimporte_quelle_taille(self):
        upload = DummyUpload("doc.pdf", size=100 * 1024 * 1024)
        assert _field().clean(upload) is upload

    def test_extension_et_taille_ensemble(self):
        upload = DummyUpload("doc.pdf", size=500)
        result = _field(allowed_extensions=["pdf"], max_size=1024).clean(upload)
        assert result is upload

    def test_extension_valide_mais_taille_invalide_refuse(self):
        upload = DummyUpload("doc.pdf", size=9999)
        with pytest.raises(ValidationError, match="volumineux"):
            _field(allowed_extensions=["pdf"], max_size=1024).clean(upload)


# ---------------------------------------------------------------------------
# Type MIME
# ---------------------------------------------------------------------------

class TestFileFieldMime:

    def test_mime_autorise_passe(self):
        upload = DummyUpload("doc.pdf", content_type="application/pdf")
        assert _field(allowed_mime_types=["application/pdf"]).clean(upload) is upload

    def test_mime_interdit_refuse(self):
        upload = DummyUpload("malware.txt", content_type="text/plain")
        with pytest.raises(ValidationError, match="MIME"):
            _field(allowed_mime_types=["application/pdf"]).clean(upload)

    def test_mime_avec_charset_normalise(self):
        upload = DummyUpload("page.html", content_type="text/html; charset=utf-8")
        assert _field(allowed_mime_types=["text/html"]).clean(upload) is upload

    def test_mime_absent_refuse_si_liste_definie(self):
        upload = DummyUpload("doc.pdf", content_type=None)
        with pytest.raises(ValidationError, match="MIME"):
            _field(allowed_mime_types=["application/pdf"]).clean(upload)

    def test_sans_contrainte_mime_passe(self):
        upload = DummyUpload("doc.pdf", content_type="text/plain")
        assert _field().clean(upload) is upload


# ---------------------------------------------------------------------------
# Label dans les messages
# ---------------------------------------------------------------------------

class TestFileFieldLabel:

    def test_label_dans_message_obligatoire(self):
        field = FileField(label="Pièce jointe", required=True)
        with pytest.raises(ValidationError) as exc:
            field.clean(None)
        assert "Pièce jointe" in str(exc.value)

    def test_label_dans_message_extension(self):
        field = FileField(label="Document", allowed_extensions=["pdf"])
        with pytest.raises(ValidationError) as exc:
            field.clean(DummyUpload("virus.exe"))
        assert "Document" in str(exc.value)

    def test_label_dans_message_taille(self):
        field = FileField(label="Fichier", max_size=10)
        with pytest.raises(ValidationError) as exc:
            field.clean(DummyUpload("gros.pdf", size=9999))
        assert "Fichier" in str(exc.value)
