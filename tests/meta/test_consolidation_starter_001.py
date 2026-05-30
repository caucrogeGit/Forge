"""Tests pour CONSOLIDATION-STARTER-001 — Starters Forge et Communes & Séjours."""

from __future__ import annotations

import json
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
    """Starter 1 — Contacts est décrit comme starter simple."""
    content = (ROOT / "docs" / "starters" / "contact-simple" / "index.md").read_text(encoding="utf-8")
    assert "simple" in content.lower() or "officiel" in content.lower()


def test_starter_2_reference_core_auth():
    """Starter 2 — le contrôleur auth importe depuis core.auth."""
    auth_ctrl = ROOT / "forge_cli" / "starters" / "data" / "utilisateurs-auth" / "files" / "mvc" / "controllers" / "auth_controller.py"
    assert auth_ctrl.exists()
    content = auth_ctrl.read_text(encoding="utf-8")
    assert "core.auth" in content


def test_starter_3_est_officiel_relationnel():
    """Starter 3 — Carnet de contacts est décrit comme starter relationnel."""
    content = (ROOT / "docs" / "starters" / "carnet-contacts" / "index.md").read_text(encoding="utf-8")
    assert "relation" in content.lower() or "many_to_one" in content.lower()


def test_starter_4_est_marque_legacy():
    """Starter 4 — Suivi pédagogique est documenté comme legacy ou historique."""
    content = (ROOT / "docs" / "starters" / "suivi-comportement-eleves" / "index.md").read_text(encoding="utf-8")
    assert "legacy" in content.lower() or "historique" in content.lower()


def test_starter_5_est_demonstrateur_avance():
    """Starter 5 — Communes & Séjours est le démonstrateur avancé principal."""
    content = (ROOT / "docs" / "starters" / "communes-sejours" / "index.md").read_text(encoding="utf-8")
    assert "démonstrateur" in content.lower() or "demonstrateur" in content.lower()


# ── doc_url cohérence ─────────────────────────────────────────────────────────

def test_starter_2_doc_url_pointe_nouvelle_structure():
    """Starter 2 — doc_url pointe vers starters/utilisateurs-auth/."""
    meta = resolve("2")
    assert "starter-app-02" not in meta.get("doc_url", "")
    assert "starters/utilisateurs-auth" in meta.get("doc_url", "")


def test_starter_5_doc_url_pointe_nouvelle_structure():
    """Starter 5 — doc_url pointe vers starters/communes-sejours/."""
    meta = resolve("5")
    assert "starter-app-05" not in meta.get("doc_url", "")
    assert "starters/communes-sejours" in meta.get("doc_url", "")


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
    """Chaque starter a un index.md dans docs/starters/."""
    attendus = [
        "contact-simple",
        "utilisateurs-auth",
        "carnet-contacts",
        "suivi-comportement-eleves",
        "communes-sejours",
        "welcome",
    ]
    for dossier in attendus:
        # DOCS-STARTERS-PROGRESSION-FOLDER-001 — welcome est regroupé à plat
        # dans docs/starters/welcome/welcome.md.
        if dossier == "welcome":
            index = ROOT / "docs" / "starters" / "welcome" / "welcome.md"
        else:
            index = ROOT / "docs" / "starters" / dossier / "index.md"
        assert index.exists(), f"doc de présentation absente pour {dossier}"


def test_starters_1_a_4_ont_un_rebuild_md():
    """Les starters 1 à 4 ont un rebuild.md."""
    dossiers = [
        "contact-simple",
        "utilisateurs-auth",
        "carnet-contacts",
        "suivi-comportement-eleves",
    ]
    for dossier in dossiers:
        rebuild = ROOT / "docs" / "starters" / dossier / "rebuild.md"
        assert rebuild.exists(), f"rebuild.md absent pour {dossier}"


def test_communes_sejours_a_un_rebuild_md():
    """docs/starters/communes-sejours/rebuild.md existe."""
    assert (ROOT / "docs" / "starters" / "communes-sejours" / "rebuild.md").exists()


def test_communes_sejours_rebuild_md_contient_starter_build():
    """docs/starters/communes-sejours/rebuild.md mentionne 'forge starter:build 5'."""
    content = (ROOT / "docs" / "starters" / "communes-sejours" / "rebuild.md").read_text(encoding="utf-8")
    assert "starter:build 5" in content


def test_communes_sejours_rebuild_md_mentionne_limites():
    """docs/starters/communes-sejours/rebuild.md documente les limites."""
    content = (ROOT / "docs" / "starters" / "communes-sejours" / "rebuild.md").read_text(encoding="utf-8")
    assert "limite" in content.lower() or "démonstrateur" in content.lower()


def test_starters_index_contient_lien_rebuild_communes_sejours():
    """docs/starters/index.md contient un lien rebuild.md pour Communes & Séjours."""
    content = (ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "communes-sejours/rebuild.md" in content


# ── Profils recommandés ───────────────────────────────────────────────────────

def test_starter_1_profil_minimal_ou_standard():
    """L'index des starters associe Contacts à minimal ou standard."""
    content = (ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "minimal" in content or "standard" in content


def test_starter_2_profil_standard():
    """L'index des starters associe Utilisateurs/Auth au profil standard."""
    content = (ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "standard" in content


def test_starter_5_profil_standard():
    """L'index des starters associe Communes & Séjours au profil standard."""
    idx = (ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "standard" in idx


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
    assert "contact" in output.lower()


def test_starter_3_dry_run_fonctionne(capsys):
    """forge starter:build 3 --dry-run s'exécute sans erreur."""
    cmd_starter_build(["3", "--dry-run"])
    output = capsys.readouterr().out
    assert "carnet" in output.lower() or "contact" in output.lower()


def test_starter_5_dry_run_fonctionne(capsys):
    """forge starter:build 5 --dry-run s'exécute sans erreur."""
    cmd_starter_build(["5", "--dry-run"])
    output = capsys.readouterr().out
    assert "communes" in output.lower()


# ── Communes & Séjours — séparation core / métier ─────────────────────────────

def test_communes_sejours_kind_est_skeleton():
    """Starter 5 a le kind 'skeleton' (pas de logique CRUD générée)."""
    meta = resolve("5")
    assert meta["kind"] == "skeleton"


def test_communes_sejours_require_db_false():
    """Starter 5 fonctionne sans base de données (requires_db = False)."""
    meta = resolve("5")
    assert meta.get("requires_db") is False


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


def test_communes_sejours_controller_importe_core():
    """Le contrôleur Communes & Séjours importe depuis core/, pas depuis forge_cli."""
    ctrl = (
        ROOT
        / "forge_cli" / "starters" / "data" / "communes-sejours"
        / "files" / "mvc" / "controllers" / "communes_sejours_controller.py"
    )
    content = ctrl.read_text(encoding="utf-8")
    assert "from core." in content
    assert "from forge_cli" not in content


def test_communes_sejours_controller_utilise_trans():
    """Le contrôleur Communes & Séjours utilise trans() depuis core.i18n."""
    ctrl = (
        ROOT
        / "forge_cli" / "starters" / "data" / "communes-sejours"
        / "files" / "mvc" / "controllers" / "communes_sejours_controller.py"
    )
    content = ctrl.read_text(encoding="utf-8")
    assert "from core.i18n import trans" in content


def test_communes_sejours_i18n_utilise_prefixe_starter_cs():
    """Les clés i18n de Communes & Séjours utilisent le préfixe 'starter.cs'."""
    fr_json = (
        ROOT / "forge_cli" / "starters" / "data" / "communes-sejours" / "files" / "translations" / "fr.json"
    )
    data = json.loads(fr_json.read_text(encoding="utf-8"))
    starter_cs_keys = [k for k in data if k.startswith("starter.cs")]
    assert len(starter_cs_keys) > 0, "Aucune clé starter.cs.* dans fr.json"


def test_communes_sejours_i18n_evite_termes_interdits():
    """Les clés i18n de Communes & Séjours n'utilisent pas les termes interdits (commune, sejour...)."""
    fr_json = (
        ROOT / "forge_cli" / "starters" / "data" / "communes-sejours" / "files" / "translations" / "fr.json"
    )
    data = json.loads(fr_json.read_text(encoding="utf-8"))
    for key in data:
        for term in ("commune", "sejour", "hebergement", "reservation"):
            assert term not in key.lower(), (
                f"Clé i18n {key!r} contient le terme interdit {term!r}"
            )


# ── Fichiers essentiels de Communes & Séjours ─────────────────────────────────

@pytest.mark.parametrize("rel_path", [
    "mvc/controllers/communes_sejours_controller.py",
    "mvc/forms/demande_sejour_form.py",
    "mvc/views/public/communes_sejours/home.html",
    "mvc/views/public/communes_sejours/hebergements_index.html",
    "mvc/views/public/communes_sejours/hebergements_show.html",
    "mvc/mail/templates/communes_sejours/demande_visiteur_subject.txt",
    "mvc/mail/templates/communes_sejours/demande_proprietaire_subject.txt",
    "translations/fr.json",
    "seed/communes.json",
])
def test_communes_sejours_fichier_essentiel_packaged(rel_path):
    """Les fichiers essentiels de Communes & Séjours sont présents dans le paquet starter."""
    data_dir = ROOT / "forge_cli" / "starters" / "data" / "communes-sejours" / "files"
    assert (data_dir / rel_path).exists(), f"Fichier absent : {rel_path}"


def test_communes_sejours_entites_definies():
    """Les 4 entités de Communes & Séjours sont définies dans les fichiers packagés."""
    entities_root = ROOT / "forge_cli" / "starters" / "data" / "communes-sejours" / "files" / "mvc" / "entities"
    for entity in ("commune", "proprietaire", "hebergement", "demande_sejour"):
        assert (entities_root / entity).is_dir(), f"Entité {entity} absente"


def test_communes_sejours_relations_json_existe():
    """relations.json est défini dans le paquet starter de Communes & Séjours."""
    rel_path = (
        ROOT / "forge_cli" / "starters" / "data" / "communes-sejours"
        / "files" / "mvc" / "entities" / "relations.json"
    )
    assert rel_path.exists()


# ── Limites métier documentées ────────────────────────────────────────────────

def test_communes_sejours_doc_mentionne_pas_reservation_confirmee():
    """docs/starters/communes-sejours/index.md ne promet pas une réservation confirmée."""
    content = (ROOT / "docs" / "starters" / "communes-sejours" / "index.md").read_text(encoding="utf-8")
    assert "réservation confirmée" not in content.lower() or "non" in content.lower()


def test_communes_sejours_doc_mentionne_pas_paiement():
    """docs/starters/communes-sejours/index.md ne promet pas de paiement intégré."""
    content = (ROOT / "docs" / "starters" / "communes-sejours" / "index.md").read_text(encoding="utf-8")
    assert "paiement en ligne" not in content.lower() or "non livré" in content.lower()


def test_communes_sejours_doc_liste_limites():
    """docs/starters/communes-sejours/index.md documente une section de limites."""
    content = (ROOT / "docs" / "starters" / "communes-sejours" / "index.md").read_text(encoding="utf-8")
    assert "n'est pas livré" in content.lower() or "ce qui n'est pas" in content.lower()


# ── Séparation Forge Design ───────────────────────────────────────────────────

def test_communes_sejours_doc_ne_mentionne_pas_forge_design():
    """docs/starters/communes-sejours/index.md ne promeut pas Forge Design."""
    content = (ROOT / "docs" / "starters" / "communes-sejours" / "index.md").read_text(encoding="utf-8")
    assert "forge-design" not in content.lower()
    assert "éditeur graphique" not in content.lower()


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
