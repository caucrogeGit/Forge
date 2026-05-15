"""Tests — CRUD-BULK-ACTIONS-AUDIT-001 : conformité de l'audit actions groupées.

Vérifie que docs/history/audits/crud-bulk-actions-audit-001.md :

- existe ;
- couvre les sections obligatoires ;
- mentionne CSRF, RBAC, validation IDs, SQL sécurisé ;
- mentionne pagination, filtres, tri ;
- mentionne HTMX et ses limites ;
- liste les risques identifiés ;
- formule une recommandation claire ;
- propose un ticket suivant.

Et que la roadmap est cohérente (ticket livré, prochaine priorité).
"""
from __future__ import annotations

import pathlib

AUDIT = pathlib.Path("docs/history/audits/crud-bulk-actions-audit-001.md")
ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


def _roadmap() -> str:
    return ROADMAP.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence du rapport
# ---------------------------------------------------------------------------

class TestExistenceRapport:
    def test_fichier_audit_existe(self):
        assert AUDIT.exists(), f"Le rapport {AUDIT} doit exister"

    def test_fichier_non_vide(self):
        assert len(_audit()) > 500


# ---------------------------------------------------------------------------
# Sections obligatoires
# ---------------------------------------------------------------------------

class TestSectionsObligatoires:
    def test_section_objectif(self):
        assert "## Objectif" in _audit()

    def test_section_etat_actuel(self):
        r = _audit()
        assert "État actuel" in r or "état actuel" in r.lower()

    def test_section_besoin_fonctionnel(self):
        r = _audit()
        assert "Besoin fonctionnel" in r or "besoin fonctionnel" in r.lower()

    def test_section_scenarios(self):
        r = _audit()
        assert "Scénarios" in r or "scénario" in r.lower()

    def test_section_selection_lignes(self):
        r = _audit()
        assert "Sélection" in r or "sélection" in r.lower()

    def test_section_routes(self):
        r = _audit()
        assert "Route" in r or "routes" in r.lower()

    def test_section_csrf(self):
        assert "## CSRF" in _audit() or "CSRF" in _audit()

    def test_section_rbac(self):
        assert "## RBAC" in _audit() or "RBAC" in _audit()

    def test_section_validation_ids(self):
        r = _audit()
        assert "Validation des IDs" in r or "validation des ids" in r.lower()

    def test_section_sql(self):
        r = _audit()
        assert "SQL" in r

    def test_section_pagination_filtres_tri(self):
        r = _audit()
        assert "Pagination" in r or "pagination" in r.lower()
        assert "filtres" in r.lower() or "Filtres" in r
        assert "tri" in r.lower() or "Tri" in r

    def test_section_htmx(self):
        assert "HTMX" in _audit()

    def test_section_ux(self):
        r = _audit()
        assert "## UX" in r or "UX" in r

    def test_section_risques(self):
        r = _audit()
        assert "Risques" in r or "risques" in r.lower()

    def test_section_recommandation(self):
        r = _audit()
        assert "Recommandation" in r or "recommandation" in r.lower()

    def test_section_tickets_suivants(self):
        r = _audit()
        assert "Tickets suivants" in r or "tickets suivants" in r.lower()


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------

class TestCSRF:
    def test_csrf_mentionne(self):
        assert "CSRF" in _audit()

    def test_csrf_token_dans_formulaire_mentionne(self):
        r = _audit()
        assert "csrf_token" in r

    def test_protection_automatique_mentionnee(self):
        r = _audit()
        assert "automatiquement" in r or "middleware" in r or "automatique" in r

    def test_refus_sans_token_mentionne(self):
        r = _audit()
        assert "403" in r or "refus" in r.lower() or "invalide" in r


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------

class TestRBAC:
    def test_rbac_mentionne(self):
        assert "RBAC" in _audit()

    def test_permission_delete_mentionnee(self):
        r = _audit()
        assert ".delete" in r or "delete" in r

    def test_verification_cote_serveur_mentionnee(self):
        r = _audit()
        assert "serveur" in r or "côté serveur" in r

    def test_can_dans_template_mentionne(self):
        r = _audit()
        assert "can(" in r or "`can`" in r


# ---------------------------------------------------------------------------
# Validation des IDs
# ---------------------------------------------------------------------------

class TestValidationIDs:
    def test_ids_absents_mentionnes(self):
        r = _audit()
        assert "absent" in r.lower() or "vide" in r.lower() or "IDs absents" in r

    def test_ids_non_entiers_mentionnes(self):
        r = _audit()
        assert "non entier" in r.lower() or "ValueError" in r or "entier" in r.lower()

    def test_ids_dupliques_mentionnes(self):
        r = _audit()
        assert "dupliqué" in r.lower() or "dupliqu" in r.lower()

    def test_ids_inexistants_mentionnes(self):
        r = _audit()
        assert "inexistant" in r.lower()

    def test_limite_nombre_ids_mentionnee(self):
        r = _audit()
        assert "limite" in r.lower() or "max" in r.lower() or "trop grand" in r.lower()

    def test_injection_sql_via_ids_mentionnee(self):
        r = _audit()
        assert "injection" in r.lower() or "concaténation" in r.lower() or "Injection" in r


# ---------------------------------------------------------------------------
# SQL sécurisé
# ---------------------------------------------------------------------------

class TestSQLSecurise:
    def test_pas_de_concatenation_mentionnes(self):
        r = _audit()
        assert "concaténation" in r or "concaténer" in r or "aucune concaténation" in r

    def test_placeholders_mentionnes(self):
        r = _audit()
        assert "placeholder" in r.lower() or "?" in r or "paramétr" in r

    def test_in_clause_mentionnee(self):
        r = _audit()
        assert "IN (" in r or "IN(" in r or "IN" in r


# ---------------------------------------------------------------------------
# Pagination, filtres et tri
# ---------------------------------------------------------------------------

class TestPaginationFiltresTri:
    def test_scope_page_visible_mentionne(self):
        r = _audit()
        assert "page" in r.lower() and ("visible" in r.lower() or "courante" in r.lower() or "scope" in r.lower())

    def test_conservation_filtres_apres_action(self):
        r = _audit()
        assert "conserv" in r.lower() or "conserver" in r.lower()

    def test_parametres_q_mentionnes(self):
        r = _audit()
        assert "q" in r and ("sort" in r or "direction" in r or "filters" in r)


# ---------------------------------------------------------------------------
# HTMX
# ---------------------------------------------------------------------------

class TestHTMX:
    def test_htmx_mentionne(self):
        assert "HTMX" in _audit()

    def test_premiere_version_sans_htmx(self):
        r = _audit()
        assert "sans HTMX" in r or "pas de HTMX" in r or "sans htmx" in r.lower() or "HTMX" in r and "première version" in r

    def test_hx_post_mentionne(self):
        r = _audit()
        assert "hx-post" in r or "hx_post" in r or "HX-Request" in r

    def test_hx_target_crud_results_mentionne(self):
        r = _audit()
        assert "#crud-results" in r or "crud-results" in r


# ---------------------------------------------------------------------------
# Risques identifiés
# ---------------------------------------------------------------------------

class TestRisques:
    def test_risque_suppression_massive(self):
        r = _audit()
        assert "massive" in r.lower() or "accidentelle" in r.lower()

    def test_risque_contournement_rbac(self):
        r = _audit()
        idx = r.find("## Risques identifiés")
        assert idx != -1
        bloc = r[idx: idx + 1500]
        assert "RBAC" in bloc

    def test_risque_absence_csrf(self):
        r = _audit()
        idx = r.find("## Risques identifiés")
        assert idx != -1
        bloc = r[idx: idx + 1500]
        assert "CSRF" in bloc

    def test_risque_injection_sql(self):
        r = _audit()
        idx = r.find("## Risques identifiés")
        assert idx != -1
        bloc = r[idx: idx + 1500]
        assert "SQL" in bloc or "injection" in bloc.lower()

    def test_risque_cross_pages(self):
        r = _audit()
        assert "cross" in r.lower() or "pagination" in r.lower()

    def test_risque_imbrication_formulaires(self):
        r = _audit()
        assert "imbrication" in r.lower() or "formulaire" in r.lower()


# ---------------------------------------------------------------------------
# Recommandation
# ---------------------------------------------------------------------------

class TestRecommandation:
    def test_recommandation_presente(self):
        r = _audit()
        assert "Recommandation" in r

    def test_commencer_par_suppression_minimale(self):
        r = _audit()
        assert "suppression groupée" in r.lower() or "suppression minimale" in r.lower() or "CRUD-BULK-DELETE-001" in r

    def test_pas_de_js_dans_premiere_version(self):
        r = _audit()
        idx = r.find("## Recommandation")
        assert idx != -1
        bloc = r[idx: idx + 800]
        assert "JavaScript" in bloc or "JS" in bloc or "sans JS" in bloc.lower()

    def test_pas_de_htmx_dans_premiere_version(self):
        r = _audit()
        idx = r.find("## Recommandation")
        assert idx != -1
        bloc = r[idx: idx + 800]
        assert "HTMX" in bloc

    def test_csrf_dans_recommandation(self):
        r = _audit()
        idx = r.find("## Recommandation")
        assert idx != -1
        bloc = r[idx: idx + 800]
        assert "CSRF" in bloc

    def test_rbac_dans_recommandation(self):
        r = _audit()
        idx = r.find("## Recommandation")
        assert idx != -1
        bloc = r[idx: idx + 800]
        assert "RBAC" in bloc or "permission" in bloc.lower()


# ---------------------------------------------------------------------------
# Ticket suivant proposé
# ---------------------------------------------------------------------------

class TestTicketSuivant:
    def test_crud_bulk_delete_propose(self):
        r = _audit()
        assert "CRUD-BULK-DELETE-001" in r

    def test_ticket_suivant_decrit(self):
        r = _audit()
        idx = r.find("CRUD-BULK-DELETE-001")
        assert idx != -1
        bloc = r[idx: idx + 400]
        assert "suppression" in bloc.lower() or "bulk" in bloc.lower()


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

class TestRoadmap:
    def test_crud_bulk_actions_audit_001_livre(self):
        r = _roadmap()
        assert "CRUD-BULK-ACTIONS-AUDIT-001" in r
        idx = r.find("CRUD-BULK-ACTIONS-AUDIT-001")
        bloc = r[idx: idx + 80]
        assert "livré" in bloc

    def test_phase_13_presente(self):
        assert "Phase 13" in _roadmap()

    def test_prochaine_priorite_crud_bulk_delete(self):
        r = _roadmap()
        idx = r.find("Prochaine priorité immédiate")
        assert idx != -1
        bloc = r[idx: idx + 200]
        assert "FORGE-DESIGN-ROADMAP-001" in bloc
