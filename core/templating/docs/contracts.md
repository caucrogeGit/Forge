# Le contrat de rendu dans Forge

Ce document décrit l'interface d'un moteur de rendu de gabarits.

Le fichier de code correspondant est `core/templating/contracts.py`.

## 1. À quoi sert ce module ?

Pour découpler le cœur d'une implémentation précise, le rendu de gabarits passe par un **protocole** : tout moteur conforme peut être branché.

## 2. Le protocole `Renderer`

`Renderer` définit l'interface attendue d'un moteur de rendu (rendre un gabarit nommé avec un contexte vers une chaîne).
Le moteur par défaut de Forge ([`TemplateManager`](manager.md), Jinja2) le respecte.

## 3. Contextes d'utilisation

- **Découplage** : typer une dépendance de rendu par `Renderer` plutôt que par une implémentation.

## 4. Voir aussi

- [Le gestionnaire de gabarits](manager.md) : l'implémentation par défaut.
