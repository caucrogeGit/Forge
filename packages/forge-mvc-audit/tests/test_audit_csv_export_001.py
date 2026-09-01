"""AUDIT-CSV-EXPORT-001 : exporter le journal d'audit, en entier.

Un journal se lit à l'écran et s'exporte pour rendre des comptes. Deux choses
l'empêchaient.

`get_audit_log` rend des `AuditEntry` quand un écrivain CSV attend des
dictionnaires : les deux ne se composaient pas.

Surtout, `get_audit_log` borne à mille entrées **en silence**. Un export
demandé sur cent mille lignes en rendait mille sans rien dire. Pour un journal
qu'on exporte précisément parce qu'il fait foi, le fichier paraissait complet.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_audit")

from forge_mvc_audit import (  # noqa: E402
    AUDIT_EXPORT_COLUMNS,
    AuditError,
    entry_to_row,
    iter_audit_rows,
)
from forge_mvc_audit.store import MAX_LIMIT, AuditEntry  # noqa: E402


class _FauxDb:
    """Journal en mémoire, respectant le curseur et la borne du SQL réel."""

    def __init__(self, total: int) -> None:
        self.entrees = [
            {
                "id": i, "actor": "roger", "action": "note.modifiee",
                "target_type": "note", "target_id": str(i), "details": None,
                "created_at": "2026-09-01 10:00:00",
            }
            for i in range(total, 0, -1)
        ]
        self.appels = 0

    def fetch_all(self, sql: str, params: Any) -> list[dict[str, Any]]:
        self.appels += 1
        limite = params[-1]
        avant = params[-2] if "id < ?" in sql else None
        lignes = [l for l in self.entrees if avant is None or l["id"] < avant]
        return lignes[:limite]


class TestExportComplet:
    def test_le_journal_sort_en_entier_au_dela_de_la_borne(self) -> None:
        """Le défaut qui motivait le ticket."""
        faux = _FauxDb(total=MAX_LIMIT + 200)

        lignes = list(iter_audit_rows(db=faux, batch_size=500))

        assert len(lignes) == MAX_LIMIT + 200

    def test_le_parcours_avance_par_lots(self) -> None:
        """Tout charger en mémoire pour écrire ligne à ligne serait absurde."""
        faux = _FauxDb(total=1200)

        list(iter_audit_rows(db=faux, batch_size=500))

        assert faux.appels == 4, "trois lots pleins, puis un vide qui arrête"

    def test_un_journal_vide_ne_rend_rien(self) -> None:
        assert list(iter_audit_rows(db=_FauxDb(total=0))) == []

    def test_l_ordre_est_du_plus_recent_au_plus_ancien(self) -> None:
        lignes = list(iter_audit_rows(db=_FauxDb(total=5)))
        assert [l["id"] for l in lignes] == [5, 4, 3, 2, 1]

    def test_aucune_entree_n_est_repetee(self) -> None:
        """Un OFFSET répéterait des lignes sur une table qui reçoit des écritures."""
        lignes = list(iter_audit_rows(db=_FauxDb(total=1200), batch_size=100))
        identifiants = [l["id"] for l in lignes]

        assert len(identifiants) == len(set(identifiants))

    @pytest.mark.parametrize("taille", [0, -1])
    def test_un_lot_nul_est_refuse(self, taille: int) -> None:
        """Le parcours n'avancerait jamais."""
        with pytest.raises(AuditError, match="batch_size"):
            list(iter_audit_rows(db=_FauxDb(total=1), batch_size=taille))


class TestLigneExportable:
    def test_les_colonnes_sont_figees_et_ordonnees(self) -> None:
        """Un ordre laissé au hasard interdirait de comparer deux exports."""
        assert AUDIT_EXPORT_COLUMNS == (
            "id", "created_at", "actor", "action", "target_type", "target_id", "details",
        )

    def test_une_entree_devient_une_ligne_complete(self) -> None:
        entree = AuditEntry(
            id=1, actor="roger", action="note.modifiee", target_type="note",
            target_id="7", details="avant 12 apres 15", created_at="2026-09-01 10:00:00",
        )

        ligne = entry_to_row(entree)

        assert set(ligne) == set(AUDIT_EXPORT_COLUMNS)
        assert ligne["details"] == "avant 12 apres 15"

    def test_une_valeur_absente_devient_une_chaine_vide(self) -> None:
        """`None` s'écrirait tel quel dans le fichier et se lirait comme une donnée."""
        entree = AuditEntry(
            id=1, actor=None, action="x", target_type=None,
            target_id=None, details=None, created_at="2026-09-01 10:00:00",
        )

        ligne = entry_to_row(entree)

        assert ligne["actor"] == ""
        assert ligne["details"] == ""


class TestFiltres:
    def test_les_filtres_du_journal_sont_transmis(self) -> None:
        vus: list[str] = []

        class _Espion(_FauxDb):
            def fetch_all(self, sql: str, params: Any) -> list[dict[str, Any]]:
                vus.append(sql)
                return super().fetch_all(sql, params)

        list(iter_audit_rows(db=_Espion(total=1), actor="roger", action="note.modifiee"))

        assert "actor = ?" in vus[0]
        assert "action = ?" in vus[0]


class TestSansDependance:
    def test_audit_n_ecrit_aucun_csv(self) -> None:
        """Il rend des lignes ; import-export les écrit, et une autre voie le pourrait."""
        from forge_mvc_audit import export

        arbre = ast.parse(Path(export.__file__).read_text(encoding="utf-8"))
        modules: list[str] = []
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                modules.extend(alias.name for alias in noeud.names)
            elif isinstance(noeud, ast.ImportFrom) and noeud.module:
                modules.append(noeud.module)

        interdits = [m for m in modules if m.startswith("forge_mvc_") and "audit" not in m]
        assert interdits == [], f"dépendance vers un autre opt-in : {interdits}"
        assert "csv" not in modules


class TestCompositionAvecImportExport:
    """Le motif que la référence donne à copier."""

    def test_du_journal_au_fichier_csv(self) -> None:
        pytest.importorskip("forge_mvc_import_export")
        from forge_mvc_import_export import to_csv

        lignes = list(iter_audit_rows(db=_FauxDb(total=3)))
        contenu = to_csv(lignes, list(AUDIT_EXPORT_COLUMNS))

        entete, *corps = contenu.splitlines()
        assert entete == "id,created_at,actor,action,target_type,target_id,details"
        assert len(corps) == 3

    def test_les_cellules_restent_inertes_pour_un_tableur(self) -> None:
        """`to_csv` échappe déjà : l'export d'audit en hérite sans rien réécrire."""
        pytest.importorskip("forge_mvc_import_export")
        from forge_mvc_import_export import to_csv

        entree = AuditEntry(
            id=1, actor="=cmd|'/c calc'!A1", action="x", target_type=None,
            target_id=None, details=None, created_at="2026-09-01 10:00:00",
        )

        contenu = to_csv([entry_to_row(entree)], list(AUDIT_EXPORT_COLUMNS))

        assert "'=cmd" in contenu, "la formule doit être neutralisée par une apostrophe"
