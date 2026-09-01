# Les statuts et transitions dans Forge (forge-mvc-workflow)

Ce document explique ce que fait l'opt-in `forge-mvc-workflow`, ce qu'il expose, et comment on s'en sert.

!!! note "Module extrait"
    Le workflow a été extrait du cœur vers le paquet `forge-mvc-workflow` ; le cœur Forge n'en dépend pas.

`forge-mvc-workflow` décrit une machine à états applicative : des statuts (brouillon, publié, archivé), des transitions autorisées entre eux, et des badges pour les afficher.

Il ne stocke rien lui-même : l'application garde le statut courant sur son entité ; l'opt-in dit quelles transitions sont permises.

??? note "1. Rôle du module"

    Beaucoup d'entités ont un cycle de vie : un article passe de `brouillon` à `publié`, puis `archivé`.

    L'opt-in modélise ce cycle : on déclare les **statuts** et les **transitions** autorisées, puis on vérifie qu'un changement est permis avant de l'appliquer.

    Il fournit aussi des **helpers Jinja** pour afficher un statut sous forme de badge coloré, sans logique dans le template.

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
    pip install --pre forge-mvc-workflow
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-workflow"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-workflow`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-workflow==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable workflow --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    Rien à faire : cet opt-in n'apporte aucune table.

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
    forge opt-in:disable workflow
    pip uninstall forge-mvc-workflow
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove workflow` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    Cet opt-in n'expose aucune commande CLI : il s'utilise **par import** dans le code applicatif (voir l'API publique ci-dessous).

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-workflow` |
    | Module | `forge_mvc_workflow` |
    | Catégorie | Données et modélisation (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` |
    | API publique | `WorkflowStatus`, `WorkflowTransition`, `make_status`, `make_transition`, `can_transition`, `get_available_transitions`, `apply_transition`, `TransitionEvent`, `statuses_from_entity_field`, helpers Jinja |
    | Persistance | aucune table imposée : l'application stocke le statut courant |
    | Helpers Jinja | `workflow_status_badge`, `workflow_status_label`, `workflow_status_color` |
    | Exceptions | `WorkflowStatusError`, `WorkflowTransitionError` |
    | Décision d'architecture | ADR-004 (opt-in officiel) |
    | Installation | `pip install --pre forge-mvc-workflow` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre les statuts, les transitions et les helpers.

    Le diagramme de séquence montre la vérification d'un changement de statut.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que les transitions relient des statuts, et que les helpers Jinja rendent un statut en badge.

    ```mermaid
    classDiagram
        direction LR

        class WorkflowStatus {
            <<dataclass>>
            +str name
            +str label
            +str color
            +bool is_initial
            +bool is_final
        }

        class WorkflowTransition {
            <<dataclass>>
            +str from_status
            +str to_status
        }

        class status {
            <<module>>
            +make_status(...) WorkflowStatus
            +find_status(...) WorkflowStatus
            +validate_statuses(...)
        }

        class transitions {
            <<module>>
            +make_transition(from, to) WorkflowTransition
            +can_transition(transitions, from, to) bool
            +get_available_transitions(transitions, from) list
            +validate_transitions(...)
        }

        class jinja {
            <<module>>
            +workflow_status_badge(...)
            +workflow_status_label(...)
            +workflow_status_color(...)
        }

        transitions --> WorkflowTransition : produit
        status --> WorkflowStatus : produit
        WorkflowTransition --> WorkflowStatus : relie
        jinja --> WorkflowStatus : affiche

    ```

    À retenir :

    - un `WorkflowStatus` porte un nom, un libellé, une couleur, des marqueurs initial/final ;
    - une `WorkflowTransition` relie un statut de départ à un statut d'arrivée ;
    - `can_transition` répond oui/non avant d'appliquer un changement ;
    - les helpers Jinja affichent un statut sans logique dans le template.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un changement de statut contrôlé.

    ```mermaid
    sequenceDiagram
        participant App as Contrôleur
        participant WF as forge_mvc_workflow
        participant Entity as Entité (statut stocké)

        App->>WF: can_transition(TRANSITIONS, "brouillon", "publie") ?
        alt transition autorisée
            WF-->>App: True
            App->>Entity: met à jour le statut = "publie"
        else transition interdite
            WF-->>App: False
            App-->>App: refuse / message d'erreur
        end
        App->>WF: get_available_transitions(TRANSITIONS, "publie")
        WF-->>App: transitions possibles (pour l'UI)

    ```

    À retenir :

    - on vérifie **avant** d'écrire le nouveau statut ;
    - l'application reste responsable de persister le statut ;
    - `get_available_transitions` alimente les boutons/menus de l'UI ;
    - une transition non déclarée est refusée.

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `make_status` | `make_status(name, label="", color="", is_initial=False, is_final=False) -> WorkflowStatus` | déclare un statut |
    | `make_transition` | `make_transition(from_status, to_status) -> WorkflowTransition` | déclare une transition |
    | `can_transition` | `can_transition(transitions, from_name, to_name) -> bool` | transition autorisée ? |
    | `apply_transition` | `apply_transition(transitions, from_status, to_status, *, before=None, commit=None, after=None, context=None) -> str` | applique dans un ordre garanti, rend le statut atteint |
    | `TransitionEvent` | `from_status`, `to_status`, `context` | ce que reçoivent les points d'accroche |
    | `statuses_from_entity_field` | `statuses_from_entity_field(entity, field_name, *, initial=None, final=None) -> list[WorkflowStatus]` | statuts lus des `choices` d'un contrat d'entité |
    | `statuses_from_choices` | `statuses_from_choices(choices, *, initial=None, final=None) -> list[WorkflowStatus]` | même conversion, depuis les choix seuls |
    | `status_values` | `status_values(statuses) -> list[str]` | noms des statuts, pour comparer deux sources |
    | `EntityStatusError` | exception | champ absent, ou choix inexploitable |
    | `get_available_transitions` | `get_available_transitions(transitions, from_name) -> list[WorkflowTransition]` | transitions possibles depuis un statut |
    | `find_status` | `find_status(...) -> WorkflowStatus` | retrouve un statut par nom |
    | `validate_statuses`, `validate_transitions` | fonctions | valident un jeu de statuts/transitions |
    | `WorkflowStatus`, `WorkflowTransition` | dataclasses | statut et transition |
    | helpers Jinja | `workflow_status_badge`, `workflow_status_badge_class`, `workflow_status_color`, `workflow_status_label`, `make_workflow_jinja_helpers` | affichage |
    | `WorkflowStatusError`, `WorkflowTransitionError` | exceptions | nom invalide, transition invalide |

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Déclarer le cycle de vie | `make_status` + `make_transition` |
    | Autoriser un changement | `can_transition(...)` |
    | Appliquer un changement | `apply_transition(...)` |
    | Refuser selon une règle métier | lever depuis `before` |
    | Éviter de déclarer les statuts deux fois | `statuses_from_entity_field(...)` |
    | Proposer les suites possibles | `get_available_transitions(...)` |
    | Valider la configuration | `validate_statuses` / `validate_transitions` |
    | Afficher un badge | `workflow_status_badge(...)` (Jinja) |

??? note "9 ter. Prendre les statuts du contrat d'entité"

    Une application qui gère un cycle de vie déclarait sa liste de statuts **deux fois**.

    Une fois en `choices` du contrat d'entité, pour que le formulaire propose un choix et que la base accepte la valeur.
    Une autre fois en Python, en `make_status`, pour que le workflow connaisse ses transitions.

    Rien ne gardait les deux identiques (`WORKFLOW-ENTITY-STATUS-001`).
    Ajouter un statut au contrat sans toucher au workflow donne un choix que le formulaire propose et que la transition refuse.
    Le retirer donne une transition vers un statut que la base n'accepte plus.
    Dans les deux cas, la panne n'apparaît qu'à l'usage, et sur un seul chemin.

    ```python
    import json
    from forge_mvc_workflow import make_transition, statuses_from_entity_field, validate_transitions

    contrat = json.loads(Path("mvc/entities/article.json").read_text(encoding="utf-8"))

    STATUSES = statuses_from_entity_field(
        contrat, "statut", initial="draft", final=("archived",)
    )
    TRANSITIONS = validate_transitions(
        [make_transition("draft", "published"), make_transition("published", "archived")],
        STATUSES,
    )
    ```

    `validate_transitions` refuse alors toute transition vers un statut que le contrat ne déclare pas, au chargement et non à l'usage.

    !!! info "Le champ est nommé, jamais deviné"
        Repérer « le champ qui ressemble à un statut » supposerait une convention de nommage que Forge n'impose pas, et se tromperait sur une entité qui en porte deux, un statut de publication et un état de paiement par exemple.

    !!! warning "Le début et la fin du cycle se déclarent"
        Un contrat d'entité dit quelles valeurs sont permises, jamais laquelle commence un cycle ni lesquelles le terminent.

        `initial` et `final` sont donc explicites, et une valeur absente des choix est refusée : une faute de frappe y produirait sinon un cycle sans début, que rien ne signalerait.

    !!! info "Aucune dépendance vers le moteur d'entités"
        Un contrat est un dictionnaire JSON dont la forme est documentée.

        Le lire ne demande pas d'importer `forge-mvc-entities`, et ce module ne le fait pas : un projet qui décrit ses entités autrement peut lui passer la même structure.

??? note "9 bis. Appliquer une transition"

    Le paquet savait dire si une transition est **permise**, jamais l'appliquer.
    Chaque application réécrivait le même enchaînement à la main, et rien n'empêchait d'appeler l'action d'après quand celle d'avant avait refusé (`WORKFLOW-HOOKS-001`).

    ```python
    from forge_mvc_workflow import apply_transition

    def publier(article, auteur):
        def verifier(evenement):
            if not article.resume:
                raise ValueError("Un article publié doit avoir un résumé.")

        def ecrire(evenement):
            article.status = evenement.to_status
            enregistrer(article)

        def prevenir(evenement):
            notifier_abonnes(article)

        return apply_transition(
            TRANSITIONS, article.status, "published",
            before=verifier, commit=ecrire, after=prevenir,
            context={"auteur": auteur},
        )
    ```

    L'ordre est garanti, et chaque étape conditionne la suivante.

    | Rang | Étape | Si elle lève |
    |---|---|---|
    | 1 | Vérification de la transition | rien d'autre n'est appelé |
    | 2 | `before` | ni l'écriture ni `after` n'ont lieu |
    | 3 | `commit` | `after` n'a pas lieu |
    | 4 | `after` | l'écriture reste faite |

    !!! info "Un refus se lève, il ne se rend pas"
        Un point d'accroche ne rend rien : pour refuser, il lève.

        Un booléen de retour obligerait Forge à inventer un message d'erreur à la place de la règle métier, alors que l'exception porte déjà le sien.
        Elle remonte telle quelle, sans enveloppe : un message maquillé ferait perdre la cause.

    !!! warning "`after` ne défait rien"
        Une exception levée après l'écriture ne l'annule pas.

        L'avaler cacherait un état déjà changé, ce qui est pire que de la laisser remonter.
        Une opération qui doit pouvoir être annulée appartient à une transaction, que l'application ouvre autour de son `commit`.

    !!! info "Le paquet ne persiste rien"
        `commit` est fourni par l'application, seule à savoir où son statut est rangé.

        Sans lui, `after` suit immédiatement `before` : le paquet n'a alors aucun moyen de savoir si l'écriture a eu lieu, et le dire vaut mieux que de laisser croire à une garantie qui n'existe pas.

??? note "10. Exemples d'utilisation"

    ### 8.1 Déclarer et vérifier

    ```python
    from forge_mvc_workflow import make_status, make_transition, can_transition

    STATUSES = [
        make_status("brouillon", "Brouillon", color="gray", is_initial=True),
        make_status("publie", "Publié", color="green"),
        make_status("archive", "Archivé", color="slate", is_final=True),

    ]
    TRANSITIONS = [
        make_transition("brouillon", "publie"),
        make_transition("publie", "archive"),

    ]

    if can_transition(TRANSITIONS, "brouillon", "publie"):
        article["status"] = "publie"      # l'application persiste

    ```

    ### 8.2 Afficher un badge dans un template

    ```html
    {{ workflow_status_badge(STATUSES, article.status) }}
    ```

    `get_available_transitions(TRANSITIONS, article.status)` donne les boutons d'action à proposer.

    !!! tip "Aide-mémoire"
        Déclarer, vérifier, afficher :

        - `make_status` / `make_transition` pour le cycle ;
        - `can_transition` / `get_available_transitions` pour la logique ;
        - les helpers Jinja pour l'affichage.

??? note "11. Persistance et validation"

    L'opt-in ne crée **aucune table** : le statut courant est un simple champ de votre entité, que vous mettez à jour vous-même après un `can_transition` positif.

    `validate_statuses` et `validate_transitions` détectent les configurations incohérentes (statut inconnu, doublon de transition) au démarrage.

    !!! note "L'opt-in décide, l'application persiste"
        `forge-mvc-workflow` répond « cette transition est-elle permise ?
        »
        ; il n'écrit jamais en base.

        Vous gardez la main sur le stockage du statut (champ d'entité, migration).

    !!! note "Affichage sans logique dans le template"
        Les helpers Jinja produisent libellé, couleur et badge à partir d'un nom de statut.

        Le template reste déclaratif ; la table des statuts vit dans votre code.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-workflow` : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Statuts (status.py)](references/status.md) : `WorkflowStatus`, validation des noms.
- [Transitions (transitions.py)](references/transitions.md) : `can_transition`, transitions disponibles.
- [Helpers Jinja (jinja.py)](references/jinja.md) : badges et libellés.
- [Welcome-Workflow](welcome/debutant/workflow-welcome.md) : parcours d'apprentissage.
