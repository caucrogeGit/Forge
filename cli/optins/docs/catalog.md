# Le catalogue des opt-ins dans Forge

Ce document décrit le catalogue canonique des opt-ins officiels.

Le fichier de code correspondant est `cli/optins/catalog.py`.

## 1. À quoi sert ce module ?

C'est la **source de vérité unique** de la famille de commandes `opt-in:*` (ADR-016).
Il décrit les opt-ins officiels, chacun distribué comme package PyPI `forge-mvc-*`.

Le catalogue décrit seulement *ce qui existe* (le plan de distribution).
L'état d'activation d'un projet donné se lit ailleurs, dans la couche `optins/`.

Chaque opt-in porte un *kind* qui dit comment il s'intègre : `route`, `library` ou transversal.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `OptIn` | description d'un opt-in officiel (nom, package, kind…) |
| `optin_names()` | liste les noms d'opt-ins connus |
| `OFFICIAL_OPTINS` | catalogue complet des opt-ins officiels |
| `KIND_LIBRARY` / `KIND_CROSSCUTTING` | constantes de classification du *kind* |

## 3. Contextes d'utilisation

- **Référentiel** : toutes les commandes `opt-in:*` lisent ce catalogue.
- **Cohérence** : aucun opt-in n'est connu en dehors de cette source unique.

## 4. Voir aussi

- [Les conseils d'activation](guidance.md) : messages selon le *kind*.
- [La commande opt-in:list](list.md) : état local des opt-ins.
