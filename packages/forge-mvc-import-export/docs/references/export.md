# L'export programmatique

Ce document décrit l'écriture de lignes en CSV.

Le fichier de code correspondant est `forge_mvc_import_export/csv_writer.py`.

## 1. `to_csv`

```python
def to_csv(rows, columns, *, delimiter: str = ",") -> str
```

`to_csv` est l'inverse de `parse_csv` : il prend des lignes (des dictionnaires) et une liste de colonnes, et renvoie le texte CSV correspondant.
La première ligne est l'en-tête (`columns`).
Pour chaque ligne, les valeurs sont prises dans l'ordre des colonnes : une valeur absente ou `None` devient une chaîne vide, les autres sont converties par `str`.

```python
from forge_mvc_import_export import to_csv

rows = [{"nom": "Alice", "classe": "6A"}, {"nom": "Bob", "classe": "6B"}]
to_csv(rows, ["nom", "classe"])
# "nom,classe\nAlice,6A\nBob,6B\n"
```

## 2. Quand l'utiliser

`to_csv` sert l'export **programmatique** : un script, un rapport, une agrégation, ou des données qui ne viennent pas d'une entité CRUD.

Pour télécharger une **entité** depuis une page web, la route d'export générée par le CRUD du cœur reste la voie officielle (principe 11).
Les deux ne se concurrencent pas : ce sont deux outils pour deux contextes.

## 3. Erreurs

`to_csv` lève `CsvImportError` si `columns` est vide.

## 4. Voir aussi

- [La lecture CSV](csv.md) : `parse_csv`, l'inverse de `to_csv`.
- [Le moteur d'import](engine.md) : valider et insérer des lignes lues.
