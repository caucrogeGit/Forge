# Les erreurs de gabarit dans Forge

Ce document décrit l'erreur de gabarit introuvable et ses messages.

Le fichier de code correspondant est `core/templating/errors.py`.

## 1. À quoi sert ce module ?

Quand un gabarit demandé n'existe pas, Forge lève une erreur claire et affiche un message **adapté à l'environnement** (pédagogique en dev, sobre en prod).

## 2. L'API

| Élément | Rôle |
|---|---|
| `TemplateNotFoundError(template, views_dir=None)` | levée quand un gabarit est introuvable |
| `format_missing_template_dev(template, views_dir)` | message pédagogique en `APP_ENV=dev` (chemin, pistes) |
| `format_missing_template_prod()` | message court en `APP_ENV=prod`, sans fuite de chemin |

## 3. Le contrat dev / prod

- **dev** : le message guide (nom du gabarit attendu, dossier des vues) ;
- **prod** : message minimal, aucune divulgation de chemin du serveur.

## 4. Contextes d'utilisation

- **Rendu** : levée par le gestionnaire de gabarits si la vue manque.

## 5. Voir aussi

- [Le gestionnaire de gabarits](manager.md).
