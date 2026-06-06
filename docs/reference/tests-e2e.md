# Tests HTTP E2E

Forge dispose de tests HTTP E2E minimaux (`tests/test_http_e2e_001.py`) qui démarrent le serveur localement sur un port libre et vérifient les réponses HTTP réelles :

- `GET /` retourne une réponse valide
- Routes inconnues retournent 404
- Headers de sécurité présents sur toutes les réponses (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
- Fichiers statiques servis correctement
- Tentatives de path traversal bloquées
- CSP nonce injecté quand `APP_CSP_NONCE_ENABLED=true`

La fixture démarre un sous-processus via `tests/_e2e_launcher.py`. Elle ne dépend pas de MariaDB.

---

## Tests E2E MariaDB

Forge dispose d'un test d'intégration MariaDB réel (`tests/test_e2e_mariadb.py`) qui applique le SQL généré sur une vraie base de données et vérifie les résultats.

**Ces tests sont désactivés par défaut.** Ils ne s'exécutent que si `FORGE_E2E_MARIADB=1` est défini.

### Activation

```bash
FORGE_E2E_MARIADB=1 \
  FORGE_E2E_DB_HOST=127.0.0.1 \
  FORGE_E2E_DB_PORT=3306 \
  FORGE_E2E_DB_NAME=forge_e2e_test \
  FORGE_E2E_DB_USER=forge_e2e_user \
  FORGE_E2E_DB_PASSWORD=secret \
  pytest tests/test_e2e_mariadb.py
```

### Variables

| Variable | Défaut | Rôle |
|---|---|---|
| `FORGE_E2E_MARIADB` | _(absent)_ | Active les tests (`1` pour activer) |
| `FORGE_E2E_DB_HOST` | `127.0.0.1` | Hôte MariaDB |
| `FORGE_E2E_DB_PORT` | `3306` | Port MariaDB |
| `FORGE_E2E_DB_NAME` | _(requis)_ | Nom de la base — **doit commencer par `forge_e2e_`** |
| `FORGE_E2E_DB_USER` | _(requis)_ | Utilisateur MariaDB |
| `FORGE_E2E_DB_PASSWORD` | _(vide)_ | Mot de passe |

### Sécurité

Si `FORGE_E2E_DB_NAME` ne commence pas par `forge_e2e_`, les tests refusent de s'exécuter (erreur de collection pytest). Cette garde protège contre toute exécution accidentelle sur une base applicative réelle.

### Préparation de la base

L'utilisateur MariaDB doit avoir les droits `SELECT`, `INSERT`, `CREATE`, `DROP` sur la base de test :

```sql
CREATE DATABASE IF NOT EXISTS forge_e2e_test
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'forge_e2e_user'@'127.0.0.1' IDENTIFIED BY 'secret';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP
  ON forge_e2e_test.* TO 'forge_e2e_user'@'127.0.0.1';
```

### Cycle testé

1. Connexion directe à MariaDB
2. Génération d'entité Contact via `make:entity --no-input`
3. Application SQL via `apply_model_sql` (SQL `CREATE TABLE IF NOT EXISTS`)
4. Vérification de la table et de la colonne `id`
5. Insertion simple et lecture
6. Nettoyage (`DROP TABLE IF EXISTS contact`) avant et après

---

## CSRF — Mécanisme et tests quasi-HTTP

### Fonctionnement

Forge protège par défaut toutes les méthodes HTTP non sûres (`POST`, `PUT`, `PATCH`, `DELETE`) via un mécanisme CSRF opt-out.

**Modèle opt-out** — `csrf=True` est la valeur par défaut de chaque route. Une route doit déclarer explicitement `csrf=False` pour être exemptée.

**Stockage du token** — `MemorySessionStore.create()` génère un token avec `secrets.token_hex(16)` et le stocke sous la clé `"csrf_token"` dans la session au moment de sa création. Le token est renouvelé lors de l'authentification (`authentifier_session()`).

**Injection dans les templates** — `BaseController.render()` injecte `csrf_token` dans le contexte Jinja2. Les générateurs CRUD (`views_builder.py`) et les formulaires publics (`public_form.py`) incluent systématiquement :
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

**Validation** — `CsrfMiddleware.check()` compare le token de session au token fourni par :
1. le champ de formulaire `csrf_token` (body) ;
2. l'en-tête HTTP `X-CSRF-Token` (AJAX).

Si aucun token attendu n'existe ou si les tokens ne correspondent pas, la réponse est `403`.

**Ordre** — la validation CSRF est effectuée **avant** les middlewares d'authentification dans `Application.dispatch()`. Un CSRF invalide retourne immédiatement 403 sans appeler les middlewares.

### Exemptions

| Cas | Comportement |
|---|---|
| Route avec `csrf=False` | Aucune vérification CSRF |
| Groupe avec `csrf=False` | Toutes les routes du groupe sont exemptées |
| Méthodes `GET`, `HEAD`, `OPTIONS` | Jamais vérifiées (méthodes sûres) |
| Route `public=True` sans `csrf=False` | CSRF requis quand même |

### Tester une route protégée

```python
from core.security import session as _sessions
from core.app.application import Application
from core.http.router import Router
from tests.fake_request import FakeRequest

sid = _sessions.creer_session()
token = _sessions.get_session(sid)["csrf_token"]

router = Router()
router.add("POST", "/form", mon_handler, public=True)
app = Application(router, middlewares=[])

# Sans token → 403
resp = app.dispatch(FakeRequest("POST", "/form", session_id=sid))
assert resp.status == 403

# Avec token valide → passe le filtre CSRF
resp = app.dispatch(FakeRequest("POST", "/form",
                                body={"csrf_token": token},
                                session_id=sid))
assert resp.status == 200

# Avec header AJAX → passe le filtre CSRF
resp = app.dispatch(FakeRequest("POST", "/form",
                                session_id=sid,
                                headers={"X-CSRF-Token": token}))
assert resp.status == 200
```

### Tests livrés

`tests/test_security_csrf_http.py` (54 tests, ticket SECURITY-CSRF-AUDIT-001) couvre :

- token absent, invalide, vide, de mauvaise session → `403` ;
- token valide via champ de formulaire → passe ;
- token valide via `X-CSRF-Token` (AJAX) → passe ;
- méthodes sûres (`GET`, `HEAD`, `OPTIONS`) → pas de vérification ;
- `POST`, `PUT`, `PATCH`, `DELETE` → vérification ;
- method override `POST→DELETE/PUT/PATCH` avec/sans token ;
- `csrf=False` (route et groupe) → exempté ;
- `public=True` sans `csrf=False` → toujours vérifié ;
- CSRF avant auth middleware (espion de middleware) ;
- cycle CRUD simulé complet (create/update/delete) ;
- vérification que `views_builder.py` et `public_form.py` génèrent le champ `csrf_token` ;
- contrat direct `CsrfMiddleware.check()` avec field_name et header_name personnalisés.

### Limites restantes

- CSRF non testé sur un vrai serveur HTTP réseau (avec port TCP, cookies Set-Cookie réels et transport HTTP/1.1). Les tests utilisent `Application.dispatch()` + `FakeRequest`, ce qui couvre le cycle CSRF complet sans couche réseau.
- Le starter 5 (Communes & Séjours) est partiellement vérifié — les formulaires présents contiennent le champ, mais il n'y a pas de test de cycle HTTP complet pour ce starter.

---

