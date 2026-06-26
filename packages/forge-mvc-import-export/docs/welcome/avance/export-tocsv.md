# Exporter avec to_csv

Objectif : produire un CSV par programme, et savoir quand utiliser `to_csv`
plutôt que la route d'export du CRUD.

**Ce que vous allez apprendre :** `to_csv` est l'inverse de `parse_csv` : il
rend une liste de dictionnaires en texte CSV.
On voit aussi la frontière avec l'export d'entité du cœur : deux outils pour
deux contextes, pas deux façons de faire la même chose.

Deuxième palier du **niveau avancé** de la progression Import/Export.

## Ce que ce starter montre

- produire un CSV avec `to_csv`, dans l'ordre des colonnes choisi ;
- le traitement des valeurs absentes ou `None` ;
- la frontière entre `to_csv` et la route d'export générée par le CRUD.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `to_csv(rows, columns)` | Rend des lignes en texte CSV. | Opt-ins |
| `to_csv(rows, columns, delimiter=...)` | Choisit le séparateur de sortie. | Opt-ins |

## 1. Rendre des lignes en CSV

```python
from forge_mvc_import_export import to_csv

rows = [
    {"nom": "Alice", "ville": "Lyon"},
    {"nom": "Bob", "ville": "Nantes"},
]

texte = to_csv(rows, columns=["nom", "ville"])
print(texte)
# nom,ville
# Alice,Lyon
# Bob,Nantes
```

### Comprendre ce code

- `columns` fixe l'en-tête et l'ordre des colonnes en sortie.
- Chaque ligne est écrite dans cet ordre, quelle que soit l'ordre des clés du
  dictionnaire.
- Une valeur absente d'une ligne, ou égale à `None`, devient une chaîne vide.
- `to_csv` lève `CsvImportError` si `columns` est vide.

## 2. Frontière avec l'export du CRUD (principe 11)

```text
Télécharger une ENTITÉ depuis une page web
    -> route d'export générée par le CRUD du cœur (voie officielle)

Produire un CSV par programme (script, rapport, données hors entité CRUD)
    -> to_csv
```

### Comprendre cette frontière

- Pour qu'un utilisateur télécharge une entité existante depuis l'interface,
  la route d'export générée par le CRUD du cœur reste la voie officielle.
- `to_csv` sert l'export **programmatique** : un script de rapport, un fichier
  de sortie, des données qui ne correspondent pas à une entité CRUD.
- Ce sont deux outils pour deux contextes différents.
  Ce n'est pas deux façons de faire la même chose, ce qui respecte le principe
  11 : une seule façon officielle par besoin.

## À retenir

- `to_csv(rows, columns)` est l'inverse de `parse_csv`.
- `columns` fixe l'en-tête et l'ordre ; une valeur absente ou `None` devient
  une chaîne vide.
- L'export d'une entité depuis une page web passe par la route du CRUD ;
  `to_csv` sert l'export programmatique.

## Après ce starter

Reste à comprendre pourquoi ce paquet ne connaît ni la base ni vos entités.

[Indépendance du cœur](import-independance.md)
