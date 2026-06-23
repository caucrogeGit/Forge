# La commande sync:landing dans Forge

Ce document décrit la commande `forge sync:landing`.

Le fichier de code correspondant est `cli/assets/sync_landing.py`.

## 1. À quoi sert cette commande ?

`forge sync:landing` synchronise la landing page vers la documentation.
La source canonique est `mvc/views/landing/index.html` ; la cible est `docs/index.html`.
Les ressources statiques (`static/`) sont copiées vers `docs/static/`.

Le fichier généré porte un en-tête de mise en garde : il ne doit pas être modifié à la main.
La source reste l'unique point de vérité.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `sync_landing(...)` | copie la landing source vers `docs/index.html` |
| `sync_static(...)` | copie `static/` vers `docs/static/` |
| `landing_is_synced(...)` | indique si la cible est à jour par rapport à la source |
| `expected_docs_content(source_path=SOURCE)` | contenu attendu de la cible (source + en-tête généré) |
| `LandingSyncError` | exception levée en cas de source absente ou invalide |
| `main(argv=None)` | point d'entrée de la commande `forge sync:landing` |

## 3. Contextes d'utilisation

- **Publication** : refléter la landing dans le site documentaire.
- **Garde-fou** : `landing_is_synced` permet à un test de détecter une dérive.

## 4. Voir aussi

- [La commande js:init](front.md) : bibliothèques front.
- [Les commandes i18n](i18n.md) : catalogues de traduction.
