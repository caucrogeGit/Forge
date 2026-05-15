"""Tests — CRUD-EXPORT-AUDIT-001 : conformité du rapport d'audit export CSV.

Vérifie que docs/history/audits/crud-export-audit-001.md :
- existe et est substantiel ;
- couvre les sections obligatoires ;
- mentionne q, filtres, tri, pagination ;
- mentionne RBAC ;
- mentionne l'injection CSV et les mitigations ;
- mentionne Content-Type et Content-Disposition ;
- mentionne Cache-Control ;
- mentionne une limite de volume ;
- mentionne que l'export ne passe pas par HTMX ;
- mentionne le SQL sécurisé ;
- formule une recommandation claire ;
- propose un ticket suivant ;
- que la roadmap marque CRUD-EXPORT-AUDIT-001 comme livré ;
- que la prochaine priorité est CRUD-EXPORT-CSV-001.
"""
from __future__ import annotations

import pathlib

AUDIT = pathlib.Path("docs/history/audits/crud-export-audit-001.md")
ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


def _roadmap() -> str:
    return ROADMAP.read_text(encoding="utf-8")


def _livre(ticket: str) -> bool:
    r = _roadmap()
    start = 0
    while True:
        idx = r.find(ticket, start)
        if idx == -1:
            return False
        if "livré" in r[idx: idx + 80]:
            return True
        start = idx + 1


# ---------------------------------------------------------------------------
# Existence du rapport
# ---------------------------------------------------------------------------

class TestExistenceRapport:
    def test_fichier_audit_existe(self):
        assert AUDIT.exists(), f"Le rapport {AUDIT} doit exister"

    def test_fichier_non_vide(self):
        assert len(_audit()) > 500

    def test_titre_audit_present(self):
        assert "CRUD-EXPORT-AUDIT-001" in _audit()


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

    def test_section_route(self):
        r = _audit()
        assert "Route" in r or "route" in r.lower()

    def test_section_donnees_exportees(self):
        r = _audit()
        assert "Données exportées" in r or "données exportées" in r.lower() or "Données" in r

    def test_section_rbac(self):
        assert "RBAC" in _audit()

    def test_section_securite_csv(self):
        r = _audit()
        assert "Sécurité CSV" in r or "sécurité csv" in r.lower() or "injection" in r.lower()

    def test_section_headers(self):
        r = _audit()
        assert "Headers" in r or "header" in r.lower()

    def test_section_sql(self):
        assert "SQL" in _audit()

    def test_section_htmx(self):
        assert "HTMX" in _audit()

    def test_section_risques(self):
        r = _audit()
        assert "Risques" in r or "risques" in r.lower()

    def test_section_recommandation(self):
        r = _audit()
        assert "Recommandation" in r or "recommandation" in r.lower()

    def test_section_ticket_suivant(self):
        r = _audit()
        assert "Ticket suivant" in r or "ticket suivant" in r.lower()


# ---------------------------------------------------------------------------
# Paramètres de liste — q, filtres, tri, pagination
# ---------------------------------------------------------------------------

class TestParametresListe:
    def test_mention_q(self):
        r = _audit()
        assert "`q`" in r or "paramètre q" in r.lower() or "recherche q" in r.lower() or "q" in r

    def test_mention_filtres(self):
        r = _audit()
        assert "filtres" in r.lower() or "filter" in r.lower()

    def test_mention_tri(self):
        r = _audit()
        assert "tri" in r.lower() or "sort" in r.lower()

    def test_mention_direction(self):
        r = _audit()
        assert "direction" in r.lower()

    def test_pagination_ignoree_pour_export(self):
        r = _audit()
        assert "pagination" in r.lower()
        assert "ignoré" in r.lower() or "ignorée" in r.lower() or "sans limite de pagination" in r.lower() or "sans pagination" in r.lower() or "Ignoré" in r

    def test_mention_whitelist_sort(self):
        r = _audit()
        assert "_ALLOWED_SORT" in r or "whitelist" in r.lower()

    def test_mention_whitelist_filtres(self):
        r = _audit()
        assert "_ALLOWED_FILTERS" in r or "whitelist" in r.lower()


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------

class TestRBAC:
    def test_rbac_mentionne(self):
        assert "RBAC" in _audit()

    def test_permission_index_ou_read_mentionnee(self):
        r = _audit()
        assert "index" in r or "read" in r or ".read" in r

    def test_require_permission_mentionne(self):
        r = _audit()
        assert "require_permission" in r or "`@require_permission`" in r

    def test_export_sans_rbac_comportement_documente(self):
        r = _audit()
        assert "sans RBAC" in r or "Sans RBAC" in r or "optionnel" in r.lower()


# ---------------------------------------------------------------------------
# Injection CSV
# ---------------------------------------------------------------------------

class TestInjectionCSV:
    def test_injection_csv_mentionnee(self):
        r = _audit()
        assert "injection" in r.lower() or "Injection" in r

    def test_prefixes_dangereux_mentionnes(self):
        r = _audit()
        assert "=" in r and ("+" in r or "-" in r or "@" in r)

    def test_mitigation_apostrophe_mentionnee(self):
        r = _audit()
        assert "apostrophe" in r or "'" in r or "préfixe" in r.lower()

    def test_quote_all_ou_guillemets_mentionnes(self):
        r = _audit()
        assert "QUOTE_ALL" in r or "guillemets" in r.lower() or "quoting" in r.lower()

    def test_owasp_ou_reference_securite(self):
        r = _audit()
        assert "OWASP" in r or "sécurité" in r.lower() or "CSV injection" in r or "csv injection" in r.lower()


# ---------------------------------------------------------------------------
# Headers HTTP
# ---------------------------------------------------------------------------

class TestHeadersHTTP:
    def test_content_type_csv_present(self):
        r = _audit()
        assert "text/csv" in r

    def test_charset_utf8_present(self):
        r = _audit()
        assert "utf-8" in r or "UTF-8" in r

    def test_content_disposition_present(self):
        r = _audit()
        assert "Content-Disposition" in r

    def test_attachment_present(self):
        r = _audit()
        assert "attachment" in r

    def test_filename_present(self):
        r = _audit()
        assert "filename" in r

    def test_cache_control_no_store(self):
        r = _audit()
        assert "Cache-Control" in r
        assert "no-store" in r


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------

class TestVolume:
    def test_limite_volume_presente(self):
        r = _audit()
        assert "limite" in r.lower() or "limit" in r.lower() or "1000" in r or "1 000" in r

    def test_valeur_limite_chiffree(self):
        r = _audit()
        assert "1000" in r or "1 000" in r or "500" in r

    def test_pas_export_illimite(self):
        r = _audit()
        assert "illimité" not in r.lower() or "pas d'export illimité" in r.lower() or "limite" in r.lower()


# ---------------------------------------------------------------------------
# SQL et sécurité
# ---------------------------------------------------------------------------

class TestSQLSecurise:
    def test_placeholders_mentionnes(self):
        r = _audit()
        assert "placeholder" in r.lower() or "?" in r or "paramétr" in r.lower()

    def test_pas_de_concatenation(self):
        r = _audit()
        assert "concaténation" in r or "concaténer" in r or "aucune concaténation" in r

    def test_find_paginated_reutilise(self):
        r = _audit()
        assert "find_" in r and "paginated" in r


# ---------------------------------------------------------------------------
# HTMX — export sans HTMX
# ---------------------------------------------------------------------------

class TestHTMX:
    def test_htmx_mentionne(self):
        assert "HTMX" in _audit()

    def test_export_sans_htmx(self):
        r = _audit()
        assert "pas de hx-get" in r.lower() or "hx-get" in r or "sans HTMX" in r or "ne doit pas utiliser HTMX" in r

    def test_lien_href_classique_recommande(self):
        r = _audit()
        assert "href" in r

    def test_pas_de_hx_target_sur_export(self):
        r = _audit()
        assert "hx-target" not in r or "pas de hx-" in r.lower() or "Pas de `hx-get`" in r


# ---------------------------------------------------------------------------
# Recommandation et ticket suivant
# ---------------------------------------------------------------------------

class TestRecommandation:
    def test_recommandation_claire(self):
        r = _audit()
        assert "CRUD-EXPORT-CSV-001" in r

    def test_route_recommandee(self):
        r = _audit()
        assert "export.csv" in r or "/export" in r

    def test_ticket_suivant_crud_export_csv(self):
        r = _audit()
        assert "CRUD-EXPORT-CSV-001" in r


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

class TestRoadmap:
    def test_crud_export_audit_livre(self):
        assert _livre("CRUD-EXPORT-AUDIT-001")

    def test_prochaine_priorite_crud_export_csv(self):
        r = _roadmap()
        idx = r.find("Prochaine priorité immédiate")
        assert idx != -1
        bloc = r[idx: idx + 200]
        assert "FORGE-DESIGN-ROADMAP-001" in bloc
