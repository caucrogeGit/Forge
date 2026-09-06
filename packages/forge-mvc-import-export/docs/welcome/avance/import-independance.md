# Indépendance du cœur

Objectif : comprendre pourquoi l'import/export est un opt-in, et non une brique du cœur.

**Ce que vous allez apprendre :** Forge Core ne dépend pas de `forge-mvc-import-export`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Le paquet ne connaît ni la base ni vos entités : le SQL d'insertion vit dans le modèle de votre application, atteint par le callback `insert`.

Troisième palier du **niveau avancé**.

## Ce que ce starter montre

- la règle de dépendance de l'opt-in ;
- pourquoi le SQL reste côté application via le callback `insert`.

## La règle

```text
Forge Core ne sait rien de l'import/export CSV.
forge-mvc-import-export fournit lecture, validation et export.
L'application décide où et comment insérer.
```

- Le paquet est en pur Python et ne déclare aucune table ni migration.
- Il ne connaît ni la base ni vos entités : `import_rows` valide des lignes, puis délègue l'écriture à la fonction `insert` que vous passez.
- Aucun fichier du cœur n'importe `forge_mvc_import_export`.

## Le SQL reste dans le modèle

```python
from forge_mvc_import_export import parse_csv, import_rows, FieldSpec, coerce_int

# add_eleve vit dans le modèle de votre application : c'est lui qui contient
# le SQL d'insertion. Le paquet ne le voit pas, il l'appelle.
from mvc.models.eleve import add_eleve

lignes = parse_csv(open("eleves.csv", encoding="utf-8").read())
specs = [FieldSpec(name="nom"), FieldSpec(name="age", coerce=coerce_int)]

rapport = import_rows(lignes, specs, add_eleve)
print(rapport.imported, "élèves importés")
```

### Comprendre ce code

- `add_eleve` est votre fonction métier : elle porte le SQL, le paquet l'ignore.
- `import_rows` ne fait que valider puis appeler ce callback : la frontière entre framework et application reste nette.
- Vous gardez le SQL visible dans votre modèle, fidèle à la charte Forge.

## Ce que cela vous apporte

- Vous n'embarquez l'import/export que si vous l'installez.
- Le cœur reste minimal et auditable, fidèle au périmètre de l'ADR-004.
- Retirer le paquet ne casse pas le cœur : il n'en a jamais dépendu.

## À retenir

- L'opt-in dépend du cœur, le cœur ignore l'opt-in.
- Le paquet n'a aucune table ; le SQL d'insertion vit dans le modèle de l'app.
- Le callback `insert` est le point de contact entre le paquet et votre base.

## Après ce starter

Vous avez fait le tour du socle.
Place au bilan du niveau avancé.

[Suivant : le registre d'importeurs](import-registre.md)
