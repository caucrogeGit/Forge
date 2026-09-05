# Le journal d'audit dans Forge (forge-mvc-audit)

Ce document explique ce que fait l'opt-in `forge-mvc-audit`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-audit` trace les actions importantes d'une application dans une table `audit_log`, avec une API explicite `record_audit` / `get_audit_log`.

Le cœur de Forge ignore tout de l'audit applicatif : ce paquet fournit la table et les helpers, l'application décide de ce qu'elle trace.

??? note "1. Rôle du module"

    Une application a besoin de garder une trace des actions sensibles : élève créé, note modifiée, rôle changé, fichier supprimé.

    L'opt-in stocke ces traces dans une table SQL (`audit_log`) et expose deux fonctions : une pour écrire une trace, une pour relire le journal.

    Son périmètre est **borné** : c'est un audit applicatif, pas un SIEM de cybersécurité (cohérent avec ADR-008, la décision de tracer reste applicative).

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
    pip install --pre forge-mvc-audit
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-audit"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-audit`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-audit==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable audit --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    ```bash
    forge audit:init
    forge migration:apply
    ```

    `audit:init` copie la migration embarquée dans `mvc/migrations/` ;
    `migration:apply` l'exécute et la trace (ADR-071).
    Sans cette étape, le premier appel échoue sur une table absente.

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
    forge opt-in:disable audit
    pip uninstall forge-mvc-audit
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove audit` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-audit` ajoute deux commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `audit:init` | Crée la table `audit_log` (DDL fournie). | `forge audit:init` |
    | `audit:gc` | Purge le journal par âge. Affiche par défaut, `--run` exécute. | `forge audit:gc --days 90 --run` |

    !!! warning "Rétention du journal"
        `audit_log` grossit à chaque action tracée et rien ne la borne d'elle-même.
        Sans purge, la table finit par peser sur les lectures, et rien ne vous préviendra.

        La rétention doit être **dite**, Forge ne suppose aucune valeur à votre place.
        Elle vient de `--days N`, ou à défaut de la variable d'environnement `AUDIT_KEEP_DAYS` ; l'option l'emporte sur la variable.

        ```bash
        forge audit:gc --days 90          # affiche le nombre d'entrées visées
        forge audit:gc --days 90 --run    # supprime
        ```

        Contrairement à `sessions:gc`, qui supprime directement, la commande affiche d'abord.
        Une session expirée n'est plus rien pour personne, son expiration est portée par la ligne elle-même.
        Une entrée d'audit est un enregistrement délibéré, et aucune date ne dit d'elle-même qu'elle a cessé de valoir.

        Forge ne fournit pas d'ordonnanceur, cette commande est le point d'entrée à brancher sur cron ou un minuteur systemd.

        Deux limites à connaître.
        Aucune archive n'est produite avant suppression, donc exportez en amont si votre obligation de conservation l'exige.
        Et la suppression tient en une instruction, si bien que sur une très grosse table le verrou peut être long.

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-audit` |
    | Module | `forge_mvc_audit` |
    | Catégorie | Sécurité et accès (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` et un backend BDD installé (ADR-054) |
    | API publique | `record_audit`, `get_audit_log`, `AuditEntry`, `iter_audit_rows`, `record_request_audit` |
    | Table SQL | `audit_log` (`TABLE_NAME`) |
    | Limite de lecture | `MAX_LIMIT` = 1000 entrées |
    | Exception liée | `AuditError` si l'action est vide ou la limite invalide |
    | Cadre | ADR-008 (Forge fournit la table et le helper) |
    | Installation | `pip install --pre forge-mvc-audit` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre l'API, l'entrée renvoyée et la table.

    Le diagramme de séquence montre l'écriture puis la relecture d'une trace.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le module écrit dans la table `audit_log` au travers d'un exécuteur **injecté** et renvoie des `AuditEntry` typés.

    ```mermaid
    classDiagram
        direction LR

        class audit {
            <<module>>
            +record_audit(action, actor, target_type, target_id, details, db) int
            +get_audit_log(limit, actor, action, target_type, target_id, db) list
        }

        class AuditEntry {
            <<dataclass>>
            +int id
            +str actor
            +str action
            +str target_type
            +str target_id
            +str details
            +str created_at
        }

        class audit_log {
            <<table>>
            +id
            +actor
            +action
            +target_type
            +target_id
            +details
            +created_at
        }

        class DBExecutor {
            +execute(sql, params)
            +fetch_all(sql, params)
        }

        class AuditError {
            <<exception>>
        }

        audit --> DBExecutor : exécuteur injecté
        DBExecutor --> audit_log : lit / écrit
        audit --> AuditEntry : renvoie 0..*
        audit ..> AuditError : peut lever

    ```

    À retenir :

    - le module expose deux fonctions, pas de classe à instancier ;
    - les traces vivent dans la table `audit_log` ;
    - `get_audit_log` renvoie des `AuditEntry` typés ;
    - le module n'ouvre jamais de connexion : il reçoit un exécuteur.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un `record_audit` suivi d'un `get_audit_log` filtré.

    ```mermaid
    sequenceDiagram
        participant App as Code applicatif
        participant Audit as forge_mvc_audit
        participant DB as Exécuteur BDD
        participant Table as audit_log

        App->>Audit: record_audit("note.update", actor="prof", target_id=42)
        Audit->>Audit: valide l'action
        Audit->>DB: execute(INSERT, params)
        DB->>Table: insère la ligne
        Audit-->>App: id de la trace
        App->>Audit: get_audit_log(action="note.update", limit=20)
        Audit->>DB: fetch_all(SELECT filtré, params)
        DB-->>Audit: lignes
        Audit-->>App: list[AuditEntry] (plus récentes d'abord)

    ```

    À retenir :

    - `record_audit` valide l'action puis insère, et renvoie l'identifiant ;
    - `get_audit_log` renvoie les entrées les plus récentes d'abord ;
    - les filtres (`actor`, `action`, `target_type`, `target_id`) sont optionnels ;
    - `limit` est plafonné à `MAX_LIMIT`.

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `record_audit` | `record_audit(action, *, actor=None, target_type=None, target_id=None, details=None, db=None) -> int` | écrit une trace, renvoie son id |
    | `get_audit_log` | `get_audit_log(*, limit=100, actor=None, action=None, target_type=None, target_id=None, db=None) -> list[AuditEntry]` | relit le journal, filtrable |
    | `AuditEntry` | dataclass | une entrée : `id`, `actor`, `action`, `target_type`, `target_id`, `details`, `created_at` |
    | `AuditError` | exception (`ValueError`) | action vide ou limite invalide |
    | `TABLE_NAME` | `"audit_log"` | nom de la table |
    | `MAX_LIMIT` | `1000` | plafond du paramètre `limit` |

    Le paramètre `action` est obligatoire : c'est une chaîne applicative (par exemple `"eleve.create"`, `"note.update"`).

    Le paramètre `db` est l'exécuteur de base de données ; omis, il utilise le backend BDD actif.

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Tracer une action | `record_audit("action", ...)` |
    | Associer un acteur | paramètre `actor=...` |
    | Désigner la cible | `target_type=...`, `target_id=...` |
    | Ajouter un détail libre | paramètre `details=...` |
    | Relire les dernières traces | `get_audit_log(limit=...)` |
    | Filtrer le journal | `actor=`, `action=`, `target_type=`, `target_id=` |
    | Créer la table | `forge audit:init` puis `forge migration:apply` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Tracer une action

    ```python
    from forge_mvc_audit import record_audit

    record_audit(
        "note.update",
        actor="prof.martin",
        target_type="note",
        target_id=42,
        details="note passée de 12 à 14",

    )
    ```

    ### 8.2 Relire et filtrer le journal

    ```python
    from forge_mvc_audit import get_audit_log

    dernieres = get_audit_log(limit=20)
    sur_les_notes = get_audit_log(action="note.update", limit=50)

    for entry in sur_les_notes:
        print(entry.created_at, entry.actor, entry.details)

    ```

    `get_audit_log` renvoie des `AuditEntry`, les plus récents d'abord.

    !!! tip "Aide-mémoire"
        Deux fonctions, une table :

        - `record_audit` pour écrire une trace ;
        - `get_audit_log` pour relire, avec des filtres optionnels.

??? note "11. Périmètre, validation et injection"

    L'action est obligatoire et non vide ; sinon `record_audit` lève `AuditError`.

    `limit` est plafonné à `MAX_LIMIT` (1000) pour éviter de charger un journal entier par mégarde.

    !!! warning "Création de la table"
        Les fonctions supposent la table `audit_log` présente.

        Créez-la avec `forge audit:init` puis `forge migration:apply`, avant le premier appel.

    !!! note "Périmètre borné"
        `forge-mvc-audit` est un journal d'audit **applicatif**, pas un SIEM de cybersécurité.

        Il trace ce que l'application décide de tracer (ADR-008) ; il ne surveille pas le système ni le réseau.

    !!! note "SQL visible et indépendance du cœur"
        Le module ne crée jamais de connexion : il reçoit un exécuteur (`execute`, `fetch_all`).

        Le cœur de Forge ne dépend pas de `forge-mvc-audit` : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Le journal d'audit (store.py)](references/store.md) : détail des fonctions et du SQL.
- [Initialisation (audit:init)](references/cli.md) : création de la table.
- [Les erreurs (errors.py)](references/errors.md) : détail de `AuditError`.
- [Welcome-Audit](welcome/debutant/audit-welcome.md) : parcours d'apprentissage.

## Déclaration de table

Le paquet ne livre plus de fichier SQL figé : il **déclare** sa table dans `tables.py`
(`AUDIT_LOG`, plus la liste `MIGRATIONS`).
Le DDL est rendu pour le backend installé par `core.database.table_ddl`, puis écrit
dans `mvc/migrations/` par `forge audit:init` (chantier `OPTIN-DDL-DIALECTAL`).
Le SQL reste donc relisible avant `forge migration:apply`, mais il est correct pour
MariaDB, SQLite, PostgreSQL comme SQL Server.

## Exporter le journal

Un journal se lit à l'écran et s'exporte pour rendre des comptes.

`get_audit_log` rend des `AuditEntry`, quand un écrivain CSV attend des dictionnaires : les deux ne se composaient pas.
Surtout, il borne à mille entrées **en silence** : un export demandé sur cent mille lignes en rendait mille sans rien dire (`AUDIT-CSV-EXPORT-001`).

Pour un journal qu'on exporte précisément parce qu'il fait foi, c'est le pire des défauts : le fichier paraît complet.

```python
from forge_mvc_audit import AUDIT_EXPORT_COLUMNS, iter_audit_rows
from forge_mvc_import_export import to_csv

lignes = list(iter_audit_rows(actor="roger"))
contenu = to_csv(lignes, list(AUDIT_EXPORT_COLUMNS))
```

| Colonne | Contenu |
|---|---|
| `id` | identifiant de l'entrée |
| `created_at` | horodatage |
| `actor` | auteur de l'action |
| `action` | l'action tracée |
| `target_type`, `target_id` | l'objet visé |
| `details` | complément libre |

!!! warning "L'export n'est pas borné, la lecture l'est"
    `get_audit_log` garde sa limite, qui protège un affichage.

    `iter_audit_rows` avance tant qu'il reste des entrées : un export doit être complet ou ne pas exister.

!!! info "L'avance se fait par identifiant, jamais par décalage"
    Un `OFFSET` sur une table qui reçoit des écritures pendant l'export sauterait ou répéterait des lignes.

    C'est exactement ce qu'un journal ne peut pas se permettre, et un test vérifie qu'aucune entrée n'est répétée.

!!! info "Le module rend des lignes, il n'écrit aucun fichier"
    `forge-mvc-import-export` les écrit, et aucun des deux paquets n'importe l'autre.

    Une application qui préfère du JSON ou un tableur passe les mêmes lignes à son propre écrivain.

!!! info "Les cellules restent inertes pour un tableur"
    `to_csv` neutralise déjà une cellule commençant par `=`, `+`, `-` ou `@`, qui redeviendrait une formule vive à l'ouverture.

    L'export d'audit en hérite sans rien réécrire, et un test le vérifie sur un cas réel.

Une valeur absente devient une chaîne vide et non `None`.
Dans un fichier destiné à être relu par un humain, `None` s'écrirait tel quel et se lirait comme une donnée.

## Borner un journal à une période

Quatre filtres d'égalité existaient déjà, par acteur, action et cible.

La question qu'on pose le plus souvent à un journal n'avait aucune réponse : « que s'est-il passé entre telle date et telle autre » (`AUDIT-FILTERS-001`).

```python
from forge_mvc_audit import get_audit_log, iter_audit_rows

# Lecture, à l'écran
get_audit_log(actor="roger", since="2026-03-01", until="2026-03-05")

# Export, même bornage
iter_audit_rows(since="2026-03-01", until="2026-03-05")
```

Les deux bornes sont **incluses**, et se combinent aux filtres d'égalité.

| Forme acceptée | Exemple |
|---|---|
| `datetime` | `datetime(2026, 3, 1, 14, 30)` |
| horodatage | `"2026-03-01 14:30:00"` |
| date seule | `"2026-03-01"` |

!!! warning "Une date de fin inclut la journée entière"
    `until="2026-03-05"` couvre jusqu'à `23:59:59`, et non jusqu'à minuit.

    C'est le piège le plus courant d'un filtre de période, et il est silencieux : à minuit, la journée du 5 serait exclue alors que l'utilisateur qui a saisi cette date l'attend incluse.
    Une date de début vaut en revanche minuit, ce qui inclut la journée aussi.

!!! info "Une période inversée est refusée"
    `since` postérieur à `until` lève, plutôt que de rendre zéro entrée.

    Un résultat vide sans motif ferait chercher un défaut ailleurs, dans les droits ou dans l'écriture du journal.

!!! info "Les bornes partent en paramètres liés"
    Aucune expression SQL de date n'entre dans la requête.

    C'est ce qui la rend portable sur les quatre backends sans effort, motif dont l'audit `OPTIN-DML-DIALECT-001` a mesuré le coût inverse.

Un champ de formulaire laissé vide ne borne rien : la chaîne vide est traitée comme une absence de filtre, pas comme une date invalide.

## Tracer depuis un contrôleur

`record_audit` demande l'acteur en paramètre, et l'exemple ci-dessus l'écrit à la main.

Dans un contrôleur il vient de la session, et chaque appel devait l'en extraire.
L'oublier une fois donne une ligne sans acteur, c'est-à-dire un journal qui ne répond plus à « qui a fait cela » (`AUDIT-ACTION-HELPER-001`).

Rien ne le signale : la ligne existe, elle est simplement inutile.

```python
from forge_mvc_audit import record_request_audit

def update(self, request):
    ...
    record_request_audit(
        request, "note.modifiee",
        target_type="note", target_id=note.id, details="12 vers 14",
    )
```

!!! info "Un acteur absent est une information"
    L'acteur vaut `None` quand personne n'est authentifié.

    Une action déclenchée par un visiteur anonyme ou par une tâche de fond n'a pas d'auteur, et inventer « system » masquerait la différence entre les deux.

!!! warning "Le journal ne fait jamais échouer l'action qu'il trace"
    Une session illisible ou un cœur indisponible donnent un acteur absent, jamais une exception.

    Un journal qui interrompt l'opération qu'il devait enregistrer serait pire que l'absence de journal.

Le reste du contrat est celui de `record_audit` : mêmes champs de cible, même refus d'une action vide, même identifiant rendu.

## Journaliser les refus d'accès

`forge-mvc-rbac` annonce ses refus de permission à qui veut les entendre, sans imposer de destinataire.
Un refus rendait sinon une 403 et rien d'autre : une énumération de droits, quelqu'un qui essaie une à une les routes protégées, ne laissait aucune trace.

Le branchement est explicite, et se pose une fois au câblage de l'application (`AUDIT-RBAC-DENIALS-BRIDGE-001`).

```python
from forge_mvc_audit import audit_permission_denials

audit_permission_denials()
```

Chaque refus devient alors une ligne du journal.

| Champ de la ligne | Contenu |
|---|---|
| `action` | `acces.refuse` (constante `DENIAL_ACTION`) |
| `actor` | l'utilisateur authentifié, ou `None` s'il ne l'était pas |
| `target_type` | `permission` (constante `DENIAL_TARGET_TYPE`) |
| `target_id` | la permission refusée, par exemple `eleve.supprimer` |
| `details` | la méthode, le chemin et la garde, par exemple `POST /admin/eleves/12 (garde : contract)` |

La permission tient dans la cible, donc les lister tous est une lecture ordinaire.

```python
from forge_mvc_audit import DENIAL_TARGET_TYPE, get_audit_log

refus = get_audit_log(target_type=DENIAL_TARGET_TYPE, limit=100)
```

!!! info "Le second branchement ne rebranche pas"
    Appeler `audit_permission_denials()` deux fois rend l'observateur déjà posé, sans en ajouter un second.

    Deux observateurs écriraient deux lignes par refus, et compter les refus donnerait le double sans que rien ne le signale.

!!! warning "Un refus ne devient jamais une panne"
    Si la base d'audit est indisponible, l'exception est avalée et journalisée par `forge-mvc-rbac`, et le refus s'applique quand même.

    Transformer un 403 en 500 parce que le journal est en panne ferait d'un contrôle d'accès qui fonctionne une panne du site.

!!! note "La garde qui a refusé est retenue, et ce n'est pas un détail"
    Un refus contractuel et un refus de permissions chargées en base ne se corrigent pas au même endroit.

    C'est pourquoi le branchement porte `source`, que la recette d'une ligne montrée dans la documentation de `forge-mvc-rbac` laissait tomber.

Si `forge-mvc-rbac` n'est pas installé, l'appel lève `AuditError` au câblage, moment où l'erreur se corrige, plutôt qu'au premier refus où elle serait avalée.
