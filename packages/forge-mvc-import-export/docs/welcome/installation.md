# Installation de forge-mvc-import-export

Objectif : installer l'opt-in Import/Export et vérifier qu'il est prêt.

Le parcours qui suit montre, en trois niveaux, comment lire un CSV, valider et insérer ses lignes, puis produire un CSV par programme.

## Installer le paquet

```bash
pip install --pre forge-mvc-import-export
```

En développement, depuis le dépôt, vous pouvez aussi l'installer en mode éditable :

```bash
pip install -e packages/forge-mvc-import-export
```

Le paquet dépend du cœur `forge-mvc` et reste en pur Python.
Il ne connaît ni la base ni vos entités : l'import insère via une fonction fournie par votre application, donc le paquet n'a aucune table ni migration qui lui soit propre.

## Vérifier l'installation

```python
from forge_mvc_import_export import parse_csv

lignes = parse_csv("nom,age\nAlice,30\nBob,25")
print(lignes)
```

Si ce script affiche une liste de dictionnaires, l'opt-in fonctionne.

## Après cette étape

Place au niveau débutant : lire votre premier CSV.

[Niveau débutant : Premier CSV](debutant/import-welcome.md)
