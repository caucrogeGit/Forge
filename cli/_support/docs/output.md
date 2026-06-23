# Le formatage de sortie CLI dans Forge

Ce document décrit les helpers de formatage des messages du CLI.

Le fichier de code correspondant est `cli/_support/output.py`.

## 1. À quoi sert ce module ?

Les commandes Forge affichent des messages **tagués** cohérents (créé, écrit, préservé, erreur…).
Ce module centralise ce formatage pour que toutes les commandes parlent le même langage visuel.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `tag(...)` | construit un message tagué générique |
| `written(path)` / `created(path)` | fichier écrit / créé |
| `preserved(path)` | fichier existant préservé (jamais écrasé) |
| `error(message)` | message d'erreur formaté |

## 3. Contextes d'utilisation

- **Toute commande CLI** : émettre des messages cohérents (`out.created(...)`, `out.preserved(...)`).

## 4. Voir aussi

- [Les erreurs CLI](errors.md) : sortie d'erreur et code retour.
