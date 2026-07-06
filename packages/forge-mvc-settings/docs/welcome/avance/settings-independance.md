# Indépendance du cœur

Objectif : comprendre pourquoi Settings est un opt-in, et comment le tester.

**Ce que vous allez apprendre :** Forge Core ne dépend pas de `forge-mvc-settings`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Le paramètre `db` injectable et la constante `CREATE_TABLE_SQL` rendent le store vérifiable et auditable.

Deuxième palier du **niveau avancé** de la progression Settings.

## Ce que ce starter montre

- la règle de dépendance de l'opt-in ;
- l'injection de `db` pour tester sans base réelle ;
- la constante `CREATE_TABLE_SQL` exposée par le module.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `set_setting(key, value, *, db=...)` | Accepte un accès base injectable. | Opt-ins |
| `CREATE_TABLE_SQL` | Définition SQL de la table, exposée pour inspection. | Opt-ins |

## 1. La règle de dépendance

```text
Forge Core ne sait rien des paramètres applicatifs.
forge-mvc-settings fournit set/get/get_all/delete.
L'application décide quels réglages elle persiste.
```

- Aucun fichier du cœur n'importe `forge_mvc_settings`, ce qui est verrouillé par un test.
- Le store importe `core.database.db` : l'opt-in dépend du cœur, c'est le sens autorisé.
- Retirer le paquet ne casse pas le cœur : il n'en a jamais dépendu.

## 2. Le paramètre `db` injectable

```python
from forge_mvc_settings import set_setting, get_setting

# En production, db vaut core.database.db par défaut.
# En test, on injecte un adapter (fetch_one, fetch_all, execute).
set_setting("maintenance", True, db=adapter_de_test)
print(get_setting("maintenance", db=adapter_de_test))   # True
```

### Comprendre ce code

- Toutes les fonctions acceptent un paramètre `db` injectable.
- Par défaut, l'accès passe par `core.database.db`, le pool configuré par l'application.
- En test, un adapter exposant `fetch_one`, `fetch_all` et `execute` suffit, sans base réelle.

## 3. La constante CREATE_TABLE_SQL

```python
from forge_mvc_settings import CREATE_TABLE_SQL, TABLE_NAME

print(TABLE_NAME)         # app_settings
print(CREATE_TABLE_SQL)   # CREATE TABLE IF NOT EXISTS app_settings ...
```

### Comprendre ce code

- `CREATE_TABLE_SQL` est la même définition que la migration embarquée.
- Elle reste visible et auditable : le SQL n'est pas caché (principe 5, SQL visible).
- `TABLE_NAME` vaut `app_settings`, le nom de la table de stockage.

## À retenir

- L'opt-in dépend du cœur, le cœur ignore l'opt-in.
- Le paramètre `db` rend le store testable sans base réelle.
- `CREATE_TABLE_SQL` et `TABLE_NAME` exposent le stockage pour inspection.

## Après ce starter

Vous avez fait le tour du socle.
Place au bilan du niveau avancé.

[Bilan avancé](bilan.md)
