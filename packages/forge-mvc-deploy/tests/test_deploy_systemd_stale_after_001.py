"""DEPLOY-SYSTEMD-STALE-AFTER-001 — `deploy:check` voit une unité systemd périmée.

`DEPLOY-BACKEND-AGNOSTIC-001` a rendu l'unité systemd dialectale : elle attend
désormais le service du backend résolu, `postgresql.service` sous PostgreSQL,
aucun sous SQLite.

Mais `deploy:init` écrit en write-if-new, et c'est juste : Forge ne réécrit pas
un fichier du projet (principe 9). Un projet provisionné avant ce correctif
garde donc son `After=network.target mariadb.service`, quel que soit son
backend, et rien ne le lui disait.

La panne qui en découle est discrète. Sous PostgreSQL, ce `After=` désigne un
service inexistant, donc systemd ne retarde rien : au démarrage de la machine,
l'application part avant sa base et rate ses premières connexions. Cela ne se
produit qu'au boot, jamais en test, et ressemble à un défaut de Forge.

Le contrôle avertit, il ne corrige pas. L'unité appartient au projet.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_deploy.cli import deploy


@pytest.fixture
def projet(tmp_path: Path):
    """Rend une fabrique d'unité systemd dans un projet jetable."""
    def _ecrire(contenu: "str | None") -> Path:
        if contenu is not None:
            dossier = tmp_path / "deploy" / "systemd"
            dossier.mkdir(parents=True, exist_ok=True)
            (dossier / "forge-app.service").write_text(
                f"[Unit]\nDescription=Forge Application\n{contenu}\n", encoding="utf-8")
        return tmp_path
    return _ecrire


@pytest.fixture
def backend(monkeypatch):
    """Force le backend résolu, sans dépendre de ce qui est installé ici."""
    def _poser(nom: "str | None") -> None:
        monkeypatch.setattr(deploy, "_backend_installe", lambda: nom)
    return _poser


# ── Le cas mesuré ────────────────────────────────────────────────────────────

def test_unite_figee_sur_mariadb_sous_postgres_avertit(projet, backend) -> None:
    """Le projet rc3 mis à jour, exactement."""
    backend("postgres")
    racine = projet("After=network.target mariadb.service")

    resultat = deploy._verifier_unite_systemd(racine)

    assert resultat.status == "warn"
    assert "postgresql.service" in resultat.detail
    assert "deploy/systemd/forge-app.service" in resultat.detail


@pytest.mark.parametrize(("nom", "service"), [
    ("mariadb", "mariadb.service"),
    ("postgres", "postgresql.service"),
    ("mssql", "mssql-server.service"),
])
def test_unite_accordee_au_backend_passe(projet, backend, nom: str, service: str) -> None:
    """Contre-épreuve : sans elle, le contrôle pourrait crier sur tout."""
    backend(nom)
    racine = projet(f"After=network.target {service}")

    assert deploy._verifier_unite_systemd(racine).status == "ok"


# ── SQLite n'attend aucun service ────────────────────────────────────────────

def test_sqlite_avec_un_service_avertit(projet, backend) -> None:
    """Attendre un serveur là où il n'y en a pas retarde le démarrage pour rien."""
    backend("sqlite")
    racine = projet("After=network.target mariadb.service")

    resultat = deploy._verifier_unite_systemd(racine)

    assert resultat.status == "warn"
    assert "sqlite" in resultat.detail


def test_sqlite_sans_service_passe(projet, backend) -> None:
    backend("sqlite")
    racine = projet("After=network.target")

    assert deploy._verifier_unite_systemd(racine).status == "ok"


# ── Ce que le contrôle n'affirme pas ─────────────────────────────────────────

def test_sans_backend_resolu_il_n_affirme_rien(projet, backend) -> None:
    """`_verifier_backend_bdd` signale déjà la cause.

    Deux messages pour une seule anomalie brouillent le diagnostic, et le
    second serait faux : sans backend, on ignore quel service attendre.
    """
    backend(None)
    racine = projet("After=network.target mariadb.service")

    resultat = deploy._verifier_unite_systemd(racine)

    assert resultat.status == "warn"
    assert "non vérifiable" in resultat.detail


def test_unite_absente_n_est_pas_une_anomalie(projet, backend) -> None:
    """Un projet qui n'a pas encore lancé `deploy:init` n'a rien fait de mal."""
    backend("postgres")
    racine = projet(None)

    assert deploy._verifier_unite_systemd(racine).status == "ok"


def test_unite_sans_ligne_after_avertit(projet, backend) -> None:
    """Sans `After=`, l'ordre de démarrage n'est garanti par rien."""
    backend("postgres")
    racine = projet("Wants=network.target")

    resultat = deploy._verifier_unite_systemd(racine)

    assert resultat.status == "warn"
    assert "After=" in resultat.detail


# ── Le contrôle est bien câblé dans deploy:check ─────────────────────────────

def test_le_controle_figure_dans_deploy_check(projet, backend) -> None:
    """Un contrôle juste que `deploy:check` n'appelle pas ne sert à rien."""
    backend("postgres")
    racine = projet("After=network.target mariadb.service")
    (racine / "mvc").mkdir(exist_ok=True)

    labels = [r.label for r in deploy._check_results(racine)]

    assert "Unité systemd" in labels


def test_il_avertit_sans_jamais_reecrire(projet, backend) -> None:
    """Principe 9 : l'unité appartient au projet, Forge n'y touche pas."""
    backend("postgres")
    racine = projet("After=network.target mariadb.service")
    unite = racine / "deploy" / "systemd" / "forge-app.service"
    avant = unite.read_text(encoding="utf-8")

    resultat = deploy._verifier_unite_systemd(racine)

    assert resultat.status != "error"
    assert unite.read_text(encoding="utf-8") == avant
