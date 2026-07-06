# La lecture CSV

Ce document décrit la lecture d'un contenu CSV en lignes de dictionnaires.

Le fichier de code correspondant est `forge_mvc_import_export/csv_reader.py`.

## 1. `parse_csv`

```python
def parse_csv(text: str, *, delimiter: str = ",") -> list[dict[str, str]]
```

`parse_csv` lit `text` (contenu CSV) et renvoie une liste de lignes.
La première ligne fournit les en-têtes, qui deviennent les clés de chaque dictionnaire.
Les valeurs sont des chaînes : la conversion typée est faite ensuite par le moteur d'import.

```python
from forge_mvc_import_export import parse_csv

rows = parse_csv("nom,age\nAlice,12\nBob,13\n")
# [{"nom": "Alice", "age": "12"}, {"nom": "Bob", "age": "13"}]
```

## 2. Règles

- Les en-têtes sont nettoyés des espaces de bord.
- Une ligne entièrement vide est ignorée.
- Une ligne plus courte que l'en-tête est complétée par des chaînes vides.
- Le séparateur par défaut est la virgule ; `delimiter` permet d'utiliser un autre caractère (par exemple `;`).

## 3. Erreurs

`parse_csv` lève `CsvImportError` si le contenu est vide, si une colonne de l'en-tête est sans nom, ou si l'en-tête contient des colonnes en double.

## 4. Voir aussi

- [Le moteur d'import](engine.md) : valider et insérer les lignes lues.
