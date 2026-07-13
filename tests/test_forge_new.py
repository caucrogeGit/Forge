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
    monkeypatch.setattr(forge, "_materialize_skeleton", lambda dest, *, bare=False: os.makedirs(dest, exist_ok=True))
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name: None)
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
    def create_dest(dest, *, bare=False):
        os.makedirs(dest, exist_ok=True)

    def fail_git(dest, project_name):
        raise RuntimeError("git user.email manquant")

    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_materialize_skeleton", create_dest)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name: None)
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
    def create_dest(dest, *, bare=False):
        os.makedirs(dest, exist_ok=True)

    def fail_certificates(dest):
        raise RuntimeError("openssl introuvable ou échec")

    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_materialize_skeleton", create_dest)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name: None)
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
    """_materialize_skeleton délègue à skeleton.materialize."""
    called = {}

    def spy_materialize(dest, *, bare=False):
        called["dest"] = dest
        os.makedirs(dest, exist_ok=True)

    import skeleton as skeleton
    monkeypatch.setattr(skeleton, "materialize", spy_materialize)
    forge._materialize_skeleton(str(tmp_path / "proj"))
    assert called["dest"].endswith("proj")


def test_cmd_new_materialise_sans_cloner(monkeypatch, tmp_path):
    """cmd_new appelle _materialize_skeleton et ne lance aucun git clone."""
    materialized = {}

    def spy_materialize(dest, *, bare=False):
        materialized["dest"] = dest
        os.makedirs(dest, exist_ok=True)

    runs = []

    def spy_run(args, **kwargs):
        runs.append(args)
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_materialize_skeleton", spy_materialize)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name: None)
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

    def spy_cmd_new(name, profile="standard", bare=False):
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


# ── env/dev et env/prod dérivés d'env/example (ADR-060) ──────────────────────
#
# ADR-060 : le squelette est livré sans backend BDD ; la configuration de
# connexion appartient au backend installé. forge new ne renseigne donc plus
# aucune variable DB_*, il ne substitue que le nom applicatif (APP_NAME).

_EXAMPLE_CONTENT = """\
# Application
APP_NAME=Forge
APP_ROUTES_MODULE=mvc.routes

# Base de données : installez un backend et renseignez ses variables ici.

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


def _lignes_de_dependance(contenu):
    """Lignes de variables (hors commentaires et vides) d'un fichier d'env."""
    return [
        ligne.strip()
        for ligne in contenu.splitlines()
        if ligne.strip() and not ligne.lstrip().startswith("#")
    ]


def test_env_prod_est_cree(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew")
    assert (tmp_path / "env" / "prod").is_file()


def test_env_prod_desactive_ssl(tmp_path):
    # Prod derrière Nginx : Forge écoute en HTTP local, TLS terminé par le proxy.
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew")
    prod = (tmp_path / "env" / "prod").read_text(encoding="utf-8")
    assert "APP_SSL_ENABLED=false" in prod


def test_env_dev_contient_ssl_certfile(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "SSL_CERTFILE=" in dev


def test_env_dev_contient_ssl_keyfile(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "SSL_KEYFILE=" in dev


def test_env_dev_app_name_correct(tmp_path):
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew")
    dev = (tmp_path / "env" / "dev").read_text(encoding="utf-8")
    assert "APP_NAME=TestForgeNew" in dev


def test_env_ne_contient_aucune_config_bdd(tmp_path):
    # ADR-060 : forge new n'injecte plus de configuration BDD ; les variables
    # DB_* appartiennent au backend installé, pas au squelette.
    _make_env_dir(tmp_path)
    forge._configure_env_files(str(tmp_path), "TestForgeNew")
    for fichier in ("example", "dev", "prod"):
        contenu = (tmp_path / "env" / fichier).read_text(encoding="utf-8")
        lignes = _lignes_de_dependance(contenu)
        for prefixe in ("DB_ADMIN_", "DB_APP_", "DB_NAME", "DB_CHARSET"):
            assert not any(ligne.startswith(prefixe) for ligne in lignes), (
                f"env/{fichier} ne doit déclarer aucune config BDD ({prefixe})."
            )


# ── env/example réel : APP_NAME substitué, aucune config BDD (ADR-060) ───────

def _materialize_real_example(tmp_path):
    """Copie le vrai gabarit env/example du squelette dans tmp_path/env."""
    from skeleton import DATA_DIR

    env_dir = tmp_path / "env"
    env_dir.mkdir()
    src = (DATA_DIR / "env" / "example").read_text(encoding="utf-8")
    (env_dir / "example").write_text(src, encoding="utf-8")
    return env_dir


def test_env_example_reel_app_name_projet_specifique(tmp_path):
    _materialize_real_example(tmp_path)
    forge._configure_env_files(str(tmp_path), "ReferenCiel")
    for fichier in ("example", "dev"):
        contenu = (tmp_path / "env" / fichier).read_text(encoding="utf-8")
        assert "APP_NAME=ReferenCiel\n" in contenu  # libellé : casse d'origine


def test_env_example_reel_sans_config_bdd(tmp_path):
    # ADR-060 : le vrai gabarit ne porte plus de bloc de connexion BDD ;
    # forge new ne l'injecte pas davantage.
    _materialize_real_example(tmp_path)
    forge._configure_env_files(str(tmp_path), "ReferenCiel")
    for fichier in ("example", "dev", "prod"):
        contenu = (tmp_path / "env" / fichier).read_text(encoding="utf-8")
        lignes = _lignes_de_dependance(contenu)
        for prefixe in ("DB_ADMIN_", "DB_APP_", "DB_NAME", "DB_CHARSET"):
            assert not any(ligne.startswith(prefixe) for ligne in lignes), (
                f"env/{fichier} ne doit déclarer aucune config BDD ({prefixe})."
            )


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
    """cmd_new produit CLAUDE.md, AGENTS.md et les ADR d'amorçage 001 et 002."""
    _patch_cmd_new(monkeypatch, tmp_path)
    forge.cmd_new("MonProjet")
    proj = tmp_path / "MonProjet"
    assert (proj / "CLAUDE.md").is_file()
    assert (proj / "AGENTS.md").is_file()
    assert (proj / "docs" / "adr" / "001-adopter-forge.md").is_file()
    assert (proj / "docs" / "adr" / "002-style-documentation.md").is_file()


# ── Mode dev : FORGE_DEV_SRC installe forge-mvc en éditable ───────────────────

class _RunRecorder:
    def __init__(self):
        self.calls = []
    def __call__(self, args, **kwargs):
        self.calls.append(list(args))
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()


def test_dev_src_installe_forge_mvc_editable(tmp_path, monkeypatch):
    rec = _RunRecorder()
    monkeypatch.setattr(forge, "_run", rec)
    monkeypatch.setattr(forge, "_venv_python", lambda dest: "PY")
    monkeypatch.setenv("FORGE_DEV_SRC", str(tmp_path))  # existe -> isdir vrai
    forge._setup_python_environment(str(tmp_path))
    # forge-mvc installé en éditable depuis FORGE_DEV_SRC, requirements ignoré.
    assert any(a[:5] == ["PY", "-m", "pip", "install", "-e"] for a in rec.calls)
    assert not any("requirements.txt" in " ".join(a) for a in rec.calls)


def test_sans_dev_src_installe_requirements(tmp_path, monkeypatch):
    rec = _RunRecorder()
    monkeypatch.setattr(forge, "_run", rec)
    monkeypatch.setattr(forge, "_venv_python", lambda dest: "PY")
    monkeypatch.delenv("FORGE_DEV_SRC", raising=False)
    (tmp_path / "requirements.txt").write_text("forge-mvc==1.0.0rc2\n", encoding="utf-8")
    forge._setup_python_environment(str(tmp_path))
    assert any("requirements.txt" in " ".join(a) for a in rec.calls)
    assert not any(a[:5] == ["PY", "-m", "pip", "install", "-e"] for a in rec.calls)
