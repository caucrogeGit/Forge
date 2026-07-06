# Aide-mémoire PostgreSQL

Synthèse du backend `forge-mvc-postgres` (Alpha).

## Installer et activer

```bash
pip install --pre forge-mvc-postgres
```

Découvert automatiquement ; si plusieurs backends : `DB_BACKEND=postgres`.
Un serveur PostgreSQL doit être joignable.

## Préparer (Alpha : manuel)

```bash
createdb mon_projet
psql -c "CREATE ROLE mon_projet LOGIN PASSWORD '...';"
psql -c "GRANT ALL ON DATABASE mon_projet TO mon_projet;"
```

## Cycle de la base

| Étape | Commande |
|---|---|
| Appliquer le schéma | `forge db:apply` |
| État des migrations | `forge migration:status` |
| Créer une migration | `forge migration:make <nom>` |
| Appliquer les migrations | `forge migration:apply` |

## À retenir

- backend PostgreSQL via `psycopg`, statut **Alpha** ;
- paramètres `?` traduits en `%s` ; identité `BIGSERIAL` ; `CREATE INDEX` séparés ;
- provisioning `db:init` **non câblé** : base + rôle à la main ;
- intégration à valider sur un serveur réel ;
- un seul backend par projet (ADR-054).

## Voir aussi

- [Référence](../reference.md) : contrat, dialecte, statut.
