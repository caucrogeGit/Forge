# Les données de démonstration et de test dans Forge (forge-mvc-fixtures)

Ce document explique ce que fait l'opt-in `forge-mvc-fixtures`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-fixtures` charge, purge et génère des **données de démonstration et de test** rejouables et cadrées par environnement, à SQL visible.

Le cœur de Forge ignore tout des fixtures : ce paquet fournit les commandes et la classe de base des factories ; l'application fournit ses fichiers `.sql` et ses factories.

??? note "1. Rôle du module"

    Une démonstration ou un projet pédagogique a besoin d'un jeu de données de départ : référentiels, comptes d'exemple, données d'atelier.

    L'opt-in couvre ce besoin par des données **rejouables** (charger, purger, recharger) et **cadrées par environnement** (`dev`, `test`, jamais `prod` par défaut).

    Il fournit :

    - le **chargement** : `fixtures:load` exécute les fichiers `mvc/fixtures/*.sql` ;
    - la **purge** : `fixtures:purge` vide les tables ciblées pour repartir d'un état propre ;
    - la **génération** : `fixtures:make-factory` échafaude une factory depuis le contrat d'entité, `fixtures:generate` l'exécute et écrit le `.sql`.

    Le SQL reste **visible** (charte principe 5) : les fixtures sont des fichiers `.sql` relus, et les commandes affichent le SQL avant de l'exécuter (charte §7).

    Frontière (ADR-074, principe 11) : le référentiel **permanent** reste une migration de seed appliquée par `forge migration:apply` ; les données de démo/test rejouables relèvent de cet opt-in.

??? note "2. Installation et désinstallation"

    ### Installation

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-fixtures
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-fixtures"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable fixtures
    ```

    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061).
    Opt-in **CLI-only** : il ajoute des commandes `fixtures:*`, sans route ni API de runtime ; une application ne l'importe pas dans le chemin d'une requête.
    `forge opt-in:install fixtures` affiche la commande `pip` sans l'exécuter.

    La génération (`fixtures:generate`) s'appuie sur **Faker**, tiré en dépendance de l'opt-in.

    ### Désinstallation

    ```bash
    forge opt-in:disable fixtures
    pip uninstall forge-mvc-fixtures
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre, sans toucher au paquet.
    `forge opt-in:remove fixtures` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Commandes"

    `forge-mvc-fixtures` ajoute quatre commandes.

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `fixtures:load` | Charge `mvc/fixtures/*.sql` dans la base de l'environnement actif. | `forge fixtures:load --run` |
    | `fixtures:purge` | Vide les tables ciblées par les fixtures. | `forge fixtures:purge --run` |
    | `fixtures:make-factory` | Échafaude une factory depuis le contrat d'entité. | `forge fixtures:make-factory ville` |
    | `fixtures:generate` | Exécute la factory et écrit `mvc/fixtures/<table>.sql`. | `forge fixtures:generate ville --rows 50 --seed 42` |

    `load` et `purge` **affichent** leur SQL par défaut ; `--run` exécute ; `--run --force` autorise `APP_ENV=prod`.
    `generate` et `make-factory` écrivent un fichier en mode write-if-new (`--force` pour remplacer).

??? note "4. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-fixtures` |
    | Module | `forge_mvc_fixtures` |
    | Catégorie | Exploitation et outillage (ADR-055) |
    | Couche | opt-in **CLI-only** (ADR-052), sans API de runtime |
    | Dépend de | `forge-mvc`, un backend BDD installé (ADR-054), et `faker` (génération) |
    | Commandes | `fixtures:load`, `fixtures:purge`, `fixtures:generate`, `fixtures:make-factory` |
    | API publique | `Factory` (classe de base des factories), `FactoryError` |
    | Table SQL | aucune (l'opt-in peuple des tables déjà provisionnées) |
    | Environnement | vise `APP_ENV` (défaut `dev`) ; production protégée (`--force`) |
    | Rendu SQL | via `dialect.render_literal` (ADR-075), correct pour le backend installé |
    | Installation | `pip install --pre forge-mvc-fixtures` |

??? note "5. Schémas UML"

    Deux vues complémentaires : la classe de génération et le flux des commandes.

    ### 5.1 Diagramme de classe

    ```mermaid
    classDiagram
        direction LR

        class Factory {
            <<classe de base>>
            +str table
            +str locale
            +faker
            +definition() dict
            +rows(count) list~dict~
            +build(count) list~dict~
        }

        class VilleFactory {
            +rows(count) list~dict~
        }

        class FactoryError {
            <<exception>>
        }

        VilleFactory --|> Factory : sous-classe (mvc/fixtures/factories/)
        Factory ..> FactoryError : lève si mal définie
    ```

    À retenir :

    - une factory produit des **dicts** (colonne vers valeur), pas du SQL ni des écritures en base ;
    - `rows(count)` est la surface de code libre (boucles, conditions, tableaux) ; `definition()` couvre le cas simple ;
    - `self.faker` est disponible mais optionnel.

    ### 5.2 Diagramme de séquence

    ```mermaid
    sequenceDiagram
        actor Dev as Développeur
        participant Make as fixtures:make-factory
        participant Gen as fixtures:generate
        participant Factory as VilleFactory
        participant Load as fixtures:load
        participant Base as Base (env actif)

        Dev->>Make: forge fixtures:make-factory ville
        Make-->>Dev: mvc/fixtures/factories/ville_factory.py
        Dev->>Gen: forge fixtures:generate ville --rows 50
        Gen->>Factory: build(50)
        Factory-->>Gen: lignes (dicts)
        Gen-->>Dev: affiche + écrit mvc/fixtures/ville.sql
        Dev->>Load: forge fixtures:load --run
        Load->>Base: exécute les INSERT
    ```

    À retenir :

    - la génération produit un `.sql` **relu et versionné** ; le chargement reste `fixtures:load` (un seul mécanisme, principe 11) ;
    - chaque valeur est rendue par `dialect.render_literal` (correcte pour le backend installé, ADR-075).

??? note "6. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `Factory` | classe de base | `table`, `locale`, `self.faker` ; à sous-classer par entité |
    | `Factory.definition` | `definition() -> dict` | une ligne (colonne vers valeur), cas simple |
    | `Factory.rows` | `rows(count) -> list[dict]` | les lignes ; surface de code libre (boucles, conditions) |
    | `Factory.build` | `build(count) -> list[dict]` | produit et valide les lignes (table définie, colonnes cohérentes) |
    | `FactoryError` | exception | factory mal définie |

    La classe de base est importée par le code de factory de l'utilisateur (`from forge_mvc_fixtures import Factory`), exécuté par `fixtures:generate` ; ce n'est pas une API de runtime.

??? note "7. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Charger un jeu écrit à la main | `mvc/fixtures/*.sql` + `fixtures:load --run` |
    | Repartir d'un état propre | `fixtures:purge --run` |
    | Échafauder une factory | `fixtures:make-factory <entity>` |
    | Générer un `.sql` volumineux | `fixtures:generate <entity> --rows N --seed S` |
    | Coder sa génération (boucles, conditions) | surcharger `rows(count)` dans la factory |
    | Cibler un autre environnement | `APP_ENV=test forge fixtures:load --run` |
    | Forcer en production (rare) | `--run --force` |

??? note "8. Exemples d'utilisation"

    ### 8.1 Une factory

    ```python
    from forge_mvc_fixtures import Factory


    class VilleFactory(Factory):
        table = "villes"

        def rows(self, count: int) -> list[dict]:
            villes = []
            for i in range(count):
                villes.append({
                    "nom": self.faker.city(),
                    "code_postal": self.faker.postcode(),
                    "prefecture": i == 0,       # condition
                })
            return villes
    ```

    ### 8.2 Générer puis charger

    ```bash
    forge fixtures:make-factory ville          # échafaude la factory
    forge fixtures:generate ville --rows 50 --seed 42   # affiche puis écrit mvc/fixtures/villes.sql
    forge fixtures:load --run                  # charge dans la base de l'environnement actif
    ```

    !!! tip "Aide-mémoire"
        Écrire ou générer un `.sql`, puis charger :

        - à la main : un fichier dans `mvc/fixtures/`, puis `fixtures:load` ;
        - généré : `make-factory` puis `generate`, puis `fixtures:load`.

??? note "9. Frontière avec la migration de seed"

    Une seule façon officielle par besoin (principe 11) :

    | Besoin | Voie |
    |---|---|
    | Données de référence **permanentes** (partout, prod comprise) | Migration de seed écrite à la main, `forge migration:apply` |
    | Données de démo/test **rejouables**, cadrées par environnement | Opt-in fixtures (`fixtures:load` / `fixtures:purge` / `fixtures:generate`) |

    Les fixtures peuplent des tables **déjà provisionnées** : le schéma vient des migrations, les données de démo viennent des fixtures.

    !!! warning "Production protégée"
        En `APP_ENV=prod`, `fixtures:load --run` et `fixtures:purge --run` sont refusés sans `--force`.
        Gardez les fixtures pour `dev` et `test` ; en production, le référentiel permanent passe par une migration de seed.

## Voir aussi

- [Référence par module (cli/, factory)](references/cli.md) : détail des fonctions et de la classe `Factory`.
- [Welcome-Fixtures](welcome/debutant/fixtures-welcome.md) : parcours d'apprentissage.
