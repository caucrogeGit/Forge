# pyright: strict
"""ADR d'amorçage pour une application Forge (ADR-047).

`forge new` (et `forge agents:init`) écrit deux ADR d'amorçage dans le projet :

- `docs/adr/001-adopter-forge.md` : adopter Forge et ses conventions ;
- `docs/adr/002-style-documentation.md` : règles de rédaction de la doc.

Les deux actent une décision réelle et servent d'exemple de format pour les ADR
suivants du projet. Versionnés avec Forge ; la date est complétée à l'écriture.
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

SEED_ADR_DOC_STYLE = """\
# ADR-002 : Style et rédaction de la documentation

## Statut

Accepté.

## Date

{date}

## Contexte

La documentation du projet (guides, pages du site, README, ADR, notes) doit
rester lisible, homogène et durable, quel que soit l'auteur, humain ou agent IA.
Sans règle explicite, le style dérive : mélange de langues, ponctuation
irrégulière, caractères typographiques hétérogènes, phrases empilées sur une
seule ligne difficiles à relire en diff.

Forge applique déjà ces conventions à sa propre documentation.
Ce projet les reprend à son compte pour partir sur une base saine.

## Décision

Toute documentation du projet respecte les règles suivantes.

1. **Langue** : rédiger en français, sauf les noms de commandes, symboles de
   code et termes techniques indispensables.
2. **Une phrase par ligne** dans la source Markdown : après le point final,
   la phrase suivante commence sur une nouvelle ligne.
   Cela garde les diffs lisibles et se prête au rendu ligne à ligne.
3. **Pas de tiret cadratin** (le caractère long).
   Préférer la virgule, le point-virgule, les deux-points, ou le trait d'union
   court selon le sens.
4. **Ponctuation française** : espaces insécables avant les signes doubles
   (deux-points, point-virgule, point d'interrogation, point d'exclamation) et
   autour des guillemets français.
5. **Liens internes** vers le fichier `.md` cible, vérifiés au build strict de
   la documentation.
6. **Éviter les anglicismes** inutiles et les tournures calquées sur l'anglais.

Cette décision porte sur la rédaction, pas sur le fond : elle s'applique aux
corrections comme aux nouveaux documents.

## Conséquences

- La documentation reste homogène et relisible, y compris en revue de diff.
- Les contributeurs, humains comme agents IA, disposent d'une règle unique et
  explicite à suivre et à faire respecter.
- Un écart de style devient un correctif simple, pas une négociation.

## Alternatives écartées

- Laisser le style au jugement de chaque auteur : rejeté, la documentation
  dérive vite et devient incohérente.
- Adopter un style typographique anglo-saxon (tiret cadratin, pas d'espaces
  insécables) : rejeté, le projet rédige en français et vise une lecture
  française correcte.

## Suite

Ces règles valent pour tous les ADR suivants et pour l'ensemble de la
documentation du projet.
"""


_DATE_PLACEHOLDER = "AAAA-MM-JJ (date de création du projet)"


def render_seed_adr(date: str | None = None) -> str:
    """Retourne l'ADR-001 d'amorçage, avec la date du jour si fournie.

    `forge new` passe la date de création ; sans date, un repère explicite est
    laissé pour que le développeur la complète.
    """
    return SEED_ADR.format(date=date or _DATE_PLACEHOLDER)


def render_seed_adr_doc_style(date: str | None = None) -> str:
    """Retourne l'ADR-002 d'amorçage (style de documentation), daté si fourni.

    Posé par `forge new` et `forge agents:init` en write-if-new, à côté de
    l'ADR-001. Donne à chaque nouveau projet une règle de rédaction explicite.
    """
    return SEED_ADR_DOC_STYLE.format(date=date or _DATE_PLACEHOLDER)
