# ADR-076 : Génération de fixtures par classes factory

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-11

## Contexte

L'opt-in `forge-mvc-fixtures` (ADR-074) charge et purge des fichiers `mvc/fixtures/*.sql` écrits à la main.
Écrire cinquante lignes de villes à la main est fastidieux ; les frameworks voisins génèrent ces données avec une bibliothèque de données factices (Faker).

Chez Symfony, la recette de génération est **du code** : une classe factory (Foundry) déclare des valeurs par défaut alimentées par Faker, et l'ORM Doctrine transforme les objets en SQL.
Forge n'a pas d'ORM et garde le **SQL visible** (principe 5) : on ne peut pas décalquer ce modèle.

Deux acquis rendent une génération possible sans trahir la charte.

- Forge génère déjà une **classe modèle** à partir du contrat d'entité JSON : une classe factory à côté relève de la même logique, ce n'est pas de la magie.
- Le contrat `Dialect` sait désormais rendre un **littéral SQL** correct pour le backend installé (`render_literal`, ADR-075).

La forme classe est retenue pour une raison qui dépasse l'ergonomie : c'est une **surface de code pédagogique**.
L'utilisateur (souvent un élève) y écrit de vraies boucles, des conditions et des tableaux pour construire ses données, puis voit le `.sql` que son code produit.
Cette boucle « code lisible vers SQL visible » sert directement le positionnement de Forge (production auditable et pédagogique, ADR-049).

## Décision

Ajouter à `forge-mvc-fixtures` une génération de fixtures **par classes factory**, écrites par l'utilisateur, qui **émettent du `.sql` relu** chargé ensuite par `fixtures:load`.

### Une classe factory par entité, possédée par l'utilisateur

`forge-mvc-fixtures` fournit une classe de base `Factory`.
L'utilisateur écrit une sous-classe par entité, sous `mvc/fixtures/factories/`, scaffoldée depuis le contrat d'entité (mode « Forge génère », write-if-new, jamais d'écrasement).

Le point d'extension principal est une méthode `rows()` que l'utilisateur écrit **librement** :

```python
from forge_mvc_fixtures import Factory

class VilleFactory(Factory):
    table = "ville"

    def rows(self, count: int) -> list[dict]:
        villes = []
        for i in range(count):
            villes.append({
                "nom": self.faker.city(),
                "code_postal": self.faker.postcode(),
                "prefecture": i == 0,
            })
        return villes
```

Boucles, conditions, tableaux : l'utilisateur code sa génération.
`count` vient de `--rows` ; l'utilisateur reste libre de l'ignorer et de fixer sa propre volumétrie.
`self.faker` est disponible (locale configurable) mais **optionnel** : les données peuvent aussi être écrites à la main ou calculées.

Une méthode `definition()` renvoyant une seule ligne est offerte pour le cas simple ; la classe de base `rows(count)` l'appelle alors `count` fois.
`rows()` prime si les deux sont définies.

### Pas de magie (principe 3)

La classe de base reste **explicite** : elle n'auto-persiste rien, ne câble aucune relation par proxy, ne s'exécute jamais dans le chemin d'une requête.
Elle n'est importée que par le code de factory de l'utilisateur, exécuté par la commande de génération (outillage de développement), jamais par l'application au runtime.
C'est le contraire des proxies de Foundry.

### Sortie en `.sql`, mécanisme de chargement unique (principe 11)

`fixtures:generate` exécute les factories, **affiche** le SQL produit (charte §7), puis écrit `mvc/fixtures/NN_<table>.sql`.
Chaque valeur est rendue par `dialect.render_literal` (ADR-075) : le `.sql` est **correct pour le backend installé**.
Le chargement reste `fixtures:load` : la génération ne crée pas de seconde voie d'écriture, elle alimente la voie existante.

Émettre du `.sql` (plutôt qu'insérer directement comme Foundry) sert le modèle Forge de fixtures **versionnées** : le fichier est déterministe (tout le monde charge les mêmes données sans dépendre de la version de Faker), diffable, et rechargeable sans régénérer.
`--seed` fixe la graine Faker pour une génération reproductible.

### Commandes

- `fixtures:make-factory <entity>` : scaffolde `mvc/fixtures/factories/<entity>_factory.py` depuis le contrat d'entité (write-if-new).
- `fixtures:generate <entity> [--rows N] [--seed S]` : exécute la factory, affiche puis écrit le `.sql`.

Elles suivent le contrat CLI des opt-ins (ADR-072). `fixtures:generate` déclare `config: True` (il lit le contrat et le backend actif) ; `fixtures:make-factory` scaffolde des fichiers sans toucher la base.

### Dépendance Faker

`faker` devient une **dépendance directe** de `forge-mvc-fixtures`.
La bibliothèque n'est utilisée qu'à la génération (outillage), jamais au runtime de l'application.

## Mise en œuvre (phasage)

Tickets distincts :

1. Classe de base `Factory` (contrat `rows()`/`definition()`, `self.faker`, rendu via `render_literal`), dépendance `faker`.
2. `fixtures:generate` (exécution des factories, affichage puis écriture du `.sql`, `--rows`/`--seed`).
3. `fixtures:make-factory` (scaffold **riche** depuis le contrat d'entité : chaque champ reçoit un provider Faker plausible deviné par type et par nom, `email` vers `faker.email()`, un champ nommé `nom`/`name` vers `faker.name()`, `date` vers `faker.date_object()`, etc. ; l'utilisateur part d'une factory qui fonctionne puis ajuste).
4. Doc embarquée et palier welcome : écrire une factory, la génération, la boucle code vers SQL.

## Conséquences

- L'opt-in gagne une capacité de génération, tout en gardant un unique mécanisme de chargement (`fixtures:load`).
- La factory est une **surface de code pédagogique** possédée par l'utilisateur (boucles, conditions, tableaux), cohérente avec le positionnement de Forge.
- La sortie `.sql` reste visible, versionnée, déterministe et correcte pour le backend installé (via ADR-075).
- `faker` entre au runtime de l'outillage (pas de l'application) ; c'est la première dépendance tierce d'un opt-in de la catégorie `operations`.
- Aucune magie de type ORM : pas d'auto-persistance, pas de proxy, pas d'exécution en requête.

## Alternatives écartées

- **Recette déclarative (fichier TOML/YAML) au lieu d'une classe.**
  Rejetée : prive l'utilisateur des boucles, conditions et tableaux, qui sont l'intérêt pédagogique ; une classe explicite reste dans l'esprit Forge (le modèle est déjà une classe générée depuis le JSON).
- **Factory qui insère directement en base (Foundry pur).**
  Rejetée : ouvrirait une seconde voie de chargement (principe 11) et produirait des données non reproductibles d'une machine à l'autre ; Forge versionne ses fixtures en `.sql`.
- **Faker en extra optionnel (`[generate]`).**
  Écartée au profit d'une dépendance directe (choix du mainteneur) : la génération est une capacité centrale de l'opt-in, pas une option marginale.
- **Génération sans passer par `render_literal`.**
  Rejetée : redonnerait un rendu de littéral dialecte-naïf, alors qu'ADR-075 fournit le rendu correct pour le backend installé.

## Référence

- Charte : `CHARTE_DOC.md` (principe 3, pas de magie ; principe 5, SQL visible ; principe 11, une seule façon officielle).
- [ADR-049](049-positioning-production-auditable.md) : positionnement production auditable et pédagogique.
- [ADR-074](074-fixtures-optin.md) : opt-in fixtures (charge/purge, cadre ici étendu).
- [ADR-075](075-dialect-literal-rendering.md) : rendu de littéral SQL par le dialecte, consommé par la génération.
- [ADR-072](072-optin-cli-command-contract.md) : contrat des commandes CLI d'opt-in.
