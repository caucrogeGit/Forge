"""E2E-LAUNCHER-APP-PATH-001 — le harnais E2E est vivant, et le dit s'il ne l'est pas.

Soixante-cinq tests, dont les trente-trois d'en-têtes de sécurité, ont cessé de
s'exécuter le 2026-06-23, quand l'ADR-044 a relocalisé l'application de
dogfooding hors de la racine du dépôt. `tests/_e2e_launcher.py` a continué de la
chercher à la racine.

Trois causes se sont additionnées pour rendre la panne muette pendant six
versions publiées :

1. le lanceur visait `ROOT / "app.py"`, disparu ;
2. son `stderr` partait dans `subprocess.DEVNULL`, donc le `FileNotFoundError`
   n'atteignait personne ;
3. l'absence de `READY:` se traduisait en `pytest.skip("Serveur Forge non
   disponible")`, formule qui décrit un poste local mal équipé, pas un bug.

Un `skip` est légitime quand l'environnement manque vraiment de quelque chose,
une base par exemple. Ici l'application servie est **dans le dépôt** : son
absence est toujours un défaut du harnais, jamais une condition de poste.

Ce fichier tient les trois causes. Il ne se saute jamais : si le harnais meurt à
nouveau, la suite rougit au lieu de se taire.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LANCEUR = ROOT / "tests" / "_e2e_launcher.py"

#: Les fichiers dont les fixtures démarrent un serveur Forge réel.
FICHIERS_E2E = (
    "tests/test_http_e2e_001.py",
    "tests/test_security_headers.py",
    "tests/test_health_endpoint_001.py",
)


def _port_libre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ── Cause 1 : le chemin ──────────────────────────────────────────────────────

def test_le_lanceur_designe_une_application_qui_existe() -> None:
    """Le contrôle qui manquait, et qui tient en une ligne."""
    source = LANCEUR.read_text(encoding="utf-8")
    espace: "dict[str, object]" = {"__file__": str(LANCEUR)}
    exec(compile(source.split("# TEST_PORT")[0], str(LANCEUR), "exec"), espace)

    app_file = espace["APP_FILE"]

    assert isinstance(app_file, Path)
    assert app_file.is_file(), (
        f"le lanceur E2E vise {app_file}, qui n'existe pas : les tests E2E "
        f"vont tous se sauter en annonçant un poste mal équipé")


# ── Le harnais tourne vraiment ───────────────────────────────────────────────

def test_le_lanceur_sert_reellement() -> None:
    """Preuve par exécution, pas par lecture de chemin.

    Un chemin juste ne garantit pas une application qui démarre : il a fallu
    aussi que son répertoire soit courant et importable, sans quoi elle échouait
    sur `No module named 'config'` bien après la résolution du fichier.
    """
    port = _port_libre()
    journal = tempfile.TemporaryFile()
    proc = subprocess.Popen(
        [sys.executable, str(LANCEUR)],
        cwd=str(ROOT),
        env={"APP_ENV": "prod", "TEST_PORT": str(port), "PATH": "/usr/bin:/bin"},
        stdout=subprocess.PIPE,
        stderr=journal,
    )
    try:
        ligne = proc.stdout.readline() if proc.stdout else b""
        if not ligne.startswith(b"READY:"):
            journal.seek(0)
            pytest.fail("le lanceur E2E n'a pas signalé READY.\n"
                        + journal.read().decode("utf-8", "replace").strip())
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as reponse:
            assert reponse.status == 200
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


# ── Cause 2 : l'erreur jetée ─────────────────────────────────────────────────

@pytest.mark.parametrize("fichier", FICHIERS_E2E)
def test_aucune_fixture_ne_jette_l_erreur_du_lanceur(fichier: str) -> None:
    """`stderr=DEVNULL` a rendu la panne indiagnosticable six semaines durant."""
    source = (ROOT / fichier).read_text(encoding="utf-8")

    assert "stderr=subprocess.DEVNULL" not in source, (
        f"{fichier} jette le stderr du lanceur : un démarrage raté y redevient "
        f"une absence de READY, sans cause lisible")


# ── Cause 3 : le skip qui ment ───────────────────────────────────────────────

@pytest.mark.parametrize("fichier", FICHIERS_E2E)
def test_aucune_fixture_ne_saute_sur_un_harnais_casse(fichier: str) -> None:
    """La formule exacte qui a fait passer un bug pour un poste mal équipé."""
    source = (ROOT / fichier).read_text(encoding="utf-8")

    assert "Serveur Forge non disponible" not in source, (
        f"{fichier} se saute en annonçant un serveur indisponible. "
        f"L'application servie est dans le dépôt : un démarrage raté est un "
        f"défaut du harnais, et doit échouer.")
