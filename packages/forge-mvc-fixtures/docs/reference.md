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

??? note "2. Installation"

    !!! warning "Prérequis : activez le venv du projet"

        Quelle que soit la source, installez **dans le venv du projet** :

        ```bash
        source .venv/bin/activate
        ```

        Lancé hors d'un venv, `pip` vise le Python **système** (Debian 12+, Ubuntu 23.04+),
        protégé par PEP 668. Il refuse alors d'installer, pour ne pas écraser les paquets
        gérés par `apt`, et affiche `externally-managed-environment`.
        Le venv de projet créé par `forge new` n'a pas ce verrou.

    #### Installer le paquet

    <div class="canal">

    #### A. Depuis PyPI (stable)

    La dernière version publiée :

    ```bash
    pip install --pre forge-mvc-fixtures
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-fixtures"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-fixtures`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-fixtures==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable fixtures --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser sa base

    Rien à faire : cet opt-in n'apporte aucune table.

    #### 4. Le brancher là où il agit

    Rien à brancher : il ajoute des commandes `forge`, sans surface de runtime.
    Une application ne l'importe pas dans le chemin d'une requête.

    #### 5. Le prouver

    ```bash
    make check
    forge doctor
    ```

    Puis un premier usage réel.
    Un opt-in installé, inscrit et provisionné qu'aucun code n'appelle n'est pas
    opérationnel : il est seulement présent.


??? note "4. Désinstallation"

    ```bash
    forge opt-in:disable fixtures
    pip uninstall forge-mvc-fixtures
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre, sans toucher au paquet.
    `forge opt-in:remove fixtures` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-fixtures` ajoute quatre commandes.

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `fixtures:load` | Charge `mvc/fixtures/*.sql` dans la base de l'environnement actif. | `forge fixtures:load --run` |
    | `fixtures:purge` | Vide les tables ciblées par les fixtures. | `forge fixtures:purge --run` |
    | `fixtures:make-factory` | Échafaude une factory depuis le contrat d'entité. | `forge fixtures:make-factory ville` |
    | `fixtures:generate` | Exécute la factory et écrit `mvc/fixtures/<table>.sql`. | `forge fixtures:generate ville --rows 50 --seed 42` |

    `load` et `purge` **affichent** leur SQL par défaut ; `--run` exécute ; `--run --force` autorise `APP_ENV=prod`.
    `generate` et `make-factory` écrivent un fichier en mode write-if-new (`--force` pour remplacer).
    `load` ordonne les fichiers par dépendances de clés étrangères (ADR-077) ; `--no-fk-checks` désactive les contraintes le temps du chargement pour les jeux non triables.

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-fixtures` |
    | Module | `forge_mvc_fixtures` |
    | Catégorie | Exploitation et outillage (ADR-055) |
    | Couche | opt-in **CLI-only** (ADR-052), sans API de runtime |
    | Dépend de | `forge-mvc`, un backend BDD installé (ADR-054), et `faker` (génération) |
    | Commandes | `fixtures:load`, `fixtures:purge`, `fixtures:generate`, `fixtures:make-factory` |
    | API publique | `Factory` (classe de base, `reference`), `Fixture` (hooks Python), `FactoryError`, `FixtureReference` |
    | Table SQL | aucune (l'opt-in peuple des tables déjà provisionnées) |
    | Environnement | vise `APP_ENV` (défaut `dev`) ; production protégée (`--force`) |
    | Rendu SQL | via `dialect.render_literal` (ADR-075), correct pour le backend installé |
    | Installation | `pip install --pre forge-mvc-fixtures` |

??? note "7. Schémas UML"

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

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `Factory` | classe de base | `table`, `locale`, `self.faker` ; à sous-classer par entité |
    | `Factory.definition` | `definition() -> dict` | une ligne (colonne vers valeur), cas simple |
    | `Factory.rows` | `rows(count) -> list[dict]` | les lignes ; surface de code libre (boucles, conditions) |
    | `Factory.build` | `build(count) -> list[dict]` | produit et valide les lignes (table définie, colonnes cohérentes) |
    | `Factory.reference` | `reference(table, key_column, value) -> FixtureReference` | relie une colonne à l'`Id` d'une autre table par une clé naturelle (ADR-077) |
    | `FixtureReference` | valeur | sentinelle rendue en sous-requête par `fixtures:generate` |
    | `FactoryError` | exception | factory mal définie |

    La classe de base est importée par le code de factory de l'utilisateur (`from forge_mvc_fixtures import Factory`), exécuté par `fixtures:generate` ; ce n'est pas une API de runtime.

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Charger un jeu écrit à la main | `mvc/fixtures/*.sql` + `fixtures:load --run` |
    | Repartir d'un état propre | `fixtures:purge --run` |
    | Échafauder une factory | `fixtures:make-factory <entity>` |
    | Générer un `.sql` volumineux | `fixtures:generate <entity> --rows N --seed S` |
    | Coder sa génération (boucles, conditions) | surcharger `rows(count)` dans la factory |
    | Cibler un autre environnement | `APP_ENV=test forge fixtures:load --run` |
    | Forcer en production (rare) | `--run --force` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Une factory

    ```python
    from forge_mvc_fixtures import Factory


    class VilleFactory(Factory):
        table = "villes"

        def rows(self, count: int) -> list[dict]:
            villes = []
            for i in range(count):
                villes.append({
                    "Nom": self.faker.city(),
                    "CodePostal": self.faker.postcode(),
                    "Prefecture": i == 0,       # condition
                })
            return villes

    ```

    Les clés du dict sont les **colonnes réelles** de la table, pas les noms de champs du contrat : `Nom`, `CodePostal` (PascalCase), une clé étrangère gardant son nom snake (`user_id`).
    C'est ce que `fixtures:make-factory` échafaude désormais (ADR-077), via le mapping canonique de `forge-mvc-entities`.

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

??? note "11. Fixtures reliées : références et ordre de chargement (ADR-077)"

    Un jeu de démo réaliste relie des tables : un `eleve` pointe un compte `users`, une `classe` pointe une `annee_scolaire`.
    Trois mécanismes rendent ce cas natif, sans bricolage dans l'application.

    ### 9.1 Colonnes réelles

    `fixtures:make-factory` échafaude le dict de la factory avec les **colonnes réelles** de l'entité, pas les noms de champs du contrat : `Nom`, `UserId` (PascalCase), une clé étrangère gardant son nom snake (`user_id`).
    Le mapping vient de `forge-mvc-entities` (source unique, `column_for_field`), donc le SQL généré tourne tel quel sur le backend installé (cohérent ADR-075).

    ### 9.2 Références inter-fixtures

    Une factory relie une ligne à une autre table par une **clé naturelle**, sans connaître l'`Id` auto-incrémenté :

    ```python
    def rows(self, count: int) -> list[dict]:
        return [{
            "Nom": self.faker.last_name(),
            "UserId": self.reference("users", "Email", "prof.durand@ecole.fr"),
        } for _ in range(count)]

    ```

    `fixtures:generate` rend `self.reference(...)` en **sous-requête SQL**, résolue à la charge contre les vrais `Id` :

    ```sql
    INSERT INTO eleve (Nom, UserId)
    VALUES ('Durand', (SELECT Id FROM users WHERE Email = 'prof.durand@ecole.fr' LIMIT 1));
    ```

    `make-factory` reconnaît les clés étrangères (type `foreign_key`, ou colonne déclarée dans `relations.json`) et échafaude un `self.reference(...)` commenté, à compléter, au lieu d'un entier aléatoire.

    ### 9.3 Ordre de chargement par dépendances

    `fixtures:load` ordonne les unités par **tri topologique** d'un graphe de dépendances : chaque `.sql` est chargé après les tables dont il dépend, qu'elles viennent d'une clé étrangère de `relations.json` (`users` avant `eleve`) ou d'une sous-requête `reference()` (`SELECT Id FROM users …`, même pour une table de socle comme `users`, hors `relations.json`).
    Les fixtures callable (chapitre 10) entrent dans le même graphe : une unité passe après **toute** unité qui fournit une table dont elle dépend, `.sql` comme `.py`.
    Repli sur l'ordre du nom de fichier si le graphe est absent ou en cas de cycle (le préfixe `01_`, `02_` reste un ordre déclaratif de secours).

    Pour un jeu non triable (cycle de dépendances), `--no-fk-checks` encadre le chargement par le levier du dialecte : `SET FOREIGN_KEY_CHECKS` en MariaDB, `PRAGMA defer_foreign_keys` en SQLite, `session_replication_role` en PostgreSQL, sans effet en SQL Server.

    Le levier SQLite reporte la vérification au `COMMIT`, il ne la supprime pas.
    Un enfant dont le parent n'existe toujours pas à la fin fait donc échouer le chargement entier, là où MariaDB l'aurait laissé passer.
    C'est le cycle de dépendances que l'option sert à charger, pas un jeu incohérent.

    ### 9.4 Colonnes timestamps automatiques

    Une entité `options.timestamps: true` déclare `CreatedAt` et `UpdatedAt` en `NOT NULL` (posées par la couche applicative, pas par un `DEFAULT`).
    Une fixture qui les omettrait serait refusée au chargement (`Field 'CreatedAt' doesn't have a default value`).

    `fixtures:generate` lit le contrat de l'entité et **ajoute automatiquement** `CreatedAt`/`UpdatedAt` aux `INSERT` quand la factory ne les fournit pas, avec un horodatage déterministe constant (fixtures reproductibles, pas de `NOW()`).
    Une colonne déjà posée par la factory est respectée, jamais écrasée ; une entité sans timestamps n'est pas touchée.

??? note "12. Fixtures callable (hooks Python, ADR-078)"

    Deux étapes d'un seed réaliste ne sont pas des données statiques et ne peuvent pas s'écrire en `.sql` : l'**import** d'un référentiel depuis une source (un JSON canonique), et des **valeurs calculées** (un agrégat).
    Pour ces cas, une **fixture callable** exécute du code Python dans le même pipeline que les `.sql`.

    On sous-classe `Fixture` dans `mvc/fixtures/<nom>.py` :

    ```python
    from forge_mvc_fixtures import Fixture
    from mvc.services.referentiel_importer import import_referentiel


    class ReferentielFixture(Fixture):
        tables = ("matiere", "niveau")      # pour l'ordre et la purge
        depends_on = ("annee_scolaire",)    # exécutée après ces tables

        def load(self, *, tx=None) -> None:
            import_referentiel("data/referentiel.json")   # écrit via core.database.db

    ```

    - `load(self, *, tx=None)` écrit en base **comme le reste du projet** (`from core.database import db`, ou une fonction applicative qui le fait) : le SQL reste paramétré et visible dans le code appelé (principe 7).
    - Propagez `tx` à vos `db.execute`, comme le fait déjà `purge()`. Le chargement se déroule dans **une seule transaction** : sans `tx`, vos écritures repartiraient sur d'autres connexions du pool, échapperaient à l'annulation en cas d'échec, et `--no-fk-checks` ne les couvrirait pas. Une fixture qui déclare `load(self)` sans `tx` est refusée, avec un message qui indique la correction.
    - `tables` et `depends_on` placent la fixture dans l'ordre de chargement (tri topologique unifié avec les `.sql`) ; un préfixe numérique (`50_referentiel.py`) ordonne les callable entre elles.
    - `purge(self)` (surchargeable) démonte la fixture ; par défaut, vide les `tables` déclarées.

    `fixtures:load` découvre les `mvc/fixtures/*.py` (hors `factories/`), **affiche** leur source par défaut, puis les exécute avec `--run`.
    `fixtures:purge` démonte dans l'ordre **inverse exact** du chargement (le même graphe topologique renversé, `.sql` et callable), dans **une seule transaction** encadrée par la **désactivation des contraintes FK** du dialecte (`SET FOREIGN_KEY_CHECKS`, `PRAGMA foreign_keys`...). `SET FOREIGN_KEY_CHECKS` étant une variable de session (par connexion), tout le démontage partage une même connexion, et `Fixture.purge(*, tx=None)` propage cette transaction (robuste même pour un callable peuplant plusieurs tables liées). Si bien que `fixtures:purge --run` puis `fixtures:load --run` reconstruit un état propre sans erreur de clé étrangère, de façon rejouable.
    Une fixture qui écrit dans des tables non déclarées et ne surcharge pas `purge()` n'est pas purgée automatiquement (limite : déclarer `tables`, ou écrire `purge()`).

    Frontière (principe 11) : la fixture callable n'est **pas** une deuxième façon d'insérer du statique (cela reste des `.sql`), mais le recours pour ce que le SQL statique ne peut pas exprimer.

??? note "13. Frontière avec la migration de seed"

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
