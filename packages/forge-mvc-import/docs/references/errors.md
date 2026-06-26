# Les erreurs

Ce document décrit l'erreur levée par `forge_mvc_import`.

Le fichier de code correspondant est `forge_mvc_import/errors.py`.

## 1. `CsvImportError`

```python
class CsvImportError(ValueError):
    ...
```

`CsvImportError` signale une entrée invalide de niveau global : un CSV illisible,
ou une liste de colonnes vide.
Elle hérite de `ValueError`.

## 2. Erreurs par ligne

Les erreurs **par ligne** ne lèvent pas d'exception : elles sont collectées dans
le `ImportReport` sous forme de `RowError` (numéro de ligne, champ, message).
C'est ce qui permet de présenter un rapport complet plutôt que de s'arrêter à la
première ligne fautive.

## 3. Quand `CsvImportError` est-elle levée ?

| Cause | Origine |
|---|---|
| Contenu CSV vide | `parse_csv` |
| En-tête sans nom ou colonnes en double | `parse_csv` |
| Liste de colonnes (`specs`) vide | `import_rows` |

## 4. Voir aussi

- [Le moteur d'import](engine.md) : `ImportReport`, `RowError`.
