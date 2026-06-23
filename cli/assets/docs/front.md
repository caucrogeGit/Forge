# La commande js:init dans Forge

Ce document décrit la commande `forge js:init` (installation des bibliothèques front htmx / Alpine).

Le fichier de code correspondant est `cli/assets/front.py`.

## 1. À quoi sert cette commande ?

`forge js:init` installe les dépendances front optionnelles du projet : htmx, Alpine, ou les deux.
Elle déclare la dépendance npm dans `package.json` puis copie le script minifié depuis `node_modules/` vers `static/vendor/`.
Elle prépare aussi `static/js/app.js` s'il est absent.

Les écritures suivent le mode write-if-new : un fichier déjà présent n'est pas écrasé.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `init_htmx(root=None)` | installe htmx |
| `init_alpine(root=None)` | installe Alpine |
| `init_htmx_alpine(root=None)` | installe les deux |
| `ensure_npm_dependency(root, package_name, default_version)` | déclare une dépendance dans `package.json` |
| `ensure_app_js(project_root)` | crée `static/js/app.js` si absent |
| `init_vendor_script(...)` | copie un script vendor minifié vers `static/vendor/` |
| `main(args)` | point d'entrée de la commande `forge js:init` |

Les versions cibles sont figées dans le module (`HTMX_VERSION`, `ALPINE_VERSION`).

## 3. Contextes d'utilisation

- **Interactivité légère** : ajouter htmx pour des échanges HTML partiels.
- **Réactivité côté client** : ajouter Alpine pour de petits comportements déclaratifs.
- **Projet vierge** : préparer `app.js` au premier branchement front.

## 4. Voir aussi

- [La commande sync:landing](sync_landing.md) : publication de la landing.
- [Les commandes i18n](i18n.md) : catalogues de traduction.
