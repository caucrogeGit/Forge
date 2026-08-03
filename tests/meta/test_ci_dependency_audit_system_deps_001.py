"""CI-DEPAUDIT-SYSTEM-DEPS-001 : l'audit hebdomadaire peut réellement s'exécuter.

`RELEASE-AUDIT-SHIPPED-SURFACE-001` a élargi l'audit à la surface expédiée,
`mariadb` compris. Ce paquet est distribué en source seule et réclame
`mariadb_config`, fourni par `libmariadb-dev`. Le runner ne l'avait pas, si bien
que pip échouait à lire les métadonnées et que `pip-audit` s'arrêtait **avant
d'auditer quoi que ce soit**.

Les trois pas d'audit portent `continue-on-error: true`, par choix : une CVE
transitoire ne doit pas masquer les autres rapports. La conséquence est qu'un
audit qui ne démarre pas ressemble trait pour trait à un audit sans découverte.

Ce qui a révélé la panne est le pas bloquant, `check_ignored_vulns.py`, dont le
rôle est de dire le jour où un avis exclu reçoit un correctif amont. Tant que le
workflow ne démarre pas, cette surveillance est éteinte, et une exclusion peut
survivre à sa raison d'être sans que personne ne le sache.

Ce garde tient le pas système tant que la surface auditée contient un paquet qui
en dépend. Il ne devine pas ces paquets : la table ci-dessous est écrite à la
main, parce que « ce paquet réclame telle bibliothèque système » est un fait sur
le paquet, que rien dans le dépôt ne permet de déduire.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "dependency-audit.yml"
SURFACE = PROJECT_ROOT / "requirements-audit.txt"

#: Paquets distribués en source seule, et la bibliothèque système qu'ils exigent
#: pour que pip puisse seulement lire leurs métadonnées.
#:
#: - `mariadb` : réclame `mariadb_config`, livré par `libmariadb-dev`. C'est le
#:   cas mesuré, le 2026-08-03, au premier passage hebdomadaire après
#:   l'élargissement de la surface auditée.
PAQUETS_A_DEPENDANCE_SYSTEME = {
    "mariadb": "libmariadb-dev",
}


def _surface() -> str:
    return SURFACE.read_text(encoding="utf-8")


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _declare(paquet: str) -> bool:
    """Dit si la surface auditée déclare `paquet` comme dépendance."""
    return bool(re.search(rf"^{re.escape(paquet)}[><=~!\s]", _surface(), re.MULTILINE))


# ── Le cas mesuré ────────────────────────────────────────────────────────────

@pytest.mark.parametrize(("paquet", "bibliotheque"),
                         sorted(PAQUETS_A_DEPENDANCE_SYSTEME.items()))
def test_le_workflow_pose_ce_que_la_surface_exige(paquet: str, bibliotheque: str) -> None:
    """Sans ce pas, pip-audit s'arrête avant d'auditer."""
    if not _declare(paquet):
        pytest.skip(f"{paquet} ne fait plus partie de la surface auditée")

    assert bibliotheque in _workflow(), (
        f"`requirements-audit.txt` déclare `{paquet}`, qui exige `{bibliotheque}` "
        f"pour que pip lise seulement ses métadonnées. "
        f"`{WORKFLOW.name}` ne l'installe pas : l'audit hebdomadaire échouera "
        f"avant d'auditer quoi que ce soit.")


def test_les_dependances_systeme_precedent_l_audit() -> None:
    """Un pas juste, mais placé après, ne sert à rien."""
    texte = _workflow()

    assert texte.index("apt-get install") < texte.index("pip-audit -r")


def test_le_pas_bloquant_survit() -> None:
    """C'est lui qui a rendu la panne visible.

    S'il repassait en `continue-on-error`, le workflow redeviendrait vert en
    n'auditant rien, exactement l'état qui a tenu jusqu'au 2026-08-03.
    """
    texte = _workflow()
    bloquant = texte[texte.index("check_ignored_vulns.py"):]

    assert "continue-on-error" not in bloquant


def test_les_trois_audits_restent_non_bloquants() -> None:
    """Contre-épreuve : le choix d'origine n'est pas ce qu'on corrige ici.

    Une CVE transitoire sur une dépendance non encore corrigée amont ne doit pas
    masquer les autres rapports. Le garde release, lui, reste dans
    `tools/release-validate.sh`, où les mêmes commandes sont bloquantes.

    Compté sur les pas seuls, jamais sur le texte entier : l'en-tête du workflow
    cite la clé pour expliquer le choix, et un simple `count` la comptait.
    """
    pas = [ligne for ligne in _workflow().splitlines()
           if ligne.strip() == "continue-on-error: true"]

    assert len(pas) == 3


def test_la_table_dit_pourquoi() -> None:
    """Une entrée sans motif écrit se transforme en trou silencieux."""
    source = Path(__file__).read_text(encoding="utf-8")
    bloc = source[source.index("#: Paquets distribués"):
                  source.index("PAQUETS_A_DEPENDANCE_SYSTEME = {")]

    for paquet in PAQUETS_A_DEPENDANCE_SYSTEME:
        assert f"`{paquet}`" in bloc
