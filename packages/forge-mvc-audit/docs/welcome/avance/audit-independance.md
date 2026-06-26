# Indépendance du cœur

Objectif : comprendre pourquoi l'audit est un opt-in, et non une brique du cœur.

**Ce que vous allez apprendre :** Forge Core ne dépend pas de
`forge-mvc-audit`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Vous verrez aussi le paramètre `db=` injectable pour les tests et la constante
`CREATE_TABLE_SQL`.

Deuxième palier du **niveau avancé** de la progression Audit.

## Ce que ce starter montre

- la règle de dépendance de l'opt-in ;
- le paramètre `db=` injectable pour les tests ;
- la constante `CREATE_TABLE_SQL`.

## La règle de dépendance

```text
Forge Core ne sait rien de l'audit.
forge-mvc-audit fournit record_audit et get_audit_log.
L'application décide ce qu'elle trace.
```

- Les helpers d'audit importent l'accès base de données du cœur : l'opt-in dépend du cœur, c'est le sens autorisé.
- Aucun fichier du cœur n'importe `forge_mvc_audit`, ce qui est verrouillé par un test.
- Retirer le paquet ne casse pas le cœur : il n'en a jamais dépendu.

## 1. Injecter une base de données dans les tests

```python
from forge_mvc_audit import record_audit, get_audit_log

# `db` est un faux module exposant insert / fetch_all, utilisé en test.
record_audit("eleve.cree", actor="prof.dupont", db=db)
entrees = get_audit_log(action="eleve.cree", db=db)
```

### Comprendre ce code

- `record_audit` et `get_audit_log` acceptent un paramètre `db=`.
- Par défaut, `db` vaut l'accès base du cœur (`core.database.db`).
- En test, on passe un double qui expose `insert` et `fetch_all`, sans toucher à une vraie base.

## 2. La constante CREATE_TABLE_SQL

```python
from forge_mvc_audit import CREATE_TABLE_SQL

print(CREATE_TABLE_SQL)
```

- `CREATE_TABLE_SQL` est le SQL de création de la table `audit_log`.
- Le SQL reste visible : aucune création de schéma cachée.
- En usage normal, on ne l'exécute pas à la main ; on applique la migration via `forge audit:init` puis `forge migration:apply`.

## À retenir

- L'opt-in dépend du cœur ; le cœur ignore l'opt-in.
- `db=` permet d'injecter une base factice dans les tests.
- `CREATE_TABLE_SQL` garde le schéma visible et auditable.

## Après ce starter

Vous avez fait le tour du socle.
Place au bilan du niveau avancé.

[Bilan avancé](bilan.md)
