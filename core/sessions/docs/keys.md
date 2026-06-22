# Les clés de session dans Forge

Ce document décrit les clés de session canoniques et le helper de lecture.

Le fichier de code correspondant est `core/sessions/keys.py`.

## 1. À quoi sert ce module ?

Les données de session sont rangées sous des **clés canoniques** (en anglais, ADR-003).
Ce module fournit ces clés et un helper de lecture sûr.

## 2. L'API

```python
from core.sessions.keys import session_get

valeur = session_get(session, "user_id", default=None)
```

| Fonction | Rôle |
|---|---|
| `session_get(session, key, default=None)` | lit une clé du dict de session, avec valeur de repli |

## 3. Contextes d'utilisation

- **Lecture sûre** : `session_get(session, "...", default=...)` plutôt qu'un accès brut au dict.

## 4. Voir aussi

- [Le contrat de backend](contract.md) : la structure de session lue ici.
- [La session (core/security)](../core-security/session.md) : l'API de cycle de vie.
