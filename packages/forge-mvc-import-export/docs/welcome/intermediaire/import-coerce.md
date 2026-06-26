# Convertir les valeurs

Objectif : convertir les chaînes du CSV en types Python et gérer les colonnes
facultatives.

**Ce que vous allez apprendre :** un `FieldSpec` peut porter une fonction de
conversion `coerce`.
Forge en fournit trois prêtes à l'emploi : `coerce_int`, `coerce_float` et
`coerce_bool`.
On voit aussi les colonnes `required=False`, qui acceptent une valeur absente.

Deuxième palier du **niveau intermédiaire** de la progression Import/Export.

## Ce que ce starter montre

- convertir une colonne avec `coerce_int`, `coerce_float`, `coerce_bool` ;
- rendre une colonne facultative avec `required=False` ;
- voir comment une conversion invalide devient une erreur de ligne.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `coerce_int(value)` | Convertit une chaîne en entier. | Opt-ins |
| `coerce_float(value)` | Convertit une chaîne en flottant. | Opt-ins |
| `coerce_bool(value)` | Convertit une chaîne en booléen. | Opt-ins |
| `FieldSpec(name, required, coerce)` | Décrit une colonne typée et facultative. | Opt-ins |

## 1. Convertir les valeurs

```python
from forge_mvc_import_export import (
    parse_csv,
    import_rows,
    FieldSpec,
    coerce_int,
    coerce_bool,
)

lignes = parse_csv("nom,age,actif\nAlice,30,oui\nBob,25,non")

specs = [
    FieldSpec(name="nom"),
    FieldSpec(name="age", coerce=coerce_int),
    FieldSpec(name="actif", coerce=coerce_bool),
]

records = []
rapport = import_rows(lignes, specs, records.append)

print(records[0])  # {"nom": "Alice", "age": 30, "actif": True}
```

### Comprendre ce code

- `coerce=coerce_int` convertit `"30"` en entier `30` ; `coerce_float` ferait
  de même pour un nombre décimal.
- `coerce_bool` accepte `1/0`, `true/false`, `oui/non`, `yes/no`, `on/off`,
  sans tenir compte de la casse.
- Le `record` transmis à `insert` contient donc des valeurs typées, prêtes pour
  le modèle.

## 2. Une conversion invalide devient une erreur

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec, coerce_int

lignes = parse_csv("nom,age\nAlice,trente")
specs = [FieldSpec(name="nom"), FieldSpec(name="age", coerce=coerce_int)]

rapport = import_rows(lignes, specs, lambda record: None)

for erreur in rapport.errors:
    print(erreur.row, erreur.field, erreur.message)
# 1 age valeur invalide : 'trente'
```

### Comprendre ce code

- `coerce_int("trente")` lève `ValueError` ; `import_rows` la capture et produit
  un `RowError` au lieu de planter.
- La ligne fautive est rapportée, jamais insérée.

## 3. Colonne facultative

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec

lignes = parse_csv("nom,surnom\nAlice,\nBob,Bobby")
specs = [
    FieldSpec(name="nom"),
    FieldSpec(name="surnom", required=False),
]

records = []
import_rows(lignes, specs, records.append)

print(records[0])  # {"nom": "Alice", "surnom": None}
print(records[1])  # {"nom": "Bob", "surnom": "Bobby"}
```

### Comprendre ce code

- `required=False` autorise une valeur absente : la ligne reste valide.
- Une valeur vide sur une colonne facultative devient `None` dans le `record`.
- Une colonne `required=True` (le défaut) produirait au contraire un `RowError`.

## À retenir

- `coerce_int`, `coerce_float`, `coerce_bool` convertissent les chaînes du CSV.
- Une conversion qui échoue devient un `RowError`, sans planter l'import.
- `required=False` accepte une valeur absente, rendue `None` dans le `record`.

## Après ce starter

Vous savez valider, convertir et insérer.
Place au bilan du niveau intermédiaire.

[Bilan intermédiaire](bilan.md)
