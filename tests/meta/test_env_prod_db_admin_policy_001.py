"""Garde-fou ENV-PROD-DB-ADMIN-SECRETS-POLICY-001.

Verrouille la politique Forge sur les secrets MariaDB admin/root :

  * **Runtime applicatif** Forge utilise **uniquement** ``DB_APP_*`` —
    ``app.py`` n'importe jamais ``DB_ADMIN_*`` depuis ``config`` ;
  * **Templates d'environnement suivis par Git** (``env/example``, et
    ``env/prod`` si présent localement) ne contiennent **aucun mot de
    passe admin/root réel** : ``DB_ADMIN_PWD`` doit être vide ou
    absent ;
  * ``.gitignore`` protège les fichiers locaux d'administration via la
    règle ``env/*.local`` (ou un pattern équivalent) ;
  * la documentation officielle (``docs/production-security.md``)
    explicite la séparation provisioning / runtime.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


_REPO_ROOT = Path(__file__).resolve().parents[2]
_GITIGNORE = _REPO_ROOT / ".gitignore"
_ENV_EXAMPLE = _REPO_ROOT / "env" / "example"
_ENV_PROD_LOCAL = _REPO_ROOT / "env" / "prod"  # untracked local file
_PROD_SECURITY_DOC = _REPO_ROOT / "docs" / "production-security.md"
_APP_PY = _REPO_ROOT / "app.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gitignore_lines() -> list[str]:
    text = _GITIGNORE.read_text(encoding="utf-8")
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _env_pairs(path: Path) -> dict[str, str]:
    """Parse simple `KEY=VALUE` lines depuis un .env. Ignore commentaires."""
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip()
    return out


# ---------------------------------------------------------------------------
# 1. Le runtime applicatif n'importe jamais DB_ADMIN_*
# ---------------------------------------------------------------------------


class TestRuntimeDoesNotImportDbAdmin:
    """Critère structurant : `app.py` ne doit JAMAIS importer
    `DB_ADMIN_*` depuis `config`. Le runtime applicatif (chaque requête
    HTTP) ne doit avoir aucune dépendance au compte admin MariaDB."""

    def test_app_py_does_not_import_db_admin(self):
        text = _APP_PY.read_text(encoding="utf-8")
        # On cherche un import au niveau module : `from config import ... DB_ADMIN_X ...`
        # Le pattern strict est : une ligne contenant `DB_ADMIN_` dans un
        # bloc `from config import (...)`.
        # Approche : isoler le bloc d'import config, puis vérifier.
        # On accepte qu'`config.py` lui-même expose `DB_ADMIN_*` —
        # c'est un module de configuration, pas le runtime.
        match = re.search(
            r"from\s+config\s+import\s+\(([^)]+)\)",
            text,
            re.DOTALL,
        )
        assert match is not None, (
            "app.py doit importer ses variables depuis `config` via un "
            "bloc `from config import (...)` parsable."
        )
        block = match.group(1)
        assert "DB_ADMIN_" not in block, (
            "app.py importe `DB_ADMIN_*` depuis config — c'est interdit : "
            "le runtime applicatif n'a pas besoin du compte admin MariaDB. "
            "ENV-PROD-DB-ADMIN-SECRETS-POLICY-001 : seul DB_APP_* est utilisé "
            "au runtime."
        )


# ---------------------------------------------------------------------------
# 2. env/example et env/prod ne contiennent pas de mot de passe admin réel
# ---------------------------------------------------------------------------


# Heuristiques d'un « vrai » mot de passe : non vide, et pas un
# placeholder évident.
_EMPTY_OR_PLACEHOLDER = (
    "",
    "<mot_de_passe_root_mariadb>",
    "<mot_de_passe_admin_mariadb>",
    "<mot_de_passe_root>",
    "<mot_de_passe_admin>",
    "<password>",
    "<your-password>",
    "change-me",
    "changeme",
    "default",
    "secret",
    "<set_in_local_file>",
)


def _is_real_secret(value: str) -> bool:
    if not value:
        return False
    v = value.strip()
    if v in _EMPTY_OR_PLACEHOLDER:
        return False
    if v.startswith("<") and v.endswith(">"):
        return False
    return True


class TestEnvTemplatesHaveNoRealAdminSecret:
    """`env/example` (tracké) et `env/prod` (local si présent) ne
    doivent pas contenir un vrai mot de passe admin."""

    def test_env_example_db_admin_pwd_is_empty_or_placeholder(self):
        pairs = _env_pairs(_ENV_EXAMPLE)
        assert "DB_ADMIN_PWD" in pairs, (
            "env/example doit contenir une ligne `DB_ADMIN_PWD=` (vide ou "
            "placeholder) pour documenter la variable."
        )
        value = pairs["DB_ADMIN_PWD"]
        assert not _is_real_secret(value), (
            f"env/example contient un mot de passe admin réel : "
            f"`DB_ADMIN_PWD={value!r}`. Doit être vide ou un placeholder "
            "explicite (`<mot_de_passe_root_mariadb>`)."
        )

    def test_env_prod_local_has_no_real_admin_pwd(self):
        """Soft check sur env/prod local : si présent, ne doit pas avoir
        de vrai mot de passe. Skip si absent (cas CI propre)."""
        if not _ENV_PROD_LOCAL.is_file():
            pytest.skip("env/prod local absent — rien à vérifier.")
        pairs = _env_pairs(_ENV_PROD_LOCAL)
        value = pairs.get("DB_ADMIN_PWD", "")
        assert not _is_real_secret(value), (
            "env/prod local contient un mot de passe admin réel "
            "(`DB_ADMIN_PWD` non vide et non placeholder). Politique "
            "ENV-PROD-DB-ADMIN-SECRETS-POLICY-001 : utiliser un fichier "
            "local non commité (env/db-admin.local) à la place."
        )


# ---------------------------------------------------------------------------
# 3. .gitignore protège env/*.local
# ---------------------------------------------------------------------------


class TestGitignoreProtectsLocalAdminFile:
    """Le fichier `env/db-admin.local` (recommandé pour les opérations
    de provisioning) doit être ignoré par Git."""

    def test_gitignore_covers_env_local(self):
        lines = _gitignore_lines()
        # Patterns acceptés (du plus permissif au plus spécifique).
        accepted_patterns = {
            "env/*.local",
            "env/db-admin.local",
            "*.local",
            "env/db-admin.local.env",
            "env/*",  # tolère un blacklist global (mais env/example doit
                      # alors être whitelisté avec !env/example)
        }
        matched = [p for p in accepted_patterns if p in lines]
        if not matched:
            pytest.fail(
                ".gitignore ne couvre pas le fichier local d'administration. "
                "Ajouter `env/*.local` pour protéger les secrets DB_ADMIN_* "
                "stockés localement (env/db-admin.local). "
                f"Patterns acceptés : {sorted(accepted_patterns)}."
            )


# ---------------------------------------------------------------------------
# 4. Documentation explicite
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def prod_security_text() -> str:
    assert _PROD_SECURITY_DOC.is_file(), (
        f"{_PROD_SECURITY_DOC.relative_to(_REPO_ROOT)} doit exister."
    )
    return _PROD_SECURITY_DOC.read_text(encoding="utf-8")


class TestDocumentationStatesThePolicy:
    def test_doc_distinguishes_provisioning_vs_runtime(self, prod_security_text):
        # « provisioning » et « runtime » doivent apparaître à proximité
        # de DB_ADMIN_* / DB_APP_*. On vérifie la présence des deux mots
        # clés dans le document.
        lowered = prod_security_text.lower()
        assert "provisioning" in lowered, (
            "La doc doit qualifier `DB_ADMIN_*` de variables de provisioning."
        )
        assert "runtime" in lowered, (
            "La doc doit qualifier `DB_APP_*` de variables de runtime."
        )

    def test_doc_mentions_no_real_admin_password_in_env_prod(
        self, prod_security_text
    ):
        # Marqueurs : la doc doit dire explicitement de ne pas stocker
        # un mot de passe admin réel dans env/prod.
        lowered = prod_security_text.lower()
        markers = (
            "aucun mot de passe root/admin",
            "ne jamais stocker",
            "ne doit pas être stocké",
            "ne JAMAIS stocker",
            "ne pas stocker",
        )
        assert any(m.lower() in lowered for m in markers), (
            "La doc doit énoncer explicitement la règle « pas de mot de "
            "passe admin réel dans env/prod »."
        )

    def test_doc_mentions_env_local_pattern(self, prod_security_text):
        # La doc doit recommander un fichier local non commité.
        markers = ("env/db-admin.local", "env/*.local")
        assert any(m in prod_security_text for m in markers), (
            "La doc doit recommander un fichier local non commité "
            "(env/db-admin.local) pour les secrets admin de provisioning."
        )

    def test_doc_separates_db_app_and_db_admin_in_table(
        self, prod_security_text
    ):
        """Le tableau de séparation des comptes doit être présent."""
        assert "DB_APP_" in prod_security_text
        assert "DB_ADMIN_" in prod_security_text
