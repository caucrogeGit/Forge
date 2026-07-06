# Aide-mémoire MariaDB

Synthèse du backend `forge-mvc-mariadb`.

## Installer et activer

```bash
pip install --pre forge-mvc-mariadb
```

Découvert automatiquement ; si plusieurs backends : `DB_BACKEND=mariadb`. Un serveur MariaDB doit être joignable.

## Comptes (ADR-033)

| Compte | Variables | Usage |
|---|---|---|
| Administration | `DB_ADMIN_*` | `db:init`, `db:apply`, `migration:*` (DDL) |
| Applicatif | `DB_APP_*` | runtime (DML) |

## Cycle de la base

| Étape | Commande |
|---|---|
| Provisionner base + compte | `forge db:init` |
| Appliquer le schéma | `forge db:apply` |
| État des migrations | `forge migration:status` |
| Créer une migration | `forge migration:make <nom>` |
| Diff entité/base | `forge migration:diff` |
| Appliquer les migrations | `forge migration:apply` |

## À retenir

- backend de production, client-serveur, pool de connexions ;
- `requires_provisioning=True` : `db:init` crée base + compte via `DB_ADMIN_*` ;
- dialecte : `INT AUTO_INCREMENT`, `ENGINE=InnoDB`, `utf8mb4`, index inline, backticks ;
- runtime limité au DML (`DB_APP_*`) ;
- un seul backend par projet (ADR-054).

## Voir aussi

- [Référence](../reference.md) : contrat, dialecte, vue d'ensemble.
