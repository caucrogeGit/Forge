# Valider et insérer

Objectif : valider chaque ligne d'un CSV, puis insérer les lignes valides.

**Ce que vous allez apprendre :** on décrit les colonnes attendues par des
`FieldSpec`, puis `import_rows` valide chaque ligne et appelle une fonction
`insert` que vous fournissez.
Le résultat est un `ImportReport` qui dit combien de lignes ont été insérées et
liste les erreurs rencontrées.

Premier palier du **niveau intermédiaire** de la progression Import/Export.

!!! note "Module opt-in"
    Si `forge-mvc-import-export` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- décrire les colonnes attendues avec `FieldSpec` ;
- valider et insérer avec `import_rows` et un callback `insert` ;
- lire le rapport `ImportReport` et ses `RowError`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `FieldSpec(name, required)` | Décrit une colonne attendue. | Opt-ins |
| `import_rows(rows, specs, insert)` | Valide les lignes, puis insère les valides. | Opt-ins |
| `ImportReport` | Rapport : lignes insérées et erreurs. | Opt-ins |
| `RowError` | Une erreur localisée (ligne, champ, message). | Opt-ins |

## 1. Décrire les colonnes et insérer

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec

lignes = parse_csv("nom,ville\nAlice,Lyon\nBob,Nantes")

specs = [
    FieldSpec(name="nom"),
    FieldSpec(name="ville"),
]

inseres = []

def insert(record):
    # Dans une vraie application, ce callback appelle le modèle,
    # par exemple add_eleve(record). Le SQL reste côté application.
    inseres.append(record)

rapport = import_rows(lignes, specs, insert)

print(rapport.imported)  # 2
print(rapport.ok)        # True
```

### Comprendre ce code

- Chaque `FieldSpec` nomme une colonne attendue ; par défaut elle est
  `required=True`.
- `import_rows` valide chaque ligne, construit un dictionnaire validé `record`,
  puis appelle `insert(record)` pour les lignes valides.
- `insert` est fourni par votre application : c'est lui qui écrit en base.
  Le paquet ne connaît ni la base ni vos entités.
- Le `ImportReport` renvoyé porte `imported` (nombre inséré) et `errors`.

## 2. Lire les erreurs

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec

lignes = parse_csv("nom,ville\nAlice,Lyon\n,Nantes")

specs = [FieldSpec(name="nom"), FieldSpec(name="ville")]

rapport = import_rows(lignes, specs, lambda record: None)

print(rapport.imported)  # 0
for erreur in rapport.errors:
    print(erreur.row, erreur.field, erreur.message)
# 2 nom valeur requise manquante
```

### Comprendre ce code

- La deuxième ligne n'a pas de `nom` : `import_rows` produit un `RowError`.
- `RowError.row` est le numéro de la ligne de données, 1-based ; la ligne 2 ici.
- `RowError.field` indique la colonne fautive, `RowError.message` le motif.
- Par défaut, une seule ligne invalide empêche toute insertion : `imported`
  vaut 0. Ce comportement « tout ou rien » est détaillé au niveau avancé.

## À retenir

- `FieldSpec(name, required)` décrit une colonne attendue.
- `import_rows(rows, specs, insert)` valide puis insère via votre callback.
- `ImportReport.imported`, `ImportReport.ok` et `ImportReport.errors`
  résument le résultat ; chaque erreur est un `RowError`.

## Après ce starter

Vous savez valider et insérer des chaînes.
Voyons comment convertir les valeurs et gérer les colonnes facultatives.

[Convertir les valeurs](import-coerce.md)
