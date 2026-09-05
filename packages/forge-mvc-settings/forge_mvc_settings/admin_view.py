# pyright: strict
"""Ce qu'il faut pour éditer les paramètres depuis un écran (ADMIN-SETTINGS-UI-001).

Un paramètre porte une valeur **et** son type, et le store déduit le second de
la première : `set_setting("port", 8000)` écrit `int`. Une page web, elle, ne
reçoit que du texte.

Brancher un CRUD générique sur la table serait un piège. Il faudrait saisir le
type à la main et le tenir cohérent avec la valeur, et une incohérence,
`value_type=int` sur une valeur `abc`, casse toute lecture ultérieure du
paramètre.

Deux pièges plus discrets attendaient une page écrite à la main.

Convertir avec `int(saisie)` lève une `ValueError` nue, donc une erreur cinq
cents là où l'appelant attendait un refus de formulaire.

Et une valeur booléenne se lit `text == "1"` : taper `oui` y enregistre
**faux**, en silence. L'exploitant croit avoir activé une option, et rien ne le
détrompe.

## Ce module ne rend aucune page

Il convertit et décrit ; la page appartient à l'application, et
`forge-mvc-admin` n'est pas importé ici. Un projet sans back-office édite ses
paramètres depuis sa propre interface avec les mêmes fonctions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

from forge_mvc_settings.errors import SettingsError
from forge_mvc_settings.store import JSON_TYPES, SUPPORTED_TYPES, SettingValue

__all__ = [
    "TRUE_INPUTS",
    "FALSE_INPUTS",
    "SettingRow",
    "parse_setting_value",
    "describe_settings",
]

#: Saisies acceptées pour vrai, insensibles à la casse et aux blancs de bord.
TRUE_INPUTS = frozenset({"1", "true", "vrai", "oui", "yes", "on"})

#: Saisies acceptées pour faux.
FALSE_INPUTS = frozenset({"0", "false", "faux", "non", "no", "off"})


@dataclass(frozen=True)
class SettingRow:
    """Un paramètre, tel qu'un écran l'affiche.

    `value` est la valeur typée, `raw` sa forme texte à mettre dans un champ de
    formulaire : afficher `True` dans un champ que l'utilisateur renverra tel
    quel produirait une saisie que `parse_setting_value` refuserait.
    """

    key: str
    value: SettingValue
    value_type: str
    raw: str


def parse_setting_value(raw: str, value_type: str) -> SettingValue:
    """Convertit une saisie texte en valeur typée.

    Contrairement à la lecture interne du store, un refus est **explicite** :
    une page web reçoit des saisies humaines, et une erreur de frappe doit
    produire un message, jamais une erreur cinq cents ni un enregistrement
    silencieusement faux.

    Raises:
        SettingsError: le type est inconnu, ou la saisie ne s'y convertit pas.
    """
    if value_type not in SUPPORTED_TYPES:
        raise SettingsError(
            f"Type inconnu : {value_type!r}. "
            f"Types acceptés : {', '.join(SUPPORTED_TYPES)}."
        )

    texte = raw.strip()
    if value_type == "str":
        # Volontairement `raw` et non `texte` : une valeur textuelle peut
        # légitimement commencer ou finir par une espace.
        return raw

    if value_type == "bool":
        minuscules = texte.lower()
        if minuscules in TRUE_INPUTS:
            return True
        if minuscules in FALSE_INPUTS:
            return False
        raise SettingsError(
            f"Valeur booléenne non reconnue : {raw!r}. "
            f"Acceptées : {', '.join(sorted(TRUE_INPUTS | FALSE_INPUTS))}."
        )

    if not texte:
        raise SettingsError(f"Valeur {value_type} manquante.")

    if value_type == "json":
        try:
            valeur: Any = json.loads(texte)
        except ValueError as exc:
            raise SettingsError(
                f"Valeur json invalide : {exc}. Attendu une liste ou un objet, "
                'par exemple ["pdf", "odt"] ou {"lundi": "8h-17h"}.'
            ) from exc
        if not isinstance(valeur, JSON_TYPES):
            raise SettingsError(
                f"Valeur json scalaire : {raw!r}. Le type json porte les "
                "valeurs composites ; un nombre, un texte ou un booléen a "
                "déjà son propre type."
            )
        return cast("list[Any] | dict[str, Any]", valeur)

    try:
        return int(texte) if value_type == "int" else float(texte)
    except ValueError as exc:
        raise SettingsError(
            f"Valeur {value_type} invalide : {raw!r}."
        ) from exc


def _raw_form(value: SettingValue, value_type: str) -> str:
    """Forme texte d'une valeur, telle qu'un champ de formulaire la porte."""
    if value_type == "bool":
        # `str(True)` donnerait « True », que `parse_setting_value` accepte,
        # mais qui dépend de la langue de Python plutôt que du contrat.
        return "1" if value else "0"
    if value_type == "json":
        # `str(dict)` rendrait la forme Python, apostrophes simples comprises,
        # que `parse_setting_value` refuserait au réenregistrement : le champ
        # aurait affiché quelque chose que l'écran ne sait pas relire.
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def describe_settings(*, db: Any = None) -> list[SettingRow]:
    """Tous les paramètres, triés par clé, prêts pour un affichage.

    Le tri est celui de la clé : un ordre laissé au hasard ferait sauter les
    lignes d'un rafraîchissement à l'autre, et rendrait la page illisible.
    """
    from forge_mvc_settings.store import get_settings_with_types

    lignes = [
        SettingRow(
            key=cle,
            value=valeur,
            value_type=type_valeur,
            raw=_raw_form(valeur, type_valeur),
        )
        for cle, valeur, type_valeur in get_settings_with_types(db=db)
    ]
    return sorted(lignes, key=lambda ligne: ligne.key)
