# Installation de forge-mvc-settings

Objectif : installer l'opt-in Settings et préparer la table des paramètres.

Le parcours qui suit montre, en trois niveaux, comment écrire et lire un paramètre applicatif, manipuler des valeurs typées, lister ou supprimer des paramètres, puis comprendre les règles de clé et l'indépendance du cœur.

## Installer le paquet

```bash
pip install --pre forge-mvc-settings
```

En développement, vous pouvez aussi l'installer en mode éditable depuis le dépôt :

```bash
pip install -e packages/forge-mvc-settings
```

Le paquet dépend du cœur `forge-mvc`.
Il stocke les paramètres dans une table MariaDB, sans aucune dépendance supplémentaire.

## Créer la table des paramètres

La table `app_settings` n'est pas créée automatiquement : c'est une écriture en base, donc elle reste explicite et visible.
Deux commandes suffisent :

```bash
forge settings:init
forge migration:apply
```

`forge settings:init` copie la migration SQL embarquée dans le paquet vers le dossier `mvc/migrations/` du projet.
`forge migration:apply` applique ensuite la migration et crée la table.

## Vérifier l'installation

```python
from forge_mvc_settings import set_setting, get_setting

set_setting("etablissement.nom", "Collège Victor Hugo")
print(get_setting("etablissement.nom"))
```

Si ce script affiche le nom enregistré, l'opt-in fonctionne et la table est en place.

## Après cette étape

Place au niveau débutant : écrire et relire votre premier paramètre.

[Niveau débutant : Premier paramètre](debutant/settings-welcome.md)
