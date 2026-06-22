# Le contrat de backend de session dans Forge

Ce document décrit l'interface qu'un backend de stockage de session doit implémenter.

Le fichier de code correspondant est `core/sessions/contract.py`.

## 1. À quoi sert ce module ?

Forge sait stocker les sessions de plusieurs façons (mémoire, fichier, base).
Ce module définit le **contrat** commun (`SessionStore`) que tout backend respecte, pour qu'ils soient interchangeables.

## 2. Le protocole `SessionStore`

Un backend de session implémente notamment :

| Méthode | Rôle |
|---|---|
| `create()` | crée une session, retourne son identifiant |
| `get(session_id)` | les données de la session, ou `None` |
| `set(session_id, data)` | remplace les données de la session |
| `delete(session_id)` | supprime la session |
| `regenerate(session_id)` | nouvel identifiant en conservant les données |
| `authenticate(session_id, user)` | marque la session authentifiée |
| `touch_expiry(session_id)` | prolonge la durée de vie |
| `set_flash` / `get_flash` | messages flash |

## 3. Contextes d'utilisation

- **Brancher un backend** : fournir un objet conforme à `set_session_store` (voir [le gestionnaire](manager.md)).
- **Backend sur mesure** : implémenter `SessionStore` pour un stockage spécifique.

## 4. Voir aussi

- [Le gestionnaire de backend](manager.md) : choisir le backend actif.
- [Backend mémoire](memory_store.md), [fichier](file_store.md), [MariaDB](mariadb_store.md).
