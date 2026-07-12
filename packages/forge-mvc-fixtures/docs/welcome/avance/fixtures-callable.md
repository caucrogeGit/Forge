# Quand le SQL ne suffit pas : fixtures callable

Objectif : exécuter du **code Python** dans le pipeline de chargement, pour ce qu'un `.sql` statique ne peut pas exprimer.

**Ce que vous allez apprendre :** écrire une fixture callable, la placer dans l'ordre de chargement, la voir affichée avant exécution, et la démonter proprement.

## Deux cas que le SQL ne couvre pas

La factory (`fixtures:generate`) et les `.sql` écrits à la main couvrent les données **statiques**, y compris reliées.
Deux étapes d'un seed réaliste leur échappent :

- **importer un référentiel** depuis une source (un JSON canonique) : le figer en `.sql` dupliquerait des dizaines d'objets et perdrait la source ;
- **calculer une valeur** à partir d'autres tables (un agrégat, un bilan).

Ces deux cas demandent du code. C'est le rôle d'une **fixture callable**.

## Écrire une fixture callable

On sous-classe `Fixture` dans un fichier `mvc/fixtures/<nom>.py` (au premier niveau, pas sous `factories/`) :

```python
from forge_mvc_fixtures import Fixture
from mvc.services.referentiel_importer import import_referentiel


class ReferentielFixture(Fixture):
    tables = ("matiere", "niveau")      # tables peuplées : pour l'ordre et la purge
    depends_on = ("annee_scolaire",)    # exécutée après ces tables

    def load(self) -> None:
        import_referentiel("data/referentiel.json")
```

Points clés :

- `load()` (obligatoire) **persiste** les données. Elle écrit en base comme le reste de votre code : `from core.database import db`, ou en appelant une fonction applicative (ici un importeur) qui le fait. Le SQL reste paramétré et vit dans votre code, visible.
- `tables` déclare les tables peuplées : elles servent à l'ordre de chargement et à la purge.
- `depends_on` liste les entités ou tables à charger avant.

`fixtures:load` place la racine du projet dans le chemin d'import : votre `from mvc.services… import …` fonctionne exactement comme dans le reste de l'application.

## Un exemple qui calcule

Rien n'oblige à appeler un importeur : `load()` est du code Python ordinaire.
Voici une fixture qui calcule un agrégat après le chargement des autres tables :

```python
from forge_mvc_fixtures import Fixture
from core.database import db


class BilanFixture(Fixture):
    tables = ("bilan_classe",)
    depends_on = ("inscription_eleve",)   # après les inscriptions

    def load(self) -> None:
        rows = db.fetch_all(
            "SELECT ClasseId, COUNT(*) AS n FROM inscription_eleve GROUP BY ClasseId"
        )
        for row in rows:
            db.execute(
                "INSERT INTO bilan_classe (ClasseId, Effectif) VALUES (?, ?)",
                (row["ClasseId"], row["n"]),
            )
```

Un préfixe numérique dans le nom du fichier ordonne les fixtures callable entre elles : `50_referentiel.py` avant `90_bilan.py`.

## Un seul pipeline, un seul ordre

`fixtures:load` découvre vos `mvc/fixtures/*.py` et les mêle aux `.sql` dans **un seul ordre** :
le tri topologique des dépendances (clés étrangères de `relations.json`, liens `reference()`, `depends_on`) place chaque unité, `.sql` comme callable, après **toute** unité qui fournit une table dont elle dépend.
Un callable déclarant `tables = ("niveau_classe",)` est donc chargé avant un `.sql` dont une clé étrangère pointe `niveau_classe`.

Comme partout dans Forge, la commande **affiche** d'abord et n'exécute rien :

```bash
forge fixtures:load          # affiche les .sql ET le source des fixtures .py
forge fixtures:load --run    # exécute les INSERT et appelle load()
```

Vous relisez le code Python qui va s'exécuter avant qu'il s'exécute. Rien de caché.
La production reste protégée : `--run` seul y est refusé, `--force` est requis.

## Démonter proprement

`fixtures:purge` démonte aussi les fixtures callable, avant les `.sql` (l'inverse du chargement).
Par défaut, une fixture vide les `tables` qu'elle a déclarées.
Pour un démontage sur-mesure (l'inverse exact de votre `load()`), surchargez `purge()` :

```python
class ReferentielFixture(Fixture):
    tables = ("matiere", "niveau")

    def load(self) -> None:
        import_referentiel("data/referentiel.json")

    def purge(self) -> None:               # optionnel : sur-mesure
        from core.database import db
        db.execute("DELETE FROM niveau")
        db.execute("DELETE FROM matiere")
```

Une fixture qui écrit dans des tables non déclarées et ne surcharge pas `purge()` n'est pas purgée automatiquement : déclarez `tables`, ou écrivez `purge()`.

## La frontière à garder en tête

La fixture callable n'est **pas** une deuxième façon d'insérer des données statiques : celles-ci restent des `.sql` (écrits ou générés).
Le callable est le recours pour ce que le SQL statique ne peut pas exprimer : import depuis une source, valeurs calculées.

## Ce qu'il faut retenir

- une fixture callable est une classe `Fixture` dans `mvc/fixtures/<nom>.py`, avec `load()` ;
- elle écrit en base comme le reste du projet (`core.database.db`) ; le SQL reste paramétré et visible ;
- `tables` et `depends_on` la placent dans l'ordre unifié avec les `.sql` ;
- `fixtures:load` l'affiche avant de l'exécuter ; `fixtures:purge` la démonte (`purge()`, défaut sur `tables`) ;
- réservée à l'import et aux valeurs calculées, pas au statique (principe 11).

## La suite

Voyons quand générer des fixtures et quand écrire une migration de seed.

[Continuer : fixtures ou migration de seed](fixtures-vs-seed.md)
