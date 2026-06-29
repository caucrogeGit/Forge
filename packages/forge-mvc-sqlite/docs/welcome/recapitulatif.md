# Aide-mémoire SQLite

Synthèse du backend `forge-mvc-sqlite`.

## Installer et activer

```bash
pip install --pre forge-mvc-sqlite
```

Découvert automatiquement ; si plusieurs backends sont installés : `DB_BACKEND=sqlite`.

## Cycle de la base

| Étape | Commande |
|---|---|
| Créer la base (fichier) | `forge db:init` |
| Appliquer le schéma | `forge db:apply` |
| État des migrations | `forge migration:status` |
| Créer une migration | `forge migration:make <nom>` |
| Appliquer les migrations | `forge migration:apply` |

## Inspecter

| Besoin | Moyen |
|---|---|
| Lister les tables | `SELECT name FROM sqlite_master WHERE type='table'` |
| Décrire une table | `PRAGMA table_info(<table>)` |
| Ouvrir le fichier | client `sqlite3` ou extension d'éditeur |

## À retenir

- une base = un fichier (`DB_NAME`), sans serveur ;
- `requires_provisioning=False` : pas de compte ni de base distante ;
- dialecte SQLite : `INTEGER PRIMARY KEY AUTOINCREMENT`, `CREATE INDEX` séparés, affinités de types ;
- idéal en développement et test ; un serveur pour la production multi-utilisateurs ;
- un seul backend par projet (ADR-054).

## Voir aussi

- [Référence](../reference.md) : contrat, dialecte, vue d'ensemble.
