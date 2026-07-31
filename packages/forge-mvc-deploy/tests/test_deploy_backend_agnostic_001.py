"""DEPLOY-BACKEND-AGNOSTIC-001 : le deploiement ne suppose plus MariaDB.

Constate en jouant le parcours de l'opt-in sur un projet SQLite. `deploy:check`
verifiait `importlib.util.find_spec("mariadb")` et rendait une **erreur** quand
le module manquait, en conseillant `pip install mariadb`. Sur trois des quatre
backends officiels, ce refus etait donc faux, et il conseillait d'installer le
pilote d'un SGBD que le projet n'emploie pas.

L'unite systemd generee portait le meme defaut : `After=network.target
mariadb.service` quel que soit le backend, soit un service inexistant sur
PostgreSQL et SQL Server, et un service attendu la ou SQLite n'a aucun serveur.

Le coeur est agnostique et resout son backend par entry point (ADR-054). La
verification pose desormais la meme question que lui, ce qui la rend juste pour
les quatre backends et pour tout backend tiers a venir.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_deploy.cli import deploy

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ── Plus aucun pilote nomme en dur ───────────────────────────────────────────

def test_le_module_mariadb_n_est_plus_exige() -> None:
    """Test d'absence : c'est ce `find_spec` qui produisait le refus faux."""
    source = (PROJECT_ROOT / "packages" / "forge-mvc-deploy" / "forge_mvc_deploy"
              / "cli" / "deploy.py").read_text(encoding="utf-8")

    assert 'find_spec("mariadb")' not in source


def test_la_verification_interroge_les_entry_points() -> None:
    """La meme question que le coeur, donc la meme reponse (ADR-054)."""
    source = (PROJECT_ROOT / "packages" / "forge-mvc-deploy" / "forge_mvc_deploy"
              / "cli" / "deploy.py").read_text(encoding="utf-8")

    assert 'group="forge_mvc.db_backend"' in source


# ── Le verdict ───────────────────────────────────────────────────────────────

class _Point:
    def __init__(self, nom: str, casse: bool = False) -> None:
        self.name = nom
        self._casse = casse

    def load(self) -> object:
        if self._casse:
            raise ImportError("libmariadb absente")
        return object


def _avec(monkeypatch: pytest.MonkeyPatch, points: "list[_Point]") -> None:
    monkeypatch.setattr("importlib.metadata.entry_points",
                        lambda group=None: points)


def test_un_backend_charge_passe(monkeypatch: pytest.MonkeyPatch) -> None:
    _avec(monkeypatch, [_Point("sqlite")])
    resultat = deploy._verifier_backend_bdd()

    assert resultat.status == "ok"
    assert "sqlite" in resultat.label


def test_aucun_backend_est_une_erreur(monkeypatch: pytest.MonkeyPatch) -> None:
    """En production, aucun backend signifie aucune base atteinte."""
    _avec(monkeypatch, [])
    resultat = deploy._verifier_backend_bdd()

    assert resultat.status == "error"
    assert "ADR-054" in resultat.detail


def test_deux_backends_sont_une_erreur(monkeypatch: pytest.MonkeyPatch) -> None:
    """Les backends sont exclusifs : le coeur refuserait de resoudre."""
    _avec(monkeypatch, [_Point("mariadb"), _Point("sqlite")])
    resultat = deploy._verifier_backend_bdd()

    assert resultat.status == "error"
    assert "mariadb" in resultat.detail and "sqlite" in resultat.detail


def test_un_backend_dont_le_pilote_manque_est_une_erreur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C'est le vrai cas que l'ancien controle visait, sans savoir le nommer."""
    _avec(monkeypatch, [_Point("mariadb", casse=True)])
    resultat = deploy._verifier_backend_bdd()

    assert resultat.status == "error"
    assert "ImportError" in resultat.detail


# ── L'unite systemd ──────────────────────────────────────────────────────────

@pytest.mark.parametrize(("backend", "attendu"), [
    ("mariadb", "After=network.target mariadb.service"),
    ("postgres", "After=network.target postgresql.service"),
    ("mssql", "After=network.target mssql-server.service"),
])
def test_l_unite_attend_le_service_du_backend(
    backend: str, attendu: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(deploy, "_backend_installe", lambda: backend)

    assert attendu in deploy._systemd_service(Path("/srv/app"))


def test_sqlite_n_attend_aucun_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans serveur, attendre un service le ferait echouer au demarrage."""
    monkeypatch.setattr(deploy, "_backend_installe", lambda: "sqlite")
    unite = deploy._systemd_service(Path("/srv/app"))

    assert "After=network.target\n" in unite
    assert ".service" not in unite.split("[Service]")[0]


def test_un_backend_inconnu_n_invente_aucun_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un backend tiers ne doit pas faire deviner un nom d'unite."""
    monkeypatch.setattr(deploy, "_backend_installe", lambda: "cockroach")

    assert "After=network.target\n" in deploy._systemd_service(Path("/srv/app"))
