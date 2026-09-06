# Indépendance du cœur

Objectif : comprendre pourquoi Settings est un opt-in, et comment le tester.

**Ce que vous allez apprendre :** Forge Core ne dépend pas de `forge-mvc-settings`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Le paramètre `db` injectable et le schéma visible via la migration rendue.

Deuxième palier du **niveau avancé** de la progression Settings.

## Ce que ce starter montre

- la règle de dépendance de l'opt-in ;
- l'injection de `db` pour tester sans base réelle ;
- La migration rendue garde le schéma visible.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `set_setting(key, value, *, db=...)` | Accepte un accès base injectable. | Opt-ins |
| `TABLE_NAME` | Nom de la table ; son schéma vit dans la migration rendue. | Opt-ins |

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

## 3. Le schéma reste visible
Le paquet ne livre pas de SQL figé : il **déclare** sa table, et `forge settings:init`
en écrit le DDL dans `mvc/migrations/`, rendu pour le backend que vous avez
installé.

```bash
forge settings:init            # écrit la migration, sans rien exécuter
forge migration:apply           # après l'avoir relue
```

```python
from forge_mvc_settings import TABLE_NAME

print(TABLE_NAME)   # "app_settings"
```

- `TABLE_NAME` vaut `"app_settings"` : le nom de la table.
- Le SQL reste visible, et il est même **relu avant d'être appliqué** : rien
  n'est exécuté dans votre dos (principe 5).
- Il est correct pour MariaDB, SQLite, PostgreSQL comme SQL Server : la même
  déclaration, rendue par le dialecte actif.

## À retenir

- L'opt-in dépend du cœur, le cœur ignore l'opt-in.
- Le paramètre `db` rend le store testable sans base réelle.
- `TABLE_NAME` nomme le stockage ; la migration rendue en montre le schéma.

## Après ce starter

Vous avez fait le tour du socle.
Place au bilan du niveau avancé.

[Suivant : le cache et les paramètres par utilisateur](settings-cache-users.md)
