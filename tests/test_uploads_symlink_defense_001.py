"""Tests — UPLOADS-SYMLINK-DEFENSE-001.

Verrouille que Forge refuse de servir tout contenu hors racine via un
symlink, sur les deux chemins de service fichier exposés par le framework :

  * **Uploads / médias** — ``forge_mvc_files.serve_media_file`` (utilisé par
    ``app.py`` pour la route ``/media/...`` et par ``core.app.wsgi`` pour le
    chemin WSGI) ;
  * **Statics** — ``app.py::RequestHandler._serve_static`` (route
    ``/static/...``). Le test s'appuie sur la même chaîne
    ``os.path.realpath()`` + ``os.path.commonpath()`` utilisée par
    ``_serve_static`` ; un garde-fou source-level vérifie que app.py
    n'a pas dévié de ce pattern.

Le principe de défense audité : ``realpath()`` / ``Path.resolve()`` suit
les symlinks (le chemin final pointe vers la cible réelle), puis
``commonpath([root, resolved])`` doit rester égal à ``root``. Toute
sortie hors racine — fichier ou répertoire-symlink intermédiaire — fait
échouer cette équation.

Les tests utilisent ``os.symlink`` ; ils se skippent proprement si le
système ne le supporte pas (Windows sans privilèges typiquement).
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_files")

from forge_mvc_files import serve_media_file


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SECRET = b"FORGE-TEST-SECRET-DO-NOT-LEAK\n"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _can_make_symlinks(tmp_path: Path) -> bool:
    """`os.symlink` peut échouer sur Windows sans privilèges développeur ;
    on saute proprement plutôt que d'imposer le test."""
    src = tmp_path / "_symlink_probe_src"
    dst = tmp_path / "_symlink_probe_dst"
    src.write_text("x")
    try:
        os.symlink(src, dst)
    except (OSError, NotImplementedError):
        return False
    dst.unlink()
    src.unlink()
    return True


@pytest.fixture
def outside_secret(tmp_path_factory) -> Path:
    """Fichier hors racine que les attaquants tenteront d'exfiltrer."""
    base = tmp_path_factory.mktemp("outside_root_secret")
    p = base / "outside-secret.txt"
    p.write_bytes(_SECRET)
    return p


@pytest.fixture
def outside_secret_dir(tmp_path_factory) -> Path:
    """Répertoire hors racine contenant un secret."""
    base = tmp_path_factory.mktemp("outside_root_secret_dir")
    secret = base / "leaked-via-dir-symlink.txt"
    secret.write_bytes(_SECRET)
    return base


# ---------------------------------------------------------------------------
# Uploads / médias — défense via `serve_media_file`
# ---------------------------------------------------------------------------


class TestUploadsSymlinkDefense:
    """``serve_media_file`` ne doit jamais retourner le contenu d'un
    fichier hors racine, qu'il soit atteint via symlink fichier ou
    symlink répertoire intermédiaire."""

    def test_symlink_file_to_outside_is_refused(self, tmp_path, outside_secret):
        if not _can_make_symlinks(tmp_path):
            pytest.skip("symlink non supporté par l'environnement.")
        upload_root = tmp_path / "uploads"
        upload_root.mkdir()
        link = upload_root / "leak.txt"
        os.symlink(outside_secret, link)

        response = serve_media_file("leak.txt", root=str(upload_root))

        assert response.status in (403, 404), (
            f"Symlink vers fichier hors racine : status attendu 403/404, "
            f"reçu {response.status}."
        )
        assert response.status != 200
        assert _SECRET not in response.body, (
            "Le contenu hors racine n'a JAMAIS le droit d'apparaître dans "
            "la réponse, même partiellement."
        )

    def test_symlink_dir_traversal_is_refused(
        self, tmp_path, outside_secret_dir
    ):
        if not _can_make_symlinks(tmp_path):
            pytest.skip("symlink non supporté par l'environnement.")
        upload_root = tmp_path / "uploads"
        upload_root.mkdir()
        link_dir = upload_root / "outside_dir"
        os.symlink(outside_secret_dir, link_dir, target_is_directory=True)

        # Demande à travers le symlink-répertoire vers un fichier réel
        # placé dans le répertoire hors racine.
        response = serve_media_file(
            "outside_dir/leaked-via-dir-symlink.txt",
            root=str(upload_root),
        )

        assert response.status in (403, 404)
        assert response.status != 200
        assert _SECRET not in response.body

    def test_path_traversal_classic_dotdot_refused(
        self, tmp_path, outside_secret
    ):
        upload_root = tmp_path / "uploads"
        upload_root.mkdir()

        # Pas de symlink ici — juste un classique `..` qui doit rester refusé.
        response = serve_media_file(
            f"../{outside_secret.name}",
            root=str(upload_root),
        )
        assert response.status in (403, 404)
        assert _SECRET not in response.body

    def test_normal_file_is_still_served(self, tmp_path):
        upload_root = tmp_path / "uploads"
        upload_root.mkdir()
        category = upload_root / "documents"
        category.mkdir()
        target = category / "ok.txt"
        target.write_bytes(b"normal content")

        # `serve_media_file` attend un chemin relatif de la forme
        # `<category>/<filename>` — voir `normalize_media_path`.
        response = serve_media_file(
            "documents/ok.txt",
            root=str(upload_root),
        )
        assert response.status == 200
        # Service délégué à Response.file (streaming) : corps dans .stream.
        body = b"".join(response.stream) if response.stream is not None else response.body
        assert body == b"normal content"

    def test_nonexistent_file_returns_404_unchanged(self, tmp_path):
        upload_root = tmp_path / "uploads"
        upload_root.mkdir()
        category = upload_root / "documents"
        category.mkdir()

        response = serve_media_file(
            "documents/missing.txt",
            root=str(upload_root),
        )
        assert response.status == 404


# ---------------------------------------------------------------------------
# Statics — défense via `os.path.realpath` + `os.path.commonpath`
# ---------------------------------------------------------------------------
#
# Le code de service statique vit dans `app.py::RequestHandler._serve_static`
# et utilise exactement deux primitives stdlib :
#
#     filepath = os.path.realpath(os.path.join(STATIC_DIR, relative))
#     if not _is_safe_static_path(STATIC_DIR, filepath):  # commonpath
#         return 403
#
# On reproduit ici la même chaîne (sans démarrer un serveur HTTP) et on
# vérifie en sus, plus bas, que `app.py` n'a pas dévié de ce pattern.


def _resolve_like_app_static(static_dir: str, public_path: str) -> str:
    """Réplique exacte de la résolution de chemin de `app.py::_serve_static`."""
    relative = public_path.removeprefix("/static/")
    return os.path.realpath(os.path.join(static_dir, relative))


def _is_safe_static_path(static_dir: str, filepath: str) -> bool:
    """Réplique exacte de `app.py::_is_safe_static_path`."""
    try:
        return os.path.commonpath([static_dir, filepath]) == static_dir
    except ValueError:
        return False


class TestStaticsSymlinkDefense:
    """La même défense `realpath` + `commonpath` doit refuser les
    symlinks dans le chemin statique servi par ``app.py``."""

    def test_symlink_file_to_outside_is_refused(self, tmp_path, outside_secret):
        if not _can_make_symlinks(tmp_path):
            pytest.skip("symlink non supporté par l'environnement.")
        static_dir = str((tmp_path / "static").resolve())
        os.makedirs(static_dir)
        os.symlink(outside_secret, os.path.join(static_dir, "link.txt"))

        resolved = _resolve_like_app_static(static_dir, "/static/link.txt")
        assert not _is_safe_static_path(static_dir, resolved), (
            "Un symlink fichier vers l'extérieur DOIT être rejeté avant "
            "ouverture (app.py renvoie 403)."
        )
        # Garantit aussi que le contenu n'est pas accidentellement lu :
        # _serve_static n'ouvre le fichier qu'APRÈS le check de sécurité.
        # Ici on vérifie juste que le check fait son travail.

    def test_symlink_dir_traversal_is_refused(
        self, tmp_path, outside_secret_dir
    ):
        if not _can_make_symlinks(tmp_path):
            pytest.skip("symlink non supporté par l'environnement.")
        static_dir = str((tmp_path / "static").resolve())
        os.makedirs(static_dir)
        os.symlink(
            outside_secret_dir,
            os.path.join(static_dir, "outside_dir"),
            target_is_directory=True,
        )
        resolved = _resolve_like_app_static(
            static_dir, "/static/outside_dir/leaked-via-dir-symlink.txt"
        )
        assert not _is_safe_static_path(static_dir, resolved)

    def test_path_traversal_classic_dotdot_refused(
        self, tmp_path, outside_secret
    ):
        static_dir = str((tmp_path / "static").resolve())
        os.makedirs(static_dir)
        resolved = _resolve_like_app_static(
            static_dir, f"/static/../{outside_secret.name}"
        )
        # `..` est résolu par realpath ; la cible est nécessairement hors
        # static_dir → commonpath ≠ static_dir → refusé.
        assert not _is_safe_static_path(static_dir, resolved)

    def test_normal_file_is_still_served(self, tmp_path):
        static_dir = str((tmp_path / "static").resolve())
        os.makedirs(static_dir)
        target = os.path.join(static_dir, "ok.txt")
        with open(target, "wb") as f:
            f.write(b"normal")
        resolved = _resolve_like_app_static(static_dir, "/static/ok.txt")
        assert _is_safe_static_path(static_dir, resolved), (
            "Un fichier normal sous la racine static doit rester servi."
        )


# ---------------------------------------------------------------------------
# Garde-fou source-level : app.py n'a pas dévié de la chaîne realpath+commonpath
# ---------------------------------------------------------------------------


class TestAppPyStillUsesProtectedChain:
    """Si quelqu'un retire `realpath()` ou `commonpath()` de `app.py`, le
    test E2E sur statics passerait toujours (car on REPRODUIT la chaîne
    dans le test). Ce garde-fou source vérifie que le code de production
    fait toujours les deux étapes."""

    def test_serve_static_uses_realpath(self):
        src = (_REPO_ROOT / "tests" / "fixtures" / "app" / "app.py").read_text(encoding="utf-8")
        # _serve_static appelle `_os.path.realpath` sur le chemin construit.
        assert re.search(
            r"_os\.path\.realpath\s*\(\s*_os\.path\.join\(STATIC_DIR",
            src,
        ), (
            "app.py::_serve_static doit résoudre le chemin via "
            "`_os.path.realpath(_os.path.join(STATIC_DIR, ...))` AVANT "
            "le check de sécurité — sinon les symlinks ne sont pas "
            "suivis et la défense `commonpath` ne s'applique pas."
        )

    def test_is_safe_static_path_uses_commonpath(self):
        src = (_REPO_ROOT / "tests" / "fixtures" / "app" / "app.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        # Cherche la fonction _is_safe_static_path et vérifie qu'elle
        # appelle os.path.commonpath.
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_is_safe_static_path":
                func_src = ast.unparse(node)
                assert "commonpath" in func_src, (
                    "_is_safe_static_path doit utiliser os.path.commonpath."
                )
                return
        pytest.fail("Fonction _is_safe_static_path introuvable dans app.py.")

    def test_serve_static_calls_is_safe_before_open(self):
        """Le check de sécurité doit précéder `open()` du fichier."""
        src = (_REPO_ROOT / "tests" / "fixtures" / "app" / "app.py").read_text(encoding="utf-8")
        # On extrait le corps de _serve_static.
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_serve_static":
                body_src = ast.unparse(node)
                idx_check = body_src.find("_is_safe_static_path")
                idx_open = body_src.find("open(filepath")
                assert idx_check != -1, "_is_safe_static_path non appelée."
                assert idx_open != -1, "Le fichier n'est jamais ouvert ?"
                assert idx_check < idx_open, (
                    "Le check de sécurité doit précéder `open(filepath)`."
                )
                return
        pytest.fail("Méthode _serve_static introuvable dans app.py.")
