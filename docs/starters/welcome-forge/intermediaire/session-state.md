# Mémoriser un état en session

Objectif : mémoriser un état côté serveur **entre** les requêtes.

**Ce que vous allez apprendre :** une requête HTTP est *sans mémoire* — le
serveur oublie tout d'une requête à l'autre. La **session** garde un état
rattaché à l'utilisateur via un cookie `session_id`. Ce palier compte les
visites de la page.

Palier 7 du **niveau intermédiaire** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Supprimer un enregistrement](delete-record.md).

## Ce que ce starter montre

- lire la session courante (`get_session_id` + `get_session`), la **créer** si
  besoin (`store.create()`) ;
- **écrire** dans la session (`store.set(session_id, {...})`) ;
- poser un cookie `session_id` **durci** (`HttpOnly`, `SameSite=Strict`,
  `Secure`) sur la réponse.

Aucune base de données : le store de session par défaut est en mémoire.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `get_session_id` / `get_session` | Lire la session courante. | [Sessions](../../../reference/sessions.md) |
| `get_session_store` | Créer une session, écrire un état. | [Sessions](../../../reference/sessions.md) |
| `BaseController` | `render(...)`. | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/session-state` puis **rechargez** plusieurs fois
→ le compteur augmente à chaque visite.

## Le contrôleur

```python
# mvc/controllers/session_state_controller.py
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store


class SessionStateController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        store = get_session_store()
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        if not session:
            session_id = store.create()
            session = get_session(session_id)

        visits = int(session.get("visits", 0)) + 1
        store.set(session_id, {"visits": visits})

        response = BaseController.render(
            "session_state/index.html",
            context={"visits": visits},
            request=request,
        )
        response.headers["Set-Cookie"] = (
            f"session_id={session_id}; Path=/; HttpOnly; SameSite=Strict; Secure"
        )
        return response
```

### Comprendre ce code

- `get_session_id(request)` lit le cookie ; `get_session(session_id)` renvoie le
  dictionnaire de session (ou `None`).
- S'il n'y a pas encore de session, on en **crée** une (`store.create()`).
- `store.set(session_id, {"visits": visits})` **fusionne** la nouvelle valeur
  dans la session.
- Le cookie `session_id` est posé avec des attributs **durcis** : `HttpOnly`
  (pas accessible en JS), `SameSite=Strict`, `Secure` (HTTPS uniquement).

## À retenir

- HTTP est sans mémoire ; la **session** garde un état entre requêtes.
- Lire / créer / écrire : `get_session`, `store.create()`, `store.set(...)`.
- Le cookie de session est toujours **durci** (`HttpOnly`, `SameSite`, `Secure`).

## Après ce starter

C'est, pour l'instant, le dernier palier disponible du **niveau intermédiaire**.
Faites le point dans le bilan du niveau.

[Bilan du niveau intermédiaire](bilan.md)
