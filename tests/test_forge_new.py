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
    monkeypatch.setattr(forge, "_clone_skeleton", lambda dest, ref=None: None)
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


def test_message_contient_python_app(monkeypatch, tmp_path, capsys):
    _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    assert "python app.py" in capsys.readouterr().out


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
    def create_dest(dest, ref=None):
        os.makedirs(dest, exist_ok=True)

    def fail_certificates(dest):
        raise RuntimeError("openssl introuvable ou échec")

    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_clone_skeleton", create_dest)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name, db: None)
    monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
    monkeypatch.setattr(forge, "_setup_node_environment", lambda dest: [])
    monkeypatch.setattr(forge, "_generate_certificates", fail_certificates)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit):
        forge.cmd_new("MonProjet")


# ── Branche de clonage (fix main) ──────────────────────────────────────────

def test_clone_utilise_main_par_defaut(monkeypatch, tmp_path):
    """Sans --ref, le clone doit cibler _FORGE_DEFAULT_BRANCH, pas _FORGE_VERSION."""
    cloned_with = {}

    def spy_clone(dest, ref=None):
        cloned_with["ref"] = ref

    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_clone_skeleton", spy_clone)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name, db: None)
    monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
    monkeypatch.setattr(forge, "_setup_node_environment", lambda dest: [])
    monkeypatch.setattr(forge, "_generate_certificates", lambda dest: None)
    monkeypatch.setattr(forge, "_reinitialize_git", lambda dest, name: None)
    monkeypatch.chdir(tmp_path)

    forge.cmd_new("MonProjet")
    assert cloned_with["ref"] is None


def test_clone_skeleton_utilise_default_branch_si_ref_none(monkeypatch):
    """_clone_skeleton sans ref doit passer main à git clone."""
    git_args = {}

    def spy_run(args, **kwargs):
        if args[0] == "git":
            git_args["branch"] = args[args.index("--branch") + 1] if "--branch" in args else None
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(forge, "_run", spy_run)
    forge._clone_skeleton("/tmp/fake_dest")

    assert forge._FORGE_DEFAULT_BRANCH == "main"
    assert git_args.get("branch") == forge._FORGE_DEFAULT_BRANCH


def test_clone_skeleton_accepte_ref_explicite(monkeypatch):
    """_clone_skeleton avec ref doit passer cette ref à git clone."""
    git_args = {}

    def spy_run(args, **kwargs):
        if args[0] == "git":
            git_args["branch"] = args[args.index("--branch") + 1] if "--branch" in args else None
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(forge, "_run", spy_run)
    forge._clone_skeleton("/tmp/fake_dest", ref="main")

    assert git_args.get("branch") == "main"


def test_dispatch_ref_transmis_a_cmd_new(monkeypatch, tmp_path, capsys):
    """forge new MonProjet --ref main doit transmettre ref='main'."""
    received = {}

    def spy_cmd_new(name, ref=None):
        received["ref"] = ref

    monkeypatch.setattr(sys, "argv", ["forge", "new", "MonProjet", "--ref", "main"])
    monkeypatch.setattr(forge, "cmd_new", spy_cmd_new)
    forge.main()

    assert received["ref"] == "main"

    assert not (tmp_path / "MonProjet").exists(), (
        "Le dossier projet doit être supprimé après échec"
    )


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
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new_db")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_APP_LOGIN=test_forge_new_app" in dev


def test_env_dev_ne_contient_pas_root_comme_app_login(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new_db")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_APP_LOGIN=root" not in dev


def test_env_dev_contient_db_admin_login(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new_db")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_ADMIN_LOGIN=" in dev


def test_env_dev_contient_db_app_host(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new_db")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_APP_HOST=" in dev


def test_env_dev_contient_db_app_port(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new_db")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_APP_PORT=" in dev


def test_env_dev_contient_ssl_certfile(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new_db")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "SSL_CERTFILE=" in dev


def test_env_dev_contient_ssl_keyfile(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new_db")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "SSL_KEYFILE=" in dev


def test_env_dev_app_name_correct(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new_db")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "APP_NAME=TestForgeNew" in dev


def test_env_dev_db_name_correct(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew", "test_forge_new_db")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_NAME=test_forge_new_db" in dev


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
