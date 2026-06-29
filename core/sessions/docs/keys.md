# Les clés de session dans Forge

Ce document décrit les clés de session canoniques et le helper de lecture.
Le fichier de code correspondant est `core/sessions/keys.py`.

## 1. Rôle

Les données rangées dans une session sont accessibles par des clés.
Pour rester cohérent, Forge fixe des clés canoniques en anglais (ADR-003).

Ce module fournit ces clés sous forme de constantes et un helper de lecture, `session_get`.
Le helper accepte aussi les anciens noms français en lecture, afin de ne pas invalider les sessions créées avant Forge 3.0.1.
Ces noms legacy seront retirés en Forge 4.0.

## 2. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Module | `core.sessions.keys` |
| Couche | Sessions |
| Rôle | clés de session canoniques et lecture tolérante au legacy |
| API publique | `session_get(...)`, `SESSION_KEY_AUTHENTICATED`, `SESSION_KEY_USER`, `SESSION_KEY_EXPIRES_AT` |
| Convention | clés en anglais (ADR-003) |
| Compatibilité | noms français acceptés en lecture jusqu'à Forge 4.0 |

## 3. Schémas UML

Ce module est un ensemble de constantes et d'une fonction, sans flux notable.
Le tableau ci-dessous résume les clés canoniques et leur repli legacy.

| Constante | Valeur canonique | Repli legacy lu |
|---|---|---|
| `SESSION_KEY_AUTHENTICATED` | `"authenticated"` | `"authentifie"` |
| `SESSION_KEY_USER` | `"user"` | `"utilisateur"` |
| `SESSION_KEY_EXPIRES_AT` | `"expires_at"` | aucun |

À retenir :

- les clés canoniques sont en anglais ;
- seuls `authenticated` et `user` ont un repli legacy ;
- `expires_at` n'a pas d'alias français ;
- `session_get` applique automatiquement ce repli en lecture.

## 4. API publique

| Élément | Signature ou valeur | Rôle |
|---|---|---|
| `session_get` | `session_get(session: dict[str, Any], key: str, default: Any = None) -> Any` | lit une clé du dict de session, avec repli sur le nom legacy français puis sur `default` |
| `SESSION_KEY_AUTHENTICATED` | `"authenticated"` | clé de l'état d'authentification |
| `SESSION_KEY_USER` | `"user"` | clé de l'identité utilisateur |
| `SESSION_KEY_EXPIRES_AT` | `"expires_at"` | clé du timestamp d'expiration |

## 5. Contextes d'utilisation

| Besoin | Élément |
|---|---|
| Lire une clé de session de façon sûre | `session_get(session, key, default=...)` |
| Référencer la clé d'authentification | `SESSION_KEY_AUTHENTICATED` |
| Référencer la clé utilisateur | `SESSION_KEY_USER` |
| Référencer la clé d'expiration | `SESSION_KEY_EXPIRES_AT` |

## 6. Exemples d'utilisation

Lire l'état d'authentification et l'utilisateur avec repli legacy automatique.

```python
from core.sessions.keys import (
    SESSION_KEY_AUTHENTICATED,
    SESSION_KEY_USER,
    session_get,
)
from core.sessions.manager import get_session_store

store = get_session_store()
session_id = store.create()
session = store.get(session_id) or {}

is_auth = session_get(session, SESSION_KEY_AUTHENTICATED, default=False)
user = session_get(session, SESSION_KEY_USER, default=None)
```

Sur une session legacy contenant `"authentifie"`, `session_get` renvoie quand même la valeur via la clé canonique.

```python
legacy_session = {"authentifie": True, "utilisateur": {"id": 7}}

session_get(legacy_session, "authenticated")   # True (repli sur "authentifie")
session_get(legacy_session, "user")            # {"id": 7} (repli sur "utilisateur")
```

!!! note "Fin de la compatibilité legacy"
    Les noms français (`authentifie`, `utilisateur`) ne sont acceptés qu'en lecture.
    Ils seront retirés en Forge 4.0 : ne pas s'appuyer dessus dans du code neuf.

## Voir aussi

- [Le contrat de backend](contract.md) : la structure de session lue ici.
- [Le backend mémoire](memory_store.md) : où ces clés sont écrites par défaut.
- [Le gestionnaire de backend](manager.md) : obtenir la session à lire.
