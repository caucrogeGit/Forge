# forge-mvc-sessions-db

Store de session persistant pour Forge, adossé à la base via le backend BDD actif.

Le cœur Forge ne fournit que `MemorySessionStore` (mono-processus) et
`FileSessionStore`, plus le contrat `SessionStore`.
Ce paquet opt-in ajoute `DbSessionStore` : les sessions vivent dans la table
`forge_sessions`, partagées entre processus (utile en multi-worker Gunicorn).

Le store est agnostique du SGBD : tout son SQL passe par `core.database.db`,
dispatché vers le backend actif (`forge-mvc-mariadb`, `forge-mvc-sqlite`, …).
Les horodatages sont calculés côté Python, sans fonction SQL propriétaire
(`NOW()`, `GETDATE()`), donc le store fonctionne sur tous les backends (ADR-054).

## Usage

```python
from forge_mvc_sessions_db import DbSessionStore

forge.configure(session_store=DbSessionStore())
```

Table requise : `forge_sessions` (voir `mvc/models/sql/forge_sessions.sql`).
