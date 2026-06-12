"""Tests documentaires — comptes MariaDB d'un projet Forge.

Garde-fous relocalisés depuis l'ancienne page « tout-en-un » windows-wsl
(INSTALL-WSL-DOCS-FIELD-FIX-001) : le parcours MariaDB sécurisé
(`forge_admin` dédié plutôt que `root`, création/réparation du compte,
droits limités) vit désormais dans `docs/install/mariadb-comptes.md`.

Ce test verrouille ce contrat de sécurité sur sa nouvelle page.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/install/mariadb-comptes.md")
MKDOCS = Path("mkdocs.yml")


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/install/mariadb-comptes.md introuvable."

    def test_titre_h1(self):
        first_h1 = next(line for line in _text().splitlines() if line.startswith("# "))
        assert "comptes MariaDB" in first_h1

    def test_nav_reference_la_page(self):
        assert "install/mariadb-comptes.md" in MKDOCS.read_text(encoding="utf-8")


class TestCompteForgeAdmin:
    def test_recommande_forge_admin(self):
        text = _text()
        assert "forge_admin" in text
        assert "DB_ADMIN_LOGIN=forge_admin" in text

    def test_ne_recommande_pas_root_comme_admin(self):
        """`DB_ADMIN_LOGIN=root` ne doit apparaître qu'en contre-exemple."""
        occurrences = _text().count("DB_ADMIN_LOGIN=root")
        assert occurrences <= 1, (
            f"`DB_ADMIN_LOGIN=root` apparaît {occurrences} fois — il ne doit "
            "jamais être présenté comme parcours principal."
        )

    def test_avertit_de_ne_pas_utiliser_root_comme_applicatif(self):
        normalized = " ".join(_text().split())
        assert "ne pas utiliser `root`" in normalized.lower() or (
            "ne pas utiliser" in normalized.lower() and "root" in normalized
        )


class TestCreationCompte:
    def test_create_user_if_not_exists(self):
        assert "CREATE USER IF NOT EXISTS 'forge_admin'@'localhost'" in _text()

    def test_alter_user_pour_reparation(self):
        """`ALTER USER` rend le tutoriel rejouable : `CREATE USER IF NOT
        EXISTS` ne modifie pas le mot de passe d'un compte existant."""
        assert "ALTER USER 'forge_admin'@'localhost'" in _text()

    def test_grant_option(self):
        """`forge_admin` doit pouvoir créer l'utilisateur applicatif."""
        text = _text()
        assert "CREATE USER" in text
        assert "WITH GRANT OPTION" in text
