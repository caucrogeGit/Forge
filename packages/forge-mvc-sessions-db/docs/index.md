# Forge Sessions BDD

`forge-mvc-sessions-db` est l'opt-in de sessions persistantes de Forge.

Il fournit `DbSessionStore` : un store de session adossé à la base de données, dans la table `forge_sessions`.
Les sessions sont partagées entre processus et survivent au redémarrage, ce qui en fait le choix d'un déploiement multi-worker (Gunicorn, uWSGI).

## Pourquoi un opt-in séparé

Le cœur de Forge est agnostique du SGBD : il ne fournit que `MemorySessionStore` (mémoire, mono-processus), `FileSessionStore` et le contrat `SessionStore`.
Un store adossé à la base n'a pas sa place dans un cœur agnostique, il vit donc dans cet opt-in (ADR-054).
La dépendance va de l'opt-in vers le cœur, jamais l'inverse (principe 8).

## Portable par construction

Le store ne dépend d'aucune fonction date propriétaire.
Les horodatages (`created_at`, `updated_at`, comparaison d'expiration) sont calculés côté Python et passés en paramètres, sans `NOW()` (MariaDB), `GETDATE()` (SQL Server) ni `datetime('now')` (SQLite).
Il fonctionne donc sur tous les backends BDD, à travers `core.database.db`.

## Mise en route

Installer le paquet, puis s'assurer que la table `forge_sessions` existe :

```bash
pip install --pre forge-mvc-sessions-db
```

```python
import core.forge as forge
from forge_mvc_sessions_db import DbSessionStore

forge.configure(session_store=DbSessionStore(ttl=3600))
```

## Périmètre

Store de session persistant complet : création, lecture, écriture (merge et remplacement), régénération anti-fixation, rotation à l'authentification, expiration, messages flash, nettoyage.
Hors périmètre : cache applicatif, secrets chiffrés, backend Redis (le store passe par la base configurée du projet).

## Pour aller plus loin

- [Le store](references/store.md) : `DbSessionStore` et ses méthodes.
- [La référence complète](reference.md) : installation, API, schémas et exemples.
