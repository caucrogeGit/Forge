# Initialisation Forge IoT — `forge iot:init`

> **Statut** : commande de **préparation**. Elle copie la migration
> SQL Forge IoT du package vers `mvc/migrations/` du projet, mais
> **n'applique pas** le SQL. C'est `forge migration:apply` qui le fait
> ensuite — séparation volontaire pour rester lisible et relisible.

## Objectif

Boucler le parcours du starter
[Bonjour IoT](../starters/welcome-iot/index.md) : passer de la
réponse pédagogique

```json
{"error": "iot_storage_not_ready"}
```

à une table `iot_events` prête à être créée par
`forge migration:apply`. Aucune connexion base, aucun SQL exécuté.

## Usage

```bash
forge iot:init
```

Aucune option à ce ticket. Aide via :

```bash
forge iot:init --help
```

## Flux recommandé

```bash
forge iot:doctor       # vérifier package, config, migration, API HTTP
forge iot:init         # copier la migration vers mvc/migrations/
forge migration:apply  # créer la table iot_events en base
forge run              # démarrer l'application
```

Avec ce parcours :

- `forge iot:doctor` confirme que `forge-mvc-iot` est installé, que la
  configuration est correcte et que la migration est embarquée dans le
  package.
- `forge iot:init` copie le `.sql` depuis le package vers
  `mvc/migrations/` du projet. Idempotent.
- `forge migration:apply` (commande Forge Core existante) crée la
  table.
- `forge run` démarre le serveur — les routes
  `/welcome-iot/events` et `/api/iot/events` peuvent maintenant
  retourner des données réelles.

## Comportement

### Cas normal — fichier copié

```text
[OK] Migration IoT copiée : mvc/migrations/20260528120000_create_iot_events.sql

[INFO] Lance maintenant : forge migration:apply
```

Exit code : `0`.

### Cas idempotent — déjà présent, contenu identique

```text
[OK] Migration IoT déjà présente (identique) : mvc/migrations/20260528120000_create_iot_events.sql

[INFO] Lance maintenant : forge migration:apply
```

Exit code : `0`. La commande est sûre à rejouer.

### Cas conflit — fichier présent, contenu différent

```text
[WARN] mvc/migrations/20260528120000_create_iot_events.sql existe et diffère — aucune modification.
```

Exit code : `0`. **Aucun écrasement** : si l'utilisateur a modifié la
migration localement, la décision lui revient — la commande ne touche
rien. Pour repartir de la version packagée, supprimer manuellement le
fichier puis relancer `forge iot:init`.

### Cas dossier inexistant

Si `mvc/` existe mais pas `mvc/migrations/`, le dossier est créé :

```text
[INFO] Dossier mvc/migrations/ créé.
[OK] Migration IoT copiée : mvc/migrations/20260528120000_create_iot_events.sql

[INFO] Lance maintenant : forge migration:apply
```

### Cas hors projet Forge

```text
[ERREUR] Ce dossier ne ressemble pas à un projet Forge.
Conseil : lance cette commande à la racine du projet (dossier mvc/ attendu).
```

Exit code : `1`.

## Lecture des migrations packagées

La commande utilise `importlib.resources` pour lire les ressources
embarquées dans le package Python — fonctionne **identiquement** en
install éditable (depuis le monorepo) et en install PyPI réelle.

Le ticket
[IOT-PACKAGE-DATA-MIGRATIONS-001](storage-events.md#schema-sql-cible)
a embarqué les `.sql` via
`[tool.setuptools.package-data]` dans `pyproject.toml`, garantissant
que `forge iot:init` trouve toujours sa source quelle que soit
l'installation.

## Hors périmètre

Sont volontairement **hors périmètre** de cette commande :

- pas de `forge migration:apply` automatique — séparation explicite
  préparation / exécution ;
- pas de connexion à MariaDB ;
- pas de vérification que la table `iot_events` existe déjà ;
- pas de rollback de migration ;
- pas d'option interactive (`--force`, `--diff`, etc.) ;
- pas de subscriber MQTT lancé ;
- pas de modification de fichiers en dehors de `mvc/migrations/`.

## Module opt-in absent

Si `forge-mvc-iot` n'est pas installé, `forge iot:init` retourne :

```text
Erreur : module forge-mvc-iot non installé.
indice : installe le module opt-in : pip install forge-mvc-iot
```

Forge Core reste fonctionnel sans le module — l'import est paresseux
côté dispatcher (`forge.py`).

## Voir aussi

- [Architecture Forge IoT](architecture.md)
- [Diagnostic — `forge iot:doctor`](doctor.md)
- [Stockage des événements](storage-events.md)
- [Starter Bonjour IoT](../starters/welcome-iot/index.md)
