"""`NOTIF-STORE-AS-VALIDATED-001` — écrire et relire donnent le même résultat.

`notify` validait le destinataire sur sa forme **élaguée** et stockait la forme
**brute**. Une notification écrite pour `"  professeur.42  "` était donc
invisible à `get_notifications`, `unread_count` et `mark_all_read`, qui
interrogent la valeur telle qu'on la leur passe.

Mesuré avant correction :

    écrit avec recipient = '  professeur.42  '
    lecture avec 'professeur.42'     -> 0 notification(s), 0 non lue(s)

Écrite, comptée comme réussie, et jamais lue. Le pire mode de panne du cycle :
tout paraît avoir marché.

## Le paquet était incohérent d'une fonction à l'autre

`mark_read` élaguait, seule de toutes. Elle a été ajoutée par
`NOTIF-HTTP-ROUTES-001`, qui a donc **creusé** l'écart sans le voir : une
notification au destinataire mal saisi pouvait être listée, par correspondance
brute, et pas marquée lue, par correspondance élaguée.

La normalisation vit désormais à un seul endroit, et l'écriture comme la lecture
la traversent.

## Le type était le seul champ sans validation

`recipient`, `message`, `data` et `target_url` sont tous validés. `type` ne
l'était pas, alors que c'est celui sur lequel un client branche son affichage.

Le vocabulaire reste **ouvert**, et ce n'est pas un oubli : une application
réelle observée écrit `type="copie_a_corriger"`, et fermer la liste à
« info, alerte, tâche » casserait ce que Forge est censé servir. Ce qui est
refusé n'est pas un mot inconnu, c'est une valeur qui ne peut pas qualifier.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_notifications")

from forge_mvc_notifications.errors import NotificationError  # noqa: E402
from forge_mvc_notifications.store import (  # noqa: E402
    TYPE_MAX_LENGTH,
    get_notifications,
    mark_all_read,
    mark_read,
    notify,
    unread_count,
)


class _Db:
    """Magasin en mémoire, à correspondance exacte comme le ferait SQL."""

    def __init__(self) -> None:
        self.lignes: "list[dict[str, Any]]" = []

    def insert(self, sql: str, params: Any) -> int:
        self.lignes.append({
            "id": len(self.lignes) + 1, "recipient": params[0], "type": params[1],
            "message": params[2], "data": params[3], "read_at": None,
            "created_at": "2026-09-05", "target_url": params[4],
        })
        return len(self.lignes)

    def fetch_all(self, sql: str, params: Any) -> "list[dict[str, Any]]":
        return [dict(l) for l in self.lignes if l["recipient"] == params[0]]

    def fetch_one(self, sql: str, params: Any) -> "dict[str, Any]":
        return {"n": sum(1 for l in self.lignes
                         if l["recipient"] == params[0] and l["read_at"] is None)}

    def execute(self, sql: str, params: Any) -> int:
        touchees = 0
        for ligne in self.lignes:
            if ligne["read_at"] is not None:
                continue
            if "id = ?" in sql:
                vise = ligne["id"] == params[0] and (
                    len(params) < 2 or ligne["recipient"] == params[1])
            else:
                vise = ligne["recipient"] == params[0]
            if vise:
                ligne["read_at"] = "lu"
                touchees += 1
        return touchees


# ─────────────────────────────────────────────────────────────────────────────
# Écrire puis relire
# ─────────────────────────────────────────────────────────────────────────────


class TestAllerRetour:

    @pytest.mark.parametrize(
        "saisi", ["professeur.42", "  professeur.42  ", "professeur.42\n", "\tprofesseur.42"],
        ids=["net", "espaces", "saut-de-ligne", "tabulation"],
    )
    def test_ce_qui_est_ecrit_se_relit(self, saisi: str) -> None:
        """Le cas qui échouait : écrit, compté comme réussi, jamais lu."""
        db = _Db()
        notify(saisi, "Copie à corriger", db=db)

        assert len(get_notifications("professeur.42", db=db)) == 1
        assert unread_count("professeur.42", db=db) == 1

    def test_la_forme_stockee_est_la_forme_validee(self) -> None:
        db = _Db()
        notify("  professeur.42  ", "message", db=db)

        assert db.lignes[0]["recipient"] == "professeur.42"

    @pytest.mark.parametrize(
        "lu", ["professeur.42", "  professeur.42  "], ids=["net", "espaces"])
    def test_la_lecture_tolere_la_meme_negligence(self, lu: str) -> None:
        db = _Db()
        notify("professeur.42", "message", db=db)

        assert len(get_notifications(lu, db=db)) == 1
        assert unread_count(lu, db=db) == 1

    def test_marquer_tout_lu_trouve_les_memes_lignes(self) -> None:
        """`mark_all_read` interrogeait la forme brute : une notification
        écrite avec des espaces restait non lue pour toujours."""
        db = _Db()
        notify("  professeur.42  ", "message", db=db)

        assert mark_all_read("professeur.42", db=db) == 1
        assert unread_count("professeur.42", db=db) == 0

    def test_marquer_une_lue_trouve_la_meme_ligne(self) -> None:
        """`mark_read` était la seule à élaguer, et creusait l'écart : une
        notification pouvait être listée sans pouvoir être marquée lue."""
        db = _Db()
        identifiant = notify("  professeur.42  ", "message", db=db)

        assert mark_read(identifiant, recipient="professeur.42", db=db) is True


# ─────────────────────────────────────────────────────────────────────────────
# Le type est validé comme les autres champs
# ─────────────────────────────────────────────────────────────────────────────


class TestTypeValide:

    def test_le_type_est_stocke_elague(self) -> None:
        db = _Db()
        notify("p.1", "message", type="  alerte  ", db=db)

        assert db.lignes[0]["type"] == "alerte"

    @pytest.mark.parametrize("vide", ["", "   ", "\n"])
    def test_un_type_vide_est_refuse(self, vide: str) -> None:
        """Se rabattre en silence sur « info » donnerait un type que personne
        n'a écrit."""
        with pytest.raises(NotificationError):
            notify("p.1", "message", type=vide, db=_Db())

    def test_le_refus_dit_comment_obtenir_le_defaut(self) -> None:
        with pytest.raises(NotificationError) as leve:
            notify("p.1", "message", type="", db=_Db())

        assert "Omettez le paramètre" in str(leve.value)

    def test_un_type_trop_long_est_refuse(self) -> None:
        """Tronquer donnerait un type sur lequel un gabarit brancherait à
        tort ; la base le tronquerait en silence sur certains backends."""
        with pytest.raises(NotificationError) as leve:
            notify("p.1", "message", type="a" * (TYPE_MAX_LENGTH + 1), db=_Db())

        assert str(TYPE_MAX_LENGTH) in str(leve.value)

    def test_la_longueur_limite_passe(self) -> None:
        db = _Db()
        notify("p.1", "message", type="a" * TYPE_MAX_LENGTH, db=db)

        assert db.lignes[0]["type"] == "a" * TYPE_MAX_LENGTH

    def test_le_plafond_est_celui_de_la_colonne(self) -> None:
        """Un plafond plus large que la colonne rendrait la validation
        décorative : la base refuserait ou tronquerait ensuite."""
        from forge_mvc_notifications.tables import NOTIFICATIONS

        colonne = next(c for c in NOTIFICATIONS.columns if c.name == "type")

        assert TYPE_MAX_LENGTH == colonne.length

    @pytest.mark.parametrize(
        "nature", ["info", "alerte", "copie_a_corriger", "tache.rappel", "URGENT"])
    def test_le_vocabulaire_reste_ouvert(self, nature: str) -> None:
        """Une application réelle écrit `copie_a_corriger` : fermer la liste
        casserait ce que Forge est censé servir."""
        db = _Db()
        notify("p.1", "message", type=nature, db=db)

        assert db.lignes[0]["type"] == nature


# ─────────────────────────────────────────────────────────────────────────────
# Aucune fonction ne reste en dehors
# ─────────────────────────────────────────────────────────────────────────────


class TestAucuneFonctionNonNormalisee:

    def test_toutes_les_fonctions_a_destinataire_normalisent(self) -> None:
        """Lu par `ast` : c'est l'incohérence d'une fonction à l'autre qui a
        fait le défaut, et une fonction ajoutée demain la referait.
        """
        import ast
        from pathlib import Path

        module = (Path(__file__).resolve().parents[1]
                  / "forge_mvc_notifications" / "store.py")
        arbre = ast.parse(module.read_text(encoding="utf-8"))

        muettes: "list[str]" = []
        for noeud in arbre.body:
            if not isinstance(noeud, ast.FunctionDef) or noeud.name.startswith("_"):
                continue
            parametres = {a.arg for a in noeud.args.args} | {
                a.arg for a in noeud.args.kwonlyargs}
            if "recipient" not in parametres:
                continue
            appels = {
                n.func.id for n in ast.walk(noeud)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
            if "_destinataire" not in appels:
                muettes.append(noeud.name)

        assert not muettes, (
            f"ces fonctions prennent un destinataire sans le normaliser : "
            f"{', '.join(muettes)}. Écrire et lire ne trouveraient plus les "
            f"mêmes lignes.")
