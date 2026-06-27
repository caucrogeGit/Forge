"""Tests de forge new — corrections V1.4.1 et V1.4.2.

Garantit que forge new :
- n'appelle plus _run_forge_initialization (bootstrap DB interactif) ;
- ne lance jamais schema:create ni db:init via subprocess ;
- atteint bien _reinitialize_git ;
- génère openssl avec capture=True (sortie silencieuse) ;
- produit un env/dev complet depuis env/example avec DB_APP_LOGIN projet-spécifique ;
- produit un message contenant les étapes forge doctor / forge db:init / env/dev.
"""
import os
import sys
import pytest
import forge


class _Recorder:
    def __init__(self, return_value=None):
        self.calls = []
        self._return = return_value

    def __call__(self, *args, **kwargs):
        self.calls.append(args)
        return self._return if self._return is not None else []


def _patch_cmd_new(monkeypatch, tmp_path):
    """Neutralise toutes les I/O de cmd_new.

    Retourne (reinit_recorder, forge_init_recorder).
    """
    reinit = _Recorder()
    forge_init = _Recorder(return_value=[])

    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_materialize_skeleton", lambda dest: os.makedirs(dest, exist_ok=True))
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name, db: None)
    monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
    monkeypatch.setattr(forge, "_setup_node_environment", lambda dest: [])
    monkeypatch.setattr(forge, "_generate_certificates", lambda dest: None)
    monkeypatch.setattr(forge, "_reinitialize_git", reinit)

    if hasattr(forge, "_run_forge_initialization"):
        monkeypatch.setattr(forge, "_run_forge_initialization", forge_init)

    monkeypatch.chdir(tmp_path)
    return reinit, forge_init


# ── Flux nominal ──────────────────────────────────────────────────────────────

def test_reinitialize_git_est_atteint(monkeypatch, tmp_path):
    reinit, _ = _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    assert len(reinit.calls) == 1


def test_reinitialize_git_recoit_le_bon_nom(monkeypatch, tmp_path):
    reinit, _ = _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    _, project_name = reinit.calls[0]
    assert project_name == "MonProjet"


# ── Bootstrap DB interactif absent ───────────────────────────────────────────

def test_ancien_bootstrap_db_non_appele(monkeypatch, tmp_path):
    """_run_forge_initialization ne doit plus être invoquée depuis cmd_new."""
    _, forge_init = _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    assert len(forge_init.calls) == 0, (
        "_run_forge_initialization ne doit plus être appelée depuis cmd_new"
    )


def test_pas_de_subprocess_schema_create(monkeypatch, tmp_path):
    """Aucun appel subprocess ne doit contenir 'schema:create'."""
    _patch_cmd_new(monkeypatch, tmp_path)
    subprocess_args = []

    def spy_run(args, **kwargs):
        subprocess_args.append(list(args))
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(forge, "_run", spy_run)
    forge.cmd_new("MonProjet")

    for call in subprocess_args:
        joined = " ".join(str(a) for a in call)
        assert "schema:create" not in joined, f"schema:create appelé : {call}"


def test_pas_de_subprocess_db_init_automatique(monkeypatch, tmp_path):
    """forge new ne doit pas lancer forge db:init automatiquement."""
    _patch_cmd_new(monkeypatch, tmp_path)
    subprocess_args = []

    def spy_run(args, **kwargs):
        subprocess_args.append(list(args))
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(forge, "_run", spy_run)
    forge.cmd_new("MonProjet")

    for call in subprocess_args:
        joined = " ".join(str(a) for a in call)
        assert "db:init" not in joined, f"db:init appelé automatiquement : {call}"


# ── Message final ─────────────────────────────────────────────────────────────

def test_message_contient_forge_doctor(monkeypatch, tmp_path, capsys):
    _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    assert "forge doctor" in capsys.readouterr().out


def test_message_contient_forge_db_init(monkeypatch, tmp_path, capsys):
    _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    assert "forge db:init" in capsys.readouterr().out


def test_message_contient_forge_run(monkeypatch, tmp_path, capsys):
    _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    assert "forge run" in capsys.readouterr().out


def test_echec_commit_git_final_conserve_le_projet(monkeypatch, tmp_path, capsys):
    def create_dest(dest):
        os.makedirs(dest, exist_ok=True)

    def fail_git(dest, project_name):
        raise RuntimeError("git user.email manquant")

    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_materialize_skeleton", create_dest)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name, db: None)
    monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
    monkeypatch.setattr(forge, "_setup_node_environment", lambda dest: [])
    monkeypatch.setattr(forge, "_generate_certificates", lambda dest: None)
    monkeypatch.setattr(forge, "_reinitialize_git", fail_git)
    monkeypatch.chdir(tmp_path)

    forge.cmd_new("MonProjet")

    assert (tmp_path / "MonProjet").is_dir()
    output = capsys.readouterr().out
    assert "commit Git initial" in output
    assert "git config --global user.email" in output


# ── OpenSSL silencieux (V1.4.2) ───────────────────────────────────────────────

def test_openssl_appele_avec_capture_true(monkeypatch, tmp_path):
    """_generate_certificates doit appeler openssl avec capture=True."""
    appels = []

    def spy_run(args, cwd=None, capture=False, check=False):
        appels.append({"args": args, "capture": capture})
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(forge, "_run", spy_run)
    forge._generate_certificates(str(tmp_path))

    openssl_appels = [a for a in appels if a["args"][0] == "openssl"]
    assert len(openssl_appels) == 1
    assert openssl_appels[0]["capture"] is True, (
        "openssl doit être appelé avec capture=True pour silencer la sortie"
    )


def test_openssl_echec_nettoie_dossier(monkeypatch, tmp_path):
    """Si la génération SSL échoue, cmd_new nettoie le dossier projet."""
    def create_dest(dest):
        os.makedirs(dest, exist_ok=True)

    def fail_certificates(dest):
        raise RuntimeError("openssl introuvable ou échec")

    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_materialize_skeleton", create_dest)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name, db: None)
    monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
    monkeypatch.setattr(forge, "_setup_node_environment", lambda dest: [])
    monkeypatch.setattr(forge, "_generate_certificates", fail_certificates)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit):
        forge.cmd_new("MonProjet")


# ── Matérialisation du squelette (NEW-MATERIALIZE-001, ADR-024) ─────────────
# forge new copie le squelette embarqué au lieu de cloner le dépôt ; le flag
# --ref (et les constantes git du clone) ont disparu.

def test_clone_skeleton_supprime():
    """L'ancien clone de dépôt n'existe plus (_FORGE_DEFAULT_REF reste comme
    métadonnée de release)."""
    assert not hasattr(forge, "_clone_skeleton")
    assert not hasattr(forge, "_FORGE_REPO")


def test_cmd_new_sans_parametre_ref():
    """cmd_new n'expose plus de paramètre ref."""
    import inspect

    assert "ref" not in inspect.signature(forge.cmd_new).parameters


def test_materialize_skeleton_copie_le_squelette(monkeypatch, tmp_path):
    """_materialize_skeleton délègue à cli.skeleton.materialize."""
    called = {}

    def spy_materialize(dest):
        called["dest"] = dest
        os.makedirs(dest, exist_ok=True)

    import cli.skeleton as skeleton
    monkeypatch.setattr(skeleton, "materialize", spy_materialize)
    forge._materialize_skeleton(str(tmp_path / "proj"))
    assert called["dest"].endswith("proj")


def test_cmd_new_materialise_sans_cloner(monkeypatch, tmp_path):
    """cmd_new appelle _materialize_skeleton et ne lance aucun git clone."""
    materialized = {}

    def spy_materialize(dest):
        materialized["dest"] = dest
        os.makedirs(dest, exist_ok=True)

    runs = []

    def spy_run(args, **kwargs):
        runs.append(args)
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_materialize_skeleton", spy_materialize)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name, db: None)
    monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
    monkeypatch.setattr(forge, "_setup_node_environment", lambda dest: [])
    monkeypatch.setattr(forge, "_generate_certificates", lambda dest: None)
    monkeypatch.setattr(forge, "_reinitialize_git", lambda dest, name: None)
    monkeypatch.chdir(tmp_path)

    forge.cmd_new("MonProjet")

    assert materialized["dest"].endswith("MonProjet")
    assert not any(
        a[:2] == ["git", "clone"] for a in runs
    ), "forge new ne doit plus cloner de dépôt."


def test_dispatch_new_sans_ref(monkeypatch, tmp_path):
    """forge new MonProjet appelle cmd_new sans paramètre ref."""
    received = {}

    def spy_cmd_new(name, profile="standard"):
        received["name"] = name
        received["profile"] = profile

    monkeypatch.setattr(sys, "argv", ["forge", "new", "MonProjet"])
    monkeypatch.setattr(forge, "cmd_new", spy_cmd_new)
    forge.main()

    assert received["name"] == "MonProjet"


def test_aide_new_ne_mentionne_plus_ref():
    """L'aide de forge new ne propose plus --ref (flag retiré avec le clone)."""
    from cli._support.help_dispatch import HELP_TEXTS_RICH

    assert "--ref" not in HELP_TEXTS_RICH["new"]


def test_version_cli_affiche_version_stable(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "--version"])

    forge.main()

    assert capsys.readouterr().out.strip() == f"Forge {forge._FORGE_VERSION}"


def test_openssl_ignoree_si_certs_existent(monkeypatch, tmp_path):
    """Si cert.pem et key.pem existent déjà, openssl n'est pas appelé."""
    (tmp_path / "cert.pem").write_text("cert", encoding="utf-8")
    (tmp_path / "key.pem").write_text("key", encoding="utf-8")

    appels = []

    def spy_run(args, **kwargs):
        appels.append(list(args))
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(forge, "_run", spy_run)
    forge._generate_certificates(str(tmp_path))

    assert all(a[0] != "openssl" for a in appels), (
        "openssl ne doit pas être appelé si les certificats existent déjà"
    )


# ── env/dev complet et DB_APP_LOGIN projet-spécifique (V1.4.2) ───────────────

_EXAMPLE_CONTENT = """\
# Application
APP_NAME=Forge
APP_ROUTES_MODULE=mvc.routes

# Administration MariaDB globale
DB_ADMIN_HOST=localhost
DB_ADMIN_PORT=3306
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=

# Base projet
DB_NAME=forge_db
DB_CHARSET=utf8mb4
DB_COLLATION=utf8mb4_unicode_ci

# Utilisateur applicatif du projet
DB_APP_HOST=localhost
DB_APP_PORT=3306
DB_APP_LOGIN=forge
DB_APP_PWD=
DB_POOL_SIZE=5

# Serveur
APP_HOST=127.0.0.1
APP_PORT=8000

# Certificats SSL
SSL_CERTFILE=cert.pem
SSL_KEYFILE=key.pem
"""


def _make_env_dir(tmp_path):
    env_dir = tmp_path / "env"
    env_dir.mkdir()
    (env_dir / "example").write_text(_EXAMPLE_CONTENT, encoding="utf-8")
    return env_dir


def test_env_dev_contient_db_app_login_projet(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    # ADR-034 : sans suffixe _app (fin de ligne exacte pour exclure ..._app)
    assert "DB_APP_LOGIN=test_forge_new\n" in dev


def test_env_dev_ne_contient_pas_root_comme_app_login(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_APP_LOGIN=root" not in dev


def test_env_prod_est_cree(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    assert (tmp_path / "env" / "prod").is_file()


def test_env_prod_contient_db_app_login_projet(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    prod = (tmp_path / "env" / "prod").read_text(encoding="utf-8")
    assert "DB_APP_LOGIN=test_forge_new\n" in prod


def test_env_prod_desactive_ssl(tmp_path):
    # Prod derrière Nginx : Forge écoute en HTTP local, TLS terminé par le proxy.
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    prod = (tmp_path / "env" / "prod").read_text(encoding="utf-8")
    assert "APP_SSL_ENABLED=false" in prod


def test_env_dev_contient_db_admin_login(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_ADMIN_LOGIN=" in dev


def test_env_dev_contient_db_app_host(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_APP_HOST=" in dev


def test_env_dev_contient_db_app_port(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_APP_PORT=" in dev


def test_env_dev_contient_ssl_certfile(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "SSL_CERTFILE=" in dev


def test_env_dev_contient_ssl_keyfile(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "SSL_KEYFILE=" in dev


def test_env_dev_app_name_correct(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "APP_NAME=TestForgeNew" in dev


def test_env_dev_db_name_correct(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_NAME=test_forge_new\n" in dev  # ADR-034 : sans suffixe _db


# ── Convention de normalisation du nom de projet (sans « _ » ajouté) ─────────

@pytest.mark.parametrize(
    "project_name, expected",
    [
        ("ReferenCiel", "referenciel"),  # casse fusionnée, aucun « _ » inséré
        ("MonProjet", "monprojet"),
        ("mon_projet", "mon_projet"),    # « _ » réellement saisi conservé
        ("Mon-Projet", "monprojet"),     # séparateur retiré, pas remplacé par « _ »
        ("Projet2024", "projet2024"),
    ],
)
def test_normalize_identifier_minuscules_sans_underscore_ajoute(project_name, expected):
    assert forge._normalize_identifier(project_name) == expected


# ── env/example ET env/dev respectent la convention (retour terrain) ─────────

def _materialize_real_example(tmp_path):
    """Copie le vrai gabarit env/example du squelette dans tmp_path/env."""
    from cli.skeleton import DATA_DIR

    env_dir = tmp_path / "env"
    env_dir.mkdir()
    src = (DATA_DIR / "env" / "example").read_text(encoding="utf-8")
    (env_dir / "example").write_text(src, encoding="utf-8")
    return env_dir


def test_env_example_identifiants_projet_specifiques(tmp_path):
    _materialize_real_example(tmp_path)
    forge._configure_env_files(str(tmp_path), "ReferenCiel", "referenciel")
    example = (tmp_path / "env" / "example").read_text(encoding="utf-8")
    assert "APP_NAME=ReferenCiel\n" in example  # libellé : casse d'origine
    assert "DB_NAME=referenciel\n" in example
    assert "DB_APP_LOGIN=referenciel\n" in example  # nu, sans suffixe _app


def test_env_example_db_admin_login_suffixe(tmp_path):
    _materialize_real_example(tmp_path)
    forge._configure_env_files(str(tmp_path), "ReferenCiel", "referenciel")
    example = (tmp_path / "env" / "example").read_text(encoding="utf-8")
    # ADR-033 : compte de provisioning distinct du compte applicatif.
    assert "DB_ADMIN_LOGIN=referenciel_admin\n" in example
    # Le commentaire d'aide référence le compte admin réel.
    assert "créez le compte referenciel_admin" in example


def test_env_dev_aucun_underscore_insere_a_la_frontiere_de_casse(tmp_path):
    """Cœur du retour terrain : « ReferenCiel » → « referenciel », jamais
    « referen_ciel », dans env/example comme dans env/dev."""
    _materialize_real_example(tmp_path)
    db_name = forge._normalize_identifier("ReferenCiel")
    forge._configure_env_files(str(tmp_path), "ReferenCiel", db_name)
    for fichier in ("example", "dev"):
        contenu = (tmp_path / "env" / fichier).read_text(encoding="utf-8")
        assert "DB_NAME=referenciel\n" in contenu
        assert "DB_APP_LOGIN=referenciel\n" in contenu
        assert "referen_ciel" not in contenu


# ── Message final — mention env/dev (V1.4.2) ─────────────────────────────────

def test_message_mentionne_ajustement_env_dev(monkeypatch, tmp_path, capsys):
    _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    assert "env/dev" in capsys.readouterr().out


# ── Validations d'entrée (régressions) ───────────────────────────────────────

def test_nom_invalide_exit(monkeypatch):
    with pytest.raises(SystemExit):
        forge.cmd_new("123Invalide")


def test_nom_vide_exit(monkeypatch):
    with pytest.raises(SystemExit):
        forge.cmd_new("")


def test_dossier_existant_exit(monkeypatch, tmp_path):
    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "ExisteDeja").mkdir()
    with pytest.raises(SystemExit):
        forge.cmd_new("ExisteDeja")


# ── CLI-NEW-DROP-STARTER-001 (ADR-023) ───────────────────────────────────────
# forge new produit toujours un projet nu : le flag --starter est retiré et
# forge starter:build est la seule façon officielle de construire un starter.

def test_cmd_new_sans_parametre_starter():
    """cmd_new n'expose plus de paramètre starter."""
    import inspect

    params = inspect.signature(forge.cmd_new).parameters
    assert "starter" not in params


def test_apply_starter_helper_supprime():
    """La fonction interne d'application de starter n'existe plus."""
    assert not hasattr(forge, "_apply_starter_to_new_project")


def test_aide_new_ne_mentionne_plus_starter():
    """L'aide de forge new ne propose plus --starter."""
    from cli._support.help_dispatch import HELP_TEXTS_RICH

    assert "--starter" not in HELP_TEXTS_RICH["new"]


# ── Guidance agent (ADR-047) ────────────────────────────────────────────────────

def test_emet_la_guidance_agent(monkeypatch, tmp_path):
    """cmd_new produit CLAUDE.md, AGENTS.md et docs/adr/001-adopter-forge.md."""
    _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    proj = tmp_path / "MonProjet"
    assert (proj / "CLAUDE.md").is_file()
    assert (proj / "AGENTS.md").is_file()
    assert (proj / "docs" / "adr" / "001-adopter-forge.md").is_file()
