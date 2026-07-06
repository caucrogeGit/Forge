# Installation : parcours « Welcome Admin »

Ce préambule installe l'opt-in `forge-mvc-admin` dans un projet Forge existant.
La progression se réalise ensuite **à la main** : chaque palier décrit les fichiers à créer et le code à écrire.

!!! info "Ce que ce parcours suppose"
    Vous avez déjà un projet Forge qui tourne, avec une entité et son CRUD.
    Le back-office **administre** une entité existante ; il ne la crée pas.
    Les exemples utilisent une entité `Article` (table `articles`, colonnes `id`, `title`, `body`, `published_at`).

## Prérequis

- **Forge installé** (core `forge-mvc`) et un projet qui démarre.
- **Une entité** déclarée et migrée, par exemple `Article`.
- **Python 3.12+**.

## 1. Installer le module opt-in

`forge-mvc-admin` est un module opt-in :

```bash
pip install --pre forge-mvc-admin
```

## 2. Préparer la structure admin

À la racine du projet :

```bash
forge admin:init
```

La commande crée `mvc/admin/__init__.py` et `mvc/admin/resources.py`.
Elle ne touche à aucun fichier existant.

## 3. Brancher le back-office

Le branchement est **explicite** : rien n'est injecté automatiquement.
Dans `mvc/routes.py`, importez les ressources et montez les routes :

```python
from forge_mvc_admin import register_admin_routes
import mvc.admin.resources  # enregistre les ressources déclarées

# ... vos routes ...

register_admin_routes(router)
```

L'import de `mvc.admin.resources` peuple le registre ; `register_admin_routes` ajoute les routes sous `/admin`.

## Étape suivante

[Commencer le niveau débutant](debutant/admin-welcome.md)
