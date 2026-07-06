# Premier CSV

Objectif : premier contact avec le module **opt-in** `forge-mvc-import-export`.

**Ce que vous allez apprendre :** la lecture d'un CSV repose sur la fonction `parse_csv`.
On lui passe le texte d'un fichier CSV et elle renvoie une liste de dictionnaires, une par ligne de données.
Le module ne sait rien de vos entités : il rend des chaînes, vous décidez ensuite quoi en faire.

Premier palier du **niveau débutant** de la progression Import/Export.

!!! note "Module opt-in"
    Si `forge-mvc-import-export` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- lire un texte CSV avec `parse_csv` ;
- observer la liste de dictionnaires renvoyée, une entrée par ligne.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `parse_csv(text)` | Lit un CSV et renvoie une liste de dictionnaires. | Opt-ins |

## 1. Lire un CSV en mémoire

```python
from forge_mvc_import_export import parse_csv

texte = "nom,age\nAlice,30\nBob,25"
lignes = parse_csv(texte)

for ligne in lignes:
    print(ligne["nom"], ligne["age"])
```

### Comprendre ce code

- `parse_csv(texte)` lit la première ligne comme en-tête : `nom` et `age` deviennent les clés.
- Chaque ligne de données devient un dictionnaire, par exemple `{"nom": "Alice", "age": "30"}`.
- Les valeurs sont des chaînes : `age` vaut `"30"`, pas l'entier `30`.
  La conversion viendra plus tard, au niveau intermédiaire.

## À retenir

- `parse_csv(texte)` renvoie une liste de dictionnaires.
- La première ligne du CSV sert d'en-tête et donne les clés.
- Toutes les valeurs sont des chaînes ; rien n'est converti automatiquement.

## Après ce starter

Vous avez votre première liste de lignes.
Regardons de plus près le comportement de `parse_csv`.

[Détails de la lecture](import-read.md)
