# Détails de la lecture

Objectif : maîtriser le comportement de `parse_csv` au-delà du cas simple.

**Ce que vous allez apprendre :** comment `parse_csv` traite l'en-tête, les lignes vides, un séparateur autre que la virgule, et les cas qu'il refuse.
Connaître ces détails évite des surprises sur des fichiers réels.

Deuxième palier du **niveau débutant** de la progression Import/Export.

## Ce que ce starter montre

- l'en-tête qui fournit les clés et les lignes vides ignorées ;
- le séparateur réglable avec `delimiter` ;
- les erreurs `CsvImportError` sur les CSV mal formés.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `parse_csv(text, delimiter=",")` | Lit un CSV avec un séparateur réglable. | Opt-ins |
| `CsvImportError` | Erreur levée sur un CSV invalide. | Opt-ins |

## 1. En-tête, lignes vides et lignes courtes

```python
from forge_mvc_import_export import parse_csv

texte = "nom,age\nAlice,30\n\nBob\n"
lignes = parse_csv(texte)

print(lignes)
# [{"nom": "Alice", "age": "30"}, {"nom": "Bob", "age": ""}]
```

### Comprendre ce code

- La première ligne, `nom,age`, donne les clés ; elle n'apparaît pas dans le résultat.
- La ligne vide entre Alice et Bob est ignorée.
- La ligne `Bob` est plus courte que l'en-tête : la colonne `age` manquante est complétée par une chaîne vide `""`.

## 2. Choisir un autre séparateur

```python
from forge_mvc_import_export import parse_csv

texte = "nom;age\nAlice;30"
lignes = parse_csv(texte, delimiter=";")

print(lignes)  # [{"nom": "Alice", "age": "30"}]
```

### Comprendre ce code

- `delimiter=";"` lit un CSV à points-virgules, courant dans les exports francophones de tableur.
- Le séparateur s'applique aussi bien à l'en-tête qu'aux lignes de données.

## 3. Les CSV refusés

```python
from forge_mvc_import_export import parse_csv, CsvImportError

try:
    parse_csv("")
except CsvImportError as erreur:
    print("CSV invalide :", erreur)
```

### Comprendre ce code

- `parse_csv` lève `CsvImportError` si le CSV est vide.
- Il refuse aussi un en-tête dont une colonne n'a pas de nom, ou un en-tête comportant deux fois la même colonne.
- Capturer `CsvImportError` permet de signaler proprement un fichier mal formé.

## À retenir

- L'en-tête fournit les clés ; les lignes vides sont ignorées.
- Une ligne plus courte que l'en-tête est complétée par `""`.
- `delimiter` change le séparateur ; un CSV invalide lève `CsvImportError`.

## Après ce starter

Vous savez lire un CSV de façon robuste.
Place au bilan du niveau débutant.

[Bilan débutant](bilan.md)
