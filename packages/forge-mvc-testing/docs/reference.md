# L'infrastructure de test dans Forge (forge-mvc-testing)

Ce document explique ce que fait l'opt-in `forge-mvc-testing`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-testing` fournit l'outillage de test partagé de Forge : la classe `FakeRequest` et un plugin pytest qui installe des fixtures (configuration du noyau, nettoyage entre tests, `fake_request`).

C'est un paquet **dev-only** (ADR-041) : il n'est **jamais** une dépendance d'exécution, on l'installe seulement pour les tests.

??? note "1. Rôle du module"

    Tester un contrôleur Forge demande une `Request` sans serveur HTTP, et un noyau configuré de façon reproductible.

    L'opt-in apporte les deux : `FakeRequest` construit une requête factice (méthode, chemin, corps, JSON, fichiers), et le **plugin pytest** configure le noyau et nettoie l'état entre les tests.

    Le plugin s'active automatiquement dès que le paquet est installé (point d'entrée `pytest11`).

??? note "2. Installation"

    Infrastructure de test réservée au développement (ADR-041), listée dans `requirements-dev.txt` :

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
    pip install forge-mvc-testing
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-testing"
    ```

    </div>

??? note "3. Commandes"

    `forge-mvc-testing` n'expose aucune commande `forge` : c'est un **plugin pytest** (point d'entrée `pytest11`) qui s'active automatiquement dès l'installation, plus l'utilitaire `FakeRequest` à importer dans les tests.

??? note "4. Désinstallation"

    ```bash
    pip uninstall forge-mvc-testing
    ```

??? note "5. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-testing` |
    | Module | `forge_mvc_testing` |
    | Catégorie | Exploitation et outillage (ADR-055), **dev-only** |
    | Couche | infrastructure de test partagée |
    | Dépend de | `forge-mvc`, `pytest` (en développement) |
    | API publique | `FakeRequest`, `tables_temporaires` |
    | Plugin pytest | point d'entrée `pytest11` (`forge_mvc_testing.plugin`) |
    | Fixtures | `fake_request`, `real_backend_db` et les trois fixtures serveur, configuration du noyau, nettoyages autouse |
    | Portée | **jamais** une dépendance runtime (ADR-041) |
    | Installation | `pip install --pre forge-mvc-testing` (dev) |

??? note "6. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires du paquet.

    Le diagramme de classe montre `FakeRequest` et le plugin.

    Le diagramme de séquence montre une session pytest qui l'utilise.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que `FakeRequest` imite l'objet `Request` du cœur, et que le plugin fournit les fixtures.

    ```mermaid
    classDiagram
        direction LR

        class FakeRequest {
            +str method
            +str path
            +dict params
            +dict body
            +json_body
            +dict files
            +query / form / json / file / header
        }

        class plugin {
            <<plugin pytest>>
            +configure_forge_kernel (session)
            +clear_sessions (autouse)
            +clear_rate_limits (autouse)
            +fake_request (fixture)
        }

        class Request {
            <<cœur>>
        }

        FakeRequest ..> Request : imite (duck typing)
        plugin --> FakeRequest : fournit via fake_request

    ```

    À retenir :

    - `FakeRequest` se comporte comme une `Request` (accesseurs `query`/`form`/`json`...) ;
    - le plugin configure le noyau une fois par session ;
    - des fixtures autouse nettoient sessions, rate-limits, etc. entre les tests ;
    - la fixture `fake_request` fabrique des requêtes factices.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre une session pytest avec le plugin actif.

    ```mermaid
    sequenceDiagram
        participant Pytest as pytest
        participant Plugin as forge_mvc_testing.plugin
        participant Test as un test
        participant Ctrl as Contrôleur

        Pytest->>Plugin: découvre le plugin (pytest11)
        Plugin->>Plugin: configure_forge_kernel (session)
        loop par test
            Plugin->>Plugin: clear_sessions / rate_limits (autouse)
            Test->>Ctrl: action(FakeRequest("POST", "/x", body=...))
            Ctrl-->>Test: Response
            Test->>Test: assertions
        end

    ```

    À retenir :

    - le plugin est découvert automatiquement (rien à importer) ;
    - le noyau est configuré pour les tests, de façon reproductible ;
    - chaque test démarre d'un état propre (fixtures autouse) ;
    - on teste un contrôleur en lui passant une `FakeRequest`.

??? note "7. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `FakeRequest` | `FakeRequest(method="GET", path="/", *, body=None, json_body=None, params=None, session_id=None, ip="127.0.0.1", headers=None, files=None)` | requête factice, compatible `Request` |

    ### Fixtures du plugin (pytest)

    | Fixture | Portée | Rôle |
    |---|---|---|
    | `configure_forge_kernel` | session, autouse | configure le noyau pour les tests |
    | `clear_sessions` | autouse | nettoie les sessions entre tests |
    | `clear_rate_limits` / `clear_upload_rate_limits` | autouse | réinitialise les rate-limits |
    | `fake_request` | fonction | fabrique une `FakeRequest` |

    Le plugin s'active par le point d'entrée `pytest11` : aucune configuration `conftest` n'est requise.

    ### Motifs de saut des tests d'intégration (`db_probe.py`)

    Une fixture d'intégration qui ne peut pas se connecter doit dire **pourquoi**, car les deux causes possibles appellent des gestes opposés.
    Un serveur absent se démarre, un serveur qui refuse les identifiants se configure.

    | Élément | Signature | Rôle |
    |---|---|---|
    | `classify_connection_error` | `classify_connection_error(error) -> str` | rend `CAUSE_AUTH`, `CAUSE_UNREACHABLE` ou `CAUSE_UNKNOWN` |
    | `connection_failure_message` | `connection_failure_message(server_label, error, *, env_prefix) -> str` | motif de saut nommant le geste attendu |
    | `CAUSE_AUTH`, `CAUSE_UNREACHABLE`, `CAUSE_UNKNOWN` | constantes | les trois causes distinguées |

    ```python
    try:
        connexion = mariadb.connect(**params)
    except Exception as erreur:
        motif = connection_failure_message("MariaDB", erreur, env_prefix="FORGE_TEST_DB")
        if REQUIRE_DB:
            pytest.fail(motif)
        pytest.skip(motif)
    ```

    Une cause non reconnue n'est jamais rangée d'office dans l'une des deux autres.
    Affirmer la mauvaise cause avec aplomb est précisément ce que ce module corrige.

    ### Fixtures serveur réel (`real_db.py`)

    Ces quatre fixtures montent Forge sur un serveur de base de test, puis rendent la main.
    Le test passe ensuite par la **vraie couche d'accès**, `core.database.db`, celle que l'application utilise en production.

    | Fixture | Portée | Serveur |
    |---|---|---|
    | `real_db` | session | MariaDB, variables `FORGE_TEST_DB_*` |
    | `real_pg_db` | fonction | PostgreSQL, variables `FORGE_TEST_PG_*` |
    | `real_mssql_db` | fonction | SQL Server, variables `FORGE_TEST_MSSQL_*` |
    | `real_backend_db` | fonction | les trois, un cas par serveur |

    `real_backend_db` est paramétrée, et **chaque paramètre porte ses propres marqueurs**.
    Un test qui la demande est donc exécuté trois fois, et chaque job de la CI sélectionne le sien avec `-m db`, `-m db_pg` ou `-m db_mssql`.
    Écrire un test d'intégration une seule fois suffit à couvrir les trois serveurs.

    ```python
    def test_le_compteur_est_portable(real_backend_db):
        from core.database import db

        db.execute("INSERT INTO app_settings (cle, valeur) VALUES (?, ?)", ("x", "1"))
        assert db.fetch_one("SELECT valeur FROM app_settings WHERE cle = ?", ("x",))
    ```

    !!! warning "Les trois fixtures directes n'apportent aucun marqueur"

        `real_db`, `real_pg_db` et `real_mssql_db` ne marquent pas le test qui les demande.
        Un fichier qui les emploie déclare donc son propre `pytestmark = pytest.mark.db`.

        Sans ce marqueur, le test est collecté dans le job de CI qui n'a aucun serveur.
        La fixture l'y **saute**, en silence, et il compte comme vert alors qu'il n'a rien vérifié.
        Un garde-fou refuse ce cas (`tests/test_testing_real_db_fixtures_001.py`).

    En l'absence de serveur, le test est **sauté** en local avec le motif réel de l'échec.
    En CI, `FORGE_REQUIRE_DB=1` et ses variantes par backend transforment le saut en **échec** : la couche base n'est jamais verte par défaut.

    ### Tables jetables (`tables_temporaires`)

    | Élément | Signature | Rôle |
    |---|---|---|
    | `tables_temporaires` | `tables_temporaires(*definitions) -> ContextManager` | crée les tables par leur DDL dialectale, rend `core.database.db`, puis les jette |

    Les `definitions` sont des `TableDefinition` du socle `core.database.table_ddl`.
    La DDL est rendue par le dialecte du backend actif, donc ce geste vaut pour les quatre backends sans une ligne de SQL écrite à la main.
    Les tables sont aussi supprimées **avant** création, pour rattraper une exécution précédente tuée en cours de route.

    ```python
    from forge_mvc_testing.real_db import tables_temporaires


    @pytest.fixture
    def ma_table(real_backend_db):
        from forge_mvc_settings.tables import APP_SETTINGS

        with tables_temporaires(APP_SETTINGS) as db:
            yield db
    ```

    Le module rendu est la vraie couche d'accès, et c'est le point de tout.
    Un test qui écrit son propre objet `execute`/`fetch_one` par-dessus une connexion pilote court-circuite la traduction des marqueurs de paramètre et la qualification d'erreur, et reste vert sur du code qui ne l'est pas.

??? note "8. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Tester un contrôleur sans serveur | `FakeRequest(...)` puis appeler l'action |
    | Éprouver du SQL sur les trois serveurs | fixture `real_backend_db` |
    | Éprouver du SQL sur un seul serveur | `real_db`, `real_pg_db` ou `real_mssql_db` |
    | Simuler un POST de formulaire | `FakeRequest("POST", "/x", body={...})` |
    | Simuler un corps JSON | `FakeRequest("POST", "/api", json_body={...})` |
    | Partir d'un état propre | fixtures autouse (automatiques) |
    | Obtenir une requête prête | fixture `fake_request` |

??? note "9. Exemples d'utilisation"

    ### 8.1 Tester un contrôleur

    ```python
    from forge_mvc_testing import FakeRequest
    from mvc.controllers.article import create


    def test_create_article():
        req = FakeRequest("POST", "/article/create", body={"title": "Bonjour"})
        response = create(req)
        assert response.status == 200

    ```

    ### 8.2 Via la fixture

    ```python
    def test_avec_fixture(fake_request):
        req = fake_request("GET", "/article?id=7")
        ...

    ```

    Les nettoyages entre tests sont automatiques (fixtures autouse du plugin).

    !!! tip "Aide-mémoire"
        Deux apports :

        - `FakeRequest` : une `Request` sans serveur HTTP ;
        - le plugin pytest : noyau configuré + état propre entre tests.

??? note "10. Dev-only et isolation"

    Ce paquet ne sert qu'aux tests : il n'est jamais installé en production et n'est pas importé par le runtime (ADR-041).

    Les fixtures autouse garantissent l'isolation : chaque test repart de sessions et de rate-limits vides, ce qui évite les interférences entre tests.

    !!! warning "Jamais une dépendance runtime"
        `forge-mvc-testing` se déclare en dépendance de développement (par exemple dans `requirements-dev`), pas dans les dépendances du projet.

        L'application ne l'importe jamais à l'exécution.

    !!! note "Activation automatique"
        Le plugin pytest est découvert par le point d'entrée `pytest11` : il suffit que le paquet soit installé dans l'environnement de test.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-testing` : la dépendance va de l'outil de test vers le cœur.

## Voir aussi

- [Welcome-Testing](welcome/debutant/testing-welcome.md) : apprendre l'outillage pas à pas.
- [ADR-041](https://forgemvc.com/docs/forge/adr/041-shared-test-support/) : infrastructure de test partagée.
