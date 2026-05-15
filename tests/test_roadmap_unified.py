"""Tests — ROADMAP-UNIFIED-001 : roadmap Forge unifiée."""

import pathlib

ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")
ARCHIVE = pathlib.Path("docs/history/forge_post_2_0_consolidation_roadmap.md")
MKDOCS = pathlib.Path("mkdocs.yml")


def _roadmap():
    return ROADMAP.read_text(encoding="utf-8")


def _archive():
    return ARCHIVE.read_text(encoding="utf-8")


def _mkdocs():
    return MKDOCS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence des fichiers
# ---------------------------------------------------------------------------


class TestExistence:
    def test_roadmap_officielle_existe(self):
        assert ROADMAP.exists()

    def test_archive_existe(self):
        assert ARCHIVE.exists()


# ---------------------------------------------------------------------------
# Roadmap officielle — contenu complet
# ---------------------------------------------------------------------------


class TestRoadmapOfficielle:
    def test_contient_phase_5_dx(self):
        r = _roadmap()
        assert "Phase 5" in r and ("DX" in r or "Expérience développeur" in r)

    def test_contient_phase_5_5_debug(self):
        r = _roadmap()
        assert "Phase 5.5" in r or "Debug runtime" in r

    def test_contient_phase_6_e2e(self):
        r = _roadmap()
        assert "Phase 6" in r and ("E2E" in r or "qualité" in r)

    def test_contient_phase_7_securite(self):
        r = _roadmap()
        assert "Phase 7" in r and ("Sécurité" in r or "sécurité" in r)

    def test_contient_phase_8_release(self):
        r = _roadmap()
        assert "Phase 8" in r and ("Release" in r or "release" in r)

    def test_contient_phase_9_doc(self):
        r = _roadmap()
        assert "Phase 9" in r and ("Documentation" in r or "documentation" in r)

    def test_contient_phase_10_api(self):
        r = _roadmap()
        assert "Phase 10" in r and ("API" in r)


# ---------------------------------------------------------------------------
# Tickets clés présents et marqués livrés
# ---------------------------------------------------------------------------


class TestTicketsLivres:
    def test_landing_refresh_livre(self):
        r = _roadmap()
        assert "LANDING-POST-2.2-REFRESH-001" in r
        idx = r.index("LANDING-POST-2.2-REFRESH-001")
        assert "livré" in r[idx: idx + 60]

    def test_roadmap_unified_livre(self):
        r = _roadmap()
        assert "ROADMAP-UNIFIED-001" in r
        idx = r.index("ROADMAP-UNIFIED-001")
        assert "livré" in r[idx: idx + 60]

    def test_dx_doctor_present(self):
        assert "DX-DOCTOR-001" in _roadmap()

    def test_e2e_cli_present(self):
        assert "E2E-CLI-001" in _roadmap()

    def test_security_audit_present(self):
        assert "SECURITY-AUDIT-001" in _roadmap()

    def test_api_doc_001_present(self):
        assert "API-DOC-001" in _roadmap()

    def test_doc_contribute_present(self):
        assert "DOC-CONTRIBUTE-001" in _roadmap()


# ---------------------------------------------------------------------------
# Prochaine priorité = POST-2.2-FINAL-AUDIT-001
# ---------------------------------------------------------------------------


class TestProchainePriorite:
    def test_prochaine_priorite_workflow_statuts(self):
        r = _roadmap()
        idx = r.find("Prochaine priorité immédiate")
        assert idx != -1
        bloc = r[idx: idx + 200]
        assert "FORGE-DESIGN-ROADMAP-001" in bloc

    def test_post_2_2_livre_dans_roadmap(self):
        r = _roadmap()
        assert "POST-2.2-FINAL-AUDIT-001" in r
        idx = r.index("POST-2.2-FINAL-AUDIT-001")
        assert "livré" in r[idx: idx + 80]


# ---------------------------------------------------------------------------
# Dettes connues présentes
# ---------------------------------------------------------------------------


class TestDettes:
    def test_section_dettes(self):
        r = _roadmap()
        assert "Dettes" in r or "dettes" in r

    def test_auth_mfa_004_presente(self):
        assert "AUTH-MFA-004" in _roadmap()


# ---------------------------------------------------------------------------
# Archive — ne contient plus de roadmap concurrente
# ---------------------------------------------------------------------------


class TestArchive:
    def test_archive_courte(self):
        archive = _archive()
        assert len(archive) < 5000, "L'archive ne doit pas contenir une roadmap complète"

    def test_archive_renvoie_vers_roadmap(self):
        archive = _archive()
        assert "forge-roadmap.md" in archive

    def test_archive_mentionne_archivee(self):
        archive = _archive()
        assert "archiv" in archive.lower()

    def test_archive_ne_contient_pas_priorite_active(self):
        archive = _archive()
        assert "Prochaine priorité immédiate" not in archive


# ---------------------------------------------------------------------------
# mkdocs.yml — une seule entrée principale
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_roadmap_forge_dans_mkdocs(self):
        assert "forge-roadmap.md" in _mkdocs()

    def test_pas_deux_roadmaps_actives(self):
        m = _mkdocs()
        assert m.count("Roadmap active") == 0 or m.count("Roadmap active") == 1

    def test_post_2_0_en_archives(self):
        m = _mkdocs()
        assert "forge_post_2_0_consolidation_roadmap.md" in m
        idx = m.index("forge_post_2_0_consolidation_roadmap.md")
        context = m[max(0, idx - 60): idx]
        assert "Archive" in context or "archive" in context or "Archives" in context
