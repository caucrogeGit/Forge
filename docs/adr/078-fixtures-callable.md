# ADR-078 : Fixtures callable (hooks Python dans le pipeline fixtures:load)

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-12

## Contexte

L'opt-in `forge-mvc-fixtures` charge, purge et génère des jeux de données (ADR-074, ADR-076, ADR-077).
Le chargement (`fixtures:load`) n'exécute que des fichiers `mvc/fixtures/*.sql` : des données statiques, relues.

Le banc d'essai RéférenCiel veut supprimer son script de seed maison et tout passer par l'opt-in.
Deux étapes d'un seed réaliste ne sont **pas** des données statiques et ne peuvent pas s'exprimer en `.sql` :

1. l'**import d'un référentiel** depuis un JSON canonique : une fonction applicative parcourt le canonique et persiste. Le figer en `.sql` dupliquerait des dizaines d'objets et perdrait la source ;
2. des **valeurs calculées** : un agrégat construit à partir d'autres tables.

Ces deux cas exigent d'exécuter du **code Python** dans le même pipeline que les `.sql`.

L'ADR-077 avait explicitement **différé** cette piste (« fixtures callable »), citant trois points à examiner : dépendance, ordre, sécurité. Cet ADR les tranche.

## Décision

### Une classe `Fixture`, une seule façon

`forge-mvc-fixtures` expose une classe de base `Fixture` (à côté de `Factory`), sous-classée dans un fichier `mvc/fixtures/<nom>.py` :

```python
from forge_mvc_fixtures import Fixture
from mvc.services.referentiel_importer import import_referentiel


class ReferentielFixture(Fixture):
    tables = ("matiere", "niveau")      # pour l'ordre et la purge
    depends_on = ("annee_scolaire",)    # exécutée après ces tables

    def load(self) -> None:
        import_referentiel("data/referentiel.json")
```

- `load(self)` (requis) écrit en base **comme le reste du projet** : la fixture importe `core.database.db` (ou appelle une fonction applicative qui le fait). Le SQL vit dans le code applicatif, paramétré et visible (principe 7).
- `tables: tuple[str, ...]` (optionnel) : les tables peuplées, pour l'ordre de chargement et la purge.
- `depends_on: tuple[str, ...]` (optionnel) : noms d'entités ou de tables à charger avant.
- `purge(self)` (optionnel) : démontage ; par défaut vide les `tables` déclarées, surchargeable pour un teardown sur-mesure.

Le **préfixe numérique** du nom de fichier (`50_referentiel.py`, `90_bilan.py`) ordonne les fixtures callable entre elles, comme secours déclaratif.

On écarte la **fonction `load()` nue** : la classe porte les métadonnées d'ordre et de purge, et reste symétrique à `Factory` (principe 11, une seule façon).

### Découverte

`fixtures:load` découvre les fixtures callable dans `mvc/fixtures/*.py` (au premier niveau).
Le sous-dossier `mvc/fixtures/factories/` (factories de génération, ADR-076) et les fichiers `__*.py` sont exclus.
Chaque module expose une sous-classe de `Fixture`.

### Ordre de chargement unifié

Le pipeline ordonne un ensemble d'**unités** : les fichiers `.sql` et les fixtures callable, ensemble.
Le rang de chaque unité vient du tri topologique F44 (graphe de clés étrangères de `relations.json`) :

- une unité `.sql` prend le rang de son entité (via `INSERT INTO <table>`), comme aujourd'hui ;
- une unité callable prend le rang **maximal** de ses `depends_on` (résolus en entités/tables), sinon de ses `tables`, sinon un rang « tardif » ;
- à rang égal, les `.sql` passent avant les callable (une callable dépend en général de tables déjà chargées), puis on départage par nom de fichier.

Repli (pas de `relations.json`, ou cycle) : les `.sql` d'abord (par nom), puis les callable (par nom, préfixe numérique compris).

### Affichage puis exécution (charte §7)

Comme pour les `.sql`, `fixtures:load` **affiche** par défaut et n'exécute rien :

- une unité `.sql` affiche son SQL ;
- une unité callable affiche le **source de son fichier `.py`** (versionné, relu).

`--run` exécute : `.sql` via `db.execute`, callable en instanciant la classe et en appelant `.load()`.
La protection production reste identique (`--run` seul refusé en `APP_ENV=prod`, `--force` pour confirmer).

### Purge

`fixtures:purge` intègre les fixtures callable au démontage, en ordre inverse du chargement (les callable, qui dépendent des tables de base, sont purgées avant les `.sql`).

Chaque `Fixture` porte une méthode `purge(self)` :

- par défaut, elle vide les `tables` déclarées (`DELETE FROM <table>` en ordre inverse) ;
- une sous-classe peut la **surcharger** pour un démontage sur-mesure (l'inverse exact de son `load()`).

Une fixture callable qui écrit dans des tables **non déclarées** et ne surcharge pas `purge()` n'est pas purgée automatiquement : limite documentée (déclarer `tables`, ou écrire `purge()`).

### Sécurité

Exécuter un `.py` de `mvc/fixtures/` revient à exécuter du code **du projet lui-même**, écrit par le développeur, versionné et relu.
Le geste est explicite (`--run`), cadré par environnement (dev/test par défaut, production protégée). Le risque est celui de lancer l'application, pas davantage : aucun code distant, aucune écriture invisible.

### Frontière réaffirmée (principe 11)

La fixture callable n'est **pas** une deuxième façon d'insérer des données statiques : celles-ci restent des `.sql` (écrits à la main ou générés par `fixtures:generate`).
Le callable est réservé à ce que le SQL statique ne peut pas exprimer : import depuis une source, valeurs calculées.

## Conséquences

- Surface d'API élargie (additive, rétro-compatible) :
    - `forge-mvc-fixtures` : classe `Fixture` (nouvelle, publique ; `load()`, `tables`, `depends_on`, `purge()`) ;
    - `fixtures:load` découvre, ordonne, affiche et exécute les `mvc/fixtures/*.py` ;
    - `fixtures:purge` démonte les fixtures callable (`purge()`, défaut sur `tables`) en ordre inverse.
- Un seed 100 % opt-in devient possible : `.sql` pour le statique et le relationnel, callable pour l'import et les agrégats, dans un ordre unique.
- Le pipeline exécute du code applicatif : posture de sécurité alignée sur « lancer le projet », documentée.
- Le SQL reste paramétré et visible (dans le code applicatif appelé) ; les fixtures `.py` sont versionnées et affichées avant exécution.

## Alternatives écartées

- **Fonction `load()` nue** (sans classe).
  Écartée : ne porte pas les métadonnées d'ordre (`depends_on`) ni de purge (`tables`) ; deux formes coexistantes casseraient le principe 11.
- **Injecter `db` en argument de `load(db)`.**
  Écartée : la fixture accède à la base « comme le reste du projet » (`from core.database import db`) ; l'injection ajouterait une convention propre aux fixtures sans gain.
- **Autoriser des fixtures en JSON/YAML déclaratif exécutées par un moteur.**
  Hors charte : masquerait le SQL (principe 5) et introduirait un moteur d'interprétation ; le `.py` reste du code Python relu.
- **Statu quo (seed maison hors opt-in).**
  Rejeté : le besoin (import canonique, agrégats) est général et récurrent ; il a sa place dans le pipeline unique de chargement.

## Référence

- Charte : `CHARTE_DOC.md` (principe 5, SQL visible ; principe 7, DML paramétrée ; principe 11, une seule façon).
- [ADR-074](074-fixtures-optin.md) : opt-in fixtures (load/purge).
- [ADR-076](076-fixtures-factory-generation.md) : génération par classes factory (`Factory`).
- [ADR-077](077-fixtures-reliees.md) : fixtures reliées ; a différé la piste callable, tranchée ici.
