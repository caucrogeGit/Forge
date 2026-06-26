# Import partiel

Objectif : choisir entre « tout ou rien » et l'insertion des seules lignes
valides.

**Ce que vous allez apprendre :** par défaut, `import_rows` est « tout ou rien »
au niveau validation : une seule ligne invalide empêche toute insertion.
L'option `partial=True` insère les lignes valides malgré des lignes en erreur.
On voit aussi comment une exception levée par `insert` est capturée et rapportée.

Premier palier du **niveau avancé** de la progression Import/Export.

!!! note "Module opt-in"
    Si `forge-mvc-import-export` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- le comportement « tout ou rien » par défaut ;
- l'insertion partielle avec `partial=True` ;
- la capture d'une erreur d'insertion levée par `insert`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `import_rows(rows, specs, insert, partial=...)` | Choisit « tout ou rien » ou import partiel. | Opt-ins |
| `ImportReport` | Rapport : lignes insérées et erreurs. | Opt-ins |

## 1. « Tout ou rien » par défaut

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec

lignes = parse_csv("nom,age\nAlice,30\nBob,")  # age manquant pour Bob

specs = [FieldSpec(name="nom"), FieldSpec(name="age")]

records = []
rapport = import_rows(lignes, specs, records.append)

print(rapport.imported)   # 0
print(len(records))       # 0
print([e.row for e in rapport.errors])  # [2]
```

### Comprendre ce code

- La ligne 2 (Bob) n'a pas d'`age` : elle est invalide.
- Par défaut, dès qu'une ligne est invalide, **rien n'est inséré** : ni Alice
  ni Bob.
- C'est volontaire : on corrige le CSV, puis on relance un import propre.

## 2. Insérer les lignes valides avec `partial=True`

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec

lignes = parse_csv("nom,age\nAlice,30\nBob,")
specs = [FieldSpec(name="nom"), FieldSpec(name="age")]

records = []
rapport = import_rows(lignes, specs, records.append, partial=True)

print(rapport.imported)   # 1 (Alice)
print(rapport.ok)         # False (Bob reste en erreur)
print([e.row for e in rapport.errors])  # [2]
```

### Comprendre ce code

- `partial=True` insère les lignes valides (Alice) malgré la ligne en erreur.
- Le rapport reste honnête : `ok` vaut `False` tant qu'il reste une erreur.
- À choisir selon le besoin : un import strict refuse tout fichier imparfait ;
  un import partiel sauve ce qui est valide et liste le reste.

## 3. Une erreur d'insertion est capturée

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec

lignes = parse_csv("nom\nAlice\nBob")
specs = [FieldSpec(name="nom")]

def insert(record):
    if record["nom"] == "Bob":
        raise RuntimeError("doublon en base")

rapport = import_rows(lignes, specs, insert)

print(rapport.imported)   # 1 (Alice)
for erreur in rapport.errors:
    print(erreur.row, erreur.field, erreur.message)
# 2 None insertion échouée : doublon en base
```

### Comprendre ce code

- Si `insert` lève une exception, `import_rows` la capture et produit un
  `RowError` dont `field` vaut `None`.
- Les lignes déjà insérées le restent ; l'import ne s'arrête pas au premier
  problème d'insertion.
- Votre callback peut donc signaler un conflit métier (doublon, contrainte)
  sans casser tout l'import.

## À retenir

- Par défaut, une seule ligne invalide annule toute l'insertion.
- `partial=True` insère les lignes valides et liste les erreurs.
- Une exception levée par `insert` devient un `RowError` (`field=None`).

## Après ce starter

Vous maîtrisez l'import. Voyons l'autre sens : produire un CSV.

[Exporter avec to_csv](export-tocsv.md)
