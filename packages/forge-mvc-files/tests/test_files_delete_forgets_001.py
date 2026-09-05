"""`FILES-DELETE-FORGETS-001` — supprimer un fichier le retire aussi du registre.

Les suppressions retiraient le fichier du disque sans toucher au registre. La
ligne restait, et `owner_usage_bytes` somme les tailles inscrites : **le quota
comptait des fichiers qui n'existaient plus**.

Mesuré avant correction :

    après 3 dépôts de 1 Mo   : 3 Mo
    après suppression des 3  : 3 Mo
    lignes restantes         : 3

Un utilisateur qui dépose et supprime finit refusé pour un espace qu'il
n'occupe pas, avec un message « quota dépassé » impossible à diagnostiquer de
l'extérieur : son stockage est vide.

## Trois chemins, un seul défaut

`delete_upload`, `delete_media_file` et `purge_orphan_variants` suppriment tous
des fichiers sous `UPLOAD_ROOT`, et aucun ne désinscrivait. Le dernier est
particulièrement ironique : c'est le nettoyage, et il faisait grossir le quota à
chaque passage.

Le défaut n'est apparu pour les images qu'avec `IMAGES-REGISTRY-RECORD-001`, qui
les a fait inscrire. Il existait déjà pour toute application suivant le chemin
documenté, `save_upload` puis `record_file`, puis `delete_upload`.

## Pourquoi l'oubli est au mieux

La table `forge_files` est optionnelle (ADR-094). Faire échouer une suppression
parce qu'un registre n'est pas provisionné **empêcherait de supprimer**, ce qui
est pire que le défaut corrigé. Sans registre, il n'y a d'ailleurs ni quota ni
purge, donc rien à fausser.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

pytest.importorskip("forge_mvc_files")


class _Registre:
    """Registre en mémoire, aux mêmes requêtes que le vrai."""

    def __init__(self) -> None:
        self.lignes: "list[dict[str, Any]]" = []

    def execute(self, sql: str, params: Any) -> int:
        if sql.strip().upper().startswith("DELETE"):
            avant = len(self.lignes)
            self.lignes[:] = [l for l in self.lignes if l["path"] != params[0]]
            return avant - len(self.lignes)
        self.lignes.append({
            "path": params[0], "size": params[3],
            "kind": params[4], "id": params[5],
        })
        return 1

    def fetch_one(self, sql: str, params: Any) -> "dict[str, Any]":
        return {"total": sum(
            l["size"] for l in self.lignes
            if l["kind"] == params[0] and l["id"] == params[1])}


@pytest.fixture
def registre() -> Any:
    magasin = _Registre()
    with patch("forge_mvc_files.registry._db", return_value=magasin):
        yield magasin


def _inscrire(registre: _Registre, chemin: str, taille: int = 1_000_000) -> None:
    from forge_mvc_files.registry import record_file

    record_file(chemin, Path(chemin).name, taille,
                owner_kind="user", owner_id=7, db=registre)


def _usage(registre: _Registre) -> int:
    from forge_mvc_files.registry import owner_usage_bytes

    return owner_usage_bytes("user", 7, db=registre)


# ─────────────────────────────────────────────────────────────────────────────
# Le quota suit les suppressions
# ─────────────────────────────────────────────────────────────────────────────


class TestDeleteUpload:

    def test_le_quota_redescend(self, registre: _Registre, tmp_path: Path) -> None:
        """Le cas mesuré : trois dépôts, trois suppressions, et un quota qui
        restait plein."""
        from forge_mvc_files import manager

        for i in range(3):
            _inscrire(registre, f"documents/f{i}.pdf")
        assert _usage(registre) == 3_000_000

        with patch.object(manager, "upload_root", return_value=tmp_path):
            for i in range(3):
                manager.delete_upload(f"documents/f{i}.pdf")

        assert _usage(registre) == 0
        assert registre.lignes == []

    def test_l_oubli_a_lieu_meme_si_le_fichier_manquait(
        self, registre: _Registre, tmp_path: Path
    ) -> None:
        """Une inscription qui décrit un fichier absent est fausse dans tous les
        cas : la corriger ne dépend pas du sort du fichier."""
        from forge_mvc_files import manager

        _inscrire(registre, "documents/disparu.pdf")

        with patch.object(manager, "upload_root", return_value=tmp_path):
            supprime = manager.delete_upload("documents/disparu.pdf")

        assert supprime is False, "le fichier n'existait pas"
        assert registre.lignes == []


class TestDeleteMediaFile:

    def test_l_original_et_ses_variantes_sont_oublies(
        self, registre: _Registre, tmp_path: Path
    ) -> None:
        """Les variantes sont inscrites depuis `IMAGES-REGISTRY-RECORD-001` :
        les oublier n'est pas optionnel."""
        pytest.importorskip("forge_mvc_images")
        from forge_mvc_files import manager

        _inscrire(registre, "images/photo.jpg")
        _inscrire(registre, "images/thumbnail/photo.jpg")
        _inscrire(registre, "images/medium/photo.jpg")

        with patch.object(manager, "upload_root", return_value=tmp_path):
            manager.delete_media_file("images/photo.jpg", variants=True)

        assert registre.lignes == [], (
            f"lignes restées au registre : {[l['path'] for l in registre.lignes]}")


class TestPurgeOrphanVariants:

    def test_le_nettoyage_ne_fait_plus_grossir_le_quota(
        self, registre: _Registre, tmp_path: Path
    ) -> None:
        """L'ironie du défaut : c'est le nettoyage, et il gonflait le quota à
        chaque passage."""
        pytest.importorskip("forge_mvc_images")
        from forge_mvc_images.variants_cleanup import purge_orphan_variants

        dossier = tmp_path / "images" / "thumbnail"
        dossier.mkdir(parents=True)
        (dossier / "orpheline.jpg").write_bytes(b"\xff\xd8\xff")
        _inscrire(registre, "images/thumbnail/orpheline.jpg", taille=5_000)
        assert _usage(registre) == 5_000

        from forge_mvc_images.variants_cleanup import VariantOrphanReport

        rapport = VariantOrphanReport(
            without_original=("images/thumbnail/orpheline.jpg",),
            from_removed_presets=(),
            scanned_variants=1,
            declared_presets=("thumbnail",),
        )
        supprimes, echecs = purge_orphan_variants(rapport, root=tmp_path)

        assert supprimes == ("images/thumbnail/orpheline.jpg",)
        assert echecs == ()
        assert _usage(registre) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Le registre indisponible n'empêche pas de supprimer
# ─────────────────────────────────────────────────────────────────────────────


class TestRegistreIndisponible:

    def test_la_suppression_aboutit(self, tmp_path: Path) -> None:
        """Faire échouer une suppression parce qu'un registre n'est pas
        provisionné empêcherait de supprimer, ce qui est pire que le défaut
        corrigé."""
        from forge_mvc_files import manager

        fichier = tmp_path / "documents" / "a.pdf"
        fichier.parent.mkdir(parents=True)
        fichier.write_bytes(b"x")

        with patch.object(manager, "upload_root", return_value=tmp_path), \
             patch("forge_mvc_files.registry.forget_file",
                   side_effect=RuntimeError("no such table: forge_files")):
            assert manager.delete_upload("documents/a.pdf") is True

        assert not fichier.exists()

    def test_l_echec_est_journalise(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Se rabattre est acceptable, se taire ne l'est pas."""
        import logging

        from forge_mvc_files import manager

        with patch.object(manager, "upload_root", return_value=tmp_path), \
             patch("forge_mvc_files.registry.forget_file",
                   side_effect=RuntimeError("table absente")), \
             caplog.at_level(logging.WARNING, logger="forge.files"):
            manager.delete_upload("documents/a.pdf")

        assert "quota" in caplog.text


# ─────────────────────────────────────────────────────────────────────────────
# La classe de défaut ne peut pas revenir
# ─────────────────────────────────────────────────────────────────────────────


class TestAucunCheminDeSuppressionMuet:

    def test_toute_suppression_de_fichier_desinscrit(self) -> None:
        """Lu par `ast` : trois chemins supprimaient sans désinscrire, et un
        quatrième ajouté demain referait le défaut.

        Sont visées les fonctions publiques qui suppriment un fichier, repérées
        par leur appel à `unlink` ou à `storage.delete_file`. `storage.py` en
        est exclu : c'est la primitive de bas niveau, qui ne connaît pas le
        registre et n'a pas à le connaître.
        """
        import ast

        racine = Path(__file__).resolve().parents[2]
        modules = [
            racine / "forge-mvc-files" / "forge_mvc_files" / "manager.py",
            racine / "forge-mvc-images" / "forge_mvc_images" / "variants_cleanup.py",
        ]

        muettes: "list[str]" = []
        for module in modules:
            if not module.is_file():
                continue
            arbre = ast.parse(module.read_text(encoding="utf-8"))
            for noeud in arbre.body:
                if not isinstance(noeud, ast.FunctionDef):
                    continue
                if noeud.name.startswith("_"):
                    continue
                appels = {
                    n.func.attr if isinstance(n.func, ast.Attribute) else
                    n.func.id if isinstance(n.func, ast.Name) else ""
                    for n in ast.walk(noeud) if isinstance(n, ast.Call)
                }
                supprime = "unlink" in appels or "delete_file" in appels
                desinscrit = {"_oublier", "_oublier_du_registre"} & appels
                if supprime and not desinscrit:
                    muettes.append(f"{module.name}:{noeud.name}")

        assert not muettes, (
            f"ces fonctions suppriment un fichier sans le désinscrire : "
            f"{', '.join(muettes)}. Le quota continuerait de le compter.")
