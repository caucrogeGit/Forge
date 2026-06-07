"""Audit sécurité — uploads et médias Forge (SECURITY-UPLOADS-AUDIT-001).

Cet audit complète la couverture existante (tests/test_uploads.py,
tests/test_media_route.py) avec des cas spécifiquement orientés sécurité :

- variantes de path traversal non encore testées ;
- extensions dangereuses exhaustives ;
- double extension (cas sûr et cas dangereux) ;
- MIME avec paramètres (spoofing via Content-Type) ;
- tailles limites (zéro, exactement max, un de trop, négatif) ;
- injection via nom de catégorie ;
- null byte dans chemin ou nom de fichier ;
- chemin retourné relatif (pas absolu) après sauvegarde ;
- suppression de fichier absent (False, pas d'exception) ;
- serve_media_file avec chemins supplémentaires dangereux.

Limite multipart HTTP réelle :
    Aucun test ne couvre un cycle HTTP multipart complet (upload via POST réel).
    Les tests existants utilisent des objets mock (UploadedFile, FakeFile).
    Ticket futur : E2E-UPLOAD-HTTP-001.

Limite MIME sniffing :
    Forge valide le Content-Type fourni par le client, pas la signature binaire
    du fichier. Un fichier PHP renommé en .jpg avec content_type=image/jpeg est
    accepté. Cette limite est documentée — corriger nécessite une dépendance
    lourde (python-magic) hors périmètre de ce ticket.
"""
from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_files")

import core.forge as forge
from core.forms.upload_exceptions import (
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadStorageError,
    UploadTooLargeError,
)
from forge_mvc_files.storage import (
    delete_file,
    normalize_media_path,
    safe_category,
    secure_filename,
    generate_unique_filename,
    media_path_to_storage_path,
)
from core.forms.upload_validation import (
    validate_extension,
    validate_mime_type,
    validate_size,
    validate_upload_metadata,
)
from forge_mvc_files.manager import (
    save_upload,
    serve_media_file,
    delete_media_file,
)
from tests._malicious_samples import fake_php_shell


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeFile:
    def __init__(self, filename: str, content: bytes = b"x", content_type: str = "image/png"):
        self.filename = filename
        self.content = content
        self.content_type = content_type


def _cfg_forge(tmp_path, *, ext=("jpg", "jpeg", "png", "pdf"), mime=("image/jpeg", "image/png", "application/pdf"), max_size=5_000_000):
    forge.configure(
        upload_root=str(tmp_path / "uploads"),
        upload_max_size=max_size,
        upload_allowed_extensions=list(ext),
        upload_allowed_mime_types=list(mime),
    )


# ---------------------------------------------------------------------------
# Path traversal — variantes supplémentaires
# ---------------------------------------------------------------------------

class TestPathTraversalVariantes:
    """Variantes de path traversal non couvertes par test_uploads.py."""

    def test_null_byte_dans_chemin_refuse(self):
        with pytest.raises(UploadStorageError):
            normalize_media_path("images/\x00photo.jpg")

    def test_null_byte_seul_refuse(self):
        with pytest.raises(UploadStorageError):
            normalize_media_path("\x00")

    def test_chemin_uniquement_points_normalise_sans_danger(self):
        """
        "..." est trois points — ce n'est pas ".." (deux points).
        normalize_media_path l'accepte comme nom de fichier relatif inhabituel.
        Il est inaccessible via le filesystem (aucun fichier ne s'appelle "...").
        """
        result = normalize_media_path("...")
        assert result == "..."
        assert ".." not in result.split("/")

    def test_double_point_seul_refuse(self):
        with pytest.raises(UploadStorageError):
            normalize_media_path("..")

    def test_unc_path_windows_refuse(self):
        with pytest.raises(UploadStorageError):
            normalize_media_path("\\\\server\\share\\file.jpg")

    def test_url_encoded_traversal_traite_litteralement(self):
        """
        %2e%2e n'est pas décodé par normalize_media_path.
        Le chemin %2e%2e/secret est traité comme un chemin relatif littéral
        — inaccessible côté filesystem. Documenter comme protection secondaire.
        """
        normalized = normalize_media_path("%2e%2e/secret")
        assert ".." not in normalized
        assert normalized == "%2e%2e/secret"

    def test_media_path_to_storage_path_reste_sous_root(self, tmp_path):
        root = tmp_path / "uploads"
        target = media_path_to_storage_path("images/photo.jpg", root=root)
        assert str(target).startswith(str(root.resolve()))


# ---------------------------------------------------------------------------
# Extensions — cas sécurité exhaustifs
# ---------------------------------------------------------------------------

class TestExtensionsSecurite:
    """Liste noire d'extensions dangereuses non autorisées par défaut."""

    _ALLOWED = ["jpg", "jpeg", "png", "pdf"]
    _ALLOWED_MIME = ["image/jpeg", "image/png", "application/pdf"]

    def _refuse(self, filename: str):
        with pytest.raises(UploadInvalidExtensionError):
            validate_extension(filename, self._ALLOWED)

    def _accept(self, filename: str):
        validate_extension(filename, self._ALLOWED)

    def test_extension_php_refusee(self):
        self._refuse("shell.php")

    def test_extension_php5_refusee(self):
        self._refuse("shell.php5")

    def test_extension_py_refusee(self):
        self._refuse("exploit.py")

    def test_extension_html_refusee(self):
        self._refuse("page.html")

    def test_extension_htm_refusee(self):
        self._refuse("page.htm")

    def test_extension_env_refusee(self):
        self._refuse(".env")

    def test_extension_js_refusee(self):
        self._refuse("script.js")

    def test_extension_svg_refusee_par_defaut(self):
        self._refuse("icon.svg")

    def test_extension_sh_refusee(self):
        self._refuse("exploit.sh")

    def test_extension_exe_refusee(self):
        self._refuse("virus.exe")

    def test_extension_majuscule_acceptee(self):
        """L'extension est normalisée en minuscules avant validation."""
        self._accept("PHOTO.JPG")

    def test_extension_mixte_acceptee(self):
        self._accept("Photo.Jpg")

    def test_extension_vide_refusee(self):
        self._refuse("fichier_sans_extension")

    def test_double_extension_dangereuse_refusee(self):
        """photo.jpg.php : extension finale .php → refusée."""
        self._refuse("photo.jpg.php")

    def test_double_extension_safe_acceptee(self):
        """
        photo.php.jpg : extension finale .jpg → acceptée.
        Limite : le nom original contient .php mais la validation ne bloque que
        la dernière extension. Le secure_filename nettoyage supprime les chars
        dangereux mais conserve les points. Documenter comme limite.
        """
        self._accept("photo.php.jpg")

    def test_extension_avec_point_prefixe_dans_liste(self):
        """La liste autorisée accepte '.jpg' ou 'jpg' indifféremment."""
        validate_extension("photo.jpg", [".jpg", ".png"])


# ---------------------------------------------------------------------------
# MIME — cas sécurité
# ---------------------------------------------------------------------------

class TestMimeSecurite:
    """Validation MIME, paramètres, et limites de sniffing."""

    def test_mime_avec_parametre_accepte(self):
        """image/png; charset=binary est normalisé en image/png avant validation."""
        validate_mime_type("image/png; charset=binary", ["image/png"])

    def test_mime_avec_espaces_accepte(self):
        validate_mime_type("image/jpeg ; q=0.9", ["image/jpeg"])

    def test_mime_uppercase_normalise(self):
        validate_mime_type("Image/PNG", ["image/png"])

    def test_mime_absent_avec_liste_non_vide_refuse(self):
        with pytest.raises(UploadInvalidMimeTypeError):
            validate_mime_type(None, ["image/png"])

    def test_mime_absent_avec_liste_vide_accepte(self):
        validate_mime_type(None, [])

    def test_mime_text_html_refuse_si_non_autorise(self):
        with pytest.raises(UploadInvalidMimeTypeError):
            validate_mime_type("text/html", ["image/png"])

    def test_limite_mime_spoofing_non_detecte(self, tmp_path):
        """
        Forge valide le Content-Type client, pas la signature binaire du fichier.
        Un fichier PHP avec content_type=image/jpeg et extension .jpg est accepté
        si image/jpeg et jpg sont dans la liste blanche.
        LIMITE CONNUE — corriger nécessite python-magic (hors périmètre).
        """
        _cfg_forge(tmp_path)
        fake_php = _FakeFile("malware.jpg", fake_php_shell("phpinfo();"), "image/jpeg")
        saved = save_upload(fake_php, category="documents")
        assert saved.mime_type == "image/jpeg"


# ---------------------------------------------------------------------------
# Tailles — limites exactes
# ---------------------------------------------------------------------------

class TestTailleSecurite:
    """Comportement précis aux bornes de la taille maximale."""

    def test_taille_zero_acceptee(self):
        validate_size(0, 100)

    def test_taille_exactement_max_acceptee(self):
        validate_size(100, 100)

    def test_taille_max_plus_un_refusee(self):
        with pytest.raises(UploadTooLargeError):
            validate_size(101, 100)

    def test_taille_negative_refusee(self):
        with pytest.raises(UploadStorageError):
            validate_size(-1, 100)

    def test_taille_zero_refusee_si_max_zero_negatif(self):
        """Si max_size vaut 0, tout fichier non-vide est refusé."""
        with pytest.raises(UploadTooLargeError):
            validate_size(1, 0)


# ---------------------------------------------------------------------------
# Catégorie — injection
# ---------------------------------------------------------------------------

class TestCategorieSecurite:
    """safe_category() refuse toute catégorie non alphanumérique."""

    def test_categorie_traversal_refusee(self):
        with pytest.raises(UploadStorageError):
            safe_category("../evil")

    def test_categorie_avec_slash_refusee(self):
        with pytest.raises(UploadStorageError):
            safe_category("images/evil")

    def test_categorie_avec_espace_refusee(self):
        with pytest.raises(UploadStorageError):
            safe_category("my images")

    def test_categorie_vide_refusee(self):
        with pytest.raises(UploadStorageError):
            safe_category("")

    def test_categorie_point_seul_refusee(self):
        with pytest.raises(UploadStorageError):
            safe_category(".")

    def test_categorie_alphanum_acceptee(self):
        assert safe_category("images") == "images"
        assert safe_category("my-files") == "my-files"
        assert safe_category("uploads_2026") == "uploads_2026"


# ---------------------------------------------------------------------------
# Nom de fichier sécurisé
# ---------------------------------------------------------------------------

class TestNomFichierSecurite:
    """secure_filename() nettoie les noms dangereux."""

    def test_null_byte_dans_nom_nettoye(self):
        result = secure_filename("file\x00.jpg")
        assert "\x00" not in result

    def test_chemin_relatif_tronque_au_basename(self):
        result = secure_filename("../../etc/passwd")
        assert "/" not in result
        assert ".." not in result

    def test_espaces_remplaces_par_underscore(self):
        result = secure_filename("mon fichier.jpg")
        assert " " not in result
        assert "_" in result

    def test_chars_speciaux_nettoyes(self):
        result = secure_filename("file<script>.jpg")
        assert "<" not in result
        assert ">" not in result

    def test_generate_unique_filename_contient_uuid(self):
        name = generate_unique_filename("photo.jpg")
        parts = name.rsplit(".", 1)[0].split("-")
        assert len(parts) >= 2

    def test_generate_unique_filename_extension_preservee(self):
        name = generate_unique_filename("document.pdf")
        assert name.endswith(".pdf")

    def test_generate_unique_filename_extension_normalisee(self):
        name = generate_unique_filename("PHOTO.JPG")
        assert name.endswith(".jpg")


# ---------------------------------------------------------------------------
# Chemin stocké relatif après sauvegarde
# ---------------------------------------------------------------------------

class TestCheminStocke:
    """SavedUpload.path est toujours relatif, jamais absolu."""

    def test_save_upload_retourne_chemin_relatif(self, tmp_path):
        _cfg_forge(tmp_path)
        f = _FakeFile("photo.jpg", b"x" * 100, "image/jpeg")
        saved = save_upload(f, category="documents")
        assert not saved.path.startswith("/")
        assert not saved.path.startswith("storage/")

    def test_save_upload_path_contient_uuid_pour_eviter_collision(self, tmp_path):
        _cfg_forge(tmp_path)
        f1 = _FakeFile("photo.jpg", b"premier", "image/jpeg")
        f2 = _FakeFile("photo.jpg", b"second", "image/jpeg")
        s1 = save_upload(f1, category="documents")
        s2 = save_upload(f2, category="documents")
        assert s1.path != s2.path

    def test_save_upload_path_est_valide_pour_serve(self, tmp_path):
        _cfg_forge(tmp_path)
        f = _FakeFile("photo.jpg", b"x" * 100, "image/jpeg")
        saved = save_upload(f, category="documents")
        response = serve_media_file(saved.path, root=tmp_path / "uploads")
        assert response.status == 200


# ---------------------------------------------------------------------------
# Suppression — cas limites
# ---------------------------------------------------------------------------

class TestSuppressionSecurite:
    """delete_file() gère correctement les cas limites."""

    def test_delete_file_absent_retourne_false(self, tmp_path):
        root = tmp_path / "uploads"
        root.mkdir()
        result = delete_file("images/inexistant.jpg", root=root)
        assert result is False

    def test_delete_media_file_absent_retourne_dict_false(self, tmp_path):
        root = tmp_path / "uploads"
        root.mkdir()
        result = delete_media_file("images/inexistant.jpg", root=root)
        assert all(v is False for v in result.values())
        assert len(result) == 1

    def test_delete_file_chemin_vide_traite_comme_racine_refusee(self, tmp_path):
        """delete_file("") pointe sur la racine uploads (répertoire) → non-fichier → erreur."""
        root = tmp_path / "uploads"
        root.mkdir()
        with pytest.raises(UploadStorageError, match="n'est pas un fichier"):
            delete_file("", root=root)

    def test_delete_file_existant_supprime_et_retourne_true(self, tmp_path):
        root = tmp_path / "uploads"
        target = root / "images"
        target.mkdir(parents=True)
        fichier = target / "photo.jpg"
        fichier.write_bytes(b"test")
        result = delete_file("images/photo.jpg", root=root)
        assert result is True
        assert not fichier.exists()


# ---------------------------------------------------------------------------
# serve_media_file — cas sécurité complémentaires
# ---------------------------------------------------------------------------

class TestServeMediaSecurite:
    """Cas complémentaires sur serve_media_file()."""

    def test_null_byte_retourne_404(self, tmp_path):
        response = serve_media_file("images/\x00photo.jpg", root=tmp_path / "uploads")
        assert response.status == 404

    def test_chemin_vide_retourne_404(self, tmp_path):
        response = serve_media_file("", root=tmp_path / "uploads")
        assert response.status == 404

    def test_chemin_uniquement_separateurs_retourne_404(self, tmp_path):
        response = serve_media_file("///", root=tmp_path / "uploads")
        assert response.status == 404

    def test_url_http_retourne_404(self, tmp_path):
        response = serve_media_file("https://example.com/evil.jpg", root=tmp_path / "uploads")
        assert response.status == 404

    def test_content_type_image_jpeg_correct(self, tmp_path):
        root = tmp_path / "uploads" / "images"
        root.mkdir(parents=True)
        (root / "photo.jpg").write_bytes(b"\xff\xd8\xff" + b"x" * 10)
        response = serve_media_file("images/photo.jpg", root=tmp_path / "uploads")
        assert response.status == 200
        assert "jpeg" in response.content_type or "jpg" in response.content_type

    def test_content_type_pdf_correct(self, tmp_path):
        root = tmp_path / "uploads" / "documents"
        root.mkdir(parents=True)
        (root / "doc.pdf").write_bytes(b"%PDF-1.4")
        response = serve_media_file("documents/doc.pdf", root=tmp_path / "uploads")
        assert response.status == 200
        assert "pdf" in response.content_type

    def test_fichier_hors_racine_retourne_404(self, tmp_path):
        secret = tmp_path / "secret.txt"
        secret.write_text("confidentiel", encoding="utf-8")
        response = serve_media_file(str(secret), root=tmp_path / "uploads")
        assert response.status == 404


# ---------------------------------------------------------------------------
# Racine uploads — isolation et structure
# ---------------------------------------------------------------------------

class TestIsolationUploads:
    """La racine uploads est isolée du reste du filesystem."""

    def test_upload_root_est_absolu(self):
        import os
        import config
        assert os.path.isabs(config.UPLOAD_ROOT)

    def test_validate_upload_metadata_complet_valide(self):
        ext = validate_upload_metadata(
            filename="photo.jpg",
            size=1024,
            mime_type="image/jpeg",
            allowed_extensions=["jpg", "png"],
            allowed_mime_types=["image/jpeg", "image/png"],
            max_size=5_000_000,
        )
        assert ext == "jpg"

    def test_validate_upload_metadata_refuse_extension_dangereuse(self):
        with pytest.raises(UploadInvalidExtensionError):
            validate_upload_metadata(
                filename="webshell.php",
                size=42,
                mime_type="image/jpeg",
                allowed_extensions=["jpg", "png"],
                allowed_mime_types=["image/jpeg"],
                max_size=5_000_000,
            )
