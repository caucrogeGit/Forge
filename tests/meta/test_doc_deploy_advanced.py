"""Tests documentaires — DOC-DEPLOY-ADVANCED-001 : guide déploiement avancé Forge."""

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/deployment/deploy-advanced.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text():
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/deployment/deploy-advanced.md introuvable"

    def test_fichier_non_vide(self):
        assert len(_text()) > 1000

    def test_titre_principal(self):
        text = _text().lower()
        assert "déploiement" in text and "forge" in text


# ---------------------------------------------------------------------------
# Sections obligatoires
# ---------------------------------------------------------------------------


class TestSections:
    def test_section_objectif(self):
        assert "Objectif" in _text()

    def test_section_architecture(self):
        text = _text().lower()
        assert "architecture" in text

    def test_section_prerequis(self):
        text = _text().lower()
        assert "prérequis" in text or "requis" in text

    def test_section_variables_environnement(self):
        text = _text().lower()
        assert "variable" in text and ("environnement" in text or "env" in text)

    def test_section_mariadb(self):
        text = _text().lower()
        assert "mariadb" in text

    def test_section_systemd(self):
        text = _text().lower()
        assert "systemd" in text

    def test_section_nginx(self):
        text = _text().lower()
        assert "nginx" in text

    def test_section_static(self):
        text = _text().lower()
        assert "static" in text

    def test_section_uploads(self):
        text = _text().lower()
        assert "upload" in text

    def test_section_logs(self):
        text = _text().lower()
        assert "log" in text

    def test_section_securite(self):
        text = _text().lower()
        assert "sécurité" in text

    def test_section_sauvegardes(self):
        text = _text().lower()
        assert "sauvegarde" in text

    def test_section_mise_a_jour(self):
        text = _text().lower()
        assert "mise à jour" in text or "update" in text

    def test_section_validation_post_deploiement(self):
        text = _text().lower()
        assert "validation" in text and "déploiement" in text

    def test_section_depannage(self):
        text = _text().lower()
        assert "dépannage" in text

    def test_section_limites(self):
        text = _text().lower()
        assert "limite" in text


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------


class TestArchitecture:
    def test_nginx_mentionne(self):
        assert "Nginx" in _text() or "nginx" in _text()

    def test_https_mentionne(self):
        text = _text().lower()
        assert "https" in text

    def test_reverse_proxy_mentionne(self):
        text = _text().lower()
        assert "reverse proxy" in text or "proxy" in text

    def test_mariadb_couche_mentionnee(self):
        text = _text().lower()
        assert "mariadb" in text

    def test_storage_uploads_mentionne(self):
        assert "storage/uploads" in _text()

    def test_principe_pas_exposition_directe(self):
        text = _text().lower()
        assert "exposé directement" in text or "sans reverse proxy" in text

    def test_secrets_hors_git(self):
        text = _text().lower()
        assert "git" in text and "secret" in text


# ---------------------------------------------------------------------------
# Variables d'environnement
# ---------------------------------------------------------------------------


class TestVariables:
    def test_app_env_prod(self):
        text = _text()
        assert "APP_ENV=prod" in text or "env prod" in text.lower() or "env/prod" in text

    def test_env_prod_non_versionne(self):
        text = _text().lower()
        assert "git" in text and ("versionn" in text or "gitignore" in text)

    def test_upload_root_mentionne(self):
        assert "UPLOAD_ROOT" in _text()

    def test_db_app_login_mentionne(self):
        assert "DB_APP_LOGIN" in _text() or "DB_APP" in _text()

    def test_app_ssl_enabled_false(self):
        assert "APP_SSL_ENABLED=false" in _text() or "ssl_enabled" in _text().lower()


# ---------------------------------------------------------------------------
# systemd
# ---------------------------------------------------------------------------


class TestSystemd:
    def test_unit_section(self):
        assert "[Unit]" in _text()

    def test_service_section(self):
        assert "[Service]" in _text()

    def test_install_section(self):
        assert "[Install]" in _text()

    def test_restart_on_failure(self):
        text = _text()
        assert "Restart" in text

    def test_journalctl_mentionne(self):
        assert "journalctl" in _text()

    def test_systemctl_start_mentionne(self):
        assert "systemctl" in _text()


# ---------------------------------------------------------------------------
# Nginx
# ---------------------------------------------------------------------------


class TestNginx:
    def test_proxy_pass(self):
        assert "proxy_pass" in _text()

    def test_ssl_certificate(self):
        assert "ssl_certificate" in _text()

    def test_x_forwarded_proto(self):
        assert "X-Forwarded-Proto" in _text()

    def test_hsts_mentionne(self):
        text = _text().lower()
        assert "hsts" in text or "strict-transport" in text

    def test_listen_443(self):
        assert "443" in _text()


# ---------------------------------------------------------------------------
# Fichiers statiques et uploads
# ---------------------------------------------------------------------------


class TestStatiquesUploads:
    def test_deux_strategies_static(self):
        text = _text().lower()
        assert "stratégie" in text or "nginx sert" in text

    def test_storage_ne_pas_exposer(self):
        text = _text().lower()
        assert "storage" in text and ("exposé" in text or "jamais" in text)

    def test_permissions_uploads(self):
        text = _text()
        assert "chown" in text or "chmod" in text

    def test_client_max_body_size(self):
        assert "client_max_body_size" in _text()


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


class TestLogs:
    def test_journalctl_commande(self):
        assert "journalctl" in _text()

    def test_storage_logs_non_expose(self):
        text = _text()
        assert "storage/logs" in text

    def test_errors_jsonl_mentionne(self):
        assert "errors.dev.jsonl" in _text() or "errors" in _text().lower()


# ---------------------------------------------------------------------------
# Sauvegardes
# ---------------------------------------------------------------------------


class TestSauvegardes:
    def test_mysqldump_mentionne(self):
        assert "mysqldump" in _text()

    def test_sauvegarde_uploads(self):
        text = _text().lower()
        assert "upload" in text and "sauvegarde" in text

    def test_sauvegarde_avant_migration(self):
        text = _text().lower()
        assert "avant" in text and ("migration" in text or "mise à jour" in text)

    def test_restauration_mentionnee(self):
        text = _text().lower()
        assert "restauration" in text or "restore" in text


# ---------------------------------------------------------------------------
# Validation post-déploiement
# ---------------------------------------------------------------------------


class TestValidationPostDeploi:
    def test_checklist_presente(self):
        text = _text()
        assert "- [ ]" in text

    def test_https_dans_checklist(self):
        text = _text().lower()
        assert "https" in text and "- [ ]" in _text()

    def test_storage_non_accessible_checklist(self):
        text = _text()
        assert "storage" in text and "- [ ]" in text

    def test_curl_verification(self):
        assert "curl" in _text()


# ---------------------------------------------------------------------------
# Dépannage
# ---------------------------------------------------------------------------


class TestDepannage:
    def test_service_ne_demarre_pas(self):
        text = _text().lower()
        assert "ne démarre pas" in text or "ne démarre" in text

    def test_erreur_502(self):
        assert "502" in _text()

    def test_permission_denied(self):
        text = _text().lower()
        assert "permission" in text

    def test_cookies_non_envoyes(self):
        text = _text().lower()
        assert "cookie" in text

    def test_upload_impossible(self):
        text = _text().lower()
        assert "upload" in text and ("impossible" in text or "échoue" in text or "trop petit" in text)


# ---------------------------------------------------------------------------
# Mkdocs
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_guide_dans_nav(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "deploy-advanced.md" in mkdocs

    def test_mkdocs_build_strict(self, tmp_path):
        import subprocess

        result = subprocess.run(
            ["mkdocs", "build", "--strict", "-d", str(tmp_path / "site")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"mkdocs build --strict a échoué :\n{result.stderr}"


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_ticket_livre_dans_roadmap(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-DEPLOY-ADVANCED-001" in text

    def test_ticket_marque_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "DOC-DEPLOY-ADVANCED-001" in line:
                assert "livré" in line.lower() or "terminé" in line.lower(), (
                    f"DOC-DEPLOY-ADVANCED-001 non marqué comme livré : {line}"
                )
                break

    def test_prochaine_priorite_doc_contribute(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-CONTRIBUTE-001" in text
