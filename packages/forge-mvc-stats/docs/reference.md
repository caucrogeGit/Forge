# Les statistiques dans Forge (forge-mvc-stats)

Ce document explique ce que fait l'opt-in `forge-mvc-stats`, ce qu'il expose, et comment on s'en sert.

!!! note "Module extrait"
    Les statistiques ont été extraites du cœur vers le paquet `forge-mvc-stats` ; le cœur Forge n'en dépend pas.

`forge-mvc-stats` enregistre des événements applicatifs dans une table (`forge_stats_events`), puis permet de les lister et de les agréger par comptage.

Forge ne trace **rien** automatiquement : le développeur appelle `track_event()` quand il le décide, et injecte lui-même l'exécuteur SQL.
Aucun cookie visiteur, aucune IP.

??? note "1. Rôle du module"

    Compter des actions (connexions, exports, corrections de QCM) demande un socle d'événements explicite.

    L'opt-in définit un `StatsEvent` (nom, libellé, catégorie, métadonnées), le stocke via un exécuteur **injecté**, et fournit deux lectures : lister les événements, ou les compter par dimension.

    L'agrégation se fait par **comptage** (ADR-037) : `count_stats_events` renvoie des totaux groupés, pas des séries temporelles complexes.

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
    pip install --pre forge-mvc-stats
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-stats"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-stats`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-stats==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable stats --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    Cet opt-in apporte une table, `forge_stats_events`, où atterrissent les événements.

    !!! warning "Prévoyez la purge dès le premier jour"
        La table reçoit une ligne par événement suivi et rien ne la borne d'elle-même.
        Une application qui trace consciencieusement y accumule des millions de lignes, et les agrégats ralentissent d'autant sans que rien ne prévienne.

        `forge stats:gc --days N` compte les événements antérieurs à la borne et les affiche ; `--run` supprime.
        La rétention doit être **dite**, par l'option ou par la variable `STATS_KEEP_DAYS` ; l'option l'emporte.

        ```bash
        forge stats:gc --days 365          # affiche le nombre d'événements visés
        forge stats:gc --days 365 --run    # supprime
        ```

        Purger **détruit de l'information** : aucun agrégat de remplacement n'est calculé.
        Si vous voulez conserver des totaux, calculez-les en amont avec `count_stats_events`, puis purgez.

        Forge ne fournit pas d'ordonnanceur, cette commande est le point d'entrée à brancher sur cron ou un minuteur systemd.

    ```bash
    forge stats:init        # écrit la migration dans mvc/migrations/, sans l'exécuter
    forge migration:apply   # après relecture
    ```

    La déclaration de cette table vit dans `tables.py`, rendue pour le backend installé.

    !!! info "Projets antérieurs à cette commande"
        `stats:init` n'a pas toujours existé, et cette page affirmait auparavant que l'opt-in n'apportait aucune table.
        Les projets d'alors ont donc créé `forge_stats_events` à la main.
        Si c'est votre cas, appliquez la migration sans crainte, les deux issues sont sûres.

        Si votre table est conforme à la déclaration, la migration ne fait rien et s'enregistre.
        Le DDL est rendu en `CREATE TABLE IF NOT EXISTS` sur les quatre backends, donc l'opération est idempotente.

        Si elle diverge, la migration échoue en nommant la colonne manquante, et **n'est pas enregistrée comme appliquée**.
        Vous corrigez votre table, puis vous rejouez `forge migration:apply`.
        À aucun moment une table divergente n'est acceptée en silence.

    #### 4. Le brancher là où il agit

    Il s'importe dans le code qui s'en sert. Il n'y a ni route à monter ni middleware
    à poser.

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
    forge opt-in:disable stats
    pip uninstall forge-mvc-stats
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove stats` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    Le suivi lui-même s'utilise **par import** dans le code applicatif, jamais par le terminal (voir l'API publique ci-dessous).
    Deux commandes couvrent en revanche le cycle de vie de la table.

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `stats:init` | Écrit la migration de `forge_stats_events` dans `mvc/migrations/`. | `forge stats:init` |
    | `stats:gc` | Purge les événements par âge. Affiche par défaut, `--run` exécute. | `forge stats:gc --days 365 --run` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-stats` |
    | Module | `forge_mvc_stats` |
    | Catégorie | Données et modélisation (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` et un backend BDD (ADR-054) |
    | API publique | `StatsEvent`, `make_event`, `track_event`, `list_stats_events`, `count_stats_events` |
    | Table SQL | `forge_stats_events` (`STATS_EVENTS_TABLE`, `get_stats_events_schema_sql`) |
    | Exécuteur | injecté en **callable** (`execute`, `fetch_all`) |
    | Exceptions | `StatsEventError`, `StatsAdminError`, `StatsAggregateError` |
    | Principe | aucun tracking automatique, pas de cookie ni d'IP |
    | Décision d'architecture | ADR-037 (agrégation par comptage) |
    | Installation | `pip install --pre forge-mvc-stats` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre l'événement, les fonctions et l'exécuteur injecté.

    Le diagramme de séquence montre l'enregistrement puis l'agrégation.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que toutes les fonctions reçoivent un exécuteur SQL (un callable), jamais une connexion ouverte par le module.

    ```mermaid
    classDiagram
        direction LR

        class stats {
            <<module>>
            +make_event(name, label, category, metadata) StatsEvent
            +track_event(execute, event_or_name, ...) StatsEvent
            +list_stats_events(fetch_all, name, category, limit) list
            +count_stats_events(fetch_all, group_by, ...) list
        }

        class StatsEvent {
            <<dataclass>>
            +str name
            +str label
            +str category
            +dict metadata
        }

        class forge_stats_events {
            <<table>>
            +name
            +label
            +category
            +metadata
            +created_at
        }

        class Executor {
            <<callable>>
            +execute(sql, params)
            +fetch_all(sql, params)
        }

        stats --> StatsEvent : valide / renvoie
        stats --> Executor : reçoit (injecté)
        Executor --> forge_stats_events : lit / écrit
        stats ..> StatsEventError : peut lever

    ```

    À retenir :

    - un `StatsEvent` est validé avant écriture (`make_event`) ;
    - les données vivent dans `forge_stats_events` ;
    - l'exécuteur SQL est passé en argument (`execute` / `fetch_all`) ;
    - rien n'est tracé sans un appel explicite à `track_event`.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un suivi d'événement puis un comptage par dimension.

    ```mermaid
    sequenceDiagram
        participant App as Code applicatif
        participant Stats as forge_mvc_stats
        participant Exec as Exécuteur (execute/fetch_all)
        participant Table as forge_stats_events

        App->>Stats: track_event(db.execute, "export.pdf", category="export")
        Stats->>Stats: valide le nom et construit StatsEvent
        Stats->>Exec: execute(INSERT, params)
        Exec->>Table: insère la ligne
        App->>Stats: count_stats_events(db.fetch_all, group_by="category")
        Stats->>Exec: fetch_all(SELECT ... GROUP BY)
        Exec-->>Stats: totaux par catégorie
        Stats-->>App: liste de comptages

    ```

    À retenir :

    - `track_event` valide puis insère via l'exécuteur fourni ;
    - le nom d'événement est une chaîne `snake_case` applicative ;
    - `count_stats_events` agrège par la dimension demandée (`group_by`) ;
    - les lectures passent par `fetch_all`, fourni par l'application.

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `make_event` | `make_event(name, label="", category="general", metadata=None) -> StatsEvent` | construit un événement validé |
    | `track_event` | `track_event(execute, event_or_name, label="", category="general", metadata=None) -> StatsEvent` | insère un événement |
    | `list_stats_events` | `list_stats_events(fetch_all, name=None, category=None, limit=...) -> list` | liste les événements |
    | `count_stats_events` | `count_stats_events(fetch_all, group_by, name=None, category=None, since=None) -> list` | compte par dimension |
    | `StatsEvent` | dataclass | `name`, `label`, `category`, `metadata` |
    | `STATS_EVENTS_TABLE` | `"forge_stats_events"` | nom de la table |
    | `get_stats_events_schema_sql` | fonction | SQL de création de la table |
    | `StatsEventError`, `StatsAdminError`, `StatsAggregateError` | exceptions | nom invalide, lecture invalide, agrégation invalide |

    `execute` et `fetch_all` sont des callables fournis par l'application (par exemple `db.execute`, `db.fetch_all`).

    ### Rétention (`retention.py`)

    Ces fonctions suivent la même convention que le reste du paquet : elles ne touchent jamais la base d'elles-mêmes, l'appelant fournit l'exécuteur.
    La commande `forge stats:gc` en est le point d'entrée en ligne de commande.

    | Élément | Signature | Rôle |
    |---|---|---|
    | `cutoff_for_days` | `cutoff_for_days(keep_days, *, now=None) -> str` | borne UTC, `keep_days` jours dans le passé |
    | `count_stats_events_before` | `count_stats_events_before(fetch_one, cutoff) -> int` | compte les événements antérieurs, sans rien supprimer |
    | `purge_stats_events_before` | `purge_stats_events_before(execute, cutoff) -> int` | supprime les événements antérieurs |
    | `get_stats_count_before_sql` | fonction | SQL du comptage |
    | `get_stats_purge_sql` | fonction | SQL de la suppression |
    | `StatsRetentionError` | exception | rétention nulle, négative, ou borne vide |

    La borne part toujours en **paramètre lié**, jamais en expression SQL de date, ce qui rend la purge portable sur les quatre backends sans rendu dialectal.

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Tracer une action | `track_event(execute, "nom")` |
    | Catégoriser | paramètre `category=...` |
    | Joindre des métadonnées | paramètre `metadata=...` |
    | Lister les événements | `list_stats_events(fetch_all)` |
    | Compter par dimension | `count_stats_events(fetch_all, group_by=...)` |
    | Créer la table | `get_stats_events_schema_sql()` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Tracer un événement

    ```python
    import core.database.db as db
    from forge_mvc_stats import track_event

    track_event(db.execute, "export.pdf", category="export", metadata={"pages": 12})
    ```

    L'exécuteur (`db.execute`) est passé explicitement : le module n'ouvre pas de connexion.

    ### 8.2 Compter par catégorie

    ```python
    import core.database.db as db
    from forge_mvc_stats import count_stats_events

    totaux = count_stats_events(db.fetch_all, group_by="category")
    # [{"category": "export", "count": 42}, {"category": "login", "count": 130}, ...]
    ```

    !!! tip "Aide-mémoire"
        Un événement, deux lectures :

        - `track_event` pour écrire ;
        - `list_stats_events` (détail) et `count_stats_events` (agrégat).

??? note "11. Tracking explicite et exécuteur injecté"

    Forge ne trace rien de lui-même : pas de middleware caché, pas de cookie, pas d'IP.
    Le développeur décide quoi compter avec `track_event`.

    Les noms d'événements sont des chaînes `snake_case` définies par l'application (principe 1) ; un nom invalide lève `StatsEventError`.

    !!! note "SQL visible et exécuteur injecté"
        Les fonctions reçoivent `execute` / `fetch_all` en argument : le module ne crée jamais de connexion et le SQL reste visible.

        En test, injectez de faux callables pour vérifier les requêtes sans base.

    !!! note "Agrégation par comptage"
        `count_stats_events` agrège par `GROUP BY` sur la dimension demandée (ADR-037).

        C'est volontairement simple : des comptes, pas un moteur d'analytics.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-stats` : la dépendance va de l'opt-in vers le cœur.

??? note "12. Adresses IP et compte de visiteurs"

    `forge-mvc-stats` ne stocke **aucune** adresse : sa table porte un nom, un libellé, une catégorie et des métadonnées libres (`STATS-IP-ANONYMISATION-001`).

    Ce n'est pas un oubli, c'est son périmètre : il compte des événements, il n'enquête pas.

    Le champ `metadata` est pourtant libre, et rien n'empêchait d'y écrire `{"ip": request.remote_addr}`. C'est le geste naturel de qui veut compter des visiteurs uniques, et il transforme une table de statistiques en fichier de données personnelles, soumis à conservation limitée et à droit d'accès, sans que personne ne l'ait décidé.

    ```python
    from forge_mvc_stats import StatsEvent, visitor_hash

    StatsEvent(
        name="page_vue",
        kind="page_view",
        metadata={"visiteur": visitor_hash(adresse, config.SECRET_KEY)},
    )
    ```

    !!! danger "Une adresse brute est refusée à l'écriture"
        `StatsEvent(metadata={"ip": "203.0.113.42"})` **lève**.

        Le refus a lieu à l'écriture : la ligne ne doit pas exister, plutôt qu'être filtrée à chaque lecture. Le message nomme les deux solutions, et rappelle que conserver une adresse à des fins de sécurité relève de `forge-mvc-audit`, pas des statistiques.

    !!! info "Le contrôle porte sur la clé, pas sur la valeur"
        « 1.2.3.4 » est une adresse IPv4 valide **et** un numéro de version tout aussi valable.

        Refuser toutes les valeurs de cette forme casserait des métadonnées légitimes. Seule une valeur d'adresse rangée sous une clé qui la nomme, `ip`, `remote_addr`, `client_ip`, est refusée.

    | Fonction | Ce qu'elle garde |
    |---|---|
    | `visitor_hash` | rien : une empreinte salée, valable une journée |
    | `anonymize_ip` | l'adresse amputée de sa partie identifiante |

    !!! warning "`anonymize_ip` ne rend pas une donnée anonyme"
        Le résultat reste rattachable à un petit ensemble d'abonnés, et sur un réseau peu peuplé il désigne parfois une seule personne.

        Pour compter des visiteurs, `visitor_hash` est meilleur sur tous les plans : deux visites du même visiteur le même jour donnent la même empreinte, le lendemain non, et rien ne permet de remonter à l'adresse.

    !!! danger "Le secret de `visitor_hash` doit être un vrai secret"
        Sans lui, l'espace des adresses IPv4 se parcourt en entier en quelques secondes, et l'empreinte ne protège plus rien.

        Un secret vide est refusé.

??? note "13. Vue de page ou action métier"

    `category` est la taxonomie de l'application, « blog » ou « boutique », et elle est libre (`STATS-EVENT-KIND-001`).

    Le type d'événement est orthogonal : une consultation passive et un geste délibéré ne se comptent pas, ne se comparent pas et ne se lisent pas pareil. Mille pages vues valent moins qu'une commande passée, et les mélanger sous un même total donne un chiffre que personne ne peut interpréter.

    ```python
    StatsEvent(name="page_accueil", kind="page_view")
    StatsEvent(name="commande_passee", kind="action")     # défaut
    ```

    !!! info "Le vocabulaire est fermé, et c'est voulu"
        `page_view` et `action`, rien d'autre.

        Un troisième type inventé par une application rendrait le champ incomparable d'un projet à l'autre, ce qui est exactement ce qu'il doit permettre. Pour une distinction propre au métier, `category` est là, et elle est libre.

    !!! info "Le défaut est `action`"
        Les événements déjà en base ont été posés par des appels délibérés de l'application, jamais par un suivi de page : c'est la valeur qui les décrit correctement.

    La colonne arrive par une **migration additive**, `ALTER TABLE`. Une table déjà créée ne se recrée pas, et c'est la seule façon de la faire évoluer sans perdre les événements enregistrés. Appliquez `forge stats:init` puis `forge migration:apply`.

??? note "14. Agréger par jour, par page et par type"

    `count_stats_events` agrégeait par `name` et par `category` seulement (`DOC-STATS-AGGREGATES-001`).

    Grouper par journée demandait de rapatrier tous les horodatages pour les tronquer en Python, ce que la base fait sans rien déplacer.

    | Dimension | Ce qu'elle répond |
    |---|---|
    | `name` | quelles pages, ou quelles actions, reviennent le plus |
    | `category` | quelle partie de l'application est sollicitée |
    | `kind` | combien de consultations, combien de gestes |
    | `day` | comment cela évolue dans le temps |

    ```python
    count_stats_events(fetch_all, group_by="day", since="2026-01-01")
    count_stats_events(fetch_all, group_by="name", kind="page_view")
    ```

    !!! info "`day` n'est pas une colonne"
        C'est une expression rendue par le dialecte : aucun des quatre backends n'écrit la troncature d'un horodatage de la même façon, `DATE()`, `date()` ou `CAST(... AS DATE)`.

        Le type de la valeur rendue varie donc aussi, date native ici, chaîne là : rendez la en texte avant de l'afficher plutôt que de supposer l'un des deux.

    !!! warning "Une série temporelle se trie par le temps"
        Les autres dimensions se trient du plus fréquent au moins fréquent, ce qui est ce qu'on leur demande.

        Trier une courbe par total décroissant la rendrait illisible : `day` se trie donc par date croissante.

    !!! danger "La liste des dimensions est une liste blanche"
        `group_by` finit dans un `GROUP BY`, où aucun backend n'accepte de paramètre lié.

        C'est la liste blanche qui empêche une injection, et non un échappement. Un `kind` inconnu lève de même, un filtre qui rend zéro sans motif faisant chercher un défaut ailleurs, dans les données ou dans l'écriture des événements.

    Les fonctions vivent dans `aggregate.py` (`get_stats_counts_sql`, `prepare_stats_counts_params`, `count_stats_events`) et l'anonymisation dans `privacy.py` (`anonymize_ip`, `visitor_hash`, `assert_no_raw_address`, `looks_like_address_key`).

## Voir aussi

- [Événements (events.py)](references/events.md) : `StatsEvent`, validation des noms.
- [Table SQL (schema.py)](references/schema.md) : `forge_stats_events`.
- [Tracking (tracking.py)](references/tracking.md) : `track_event`.
- [Affichage admin (admin.py)](references/admin.md) : lister et filtrer.
- [Agrégation (aggregate.py)](references/aggregate.md) : compter par dimension (ADR-037).
- [Welcome-Stats](welcome/debutant/stats-welcome.md) : parcours d'apprentissage.

## Un tableau de bord minimal

Forge affiche, il ne génère pas d'écran de statistiques (principe 1, et ADR-035 pour les parcours faits à la main).
Voici les quatre chiffres qui suffisent à un tableau de bord, et le code à copier dans un contrôleur.

```python
from forge_mvc_stats import (
    KIND_ACTION, KIND_PAGE_VIEW, count_stats_events, list_stats_events,
)

def tableau_de_bord(fetch_all, *, depuis: str) -> dict[str, object]:
    return {
        "pages_les_plus_vues": count_stats_events(
            fetch_all, group_by="name", kind=KIND_PAGE_VIEW, since=depuis),
        "actions_les_plus_frequentes": count_stats_events(
            fetch_all, group_by="name", kind=KIND_ACTION, since=depuis),
        "consultations_par_jour": count_stats_events(
            fetch_all, group_by="day", kind=KIND_PAGE_VIEW, since=depuis),
        "derniers_evenements": list_stats_events(fetch_all, limit=20),
    }
```

Les trois premiers rendent des `{"bucket", "total"}`, le dernier des lignes normalisées.
Un gabarit Jinja les parcourt sans autre traitement.

```html
<h2>Pages les plus vues</h2>
<table>
  <tr><th>Page</th><th>Vues</th></tr>
  {% for ligne in pages_les_plus_vues %}
    <tr><td>{{ ligne.bucket }}</td><td>{{ ligne.total }}</td></tr>
  {% endfor %}
</table>
```

!!! warning "Séparer les deux types n'est pas un raffinement"
    Sans `kind`, les deux premières lignes rendraient le même total mêlé.

    Mille pages vues valent moins qu'une commande passée, et les additionner donne un chiffre que personne ne peut interpréter.

!!! info "`bucket` d'une série temporelle se rend en texte"
    Le type de la valeur varie selon le backend, date native ici, chaîne là.

    Convertissez-la avant de l'afficher plutôt que de supposer l'un des deux.

!!! note "Cet écran est à vous"
    Le tri, la période, la mise en forme et le contrôle d'accès relèvent de l'application.

    Une page de statistiques expose l'activité d'un site : protégez la route, par exemple avec `forge-mvc-rbac`.
