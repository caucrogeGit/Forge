from io import BytesIO
from types import SimpleNamespace

import pytest
pytest.importorskip("forge_mvc_files")
pytest.importorskip("forge_mvc_images")
from PIL import Image

import app
import core.forge as forge
from core.http.response import Response
from forge_mvc_files import delete_media_file, serve_media_file

# CORE-SAVEUPLOAD-GENERIC-CLEANUP (ADR-018) : chemin image-aware côté opt-in.
from forge_mvc_images import save_image_upload


def _image_file(filename="photo.png", *, size=(2000, 1000), content_type="image/png"):
    buffer = BytesIO()
    image = Image.new("RGB", size, color=(80, 130, 210))
    image.save(buffer, format="PNG")
    return SimpleNamespace(filename=filename, content=buffer.getvalue(), content_type=content_type)


class _MediaHandler:
    def __init__(self):
        self.responses = []

    def _send_response(self, response):
        self.responses.append(response)


def test_serve_media_file_image_existante_retourne_200(tmp_path):
    root = tmp_path / "uploads"
    target = root / "images" / "photo.png"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"png")

    response = serve_media_file("images/photo.png", root=root)

    assert response.status == 200
    assert response.body == b"png"
    assert response.content_type == "image/png"


def test_serve_media_file_variante_medium_existante_retourne_200(tmp_path):
    root = tmp_path / "uploads"
    target = root / "images" / "medium" / "photo.png"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"medium")

    response = serve_media_file("images/medium/photo.png", root=root)

    assert response.status == 200
    assert response.body == b"medium"
    assert response.content_type == "image/png"


def test_serve_media_file_document_existant_retourne_200(tmp_path):
    root = tmp_path / "uploads"
    target = root / "documents" / "contrat.pdf"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"%PDF")

    response = serve_media_file("documents/contrat.pdf", root=root)

    assert response.status == 200
    assert response.body == b"%PDF"
    assert response.content_type == "application/pdf"


def test_serve_media_file_type_inconnu_retourne_octet_stream(tmp_path):
    root = tmp_path / "uploads"
    target = root / "documents" / "archive.unknownext"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"data")

    response = serve_media_file("documents/archive.unknownext", root=root)

    assert response.status == 200
    assert response.content_type == "application/octet-stream"


def test_serve_media_file_absent_retourne_404(tmp_path):
    response = serve_media_file("images/missing.png", root=tmp_path / "uploads")

    assert response.status == 404


def test_serve_media_file_dossier_refuse(tmp_path):
    root = tmp_path / "uploads"
    (root / "images" / "album").mkdir(parents=True)

    response = serve_media_file("images/album", root=root)

    assert response.status == 404


@pytest.mark.parametrize(
    "path",
    [
        "../secret.txt",
        "images/../../secret.txt",
        "/etc/passwd",
        "https://example.com/file.png",
        "file:///tmp/test.png",
        r"C:\Users\roger\file.png",
    ],
)
def test_serve_media_file_chemin_dangereux_refuse(tmp_path, path):
    response = serve_media_file(path, root=tmp_path / "uploads")

    assert response.status == 404


def test_serve_media_file_ne_lit_pas_hors_uploads(tmp_path):
    root = tmp_path / "uploads"
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    response = serve_media_file(str(outside), root=root)

    assert response.status == 404
    assert response.body != b"secret"


def test_serve_media_file_refuse_symlink_sortant_de_uploads(tmp_path):
    root = tmp_path / "uploads"
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")
    link = root / "images" / "photo.png"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)

    response = serve_media_file("images/photo.png", root=root)

    assert response.status == 404
    assert outside.exists()


def test_request_handler_route_media_delegue_au_service(monkeypatch):
    # CORE-DROP-UPLOADS-001 (ADR-019) : _serve_media importe serve_media_file en
    # lazy depuis forge_mvc_files (opt-in) — on patche la vraie cible.
    import forge_mvc_files
    monkeypatch.setattr(forge_mvc_files, "serve_media_file",
                        lambda path: Response(200, path, "text/plain"))

    handler = _MediaHandler()
    app.RequestHandler._serve_media(handler, "/media/images/photo.png")

    response = handler.responses[-1]
    assert response.status == 200
    assert response.body == b"images/photo.png"


def test_serve_media_file_est_exporte_dans_api_publique():
    from forge_mvc_files import serve_media_file as exported_serve_media_file

    assert exported_serve_media_file is serve_media_file


def test_save_image_upload_variants_et_delete_media_file_restent_compatibles(tmp_path):
    forge.configure(
        upload_root=str(tmp_path / "uploads"),
        upload_max_size=10_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    saved = save_image_upload(_image_file(), category="images", variants=True)
    response = serve_media_file(saved.variants["medium"], root=tmp_path / "uploads")
    deleted = delete_media_file(saved.path, root=tmp_path / "uploads", variants=True)

    assert response.status == 200
    assert deleted[saved.path] is True
    assert deleted[saved.variants["medium"]] is True
    assert deleted[saved.variants["thumbnail"]] is True
