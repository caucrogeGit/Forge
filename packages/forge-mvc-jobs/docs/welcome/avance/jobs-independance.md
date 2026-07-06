# Indépendance du cœur

Objectif : comprendre pourquoi Jobs est un opt-in, et comment l'isoler pour les tests.

**Ce que vous allez apprendre :** Forge Core ne dépend pas de `forge-mvc-jobs`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Le paramètre `db=` rend la file injectable, ce qui facilite les tests, et la constante `CREATE_TABLE_SQL` décrit la table en SQL visible.

Deuxième palier du **niveau avancé** de la progression Jobs.

## Ce que ce starter montre

- la règle de dépendance de l'opt-in ;
- le paramètre `db=` injectable pour les tests ;
- la constante `CREATE_TABLE_SQL`.

## La règle de dépendance

```text
Forge Core ne sait rien des tâches de fond.
forge-mvc-jobs fournit enqueue, drain et run_worker.
L'application décide quels travaux elle déporte.
```

- Aucun fichier du cœur n'importe `forge_mvc_jobs`, ce qui est verrouillé par un test.
- Le paquet importe le cœur pour l'accès base : l'opt-in dépend du cœur, c'est le sens autorisé.
- Retirer le paquet ne casse pas le cœur : il n'en a jamais dépendu, fidèle à l'ADR-004.

## Une file injectable pour les tests

```python
from forge_mvc_jobs import enqueue, drain


def test_envoi(db):
    enqueue("email.envoi", {"to": "a@b.fr"}, db=db)

    appels = []
    handlers = {"email.envoi": lambda payload: appels.append(payload["to"])}

    traitees = drain(handlers, db=db)

    assert traitees == 1
    assert appels == ["a@b.fr"]
```

### Comprendre ce code

- Chaque fonction accepte un paramètre `db=` : vous injectez la base de votre choix.
- Dans un test, vous passez une base de test ; en production, vous laissez la valeur par défaut.
- Le gestionnaire de test enregistre simplement les appels, sans effet de bord réel.

## La constante CREATE_TABLE_SQL

```python
from forge_mvc_jobs import CREATE_TABLE_SQL, TABLE_NAME

print(TABLE_NAME)        # "jobs"
print(CREATE_TABLE_SQL)  # le SQL de création de la table
```

- `TABLE_NAME` vaut `"jobs"` : le nom de la table de la file.
- `CREATE_TABLE_SQL` est le SQL de création, lisible et auditable.
- Le SQL reste visible : rien n'est généré dans votre dos.

## À retenir

- L'opt-in dépend du cœur ; le cœur ignore l'opt-in.
- `db=` rend la file injectable, ce qui simplifie les tests.
- `TABLE_NAME` et `CREATE_TABLE_SQL` exposent la table en SQL visible.

## Après ce starter

Vous avez fait le tour du socle.
Place au bilan du niveau avancé.

[Bilan avancé](bilan.md)
