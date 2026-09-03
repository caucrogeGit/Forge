"""`MFA-REQUIRED-BY-ROLE-001` — rendre le facteur obligatoire pour un rôle.

Le paquet savait dire si un utilisateur **a** un facteur actif. Il ne savait
pas dire s'il **devrait** en avoir un.

L'application écrivait donc, dans chaque contrôleur sensible, un « si cet
utilisateur est administrateur et n'a pas de MFA, alors refuser ». Elle
l'écrivait bien la première fois, et l'oubliait au troisième écran
d'administration ajouté six mois plus tard.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_mfa")

from forge_mvc_mfa.policy import (  # noqa: E402
    ENV_REQUIRED_ROLES,
    MfaPolicyError,
    check_mfa_requirement,
    is_mfa_required_for,
    required_roles,
    roles_of,
)

_ENV = {ENV_REQUIRED_ROLES: "Admin, comptable"}


class TestPolitique:

    def test_sans_declaration_rien_n_est_obligatoire(self) -> None:
        """Le paquet n'impose pas une politique que personne n'a demandée."""
        assert required_roles(env={}) == frozenset()

    def test_les_noms_sont_normalises(self) -> None:
        """`Admin` et `admin` désignent la même chose, et les distinguer ferait
        échouer une politique pour une majuscule."""
        assert required_roles(env=_ENV) == {"admin", "comptable"}

    def test_une_declaration_sans_role_exploitable_leve(self) -> None:
        with pytest.raises(MfaPolicyError, match="Retirez la variable"):
            required_roles(env={ENV_REQUIRED_ROLES: " , , "})

    def test_un_role_concerne_est_reconnu(self) -> None:
        assert is_mfa_required_for(["Admin"], env=_ENV)

    def test_un_role_ordinaire_ne_l_est_pas(self) -> None:
        assert not is_mfa_required_for(["lecteur"], env=_ENV)


class TestLectureDesRoles:

    @pytest.mark.parametrize(
        "session",
        [
            {"user": {"roles": ["Admin"]}},
            {"user": {"role": "Admin"}},
            {"roles": ["Admin"]},
        ],
    )
    def test_les_trois_emplacements_sont_lus(self, session: "dict[str, Any]") -> None:
        """N'en reconnaître qu'un ferait échouer la politique en silence, ce
        qui est la pire issue pour un contrôle de sécurité."""
        assert "admin" in roles_of(session)

    def test_une_session_vide_ne_leve_pas(self) -> None:
        assert roles_of(None) == frozenset()
        assert roles_of({}) == frozenset()

    def test_une_valeur_inattendue_est_ignoree(self) -> None:
        assert roles_of({"user": {"roles": 42}}) == frozenset()


class TestVerdict:

    def test_un_admin_sans_facteur_doit_s_inscrire(self) -> None:
        verdict = check_mfa_requirement({"user": {"roles": ["Admin"]}}, [], env=_ENV)

        assert verdict.must_enroll
        assert verdict.matching_roles == ("admin",)

    def test_le_motif_nomme_le_role(self) -> None:
        """L'écran qui conduit vers l'inscription doit pouvoir le dire."""
        verdict = check_mfa_requirement({"user": {"roles": ["Admin"]}}, [], env=_ENV)

        assert "admin" in verdict.reason

    def test_plusieurs_roles_concernes_sont_tous_nommes(self) -> None:
        verdict = check_mfa_requirement(
            {"user": {"roles": ["admin", "comptable"]}}, [], env=_ENV
        )

        assert verdict.matching_roles == ("admin", "comptable")
        assert "rôles" in verdict.reason

    def test_un_role_ordinaire_n_est_pas_concerne(self) -> None:
        verdict = check_mfa_requirement({"user": {"roles": ["lecteur"]}}, [], env=_ENV)

        assert not verdict.required
        assert not verdict.must_enroll

    def test_un_admin_avec_facteur_est_satisfait(self) -> None:
        from forge_mvc_mfa.mfa import MFA_STATUS_ACTIVE

        facteurs = [{"user_id": 1, "type": "totp", "status": MFA_STATUS_ACTIVE,
                     "secret": "A" * 32, "created_at": None}]
        verdict = check_mfa_requirement(
            {"user": {"roles": ["admin"]}}, facteurs, env=_ENV
        )

        assert verdict.required
        assert verdict.satisfied
        assert not verdict.must_enroll

    def test_une_session_mal_formee_ne_leve_pas(self) -> None:
        """Un contrôle de sécurité qui échoue en levant priverait d'accès un
        utilisateur légitime."""
        assert not check_mfa_requirement(None, None, env=_ENV).must_enroll

    def test_sans_politique_rien_n_est_exige(self) -> None:
        verdict = check_mfa_requirement({"user": {"roles": ["admin"]}}, [], env={})

        assert not verdict.required
        assert verdict.reason == ""

    def test_le_paquet_n_importe_aucun_opt_in(self) -> None:
        """Les rôles sont lus dans la session, où l'authentification les a
        rangés : la politique n'a pas besoin de savoir d'où ils viennent."""
        import ast
        from pathlib import Path

        import forge_mvc_mfa.policy as module

        arbre = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        importes = {
            (n.module or "") for n in ast.walk(arbre) if isinstance(n, ast.ImportFrom)
        }
        autres = [
            m for m in importes
            if m.startswith("forge_mvc_") and not m.startswith("forge_mvc_mfa")
        ]

        assert autres == []
