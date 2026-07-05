"""FORGE-NEW-INSTALL-SOURCE-001 (ADR-062).

`forge new` épingle le projet généré sur la source dont provient le CLI :
- FORGE_DEV_SRC (dossier local) : éditable, priorité maximale (couvert ailleurs) ;
- installation depuis Git : `forge-mvc @ git+<url>@<commit>` ;
- sinon PyPI : pin `forge-mvc==<version>` (défaut).

Ces tests couvrent la détection (`forge_mvc_git_spec`) et la réécriture du
requirements.txt généré (`pin_forge_mvc_to_git`), dans `cli/project/install_source.py`,
par mock des métadonnées.
"""
import json

from cli.project.install_source import forge_mvc_git_spec, pin_forge_mvc_to_git


class _FakeDist:
    """Distribution factice : expose read_text('direct_url.json')."""

    def __init__(self, payload: str | None):
        self._payload = payload

    def read_text(self, name: str) -> str | None:
        if name == "direct_url.json":
            return self._payload
        return None


def _patch_dist(monkeypatch, payload):
    monkeypatch.setattr(
        "importlib.metadata.distribution", lambda name: _FakeDist(payload)
    )


# ── Détection de la source Git ───────────────────────────────────────────────

def test_git_spec_detecte_vcs_commit(monkeypatch):
    payload = json.dumps({
        "url": "https://github.com/caucrogeGit/Forge.git",
        "vcs_info": {"vcs": "git", "commit_id": "abc123", "requested_revision": "main"},
    })
    _patch_dist(monkeypatch, payload)
    assert forge_mvc_git_spec() == (
        "forge-mvc @ git+https://github.com/caucrogeGit/Forge.git@abc123"
    )


def test_git_spec_fallback_sur_requested_revision(monkeypatch):
    payload = json.dumps({
        "url": "https://github.com/caucrogeGit/Forge.git",
        "vcs_info": {"vcs": "git", "requested_revision": "main"},
    })
    _patch_dist(monkeypatch, payload)
    assert forge_mvc_git_spec() == (
        "forge-mvc @ git+https://github.com/caucrogeGit/Forge.git@main"
    )


def test_git_spec_none_pour_pypi(monkeypatch):
    # Installation PyPI classique : pas de direct_url.json.
    _patch_dist(monkeypatch, None)
    assert forge_mvc_git_spec() is None


def test_git_spec_none_pour_editable_local(monkeypatch):
    # Éditable local (dir_info), pas de vcs_info : ce n'est pas le cas Git.
    payload = json.dumps({"url": "file:///home/x/Forge", "dir_info": {"editable": True}})
    _patch_dist(monkeypatch, payload)
    assert forge_mvc_git_spec() is None


def test_git_spec_none_si_distribution_absente(monkeypatch):
    import importlib.metadata as ilm

    def boom(name):
        raise ilm.PackageNotFoundError(name)

    monkeypatch.setattr("importlib.metadata.distribution", boom)
    assert forge_mvc_git_spec() is None


# ── Réécriture du requirements.txt généré ────────────────────────────────────

def test_pin_remplace_la_ligne_forge_mvc(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text(
        "# Dependances du projet Forge.\nforge-mvc==1.0.0rc2\n# Base de donnees\n",
        encoding="utf-8",
    )
    spec = "forge-mvc @ git+https://github.com/caucrogeGit/Forge.git@abc123"
    assert pin_forge_mvc_to_git(str(req), spec) is True
    content = req.read_text(encoding="utf-8")
    assert spec in content
    assert "forge-mvc==1.0.0rc2" not in content
    # Les commentaires et le reste du fichier sont préservés.
    assert "# Dependances du projet Forge." in content
    assert "# Base de donnees" in content


def test_pin_ne_touche_qu_une_ligne(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("forge-mvc==1.0.0rc2\nautre-paquet==1.0\n", encoding="utf-8")
    spec = "forge-mvc @ git+https://github.com/x/Forge.git@sha"
    pin_forge_mvc_to_git(str(req), spec)
    content = req.read_text(encoding="utf-8")
    assert "autre-paquet==1.0" in content
    assert content.count("forge-mvc") == 1


def test_pin_sans_fichier_retourne_false(tmp_path):
    assert pin_forge_mvc_to_git(str(tmp_path / "absent.txt"), "x") is False
