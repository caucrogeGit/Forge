"""`RBAC-CONTRACT-EXPORT-001` — rendre le contrat lisible.

`rbac:validate` dit si le contrat est valide, `rbac:audit` le compare à la
base. Ni l'un ni l'autre ne répond à « qui a le droit de faire quoi », question
d'une revue de sécurité, d'un audit, ou d'un nouveau venu dans l'équipe.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac.export import (  # noqa: E402
    CSV_COLUMNS,
    RbacExportError,
    contract_rows,
    to_csv,
    to_markdown,
)

_CONTRAT: "dict[str, Any]" = {
    "roles": {
        "admin": {"Article": ["index", "create", "destroy"], "User": True},
        "editeur": {"Article": ["index", "create"]},
    }
}


class TestLignesDuContrat:

    def test_un_triplet_par_action(self) -> None:
        """C'est la granularité d'une revue, qui se demande « ce rôle peut il
        supprimer », pas « ce rôle touche il à cette entité »."""
        assert ("admin", "Article", "destroy") in contract_rows(_CONTRAT)

    def test_le_resultat_est_trie(self) -> None:
        """Sans tri, un réarrangement du JSON ferait apparaître une différence
        là où rien n'a changé."""
        lignes = contract_rows(_CONTRAT)

        assert lignes == sorted(lignes)

    def test_la_forme_abregee_devient_une_etoile(self) -> None:
        assert ("admin", "User", "*") in contract_rows(_CONTRAT)

    def test_un_contrat_absent_ne_leve_pas(self) -> None:
        assert contract_rows(None) == []

    def test_un_contrat_sans_roles_leve(self) -> None:
        with pytest.raises(RbacExportError, match="roles"):
            contract_rows({"autre": 1})


class TestMarkdown:

    def test_il_porte_un_tableau(self) -> None:
        rendu = to_markdown(_CONTRAT)

        assert "| Rôle | Entité | Actions |" in rendu

    def test_les_actions_d_un_couple_sont_reunies(self) -> None:
        """Un tableau d'une ligne par action serait exact et illisible, et
        c'est la lisibilité qui est la raison d'être de cette sortie."""
        rendu = to_markdown(_CONTRAT)

        assert "| `admin` | `Article` | create, destroy, index |" in rendu

    def test_il_compte(self) -> None:
        rendu = to_markdown(_CONTRAT)

        assert "2 rôle(s)" in rendu
        assert "6 permission(s)" in rendu

    def test_il_dit_qu_il_rend_le_contrat_et_non_la_base(self) -> None:
        """Confondre les deux ferait prendre une intention pour un état."""
        assert "rbac:audit" in to_markdown(_CONTRAT)

    def test_un_contrat_vide_le_dit(self) -> None:
        assert "Aucun rôle déclaré" in to_markdown({"roles": {}})


class TestCsv:

    def test_l_en_tete_est_celui_attendu(self) -> None:
        assert to_csv(_CONTRAT).splitlines()[0] == ",".join(CSV_COLUMNS)

    def test_un_triplet_par_ligne(self) -> None:
        lignes = to_csv(_CONTRAT).splitlines()

        assert "admin,Article,create" in lignes

    def test_les_cellules_sont_echappees(self) -> None:
        """Un nom de rôle commençant par `=` redeviendrait une formule vive."""
        rendu = to_csv({"roles": {"=cmd|calc": {"A": ["index"]}}})

        assert "'=cmd" in rendu

    def test_un_contrat_vide_rend_l_en_tete_seul(self) -> None:
        assert to_csv({"roles": {}}).strip() == ",".join(CSV_COLUMNS)


class TestCommande:

    def test_un_format_inconnu_est_refuse(self) -> None:
        from forge_mvc_rbac.cli.export import parse_options

        assert parse_options(["--format", "pdf"]).error is not None

    def test_un_argument_inattendu_est_refuse(self) -> None:
        from forge_mvc_rbac.cli.export import parse_options

        assert parse_options(["Article"]).error is not None

    @pytest.mark.parametrize("argv", [["--format", "csv"], ["--format=csv"]])
    def test_les_deux_ecritures_sont_lues(self, argv: list[str]) -> None:
        from forge_mvc_rbac.cli.export import parse_options

        assert parse_options(argv).fmt == "csv"

    def test_le_defaut_est_markdown(self) -> None:
        from forge_mvc_rbac.cli.export import parse_options

        assert parse_options([]).fmt == "markdown"
