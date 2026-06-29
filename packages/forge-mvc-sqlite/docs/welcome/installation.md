# Installation de forge-mvc-sqlite

Objectif : installer le backend SQLite et vérifier que le cœur le découvre.

Le parcours qui suit montre, en trois niveaux, comment créer la base, appliquer un schéma, faire évoluer le schéma par migrations, puis comprendre le dialecte SQLite.

## Installer le paquet

```bash
pip install --pre forge-mvc-sqlite
```

Le paquet dépend du cœur `forge-mvc` et de `sqlite3`, inclus dans la bibliothèque standard de Python : aucune dépendance externe, aucun serveur.

## Vérifier que le cœur le découvre

```python
from importlib.metadata import entry_points

names = {e.name for e in entry_points(group="forge_mvc.db_backend")}
print("sqlite" in names)
```

Si la sortie est `True`, le backend est découvrable par le cœur.

!!! note "Un seul backend par projet"
    Le cœur n'utilise qu'un backend BDD à la fois.

    Si un autre backend est installé, fixez `DB_BACKEND=sqlite` pour choisir celui-ci.

## Après cette étape

Place au niveau débutant : créer votre première base SQLite.

[Niveau débutant : Première base](debutant/sqlite-welcome.md)
