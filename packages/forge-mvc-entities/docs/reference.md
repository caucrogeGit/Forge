# Le moteur d'entités dans Forge

Ce document explique l'opt-in `forge-mvc-entities` : ce qu'il fait, ses commandes, et comment on s'en sert.

Le moteur d'entités porte toute la chaîne de la **couche de données** : déclarer des entités et leurs relations par des contrats JSON explicites, en dériver le SQL, le modèle et le CRUD, et faire évoluer le schéma par migrations.
Il inclut aussi le **pivot enrichi** (associations `many_to_many` portant des attributs), détaillé au chapitre 6.

Extrait du cœur (ADR-070) : le cœur reste un noyau web avec la seule couture runtime d'accès base (`core/database`, contrat `Dialect`) ; le moteur d'entités est une brique opt-in, indépendante du SGBD (il consomme le contrat `Dialect` exposé par le backend installé).

??? note "1. Rôle"

    Une application qui manipule des données déclare des **entités** : un contrat JSON par entité (`mvc/entities/<nom>/<nom>.json`), source unique dont Forge dérive tout le reste.

    Le moteur fournit :

    - la **génération** : `make:entity`, `make:relation`, `make:crud`, `make:pivot-crud` ;
    - la **modélisation** : normalisation canonique, validation (`entity:validate`), documentation (`entity:doc`), dérivation SQL et modèle (`build:model`) ;
    - l'**évolution** : provisioning (`db:config`, `db:init`, `db:apply`) et migrations (`migration:*`) ;
    - le **pivot enrichi** : `PivotAdvancedService` et `make:pivot-crud` (chapitre 6).

    Le SQL reste **visible** (aucun ORM, charte principe 5) : le contrat est la source, le SQL et le modèle en sont des projections lisibles.

??? note "2. Installation"

    Le squelette est livré sans moteur d'entités (comme sans backend, ADR-060) : on l'installe explicitement quand on veut une couche de données.

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
    pip install --pre forge-mvc-entities
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-entities"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-entities`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-entities==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    Rien à faire : ses commandes sont découvertes par l'entry point
    `forge_mvc.commands` dès l'installation (ADR-070).

    #### 3. Poser ce dont il a besoin

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
    pip uninstall forge-mvc-entities
    ```

    Retirez aussi sa ligne de `requirements.txt`.

    Il n'y a pas d'`opt-in:disable` : le moteur est découvert par son entry point
    `forge_mvc.commands` (ADR-070), donc retirer le paquet suffit à ce que le cœur ne le
    voie plus.

    Ce que la désinstallation **ne fait pas** : vos contrats d'entités
    (`mvc/entities/*.json`), le code généré et les migrations déjà appliquées restent en
    place. C'est voulu : ils vous appartiennent (principe 4).
    Sans le moteur, les commandes `make:entity`, `make:crud`, `migration:*` et `db:*`
    disparaissent simplement de `forge`, mais l'application continue de tourner sur le code
    déjà généré.

??? note "5. Commandes"

    Le moteur d'entités ajoute ces commandes (découvertes dès l'installation, entry point `forge_mvc.commands`) :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `make:entity` | Crée le contrat JSON d'une entité. | `forge make:entity Article` |
    | `make:relation` | Déclare une relation ; injecte la clé étrangère (`many_to_one`). | `forge make:relation` |
    | `make:crud` | Génère le CRUD complet d'une entité. | `forge make:crud Article` |
    | `make:pivot-crud` | Génère le sous-CRUD d'un pivot enrichi. | `forge make:pivot-crud Article tags` |
    | `entity:validate` | Valide forme et sémantique des contrats. | `forge entity:validate` |
    | `entity:doc` | Vue globale entités + relations (Markdown/Mermaid). | `forge entity:doc` |
    | `build:model` | Dérive le SQL et le modèle depuis les contrats. | `forge build:model` |
    | `check:model` | Détecte une divergence contrat / modèle généré. | `forge check:model` |
    | `migration:make` / `migration:apply` | Génère / applique les migrations. | `forge migration:apply` |
    | `db:config` / `db:init` / `db:apply` | Configure, provisionne et applique le schéma. | `forge db:init --run` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-entities` |
    | Module | `forge_mvc_entities` |
    | Catégorie | Données et modélisation |
    | Couche | opt-in (moteur d'entités) |
    | Dépend de | `forge-mvc` et un backend BDD (ADR-054) |
    | Génération | `make:entity`, `make:relation`, `make:crud`, `make:pivot-crud` |
    | Modélisation | `build:model`, `entity:validate`, `entity:doc`, `migration:*`, `db:*` |
    | Contrats de données | entité et relations = contrats du cœur (`cli/schemas`, ADR-058) ; `pivot.schema.json` embarqué (ADR-057) |
    | API runtime | `PivotAdvancedService`, `PivotRow`, `PivotFieldConstraint`, `PivotConstraintError`, `PivotFormError`, `pivot_error_to_form_error` (pivot enrichi) |
    | Décisions d'architecture | ADR-070 (extraction), ADR-021/057 (pivot), ADR-054 (dialecte), ADR-069 (`foreign_key`) |
    | Installation | `pip install --pre forge-mvc-entities` (opt-in explicite, non installé par `forge new`) |

??? note "7. Le workflow de modélisation"

    La chaîne de base va du contrat à l'application, chaque étape à SQL visible.

    | Étape | Commande | Détail |
    |---|---|---|
    | 1. Déclarer une entité | `make:entity` | [make:entity](modules/make_entity.md) |
    | 2. Relier (clé étrangère de 1re classe, ADR-069) | `make:relation` | [make:relation](modules/make_relation.md) |
    | 3. Dériver le SQL et le modèle | `build:model` | [model](modules/model.md) |
    | 4. Générer le CRUD | `make:crud` | [make:crud](modules/make_crud.md) |
    | 5. Faire évoluer le schéma | `migration:make` / `migration:apply` | [migrations](modules/migrations.md) |

    Apprentissage guidé, pas à pas : [Welcome-Entités](welcome/debutant/entity-welcome.md).

??? note "8. Le pivot enrichi"

    Un pivot **enrichi** est une association `many_to_many` dont la table de liaison **porte des attributs** : entre un `Article` et un `Tag`, la table `article_tag` peut stocker une `position` et un drapeau `epingle`.

    Le `many_to_many` de base (jonction simple) et l'enrichi (jonction avec données) vivent tous deux dans ce paquet (ADR-070, qui a absorbé l'ancien `forge-mvc-pivot`, ADR-021).
    `PivotAdvancedService` lit et écrit les lignes pivot ; `forge make:pivot-crud` génère un sous-CRUD dédié.
    Le contrat du bloc pivot est décrit par `pivot.schema.json`, embarqué (ADR-057).

    ### 6.1 Schémas UML

    Le diagramme de classe montre que `PivotAdvancedService` lit et écrit des `PivotRow` via un exécuteur **injecté**, en respectant des `PivotFieldConstraint`.

    ```mermaid
    classDiagram
        direction LR

        class PivotAdvancedService {
            +attach(source_id, target_id, pivot_data)
            +update(source_id, target_id, pivot_data)
            +detach(source_id, target_id) int
            +list_for_source(source_id) list
            +get(source_id, target_id) PivotRow
            +get_by_id(pivot_id) PivotRow
        }

        class PivotRow {
            <<dataclass>>
            +source_id
            +target_id
            +dict pivot_data
        }

        class PivotFieldConstraint {
            <<dataclass>>
            +str name
            +bool required
            +bool nullable
        }

        class Executor {
            <<callable>>
            +fetch_one / fetch_all / execute
        }

        class pivot_table {
            <<table>>
            +source_key
            +target_key
            +attributs...
        }

        PivotAdvancedService --> PivotRow : lit / écrit
        PivotAdvancedService --> PivotFieldConstraint : valide selon
        PivotAdvancedService --> Executor : exécuteur injecté
        Executor --> pivot_table : SQL

    ```

    Le diagramme de séquence montre l'attachement d'un cours à un élève avec une note.

    ```mermaid
    sequenceDiagram
        participant App as Contrôleur
        participant Svc as PivotAdvancedService
        participant Exec as Exécuteur BDD
        participant Table as table pivot

        App->>Svc: attach(eleve_id, cours_id, {"note": 14})
        Svc->>Svc: valide les attributs (contraintes)
        Svc->>Exec: execute(INSERT pivot)
        Exec->>Table: insère la ligne
        App->>Svc: list_for_source(eleve_id)
        Svc->>Exec: fetch_all(SELECT)
        Exec-->>Svc: lignes
        Svc-->>App: list[PivotRow]

    ```

    À retenir :

    - `attach` valide puis insère l'association avec ses attributs ;
    - `unique_pair` empêche les doublons source/cible si activé ;
    - les lectures renvoient des `PivotRow` typés ;
    - une donnée invalide lève `PivotConstraintError` (convertible en erreur de formulaire).

    ### 6.2 API publique du pivot

    | Élément | Signature | Rôle |
    |---|---|---|
    | `PivotAdvancedService` | `PivotAdvancedService(table, source_key, target_key, *, pivot_fields=None, pivot_constraints=None, unique_pair=False, id_field=None, fetch_one=..., fetch_all=..., execute=...)` | service de persistance |
    | `.attach` | `attach(source_id, target_id, pivot_data)` | crée l'association enrichie |
    | `.update` | `update(source_id, target_id, pivot_data)` | met à jour les attributs |
    | `.detach` | `detach(source_id, target_id) -> int` | supprime l'association |
    | `.list_for_source` | `list_for_source(source_id) -> list[PivotRow]` | associations d'une source |
    | `.get` / `.get_by_id` | lecture | une association |
    | `PivotRow` | dataclass | `source_id`, `target_id`, `pivot_data` |
    | `PivotFieldConstraint` | dataclass | `name`, `required`, `nullable` |
    | `PivotConstraintError`, `PivotFormError` | exceptions | attribut invalide |
    | `pivot_error_to_form_error` | fonction | convertit une erreur en erreur de formulaire |

    Ces symboles sont ré-exportés à la racine du paquet : `from forge_mvc_entities import PivotAdvancedService`.

    ### 6.3 Exemples

    Configurer le service et attacher une association :

    ```python
    import core.database.db as db
    from forge_mvc_entities import PivotAdvancedService, PivotFieldConstraint

    service = PivotAdvancedService(
        table="inscription",
        source_key="eleve_id",
        target_key="cours_id",
        pivot_fields=["note"],
        pivot_constraints=[PivotFieldConstraint("note", required=True)],
        unique_pair=True,
        fetch_one=db.fetch_one, fetch_all=db.fetch_all, execute=db.execute,

    )

    service.attach(eleve_id=1, target_id=7, pivot_data={"note": 14})
    inscriptions = service.list_for_source(1)
    ```

    Générer le sous-CRUD à partir d'une relation `many_to_many` déclarée :

    ```bash
    forge make:pivot-crud Article tags
    ```

    ### 6.4 Périmètre et exécuteur

    Le pivot enrichi gère la jonction **avec attributs** ; le `many_to_many` de base (sans attributs) reste une simple relation déclarée.

    Les contraintes (`required`, `nullable`) valident les attributs avant écriture ; une violation lève `PivotConstraintError`, convertible en `PivotFormError` pour l'affichage.

    !!! note "SQL visible et exécuteur injecté"
        Le service reçoit `fetch_one` / `fetch_all` / `execute` : il ne crée pas de connexion et le SQL reste visible.

        En test, injectez de faux exécuteurs.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-entities` : la dépendance va de l'opt-in vers le cœur.

??? note "9. Connexion sans serveur (`serverless_db.py`)"

    `configure_serverless_db` fournit la connexion runtime d'un backend BDD **sans serveur** (SQLite, ADR-054), qui n'a pas de comptes d'administration `DB_ADMIN_*`.
    Elle est utilisée hors du flux `db:init` / `db:apply`, réservé aux SGBD serveur.

??? note "10. Champs dérivés, en lecture seule"

    Un total de ligne, un âge, un nom complet : la valeur se calcule depuis d'autres colonnes, et l'écrire en base la ferait mentir dès qu'une source change (`ENTITIES-COMPUTED-FIELDS-001`).

    L'application dupliquait donc l'expression dans chaque requête, ou la recalculait en Python après avoir tout rapatrié.

    ```json
    {"name": "total", "column": "total", "sql_type": "INTEGER",
     "python_type": "int", "nullable": true, "computed": "qte * pu"}
    ```

    Le champ est **projeté** dans les lectures, `(qte * pu) AS "total"`, et **absent** des écritures.

    !!! danger "Il n'a pas de colonne à écrire"
        L'inclure dans un `INSERT` ferait échouer la requête sur les quatre backends.

        Le générateur l'exclut donc de l'`INSERT` et de l'`UPDATE`, et il n'y a rien à faire pour cela.

    !!! info "L'alias reste entre guillemets"
        C'est lui qui préserve la casse sur PostgreSQL, qui replie tout identifiant non protégé en minuscules.

        Le perdre rendrait la clé en minuscules, et un gabarit lisant `{{ ligne.Total }}` afficherait du vide sans une ligne de journal.

    !!! danger "L'expression n'est pas paramétrable, et c'est voulu"
        Elle part telle quelle dans la projection. Une expression construite depuis une saisie serait une injection.

        Le contrat d'entité est du code du projet, relu et versionné, pas une donnée d'utilisateur. Un point-virgule y est néanmoins refusé : l'expression est projetée dans un `SELECT`, pas exécutée comme une instruction.

    Quatre combinaisons sont refusées, chacune parce qu'elle produirait un SQL faux plutôt qu'une simple maladresse : clé primaire, contrainte `UNIQUE`, valeur par défaut, et présence dans un formulaire.

??? note "11. Validation métier déclarable"

    Le contrat décrit des **types** et des contraintes de forme (`ENTITIES-BUSINESS-VALIDATION-001`). Il ne peut rien dire de « la date de fin doit suivre la date de début », ni de « une remise au delà de trente pour cent demande une validation ».

    Ces règles vivaient donc dans les contrôleurs, réécrites à chaque point d'entrée. Une entité créée par l'écran passait le contrôle ; la même créée par un import CSV ne le passait pas, et rien ne le signalait.

    ```python
    from forge_mvc_entities import ValidationIssue, ensure_entity_data, register_entity_validator

    def dates_coherentes(donnees, contexte):
        if donnees["fin"] < donnees["debut"]:
            return [ValidationIssue("la date de fin doit suivre la date de début")]
        return []

    register_entity_validator("Contrat", dates_coherentes)
    ensure_entity_data("Contrat", form.cleaned_data)
    ```

    !!! info "Une fonction, et non une expression au contrat"
        Une règle métier a besoin de la base, de l'heure, parfois d'un service.

        Une mini-langue d'expressions dans le JSON en couvrirait un dixième et demanderait un interpréteur, c'est à dire du code caché dans de la donnée, que le principe 3 refuse. Le contrat déclare qu'une entité **a** des règles ; le code dit lesquelles.

    !!! info "Toutes les règles sont évaluées"
        Rendre le premier problème seul obligerait l'utilisateur à corriger son formulaire une erreur à la fois.

        `ValidationReport.by_field()` les groupe pour les rendre en face de leur champ. Un problème sans champ est permis : « la date de fin doit suivre la date de début » n'appartient à aucun des deux.

    !!! danger "Une règle qui échoue refuse l'écriture"
        Une règle qui lève ne dit pas que la donnée est valide, elle ne dit rien.

        Le jour où le service qu'elle interroge tombe, tout passerait.

    `validate_entity_data` ne lève jamais et sert à afficher ; `ensure_entity_data` sert à refuser.

??? note "12. URL publique par slug"

    La recherche par slug existait depuis l'ADR-017, `get_<snake>_by_<slug>`, et **aucune route ne s'en servait** (`ENTITIES-SLUG-ROUTES-001`).

    Une URL publique lisible demandait donc d'écrire la méthode et la route à la main, dans chaque projet.

    ```python
    with router.group("/article", public=True, csrf=False) as public:
        public.add("GET", "/{slug}", ArticleController.show_by_slug,
                   name="article-show_by_slug")
    ```

    La méthode `show_by_slug` et sa route sont engendrées dès que l'entité porte un champ de formulaire `slug`. Une entité sans slug ne voit aucun changement.

    !!! warning "La route est déclarée en dernier, et ce n'est pas cosmétique"
        Les segments fixes, `/new`, `/edit/{id}`, `/export-csv`, sont déclarés avant.

        Un slug valant « new » serait capturé par eux, et sa fiche resterait inatteignable. `RESERVED_SLUG_SEGMENTS` nomme ces valeurs, pour que l'application les écarte à l'écriture : Forge ne peut pas le faire à sa place, un slug étant une donnée.

    !!! info "Distincte de `show`, qui adresse par clé primaire"
        Les deux rendent la même vue.

        Un identifiant numérique dans une URL publique renseigne sur le volume de la table, ce qu'un slug ne fait pas.

??? note "13. Lire un diff de schéma, et l'essayer à blanc"

    `migration:diff` rendait un tableau de lignes, sans total (`ENTITIES-MIGRATION-DIFF-READABLE-001`). Sur une entité de trente colonnes, savoir s'il reste un écart demandait de lire les trente lignes et de compter à la main, ce qui se fait mal et se fait faux.

    ```bash
    forge migration:diff Article
    forge migration:diff Article --sql      # essai à blanc
    forge migration:diff Article --check    # échoue s'il reste un écart
    ```

    La sortie porte désormais un résumé, le nombre de colonnes examinées et le nombre d'écarts, avec le détail par statut.

    !!! info "`--sql` montre sans écrire"
        C'est l'essai à blanc : lire le SQL avant de créer un fichier évite d'avoir à supprimer une migration qu'on vient d'engendrer.

        Un diff risqué, colonne changée ou colonne en trop, ne se traduit pas en SQL automatiquement. La commande le dit à cet instant, plutôt que de laisser l'exploitant découvrir le refus au moment où il croyait créer sa migration.

    !!! info "`--check` sert à l'intégration continue"
        Il rend un code de sortie non nul quand un écart subsiste.

        Le comportement par défaut reste inchangé : faire échouer la commande d'office aurait cassé les scripts qui l'appellent aujourd'hui.

    Une table absente compte comme un écart, et c'est même le plus grand.

    Les fonctions vivent dans `validators.py` (`register_entity_validator`, `validate_entity_data`, `ensure_entity_data`, `ValidationIssue`, `ValidationReport`) et dans `crud/routes_slug.py` (`slug_field_of`, `slug_route_lines`, `RESERVED_SLUG_SEGMENTS`).

## Voir aussi

- [Référence par module](modules/make_entity.md) : une page par commande et module du moteur.
- [Service pivot (service.py)](references/service.md) : détail du CRUD de la jonction enrichie.
- [Générateur de sous-CRUD (make_pivot_crud.py)](references/make_pivot_crud.md) : `make:pivot-crud`.
- [Welcome-Entités](welcome/debutant/entity-welcome.md) : apprendre le moteur pas à pas.
