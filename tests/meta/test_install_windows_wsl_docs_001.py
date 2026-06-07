"""Tests documentaires — INSTALL-WSL-DOCS-001 + INSTALL-WSL-DOCS-FIELD-FIX-001.

Verrouille le contrat de la page d'installation Windows + WSL ajoutée
sous `docs/install/windows-wsl.md` :

- le fichier existe ;
- la navigation MkDocs le référence ;
- le parcours `pipx install --pip-args="--pre" forge-mvc` est présent ;
- le mauvais paquet `forge` est explicitement écarté ;
- le système de fichiers Linux WSL est imposé (pas `/mnt/c`) ;
- `forge run` est la commande principale de lancement ;
- `python app.py` n'est PAS le chemin principal ;
- la doc référence la version via la variable `{{forge_version}}`
  (pas de version figée) ;
- le parcours MariaDB recommandé crée un compte `forge_admin@localhost`
  dédié, pas `root` (INSTALL-WSL-DOCS-FIELD-FIX-001) ;
- la page documente `ALTER USER` pour réparer un compte `forge_admin`
  existant ;
- la page met en garde contre le commit des secrets ;
- la convention de dossier utilisateur est `~/Projets/` (cohérente
  avec les procédures terrain).
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/install/windows-wsl.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/install/windows-wsl.md introuvable."

    def test_fichier_substantiel(self):
        assert len(_text()) > 2_000

    def test_titre_h1_correct(self):
        first_h1 = next(
            line for line in _text().splitlines() if line.startswith("# ")
        )
        assert "WSL" in first_h1 and "Windows" in first_h1


class TestParcoursPipx:
    def test_mentionne_pipx(self):
        text = _text()
        assert "pipx" in text

    def test_commande_install_canonique(self):
        text = _text()
        assert 'pipx install --pip-args="--pre" forge-mvc' in text

    def test_avertit_de_ne_pas_installer_forge(self):
        text = _text()
        # Doit mettre en garde contre l'installation du paquet `forge`
        # (la mise en page Markdown peut introduire des retours ligne).
        normalized = " ".join(text.split())
        assert "Ne pas installer le paquet `forge`" in normalized or (
            "ne pas installer" in normalized.lower() and "`forge`" in normalized
        )


class TestSystemeFichiersLinux:
    def test_recommande_le_home_linux(self):
        """La convention de dossier utilisateur est `~/Projets/`
        (cohérente avec les procédures terrain Forge —
        INSTALL-WSL-DOCS-FIELD-FIX-001)."""
        text = _text()
        assert "~/Projets" in text

    def test_ne_recommande_plus_dev(self):
        """L'ancienne convention `~/dev/` a été remplacée par `~/Projets/`."""
        text = _text()
        assert "~/dev" not in text, (
            "La page ne doit plus mentionner `~/dev` (convention "
            "remplacée par `~/Projets`)."
        )

    def test_avertit_contre_mnt_c(self):
        text = _text()
        assert "/mnt/c" in text


class TestLancementForgeRun:
    def test_forge_run_est_le_lancement_principal(self):
        text = _text()
        # `forge run` doit apparaître plusieurs fois (commande principale).
        assert text.count("forge run") >= 3

    def test_python_app_py_pas_principal(self):
        """`python app.py` ne doit apparaître que comme note bas niveau."""
        text = _text()
        # Au plus une occurrence, et présentée comme une alternative.
        occurrences = text.count("python app.py")
        assert occurrences <= 2, (
            f"`python app.py` apparaît {occurrences} fois — il ne doit pas "
            "être présenté comme parcours principal."
        )

    def test_python_app_py_encadre_par_une_note(self):
        text = _text()
        if "python app.py" in text:
            # Une note (admonition !!! ou texte explicite) doit relativiser.
            assert (
                "bas niveau" in text.lower()
                or "alternative" in text.lower()
                or "reste possible" in text.lower()
            ), "L'usage de `python app.py` doit être encadré d'une note."


class TestVersionNonFigee:
    def test_utilise_la_variable_documentaire(self):
        text = _text()
        # La version doit passer par la variable {{forge_version}} pour
        # rester à jour automatiquement.
        assert "{{forge_version}}" in text

    def test_ne_fige_pas_une_version_obsolete(self):
        text = _text()
        # Pas de version 1.0.0b10 figée en dur (la variable doit s'en charger).
        # Tolérance : la chaîne peut apparaître si elle illustre un format,
        # mais pas comme version officielle de la doc.
        for forbidden_pattern in ("Forge 1.0.0b10\n", "Forge 1.0.0b10 "):
            assert forbidden_pattern not in text, (
                "Version 1.0.0b10 figée détectée — utiliser la variable "
                "documentaire {{forge_version}}."
            )


class TestRoutesStarter:
    def test_starter_welcome_recommande(self):
        text = _text()
        assert "forge starter:build welcome" in text

    def test_routes_welcome_listees(self):
        text = _text()
        # Le starter minimal expose une seule route texte : /welcome.
        # (request.param / /welcome/greet appartiennent au palier query-params.)
        assert "/welcome" in text
        assert "/welcome/greet" not in text

    def test_routes_retirees_absentes(self):
        """STARTER-BONJOUR-FORGE-MINIMAL-001 : les routes /inspect, /cycle,
        /request, /response, /routing, /404-demo ont été retirées."""
        text = _text()
        for retired in ("/welcome/inspect", "/welcome/cycle",
                        "/welcome/request", "/welcome/response",
                        "/welcome/routing", "/welcome/404-demo"):
            assert retired not in text, (
                f"La doc install ne doit plus mentionner {retired}"
            )


class TestPrerequisLinux:
    def test_mentionne_node_20(self):
        text = _text()
        assert "Node.js 20" in text or "setup_20.x" in text

    def test_mentionne_ubuntu_24_04(self):
        text = _text()
        assert "Ubuntu 24.04" in text or "Ubuntu-24.04" in text

    def test_mentionne_python_3_12(self):
        text = _text()
        assert "Python 3.12" in text or "python3.12" in text


class TestMariaDB:
    def test_mentionne_mariadb_server(self):
        text = _text()
        assert "mariadb-server" in text

    def test_mentionne_forge_db_init(self):
        text = _text()
        assert "forge db:init" in text


# ---------------------------------------------------------------------------
# INSTALL-WSL-DOCS-FIELD-FIX-001 — parcours MariaDB forge_admin
# ---------------------------------------------------------------------------


class TestForgeAdminAccount:
    def test_recommande_forge_admin(self):
        text = _text()
        assert "forge_admin@localhost" in text
        # Et passe explicitement par le compte dans env/dev.
        assert "DB_ADMIN_LOGIN" in text
        assert "forge_admin" in text

    def test_ne_recommande_pas_root_comme_admin(self):
        """`DB_ADMIN_LOGIN=root` ne doit pas être présenté comme
        parcours principal (uniquement comme contre-exemple expliqué)."""
        text = _text()
        # Au plus une occurrence (dans la warning expliquant pourquoi
        # ne pas faire ça).
        occurrences = text.count("DB_ADMIN_LOGIN=root")
        assert occurrences <= 1, (
            f"`DB_ADMIN_LOGIN=root` apparaît {occurrences} fois — il ne "
            "doit jamais être présenté comme parcours principal."
        )

    def test_avertit_de_ne_pas_utiliser_root(self):
        text = _text()
        normalized = " ".join(text.split())
        assert "Ne pas utiliser `root` MariaDB" in normalized or (
            "ne pas utiliser" in normalized.lower()
            and "root" in normalized
            and "compte admin" in normalized.lower()
        )

    def test_create_user_if_not_exists(self):
        text = _text()
        # Le compte forge_admin doit être créé si absent…
        assert "CREATE USER IF NOT EXISTS 'forge_admin'@'localhost'" in text

    def test_alter_user_pour_reparation(self):
        """`ALTER USER` doit suivre `CREATE USER IF NOT EXISTS` pour
        que le tutoriel soit rejouable : `CREATE USER IF NOT EXISTS`
        ne modifie pas le mot de passe d'un compte existant."""
        text = _text()
        assert "ALTER USER 'forge_admin'@'localhost' IDENTIFIED BY" in text

    def test_grant_includes_create_user(self):
        text = _text()
        # `forge db:init` crée l'utilisateur applicatif — forge_admin
        # doit donc avoir CREATE USER + GRANT OPTION.
        assert "CREATE USER" in text
        assert "WITH GRANT OPTION" in text

    def test_forge_db_init_apres_forge_admin(self):
        """`forge db:init` doit être lancé APRÈS la création du compte
        forge_admin."""
        text = _text()
        idx_alter = text.find("ALTER USER 'forge_admin'@'localhost' IDENTIFIED BY")
        idx_db_init = text.find("forge db:init")
        assert idx_alter != -1 and idx_db_init != -1
        # Au moins une occurrence de `forge db:init` doit apparaître
        # APRÈS la création/réparation du compte.
        idx_db_init_after = text.find("forge db:init", idx_alter)
        assert idx_db_init_after != -1, (
            "`forge db:init` doit apparaître après la création/réparation "
            "du compte forge_admin."
        )

    def test_ne_jamais_commiter_les_secrets(self):
        text = _text()
        normalized = text.lower()
        assert (
            "ne jamais commiter" in normalized
            or "ne pas commiter" in normalized
            or "ne pas pousser de secrets" in normalized
        )

    def test_access_denied_documente(self):
        """Le diagnostic `Access denied for user 'forge_admin'@'localhost'`
        doit être documenté avec la solution `ALTER USER`."""
        text = _text()
        assert "Access denied for user 'forge_admin'@'localhost'" in text

    def test_mariadb_n_est_pas_actif_documente(self):
        text = _text()
        normalized = " ".join(text.split())
        assert "MariaDB n'est pas actif" in normalized or (
            "service mariadb" in normalized.lower() and "start" in normalized.lower()
        )

    def test_connexion_admin_impossible_documente(self):
        text = _text()
        assert "Connexion MariaDB admin impossible" in text

    def test_script_python_genere_mots_de_passe(self):
        """Le script doit utiliser `secrets` pour les mots de passe
        (et pas un mot de passe en clair dans la doc)."""
        text = _text()
        assert "import secrets" in text
        assert "secrets.choice" in text


class TestMkdocs:
    def test_nav_reference_la_page(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "install/windows-wsl.md" in mkdocs

    def test_libelle_nav(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "Windows + WSL" in mkdocs

    def test_mkdocs_build_strict(self):
        import subprocess

        result = subprocess.run(
            ["mkdocs", "build", "--strict"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"mkdocs build --strict a échoué :\n{result.stderr}"
        )


class TestRoadmap:
    def test_ticket_present(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "INSTALL-WSL-DOCS-001" in text

    def test_ticket_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "INSTALL-WSL-DOCS-001" in line:
                assert "livré" in line.lower(), (
                    f"INSTALL-WSL-DOCS-001 non marqué comme livré : {line}"
                )
                return
        pytest.fail("Ligne INSTALL-WSL-DOCS-001 introuvable.")


class TestLiensInternes:
    def test_lien_vers_bonjour_forge(self):
        text = _text()
        assert "../guide/bonjour-forge.md" in text

    def test_lien_vers_getting_started(self):
        text = _text()
        assert "../guide/getting-started.md" in text

    def test_lien_vers_installation_mariadb(self):
        text = _text()
        assert "mariadb.md" in text

    def test_lien_vers_starter_welcome(self):
        text = _text()
        assert "../starters/welcome-forge/debutant/welcome.md" in text
