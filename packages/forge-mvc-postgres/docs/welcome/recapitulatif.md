# Aide-mémoire PostgreSQL

Synthèse du backend `forge-mvc-postgres` (niveau plein, ADR-084).

## Installer et activer

```bash
pip install --pre forge-mvc-postgres
```

Découvert automatiquement ; si plusieurs backends : `DB_BACKEND=postgres`.
Un serveur PostgreSQL doit être joignable.

## Provisionner

```bash
forge db:init        # affiche le SQL de provisioning
forge db:init --run  # l'exécute (le compte DB_ADMIN_* doit exister)
```

## Cycle de la base

| Étape | Commande |
|---|---|
| Provisionner la base | `forge db:init --run` |
| Appliquer le schéma | `forge db:apply` |
| État des migrations | `forge migration:status` |
| Créer une migration | `forge migration:make <nom>` |
| Appliquer les migrations | `forge migration:apply` |

## À retenir

- backend PostgreSQL via `psycopg`, **niveau plein** (ADR-084) ;
- paramètres `?` traduits en `%s` ; identité `BIGSERIAL` ; `CREATE INDEX` séparés ;
- provisioning par `forge db:init` (affichage du SQL ; `--run` pour exécuter) ;
- intégration validée en CI contre un vrai PostgreSQL 16 ;
- un seul backend par projet (ADR-054).

## Voir aussi

- [Référence](../reference.md) : contrat, dialecte, statut.
