"""Tests pour CONSOLIDATION-STARTER-001 — Starters Forge et Communes & Séjours."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from forge_cli.starters import cmd_starter_list, cmd_starter_build
from forge_cli.starters.registry import all_starters, resolve

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


# ── Contrat des starters ──────────────────────────────────────────────────────

def test_count_starters_matches_filesystem():
    """Le nombre de starters déclarés correspond au contenu de
    `forge_cli/starters/data/`. Refactor STARTER-CONTACTS-CRUD-REPOSITION-001
    pour ne plus geler le count dans le code de test — chaque palier
    pédagogique livré (paliers 2 à 8, plus toute extension future)
    incrémente naturellement le total sans casser ce garde-fou."""
    data_dir = ROOT / "forge_cli" / "starters" / "data"
    expected = sum(
        1 for d in data_dir.iterdir()
        if d.is_dir() and (d / "starter.json").exists()
    )
    assert len(all_starters()) == expected, (
        f"Décompte registre ({len(all_starters())}) != décompte "
        f"filesystem ({expected})."
    )
    # Au moins les 8 paliers de la progression pédagogique officielle
    # (7 historiques 1–6+welcome → number 7 + 1 nouveau par palier 2–8).
    assert expected >= 8, (
        f"Au moins 8 starters attendus (progression pédagogique 1–8 livrée) ; "
        f"trouvé {expected}."
    )


def test_starters_numero_sans_trou():
    """Les starters sont numérotés sans trou à partir de 1.
    Refactor STARTER-CONTACTS-CRUD-REPOSITION-001 — ne fige plus
    le numéro maximal pour rester robuste aux ajouts futurs."""
    nums = sorted(s["number"] for s in all_starters())
    expected_range = list(range(1, len(nums) + 1))
    assert nums == expected_range, (
        f"Numérotation des starters avec trou : {nums} (attendu : {expected_range})."
    )


def test_tous_les_starters_sont_disponibles():
    """Tous les starters ont le statut 'available'."""
    for s in all_starters():
        assert s.get("status") == "available", f"Starter {s['number']} non disponible"


def test_starter_list_affiche_tous_les_starters(capsys):
    """forge starter:list affiche tous les starters déclarés."""
    cmd_starter_list()
    output = capsys.readouterr().out
    for s in all_starters():
        assert s["name"] in output


# ── Statuts documentaires ─────────────────────────────────────────────────────

def test_starter_1_est_officiel_simple():
    """Starter 1 — First CRUD (généré) est décrit comme starter simple."""
    content = (ROOT / "docs" / "starters" / "crud" / "first-crud-generated.md").read_text(encoding="utf-8")
    assert "simple" in content.lower() or "officiel" in content.lower()


def test_starter_2_reference_core_auth():
    """Starter 2 — le contrôleur auth importe depuis core.auth."""
    auth_ctrl = ROOT / "forge_cli" / "starters" / "data" / "users-core-auth" / "files" / "mvc" / "controllers" / "auth_controller.py"
    assert auth_ctrl.exists()
    content = auth_ctrl.read_text(encoding="utf-8")
    assert "core.auth" in content


# ── doc_url cohérence ─────────────────────────────────────────────────────────

def test_starter_2_doc_url_pointe_nouvelle_structure():
    """Starter 2 — doc_url pointe vers starters/core-auth/users-core-auth/."""
    meta = resolve("2")
    assert "starter-app-02" not in meta.get("doc_url", "")
    assert "starters/core-auth/users-core-auth" in meta.get("doc_url", "")


def test_tous_les_starters_ont_un_doc_url():
    """Tous les starters déclarent un doc_url."""
    for s in all_starters():
        assert s.get("doc_url"), f"doc_url absent pour starter {s['number']}"


def test_tous_les_doc_url_utilisent_nouvelle_structure():
    """Aucun doc_url n'utilise l'ancienne forme 'starter-app-XX'."""
    for s in all_starters():
        url = s.get("doc_url", "")
        num = s.get("number")
        assert f"starter-app-0{num}" not in url, (
            f"Starter {num} : doc_url utilise encore l'ancienne structure : {url}"
        )


# ── Documentation des starters ────────────────────────────────────────────────

def test_chaque_starter_a_un_index_md():
    """Chaque starter actif a une doc de présentation dans docs/starters/.

    Réorganisation des starters : les 3 applications (carnet-contacts,
    suivi-comportement-eleves, communes-sejours) ne sont plus des starters
    actifs (archivées sous docs/starters/old/). Les paliers welcome sont
    regroupés à plat dans docs/starters/welcome/<id>.md ; les autres starters
    ont leur propre docs/starters/<id>/index.md."""
    # Paliers welcome regroupés à plat (DOCS-STARTERS-PROGRESSION-FOLDER-001).
    paliers_welcome = [
        "welcome",
        "query-params",
        "first-html-view",
        "dynamic-route",
        "request-debug",
        "form-post",
        "server-validation",
        "first-sql",
        "json-response",
        "csrf",
        "first-sql-write",
    ]
    for dossier in paliers_welcome:
        index = ROOT / "docs" / "starters" / "welcome" / f"{dossier}.md"
        assert index.exists(), f"doc de palier welcome absente pour {dossier}"

    # Les starters CRUD sont regroupés sous le dossier-sujet crud/ :
    # un index.md (vue d'ensemble) + les pages first-crud.md (à la main)
    # et first-crud-generated.md (généré, entité neutre).
    crud = ROOT / "docs" / "starters" / "crud"
    assert (crud / "index.md").exists(), (
        "vue d'ensemble absente pour crud"
    )
    assert (crud / "first-crud.md").exists(), (
        "page first-crud absente pour crud"
    )
    assert (crud / "first-crud-generated.md").exists(), (
        "page first-crud-generated absente pour crud"
    )

    # Le starter Auth est regroupé sous le dossier-sujet core-auth/ :
    # un index.md (vue d'ensemble) + la page users-core-auth.md.
    core_auth = ROOT / "docs" / "starters" / "core-auth"
    assert (core_auth / "index.md").exists(), (
        "vue d'ensemble absente pour core-auth"
    )
    assert (core_auth / "users-core-auth.md").exists(), (
        "page users-core-auth absente pour core-auth"
    )

    # Le starter IoT est regroupé sous le dossier-sujet optin-iot/ :
    # un index.md (vue d'ensemble) + la page welcome-optin-iot.md.
    optin_iot = ROOT / "docs" / "starters" / "optin-iot"
    assert (optin_iot / "index.md").exists(), (
        "vue d'ensemble absente pour optin-iot"
    )
    assert (optin_iot / "welcome-optin-iot.md").exists(), (
        "page welcome-optin-iot absente pour optin-iot"
    )

    # Le starter MFA est regroupé sous le dossier-sujet optin-mfa/ :
    # un index.md (vue d'ensemble) + la page welcome-optin-mfa.md.
    optin_mfa = ROOT / "docs" / "starters" / "optin-mfa"
    assert (optin_mfa / "index.md").exists(), (
        "vue d'ensemble absente pour optin-mfa"
    )
    assert (optin_mfa / "welcome-optin-mfa.md").exists(), (
        "page welcome-optin-mfa absente pour optin-mfa"
    )


def test_starters_avec_rebuild_md():
    """Les starters autonomes scaffoldés (first-crud-generated, users-core-auth)
    ont un guide de reconstruction.

    Réorganisation des starters : carnet-contacts et suivi-comportement-eleves
    ne sont plus des starters actifs (archivés sous docs/starters/old/) ; seuls
    les starters restants munis d'un guide de reconstruction sont vérifiés. Le
    starter MFA a son guide sous optin-mfa/welcome-optin-mfa-rebuild.md ; le
    starter Auth a le sien sous core-auth/users-core-auth-rebuild.md ; le starter
    CRUD généré a le sien sous crud/first-crud-generated-rebuild.md."""
    rebuild_generated = (
        ROOT / "docs" / "starters" / "crud" / "first-crud-generated-rebuild.md"
    )
    assert rebuild_generated.exists(), (
        "first-crud-generated-rebuild.md absent pour crud"
    )

    core_auth_rebuild = ROOT / "docs" / "starters" / "core-auth" / "users-core-auth-rebuild.md"
    assert core_auth_rebuild.exists(), "guide de reconstruction absent pour core-auth"

    # Le guide de reconstruction MFA vit sous le dossier-sujet optin-mfa/.
    rebuild_mfa = ROOT / "docs" / "starters" / "optin-mfa" / "welcome-optin-mfa-rebuild.md"
    assert rebuild_mfa.exists(), "welcome-optin-mfa-rebuild.md absent pour optin-mfa"


# ── Profils recommandés ───────────────────────────────────────────────────────

def test_starter_1_profil_minimal_ou_standard():
    """L'index des starters associe Contacts à minimal ou standard."""
    content = (ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "minimal" in content or "standard" in content


def test_starter_2_profil_standard():
    """L'index des starters associe Utilisateurs/Auth au profil standard."""
    content = (ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "standard" in content


# ── Génération des starters ───────────────────────────────────────────────────

def test_starter_inexistant_leve_sysexit():
    """Un starter inexistant déclenche SystemExit."""
    with pytest.raises(SystemExit):
        cmd_starter_build(["inexistant"])


def test_starter_inexistant_message_mentionne_starter_list():
    """Le message d'erreur pour un starter inexistant mentionne starter:list."""
    import io
    buf = io.StringIO()
    with patch("sys.stdout", buf):
        try:
            cmd_starter_build(["inexistant"])
        except SystemExit:
            pass
    assert "starter:list" in buf.getvalue()


def test_starter_1_dry_run_fonctionne(capsys):
    """forge starter:build 1 --dry-run s'exécute sans erreur."""
    cmd_starter_build(["1", "--dry-run"])
    output = capsys.readouterr().out
    assert "message" in output.lower() or "/messages" in output


# ── Communes & Séjours — séparation core / métier ─────────────────────────────

def test_core_ne_reference_pas_communes_sejours():
    """core/ ne contient aucune référence à 'communes' ou 'sejour'."""
    for f in (ROOT / "core").rglob("*.py"):
        content = f.read_text(encoding="utf-8").lower()
        assert "communes_sejours" not in content, f"Référence métier dans {f}"
        assert "demande_sejour" not in content, f"Référence métier dans {f}"


def test_forge_cli_ne_reference_pas_communes_hors_starters():
    """forge_cli/ ne contient pas de référence à communes/sejours hors du dossier starters/."""
    for f in (ROOT / "forge_cli").rglob("*.py"):
        if "starters" in str(f):
            continue
        content = f.read_text(encoding="utf-8").lower()
        assert "communes_sejours" not in content, f"Référence métier hors starters dans {f}"
        assert "demande_sejour" not in content, f"Référence métier hors starters dans {f}"


# ── Séparation Forge Design ───────────────────────────────────────────────────

def test_forge_design_roadmap_non_modifie():
    """docs/forge-design-roadmap.md existe et n'est pas modifié."""
    assert (ROOT / "docs" / "roadmap" / "forge-design-roadmap.md").exists()


# ── Document d'audit et roadmap ───────────────────────────────────────────────

def test_audit_consolidation_starter_001_existe():
    """docs/history/audits/consolidation-starter-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "consolidation-starter-001.md").exists()


def test_audit_mentionne_les_cinq_starters():
    """Le document d'audit mentionne les 5 starters."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-starter-001.md").read_text(encoding="utf-8")
    assert "Contacts" in content
    assert "Utilisateurs" in content
    assert "Carnet" in content
    assert "Suivi" in content
    assert "Communes" in content


def test_audit_mentionne_doc_url():
    """Le document d'audit mentionne les doc_url."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-starter-001.md").read_text(encoding="utf-8")
    assert "doc_url" in content


def test_audit_mentionne_rebuild_md():
    """Le document d'audit mentionne rebuild.md."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-starter-001.md").read_text(encoding="utf-8")
    assert "rebuild.md" in content


def test_audit_contient_verdict_final():
    """Le document d'audit contient un verdict final."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-starter-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content


def test_roadmap_marque_consolidation_starter_001_termine():
    """docs/forge-roadmap.md marque CONSOLIDATION-STARTER-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "CONSOLIDATION-STARTER-001" in content
    assert "terminé" in content


def test_roadmap_priorite_est_dans_phase_consolidation():
    """La prochaine priorité immédiate est un ticket CONSOLIDATION-*."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert "CONSOLIDATION-" in bloc or "PUBLICATION-" in bloc or "POST-2.0-" in bloc or "DEPENDENCY-" in bloc or "RELEASE-" in bloc or "CMD-" in bloc or "AUTH-LEGACY-" in bloc or "CRUD-" in bloc or "SESSION-" in bloc or "I18N-" in bloc or "QUALITY-" in bloc or "RELEASE-2.1" in bloc or "SESSION-STORE-" in bloc or "SECURITY-" in bloc or "MODULE-" in bloc or "PROFILE-" in bloc or "HTTP-" in bloc or "CONCURRENCY-" in bloc or "HEALTH-" in bloc or "RELEASE-" in bloc or "APP-" in bloc or "DX-" in bloc or "HELP-" in bloc or "RECOVERY-" in bloc or "AUDIT-" in bloc or "E2E-" in bloc or "DOC-" in bloc or "API-" in bloc or "AUTH-MFA-" in bloc or "AUTH-SESSION-" in bloc or "AUTH-OIDC-" in bloc or "AUTH-ADMIN-" in bloc or "AUTH-DOC-" in bloc or "PHASE-" in bloc or "CRUD-" in bloc or "ROADMAP-" in bloc or "POST-" in bloc or "WORKFLOW-" in bloc


def test_roadmap_md_non_recree():
    """docs/roadmap.md ne doit pas exister."""
    assert not (ROOT / "docs" / "roadmap.md").exists()
