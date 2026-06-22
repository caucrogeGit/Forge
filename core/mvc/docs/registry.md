# Le registre de contexte Jinja dans Forge

Ce document décrit l'enregistrement de fournisseurs de contexte de gabarit.

Le fichier de code correspondant est `core/mvc/controller/registry.py`.

## 1. À quoi sert ce module ?

Certaines valeurs doivent être disponibles dans **tous** les gabarits (utilisateur courant, helpers…).
Ce registre permet d'enregistrer des **fournisseurs de contexte** que `BaseController.render` injecte automatiquement.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `register_jinja_context_provider(provider)` | enregistre un fournisseur de contexte Jinja2 |
| `iter_jinja_context_providers()` | retourne une copie de la liste des fournisseurs enregistrés |

## 3. Le pattern

C'est un point d'extension : un opt-in (ou l'application) enregistre un fournisseur (ex. helpers `can()` du contrôle d'accès, badges de statut) sans modifier le cœur du rendu.

## 4. Contextes d'utilisation

- **Démarrage** : enregistrer les fournisseurs de contexte transverses.

## 5. Voir aussi

- [Le contrôleur de base](base_controller.md) : `render` consomme ces fournisseurs.
