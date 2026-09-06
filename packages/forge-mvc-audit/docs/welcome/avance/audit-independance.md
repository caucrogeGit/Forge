# Indépendance du cœur

Objectif : comprendre pourquoi l'audit est un opt-in, et non une brique du cœur.

**Ce que vous allez apprendre :** Forge Core ne dépend pas de `forge-mvc-audit`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Vous verrez aussi le paramètre `db=` injectable pour les tests et le schéma visible via la migration rendue.

Deuxième palier du **niveau avancé** de la progression Audit.

## Ce que ce starter montre

- la règle de dépendance de l'opt-in ;
- le paramètre `db=` injectable pour les tests ;
- le schéma visible via la migration rendue.

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

## 2. Le schéma reste visible
Le paquet ne livre pas de SQL figé : il **déclare** sa table, et `forge audit:init`
en écrit le DDL dans `mvc/migrations/`, rendu pour le backend que vous avez
installé.

```bash
forge audit:init            # écrit la migration, sans rien exécuter
forge migration:apply           # après l'avoir relue
```

```python
from forge_mvc_audit import TABLE_NAME

print(TABLE_NAME)   # "audit_log"
```

- `TABLE_NAME` vaut `"audit_log"` : le nom de la table.
- Le SQL reste visible, et il est même **relu avant d'être appliqué** : rien
  n'est exécuté dans votre dos (principe 5).
- Il est correct pour MariaDB, SQLite, PostgreSQL comme SQL Server : la même
  déclaration, rendue par le dialecte actif.

## À retenir

- L'opt-in dépend du cœur ; le cœur ignore l'opt-in.
- `db=` permet d'injecter une base factice dans les tests.
- La migration rendue garde le schéma visible et auditable.

## Après ce starter

Vous avez fait le tour du socle.
Place au bilan du niveau avancé.

[Suivant : refus d'accès et rétention](audit-refus-purge.md)
