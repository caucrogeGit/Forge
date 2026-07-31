# La factory comme code

Objectif : écrire soi-même la génération dans une factory, avec des boucles, des conditions et des tableaux.

**Ce que vous allez apprendre :** la factory est une classe Python ; vous y codez vraiment votre jeu de données, et vous voyez le SQL qu'il produit.

## Deux façons de définir une factory

La classe de base `Factory` offre deux points d'extension.

Pour le cas simple, `definition()` renvoie **une ligne** ; la génération la répète `--rows` fois :

```python
from forge_mvc_fixtures import Factory


class VilleFactory(Factory):
    table = "villes"

    def definition(self) -> dict:
        return {"nom": self.faker.city()}
```

Pour tout contrôler, `rows(count)` renvoie **la liste des lignes** ; vous écrivez la génération :

```python
class VilleFactory(Factory):
    table = "villes"

    def rows(self, count: int) -> list[dict]:
        villes = []
        for i in range(count):
            villes.append({
                "nom": self.faker.city(),
                "code_postal": self.faker.postcode(),
                "prefecture": i == 0,          # une seule préfecture
            })
        return villes
```

Boucles, conditions, tableaux : c'est du vrai code, et c'est un bon exercice.

## Faker est optionnel

`self.faker` fournit des données factices, mais rien ne vous y oblige.
Vous pouvez écrire les données à la main, les calculer, ou piocher dans une liste :

```python
    CHEFS_LIEUX = ["Lyon", "Marseille", "Lille"]

    def rows(self, count: int) -> list[dict]:
        return [{"nom": nom, "prefecture": True} for nom in self.CHEFS_LIEUX]
```

## La boucle code vers SQL

Lancez la génération et lisez le `.sql` produit :

```bash
forge fixtures:generate ville --rows 3 --seed 1 --force
```

`--force` est nécessaire ici : `ville.sql` existe déjà, produit au niveau intermédiaire, et Forge n'écrase jamais un fichier sans un geste explicite (charte, principe 9).
C'est justement la boucle de travail de ce palier, où l'on régénère encore et encore le même fichier.

Vous voyez immédiatement le SQL que votre code a fabriqué, chaque valeur rendue correctement pour votre backend.
Modifiez la factory, régénérez, comparez : la rétroaction est directe.

## Ce que la factory ne fait pas

Elle ne touche jamais la base et ne rend pas le SQL elle-même : elle produit des lignes (des dicts).
C'est `fixtures:generate` qui écrit le `.sql`, et `fixtures:load` qui charge.
Aucune magie, aucune écriture cachée.

## La suite

Voyons comment relier plusieurs tables entre elles, sans coder d'`Id` en dur.

[Continuer : relier les fixtures entre elles](fixtures-reliees.md)
