# pyright: strict
"""ADR-001 d'amorçage pour une application Forge (ADR-047).

`forge new` (et `forge agents:init`) écrit ce premier ADR dans
`docs/adr/001-adopter-forge.md` du projet. Il acte une décision réelle (adopter
Forge et ses conventions) et sert d'exemple de format pour les ADR suivants du
projet. Versionné avec Forge ; la date est complétée à l'écriture.
"""
from __future__ import annotations

SEED_ADR = """\
# ADR-001 — Adopter Forge et ses conventions

## Statut

Accepté.

## Date

{date}

## Contexte

Ce projet est une application web bâtie sur le framework Forge.
Forge est un framework MVC Python explicite, testable et durable : pas de magie
cachée, SQL visible, sécurité par défaut, et une CLI qui génère le code répétitif.

Choisir Forge engage le projet sur des conventions précises.
Ce premier ADR les acte et amorce la pratique des ADR pour les décisions à venir.

## Décision

1. Le projet adopte Forge et ses conventions :
   - structure MVC explicite (`mvc/entities`, `models`, `controllers`, `views`,
     `routes.py`) ;
   - entités décrites par des contrats JSON (source de vérité), code généré
     régénérable, code manuel préservé ;
   - routes nommées selon la convention `/<controleur>/<methode>` ;
   - accès base via `core.database.db`, requêtes paramétrées, sans ORM ;
   - sécurité par défaut (authentification, CSRF, sessions) jamais désactivée
     pour aller plus vite ;
   - fonctionnalités optionnelles ajoutées via les opt-ins `forge-mvc-*` à la
     demande.
2. Le projet adopte la **discipline ADR** : toute décision structurante
   (architecture, convention, dépendance, choix difficile à défaire) est
   consignée dans `docs/adr/`, au format de cet ADR.
3. On privilégie les petits incréments à une responsabilité, et on révèle la
   cause d'un problème avant d'en corriger le symptôme.

## Conséquences

- Le « pourquoi » des choix du projet reste tracé et partageable.
- Les contributeurs, humains comme agents IA, disposent d'un cadre commun
  (voir aussi `CLAUDE.md` et `AGENTS.md` à la racine du projet).
- S'écarter d'une convention Forge devient une décision explicite, documentée
  par un nouvel ADR, plutôt qu'une dérive silencieuse.

## Alternatives écartées

- Un framework « tout inclus » avec ORM et comportements implicites : rejeté,
  Forge privilégie l'explicite et le SQL visible.
- Un micro-framework nu sans conventions : rejeté, on perdrait le cadre et les
  générateurs qui font la valeur de Forge.

## Suite

Numéroter les ADR suivants `002`, `003`, etc. dans `docs/adr/`.
"""

_DATE_PLACEHOLDER = "AAAA-MM-JJ (date de création du projet)"


def render_seed_adr(date: str | None = None) -> str:
    """Retourne l'ADR-001 d'amorçage, avec la date du jour si fournie.

    `forge new` passe la date de création ; sans date, un repère explicite est
    laissé pour que le développeur la complète.
    """
    return SEED_ADR.format(date=date or _DATE_PLACEHOLDER)
