"""`WORKFLOW-CONDITIONS-APPLIED-001` — les conditions enregistrées sont consultées.

`WORKFLOW-CONDITIONS-001` a livré un registre de conditions, et sa raison d'être
est écrite dans son propre module : l'application vérifiait ses règles avant
d'appeler, chacune à sa façon, si bien que « deux chemins menant au même état
s'oubliaient l'un l'autre, et le second passait sans contrôle ».

Le registre ne corrigeait pas cela. `apply_transition`, la seule fonction du
paquet qui sait qu'une transition a lieu, ne le consultait pas. Il fallait
appeler `ensure_conditions` à chaque site, donc se souvenir à chaque site, donc
reproduire exactement le défaut visé.

Mesuré avant correction : une condition enregistrée pour refuser le passage à
`validee` n'était jamais appelée, et `apply_transition` rendait `'validee'`.

## Ce n'est pas de la magie cachée, c'est l'inverse

L'application a **explicitement** enregistré ses conditions. Les consulter à
l'endroit où une transition a lieu est ce pour quoi le registre existe. Un
registre que rien ne lit est une décoration.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_workflow")

from forge_mvc_workflow import (  # noqa: E402
    WorkflowTransitionError,
    apply_transition,
    clear_conditions,
    make_transition,
    register_condition,
)

TRANSITIONS = [
    make_transition("brouillon", "validee"),
    make_transition("validee", "expediee"),
]


@pytest.fixture(autouse=True)
def registre_vide() -> Any:
    clear_conditions()
    yield
    clear_conditions()


# ─────────────────────────────────────────────────────────────────────────────
# Le contrôle décisif
# ─────────────────────────────────────────────────────────────────────────────


class TestConditionConsultee:

    def test_une_condition_qui_refuse_bloque_la_transition(self) -> None:
        """Le cas qui passait, et qui motive le ticket."""
        register_condition(lambda d, v, c: "le stock doit être vérifié",
                           to_status="validee")

        with pytest.raises(WorkflowTransitionError):
            apply_transition(TRANSITIONS, "brouillon", "validee")

    def test_le_refus_porte_le_motif(self) -> None:
        """« Transition impossible » n'indique rien à corriger."""
        register_condition(lambda d, v, c: "le stock doit être vérifié",
                           to_status="validee")

        with pytest.raises(WorkflowTransitionError) as leve:
            apply_transition(TRANSITIONS, "brouillon", "validee")

        assert "le stock doit être vérifié" in str(leve.value)

    def test_une_condition_satisfaite_laisse_passer(self) -> None:
        register_condition(
            lambda d, v, c: None if c.get("stock_ok") else "stock non vérifié",
            to_status="validee")

        assert apply_transition(
            TRANSITIONS, "brouillon", "validee",
            context={"stock_ok": True}) == "validee"

    def test_le_contexte_atteint_la_condition(self) -> None:
        """Sans lui, une condition ne peut rien décider d'utile."""
        vus: "list[Any]" = []
        register_condition(lambda d, v, c: vus.append((d, v, dict(c))) or None)

        apply_transition(TRANSITIONS, "brouillon", "validee",
                         context={"utilisateur": 7})

        assert vus == [("brouillon", "validee", {"utilisateur": 7})]

    def test_sans_condition_rien_ne_change(self) -> None:
        """Un projet qui n'en enregistre aucune ne doit voir aucune différence."""
        assert apply_transition(TRANSITIONS, "brouillon", "validee") == "validee"

    def test_une_condition_visant_un_autre_etat_ne_s_applique_pas(self) -> None:
        register_condition(lambda d, v, c: "jamais atteinte", to_status="expediee")

        assert apply_transition(TRANSITIONS, "brouillon", "validee") == "validee"


# ─────────────────────────────────────────────────────────────────────────────
# L'ordre, et ce qu'il protège
# ─────────────────────────────────────────────────────────────────────────────


class TestOrdre:

    def _etapes(self, faits: "list[str]") -> "dict[str, Any]":
        return {
            "before": lambda e: faits.append("before"),
            "commit": lambda e: faits.append("commit"),
            "after": lambda e: faits.append("after"),
        }

    def test_aucun_effet_de_bord_si_une_condition_refuse(self) -> None:
        """`before` peut écrire : refuser après lui laisserait la trace d'une
        transition qui n'a pas eu lieu."""
        register_condition(lambda d, v, c: "non", to_status="validee")
        faits: "list[str]" = []

        with pytest.raises(WorkflowTransitionError):
            apply_transition(TRANSITIONS, "brouillon", "validee",
                             **self._etapes(faits))

        assert faits == []

    def test_l_ordre_reste_celui_qui_est_annonce(self) -> None:
        faits: "list[str]" = []

        apply_transition(TRANSITIONS, "brouillon", "validee", **self._etapes(faits))

        assert faits == ["before", "commit", "after"]

    def test_une_transition_non_declaree_est_refusee_avant_les_conditions(
        self,
    ) -> None:
        """Consulter les conditions d'un passage qui n'existe pas ferait
        exécuter du code de l'application pour rien, et rendrait un motif
        métier là où le contrat est en cause."""
        vus: "list[Any]" = []
        register_condition(lambda d, v, c: vus.append(1) or None)

        with pytest.raises(WorkflowTransitionError) as leve:
            apply_transition(TRANSITIONS, "brouillon", "expediee")

        assert "non déclarée" in str(leve.value)
        assert vus == []


# ─────────────────────────────────────────────────────────────────────────────
# Une condition en panne ne laisse pas passer
# ─────────────────────────────────────────────────────────────────────────────


class TestPanneDUneCondition:
    """Le jour où le service qu'une condition interroge tombe, toutes les
    transitions passeraient si l'on traitait son silence comme un accord."""

    def test_une_condition_qui_leve_refuse(self) -> None:
        def _casse(depuis: str, vers: str, contexte: "dict[str, Any]") -> None:
            raise RuntimeError("service indisponible")

        register_condition(_casse, to_status="validee")

        with pytest.raises(WorkflowTransitionError):
            apply_transition(TRANSITIONS, "brouillon", "validee")

    def test_une_condition_au_verdict_illisible_refuse(self) -> None:
        register_condition(lambda d, v, c: 42, to_status="validee")  # type: ignore[arg-type,return-value]

        with pytest.raises(WorkflowTransitionError):
            apply_transition(TRANSITIONS, "brouillon", "validee")


# ─────────────────────────────────────────────────────────────────────────────
# Le paquet ne laisse plus une transition ignorer son registre
# ─────────────────────────────────────────────────────────────────────────────


class TestAucunCheminNonControle:

    def test_apply_transition_consulte_le_registre(self) -> None:
        """Lu par `ast` : une réécriture qui perdrait cet appel rendrait le
        registre décoratif, et le défaut reviendrait en silence."""
        import ast
        from pathlib import Path

        module = (Path(__file__).resolve().parents[1]
                  / "forge_mvc_workflow" / "hooks.py")
        arbre = ast.parse(module.read_text(encoding="utf-8"))
        fonction = next(
            n for n in ast.walk(arbre)
            if isinstance(n, ast.FunctionDef) and n.name == "apply_transition")
        appels = {
            n.func.id for n in ast.walk(fonction)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}

        assert "ensure_conditions" in appels
