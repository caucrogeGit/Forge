# Migrations SQL

Forge utilise des migrations SQL versionnées pour faire évoluer le schéma de la
base applicative.

Le principe reste volontairement explicite :

- le SQL reste visible dans `mvc/migrations/` ;
- Forge n'ajoute pas d'ORM ;
- le développeur relit les migrations avant application ;
- Forge assiste la création et le suivi, mais n'applique rien sans commande
  explicite.

## Initialiser le suivi

```bash
forge db:init
```

Cette commande prépare la base applicative et crée aussi la table technique
`forge_migrations` avec `CREATE TABLE IF NOT EXISTS`. Cette table enregistre les
migrations déjà appliquées.

## Créer une migration vide

```bash
forge migration:make create_contacts
```

Forge crée un fichier SQL vide dans `mvc/migrations/`, avec un nom versionné :

```text
mvc/migrations/20260502214530_create_contacts.sql
```

Le développeur écrit lui-même le SQL dans ce fichier.

## Créer une migration depuis une entité

```bash
forge migration:make create_contacts --from-entity Contact
```

Forge copie le SQL déjà généré pour l'entité :

```text
mvc/entities/contact/contact.sql
```

La commande ne compare pas avec la base et n'applique rien.

## Créer une migration depuis toutes les entités

```bash
forge migration:make initial_schema --from-entities
```

Forge concatène les fichiers :

```text
mvc/entities/*/*.sql
```

Les fichiers sont inclus dans l'ordre alphabétique des chemins, avec un
séparateur lisible avant chaque bloc SQL.

## Voir l'état des migrations

```bash
forge migration:status
```

La commande compare les fichiers locaux dans `mvc/migrations/` avec les lignes
présentes dans `forge_migrations`.

Statuts possibles :

| Statut | Signification |
|---|---|
| `APPLIED` | Fichier local présent et ligne en base avec checksum identique. |
| `PENDING` | Fichier local présent mais non enregistré en base. |
| `CHANGED` | Fichier local présent mais checksum différent de celui enregistré. |
| `MISSING` | Ligne enregistrée en base mais fichier local absent. |

## Appliquer les migrations

```bash
forge migration:apply
```

Forge applique uniquement les migrations `PENDING`, dans l'ordre croissant de
version, puis enregistre chaque application dans `forge_migrations`.

La commande refuse l'application si une migration est `CHANGED` ou `MISSING`.

!!! warning "DDL MariaDB"
    MariaDB ne garantit pas un rollback complet des DDL. Forge s'arrête au
    premier échec, mais ne prétend pas annuler ce que MariaDB a déjà exécuté.
    Relisez les migrations SQL avant application.

## Comparer une entité avec la base

```bash
forge migration:diff --entity Contact
```

Forge compare le JSON canonique de l'entité avec les colonnes réelles de la
table MariaDB.

Cette commande est strictement en lecture seule :

- elle ne crée aucun fichier ;
- elle n'applique aucun SQL ;
- elle n'écrit pas dans `forge_migrations` ;
- elle ne modifie pas la base.

Statuts du diff :

| Statut | Signification |
|---|---|
| `OK` | Colonne attendue et colonne réelle identiques pour ce diff minimal. |
| `TABLE_MISSING` | La table attendue n'existe pas en base. |
| `COLUMN_MISSING` | Colonne présente dans le JSON mais absente en base. |
| `COLUMN_EXTRA` | Colonne présente en base mais absente du JSON. |
| `COLUMN_CHANGED` | Type SQL, nullabilité ou auto-increment différent. |

## Générer depuis un diff prudent

```bash
forge migration:make add_contact_fields --from-diff Contact
```

Forge réutilise le diff de schéma et génère une migration seulement dans les cas
prudenciels.

Cas autorisés :

- table absente : Forge recopie le SQL complet de l'entité ;
- colonnes manquantes : Forge génère des `ALTER TABLE ... ADD COLUMN`.

Cas refusés :

- `COLUMN_CHANGED` ;
- `COLUMN_EXTRA` ;
- `DROP COLUMN` ;
- `MODIFY COLUMN` ;
- `CHANGE COLUMN` ;
- index ;
- clés étrangères ;
- relations ;
- rollback.

Les modifications destructives ou ambiguës restent des migrations manuelles.

## Workflow : premier schéma

```bash
forge sync:entity Contact
forge migration:make initial_schema --from-entities
forge migration:status
forge migration:apply
```

Ce workflow convient pour poser un premier schéma lisible à partir des SQL
d'entités générés.

## Workflow : évolution prudente

```bash
forge sync:entity Contact
forge migration:diff --entity Contact
forge migration:make add_contact_fields --from-diff Contact
forge migration:status
forge migration:apply
```

Ce workflow convient pour ajouter des colonnes déclarées dans le JSON mais
encore absentes de la base.

Pour modifier un type, supprimer une colonne, changer une contrainte, ajouter un
index ou gérer une clé étrangère, créez une migration manuelle et relisez le SQL
avant application.
