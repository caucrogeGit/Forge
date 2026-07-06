# Aide-mémoire Import/Export

Synthèse de l'API de `forge-mvc-import-export`, à garder sous la main.

## Lecture CSV

| Appel | Résultat |
|-------|----------|
| `parse_csv(texte)` | Liste de dictionnaires (1re ligne = en-tête). |
| `parse_csv(texte, delimiter=";")` | Lecture avec un autre séparateur. |
| `CsvImportError` | Levée sur CSV vide, en-tête sans nom ou colonnes en double. |

## Validation et insertion

| Appel | Résultat |
|-------|----------|
| `FieldSpec(name, required=True, coerce=None)` | Décrit une colonne attendue. |
| `import_rows(rows, specs, insert)` | Valide puis insère ; « tout ou rien » par défaut. |
| `import_rows(rows, specs, insert, partial=True)` | Insère les lignes valides malgré des erreurs. |
| `ImportReport(imported, errors)` | Rapport ; `.ok` vaut `True` si aucune erreur. |
| `RowError(row, field, message)` | Erreur localisée (`row` 1-based). |

## Conversions

| Appel | Résultat |
|-------|----------|
| `coerce_int(valeur)` | Entier (lève `ValueError` si invalide). |
| `coerce_float(valeur)` | Flottant (lève `ValueError` si invalide). |
| `coerce_bool(valeur)` | Booléen (`1/0`, `true/false`, `oui/non`, `yes/no`, `on/off`). |

## Export programmatique

| Appel | Résultat |
|-------|----------|
| `to_csv(rows, columns)` | Texte CSV ; `columns` fixe l'en-tête et l'ordre. |
| `to_csv(rows, columns, delimiter=";")` | Export avec un autre séparateur. |

## Rappel

Forge Core ne dépend pas du paquet.
Le paquet n'a aucune table : le SQL d'insertion vit dans le modèle de votre application, atteint par le callback `insert`.
Pour télécharger une entité depuis une page web, la route d'export du CRUD reste la voie officielle ; `to_csv` sert l'export programmatique.
