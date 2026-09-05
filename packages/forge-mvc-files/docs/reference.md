# L'upload de fichiers dans Forge (forge-mvc-files)

Ce document explique ce que fait l'opt-in `forge-mvc-files`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-files` détient le pipeline d'upload générique : valider, écrire sur disque de façon sécurisée, servir un fichier en streaming, le supprimer, limiter le débit d'upload.

C'est le socle des médias : `forge-mvc-images`, `forge-mvc-video` et `forge-mvc-audio` s'appuient dessus.

??? note "1. Rôle du module"

    Recevoir un fichier d'un formulaire et le stocker en toute sécurité demande plusieurs étapes : valider l'extension, le type MIME et la taille, neutraliser le nom (anti-traversal), écrire sur disque, puis savoir le re-servir.

    L'opt-in regroupe ce pipeline derrière une API simple : `save_upload` pour entrer un fichier, `serve_media_file` pour le ressortir.

    La **validation pure** (extension, MIME, taille) reste dans le cœur (`core.forms.upload_validation`, ADR-019) et est réexportée ici : le cœur ne peut pas dépendre d'un opt-in (ADR-004).

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
    pip install --pre forge-mvc-files
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-files"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-files`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-files==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable files --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    Cet opt-in n'apporte aucune table, mais il a tout de même une initialisation :

    ```bash
    forge upload:init
    ```

    Elle crée `storage/uploads/` et ses sous-dossiers `images/`, `documents/` et `tmp/`.
    Ne pas avoir de tables ne veut pas dire n'avoir rien à faire.

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
    forge opt-in:disable files
    pip uninstall forge-mvc-files
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove files` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-files` ajoute ces commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `upload:init` | Initialise les dossiers de stockage d'upload. | `forge upload:init` |
    | `media:init` | Initialise les dossiers de stockage média. | `forge media:init` |
    | `files:init` | Écrit la migration du registre de fichiers. | `forge files:init` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-files` |
    | Module | `forge_mvc_files` |
    | Catégorie | Médias et fichiers (ADR-055) |
    | Couche | opt-in (brique optionnelle), socle des médias |
    | Dépend de | `forge-mvc` (validation et exceptions restent au cœur) |
    | API publique | `save_upload`, `SavedUpload`, `serve_media_file`, `delete_upload`, `delete_media_file`, primitives de stockage, rate-limit, registre (`record_file`, `owner_usage_bytes`) |
    | Table SQL | `forge_files`, optionnelle (ADR-094) |
    | Objet renvoyé | `SavedUpload` (métadonnées du fichier écrit) |
    | Service HTTP | `serve_media_file` (streaming, HTTP Range) |
    | Racine de stockage | variable d'environnement `UPLOAD_ROOT` (défaut `storage/uploads`) |
    | Exceptions | `UploadError` et ses sous-classes (extension, MIME, taille, stockage) |
    | Décisions d'architecture | ADR-019 (extraction), ADR-020 (primitives) |
    | Installation | `pip install --pre forge-mvc-files` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre l'API d'upload, les primitives de stockage et la hiérarchie d'exceptions.

    Le diagramme de séquence montre l'enregistrement d'un upload puis sa relecture.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que `save_upload` valide (via le cœur), écrit via les primitives de stockage, et renvoie un `SavedUpload` ; `serve_media_file` produit une `Response` du cœur.

    ```mermaid
    classDiagram
        direction LR

        class files {
            <<module>>
            +save_upload(file, category) SavedUpload
            +serve_media_file(path, root, request) Response
            +delete_upload(path) bool
            +get_upload_path(filename, category) Path
            +upload_root() Path
        }

        class SavedUpload {
            <<dataclass>>
            +str filename
            +str original_name
            +str path
            +str category
            +int size
            +str mime_type
            +dict variants
        }

        class storage {
            <<module>>
            +secure_filename(name) str
            +save_bytes(data, ...) str
            +is_safe_media_path(path) bool
        }

        class UploadError {
            <<exception>>
        }

        class Response {
            +int status
            +body
        }

        files --> storage : écrit via
        files --> SavedUpload : renvoie
        files --> Response : serve_media_file
        files ..> UploadError : peut lever

    ```

    À retenir :

    - `save_upload` est l'entrée unique : valider, sécuriser, écrire ;
    - il renvoie un `SavedUpload` (nom stocké, chemin, taille, MIME) ;
    - `serve_media_file` ressort le fichier en `Response`, avec HTTP Range ;
    - toute anomalie d'upload lève une sous-classe de `UploadError`.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un upload de formulaire puis l'affichage du média.

    ```mermaid
    sequenceDiagram
        actor Navigateur
        participant Ctrl as Contrôleur
        participant Files as forge_mvc_files
        participant Core as Validation (cœur)
        participant Disk as Disque (UPLOAD_ROOT)

        Navigateur->>Ctrl: POST formulaire (multipart, fichier)
        Ctrl->>Files: save_upload(file, category="images")
        Files->>Core: valide extension / MIME / taille
        Files->>Files: secure_filename (anti-traversal)
        Files->>Disk: écrit les octets
        Files-->>Ctrl: SavedUpload (path, size, mime_type)

        Navigateur->>Ctrl: GET /media/<path>
        Ctrl->>Files: serve_media_file(path, request=request)
        Files->>Disk: lit le fichier (par plage si Range)
        Files-->>Ctrl: Response (streaming, 200 ou 206)
        Ctrl-->>Navigateur: le média

    ```

    À retenir :

    - la validation s'appuie sur le cœur, mais l'écriture vit dans l'opt-in ;
    - le nom de fichier est neutralisé avant écriture (anti-traversal) ;
    - `serve_media_file` répond `206 Partial Content` si la requête envoie un `Range` ;
    - le chemin servi est validé pour rester sous la racine de stockage.

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `save_upload` | `save_upload(file, category="documents") -> SavedUpload` | valide, sécurise et écrit un upload |
    | `SavedUpload` | dataclass | `filename`, `original_name`, `path`, `category`, `size`, `mime_type`, `variants` |
    | `serve_media_file` | `serve_media_file(path, *, root=None, request=None) -> Response` | sert un fichier (streaming, HTTP Range) |
    | `delete_upload` | `delete_upload(path) -> bool` | supprime un fichier uploadé |
    | `delete_media_file` | `delete_media_file(path, *, root=None, variants=False) -> dict` | supprime un média et ses variantes |
    | `get_upload_path` | `get_upload_path(filename, category="documents") -> Path` | chemin disque d'un fichier |
    | `upload_root` | `upload_root() -> Path` | racine de stockage (`UPLOAD_ROOT`) |
    | primitives stockage | `secure_filename`, `save_bytes`, `is_safe_media_path`, `normalize_media_path`, `delete_file` | briques bas niveau (ADR-020) |
    | rate-limit | `is_upload_rate_limited`, `record_upload_attempt` | limiter le débit d'upload |
    | exceptions | `UploadError`, `UploadInvalidExtensionError`, `UploadInvalidMimeTypeError`, `UploadTooLargeError`, `UploadStorageError` | erreurs d'upload (réexportées du cœur) |

    `category` range le fichier dans un sous-dossier (`documents`, `images`...).

    `file` est un objet d'upload duck-typé (champ multipart, fichier Python, wrapper applicatif).

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Enregistrer un fichier reçu | `save_upload(file, category=...)` |
    | Servir un fichier | `serve_media_file(path, request=request)` |
    | Supprimer un fichier | `delete_upload(path)` |
    | Connaître la racine de stockage | `upload_root()` ou `UPLOAD_ROOT` |
    | Sécuriser un nom de fichier | `secure_filename(name)` |
    | Limiter les uploads abusifs | `is_upload_rate_limited(...)` |
    | Gérer un upload refusé | intercepter `UploadError` |
    | Inscrire un fichier écrit | `record_file(path, original_name, size_bytes, ...)` |
    | Calculer un quota | `owner_usage_bytes(kind, id)` |
    | Repérer des orphelins | `list_all_paths()` |

??? note "9 bis. Le registre des fichiers écrits"

    Le paquet écrivait des fichiers sans garder trace de ce qu'il avait écrit.

    Sans registre, aucun quota n'est calculable, aucun orphelin n'est repérable, et le nom d'origine ne survit pas au mode UUID, qui l'efface du chemin par sécurité.
    L'ADR-094 amende l'ADR-020 sur ce seul point.

    ```bash
    forge files:init          # écrit la migration
    forge migration:apply     # l'applique
    ```

    L'inscription est **explicite**, comme l'écriture.

    ```python
    from forge_mvc_files import record_file, save_upload

    enregistre = save_upload(fichier, category="documents")
    record_file(
        enregistre.path,
        enregistre.original_name,
        enregistre.size,
        mime_type=enregistre.mime_type,
        owner_kind="user",
        owner_id=utilisateur.id,
    )
    ```

    Le quota se calcule ensuite sur le registre.

    ```python
    from forge_mvc_files import owner_usage_bytes

    if owner_usage_bytes("user", utilisateur.id) + enregistre.size > PLAFOND:
        return refuser("Quota dépassé.")
    ```

    !!! info "Écrire un fichier n'inscrit rien de soi même"
        `save_upload` ne touche pas au registre, et un test le vérifie sur la source.

        Un opt-in qui écrirait en base à l'insu de son appelant serait de la magie cachée, que le principe 3 refuse.
        Le paquet reste donc utilisable **sans base**, pour qui ne veut que des primitives de stockage.

    !!! info "Le propriétaire est libre"
        `owner_kind` et `owner_id` forment un couple que l'application remplit comme elle l'entend.

        `forge-mvc-files` ne sait pas ce qu'est un utilisateur, et ne cherche pas à le savoir.
        Les deux vont de pair : fournir l'un sans l'autre est refusé, car un identifiant sans nature ne désigne personne.

    !!! warning "Le registre ne touche jamais au disque"
        `forget_file` retire une ligne, il ne supprime aucun fichier.

        L'appelant décide de l'ordre entre le disque et le registre, et reste seul à connaître sa racine de stockage.

    !!! info "Deux tables décrivent des fichiers"
        `forge-mvc-images` porte une table `media`, avec le rôle, la position et le texte alternatif dont une galerie a besoin.

        Le registre ne porte aucune de ces colonnes : il dit ce que le stockage sait, jamais une notion métier.
        Le doublon partiel est assumé le temps de la série 1.x, la convergence appartenant à un ticket post-1.0.

??? note "10. Exemples d'utilisation"

    ### 8.1 Enregistrer un upload depuis un contrôleur

    ```python
    from core.http.request import Request
    from core.http.response import Response
    from forge_mvc_files import save_upload, UploadError


    def upload(request: Request) -> Response:
        file = request.file("document")
        try:
            saved = save_upload(file, category="documents")
        except UploadError as exc:
            return Response.text(f"Upload refusé : {exc}", status=400)
        return Response.text(f"Reçu : {saved.path} ({saved.size} octets)")

    ```

    ### 8.2 Servir un fichier (avec HTTP Range)

    ```python
    from forge_mvc_files import serve_media_file


    def media(request: Request) -> Response:
        path = request.route("path")
        return serve_media_file(path, request=request)

    ```

    En passant `request`, le service honore l'en-tête `Range` et répond `206 Partial Content` quand le client demande une plage.

    !!! tip "Aide-mémoire"
        Deux verbes pour le cycle de vie d'un fichier :

        - `save_upload` pour entrer (valide, sécurise, écrit) ;
        - `serve_media_file` pour sortir (streaming, Range).

??? note "11. Sécurité, stockage et validation"

    Les noms de fichiers fournis par le navigateur ne sont jamais utilisés tels quels : `secure_filename` neutralise les chemins (anti-traversal).

    Le chemin servi par `serve_media_file` est validé pour rester sous `UPLOAD_ROOT` (`is_safe_media_path`).

    !!! warning "Ne jamais faire confiance au nom client"
        Le nom d'origine est conservé dans `SavedUpload.original_name` pour l'affichage, mais le **nom de stockage** est toujours sécurisé.

        Contrôlez extension, type MIME, taille et emplacement final (c'est ce que fait `save_upload`).

    !!! note "Validation au cœur, écriture dans l'opt-in"
        La validation pure (extension, MIME, taille) vit dans `core.forms.upload_validation` et est réexportée ici (ADR-019).

        L'écriture, le service et le rate-limit vivent dans l'opt-in.
        Le cœur ne dépend pas de `forge-mvc-files` (ADR-004).

    !!! note "Configuration du stockage"
        La racine de stockage est `UPLOAD_ROOT` (défaut `storage/uploads`).

        Seul `upload_max_size` reste une config du cœur (ADR-032) ; le reste est lu par l'opt-in depuis l'environnement.

??? note "12. Quota de stockage par propriétaire"

    Un compte pouvait remplir le disque un fichier valide à la fois : chaque envoi passait la taille maximale, et rien ne regardait la somme (`FILES-QUOTA-001`).

    Le quota s'appuie sur le registre de l'ADR-094, et porte sur le couple propriétaire. Deux natures ont donc deux quotas, ce qui est le sens de « par utilisateur et par ressource ».

    ```python
    from forge_mvc_files import QuotaExceededError, check_quota, record_file, save_upload

    try:
        check_quota("user", utilisateur.id, request.content_length or 0)
    except QuotaExceededError as exc:
        return self.render("upload.html", {"erreur": str(exc)})

    depot = save_upload(request.files["fichier"])
    record_file(depot.path, depot.original_name, depot.size,
                owner_kind="user", owner_id=utilisateur.id)
    ```

    Le contrôle passe **avant** l'écriture. Après coup, il faudrait supprimer un fichier déjà posé, et un incident entre les deux gestes laisserait une trace sur le disque.

    La longueur du corps de la requête convient comme taille entrante, et surestime un peu, l'enveloppe multipart y étant comptée. Pour un quota, l'erreur va dans le bon sens.

    | Variable | Effet |
    |---|---|
    | `FILES_QUOTA_BYTES` | octets autorisés, toutes natures confondues |
    | `FILES_QUOTA_FILES` | nombre de fichiers autorisés |
    | `FILES_QUOTA_USER_BYTES` | octets autorisés pour la nature `user`, prioritaire |
    | `FILES_QUOTA_USER_FILES` | nombre de fichiers pour la nature `user` |

    Sans aucune de ces variables, rien n'est borné : le paquet ne limite pas ce que l'exploitant n'a pas demandé.

    !!! danger "Une valeur illisible lève, elle n'est pas ignorée"
        `FILES_QUOTA_BYTES=50MB` **interrompt** la lecture du quota.

        Les suffixes ne sont pas lus, il faut écrire `52428800`. Retomber en silence sur « aucune limite » à cause d'une faute de frappe irait exactement dans le mauvais sens, et personne ne le verrait avant que le disque soit plein.

    !!! warning "Ce n'est pas une borne infranchissable"
        Le contrôle lit la somme inscrite, puis l'appelant écrit. Deux envois simultanés du même compte peuvent passer tous les deux.

        Le dépassement est alors borné par `upload_max_size` et par le nombre de requêtes concurrentes, jamais illimité. Fermer cette fenêtre demanderait de sérialiser les envois d'un même compte, pour une garantie que personne n'a demandée.

        La borne dure contre l'épuisement du disque reste la taille maximale d'un envoi, appliquée avant toute lecture du corps.

    `quota_usage` rend l'état courant sans rien refuser, de quoi afficher une jauge. `remaining_bytes` vaut `None` quand le quota est sans limite, et jamais un nombre négatif : un quota abaissé après coup laisse des propriétaires au dessus.

??? note "13. Brancher une analyse antivirus"

    Forge valide l'extension, le type MIME, la taille et les premiers octets. Aucun de ces contrôles ne dit si le contenu est malveillant : un PDF porteur d'une charge active a l'extension, le type et la signature d'un PDF.

    Le paquet ne fournit **aucune analyse**, et n'en fournira pas (`FILES-SCAN-HOOK-001`). Un moteur antivirus est un service à installer, à tenir à jour et à surveiller. L'embarquer ferait de `forge-mvc-files` une usine métier, et donnerait au projet une base de signatures périmée le jour de sa publication.

    Le paquet fournit la prise.

    ```python
    from forge_mvc_files import ScanVerdict, register_file_scanner

    def analyse_clamav(data: bytes, nom: str) -> ScanVerdict:
        rapport = mon_client_clamd.instream(data)      # à vous
        if rapport.is_infected:
            return ScanVerdict.infected(rapport.signature)
        return ScanVerdict.clean()

    register_file_scanner(analyse_clamav)              # au démarrage
    ```

    Une fois branché, l'analyseur est consulté par `save_upload` à chaque dépôt, comme un middleware inscrit tourne à chaque requête. Sans enregistrement, rien ne change et rien ne coûte.

    !!! danger "Une analyse qui échoue refuse le dépôt"
        C'est la règle qui fait tout l'intérêt de la prise.

        Un analyseur qui lève, qui expire ou qui rend autre chose qu'un `ScanVerdict` ne dit **pas** que le fichier est sain, il ne dit rien. Traiter ce silence comme un feu vert est la faute classique de ce genre de branchement : le jour où le service antivirus tombe, tout passe, et rien ne le signale.

        Forge lève alors `ScannerUnavailableError`, distincte de `UploadRejectedByScanError`. La première est une **panne** à réparer, la seconde un avis rendu sur un fichier. Les confondre dans les journaux ferait chercher un problème de fichier là où le service est à terre.

    !!! info "L'analyse précède l'écriture"
        Un fichier analysé après avoir touché le disque y est déjà, et l'y laisser quelques millisecondes suffit à ce qu'une sauvegarde ou un indexeur le voie.

    !!! warning "Le délai d'attente vous appartient"
        L'analyseur est appelé pendant la requête, et une analyse qui traîne la retient.

        Borner cette durée appartient à l'implémentation, qui seule sait parler à son moteur.

    Les deux exceptions descendent d'`UploadError` : une application qui entoure déjà `save_upload` d'un `except UploadError` traite les refus sans changer une ligne.

??? note "14. Purger les fichiers sans référence"

    Un fichier déposé puis détaché de l'entité qui le portait reste sur le disque. Personne ne le sert, personne ne le supprime, et il compte dans la sauvegarde.

    ```bash
    forge files:orphans                      # affiche seulement
    forge files:orphans --delete             # applique
    forge files:orphans --min-age 604800     # candidats vieux d'une semaine
    ```

    Deux orphelins existent, et ils n'appellent pas le même geste.

    | Situation | Ce que la purge fait |
    |---|---|
    | Sur disque, aucune inscription | supprime le fichier |
    | Inscrit, fichier disparu | retire la ligne du registre |

    !!! danger "Un registre vide interrompt la commande"
        L'inscription au registre est **explicite** (ADR-094) : une application qui n'appelle jamais `record_file` a un registre vide et des fichiers parfaitement vivants.

        Sans ce refus, la première exécution de la purge effacerait la totalité des uploads du projet. C'est le scénario qui coûte le plus cher, et il est atteint par la commande la plus banale.

        `--allow-empty-registry` lève le refus pour **inspecter**, et reste interdit avec `--delete`.

    !!! warning "Un fichier récent n'est jamais candidat"
        Entre l'écriture et l'inscription il s'écoule un instant, davantage si l'application inscrit après avoir validé un formulaire.

        Une purge qui tourne dans cet intervalle supprimerait un fichier que son propriétaire est en train de déposer. L'âge minimal par défaut est d'un jour, largement au delà de toute fenêtre plausible.

    Le rapport dit toujours ce qu'il a **écarté**, pas seulement ce qu'il a trouvé. Un exploitant qui ne voit pas son fichier dans la liste doit pouvoir savoir s'il a été jugé sain ou seulement jugé trop récent.

    En Python, `find_orphans` rend le rapport et `purge_orphans` l'applique. Séparer les deux permet de regarder avant, et garantit qu'un fichier déposé entre les deux gestes n'entre pas dans la fournée.

??? note "15. Déléguer l'envoi au serveur frontal"

    `serve_media_file` sert le fichier depuis Python, en streaming, avec le support des requêtes `Range`. C'est correct, et c'est ce qu'il faut tant que le volume reste modeste.

    Un travailleur reste toutefois occupé pendant tout l'envoi. Sur un fichier de 200 Mo et une connexion lente, un travailleur Gunicorn est immobilisé plusieurs minutes pour recopier des octets, travail que nginx fait mieux et sans processus Python.

    Le motif de production consiste à laisser le contrôleur **décider**, et le serveur frontal **envoyer** (`DOC-FILES-XACCEL-001`).

    ```nginx
    location /protected/ {
        internal;
        alias /srv/monapp/storage/uploads/;
    }
    ```

    ```python
    from core.http.response import Response

    class DocumentController(Controller):
        def download(self, request):
            document = self.repo.find(request.route("id"))
            if not self.peut_lire(request, document):
                return Response(403, b"Interdit", "text/plain; charset=utf-8")

            reponse = Response(200, b"", "application/pdf")
            reponse.headers["X-Accel-Redirect"] = f"/protected/{document.path}"
            reponse.headers["Content-Disposition"] = 'attachment; filename="rapport.pdf"'
            return reponse
    ```

    Le contrôle d'accès reste en Python, où il doit être. Seul l'envoi est délégué.

    !!! danger "Sans `internal;`, la délégation est une faille"
        C'est le seul point de cette section qui ne se rattrape pas.

        `internal;` interdit à nginx de servir cette `location` sur une requête venue de l'extérieur : elle n'est atteignable que par un en-tête émis par l'application. Sans cette directive, `https://exemple.fr/protected/documents/paie.pdf` répond directement, et le contrôle d'accès du contrôleur ne sert plus à rien.

        La délégation devient alors **pire** que le service par Python, puisqu'elle publie l'intégralité du dossier d'upload.

        Vérifiez la directive avant de déployer, puis demandez une URL protégée sans être authentifié.

    !!! warning "Le chemin part d'une donnée en base"
        `document.path` vient du registre ou de votre table, et un chemin porteur de `..` sortirait de l'`alias`.

        Passez le chemin par `normalize_media_path`, qui refuse la traversée, avant de le poser dans l'en-tête.

    !!! info "Pourquoi Forge ne fournit pas d'assistant"
        La moitié qui protège est la directive `internal;`, dans une configuration que Forge ne lit pas et n'écrit pas.

        Un assistant `accel_redirect_response()` laisserait croire que l'appeler suffit, alors qu'il ne garantit rien sans la configuration correspondante. Trois lignes explicites dans un contrôleur montrent exactement ce qui part, et n'endorment personne.

    Apache et lighttpd suivent le même motif sous le nom `X-Sendfile`, avec un chemin absolu au lieu d'une `location`. Le nom de l'en-tête et la forme du chemin changent, la règle ne change pas.

## Voir aussi

- [Upload générique (manager.py)](references/manager.md) : détail de `save_upload` / `serve_media_file`.
- [Primitives de stockage (storage.py)](references/storage.md) : anti-traversal, écriture bas niveau (ADR-020).
- [Rate-limit d'upload (rate_limit.py)](references/rate_limit.md) : limiter le débit.
- [Welcome-Files](welcome/debutant/files-welcome.md) : parcours d'apprentissage.


## Ce que la purge d'orphelins ne peut pas savoir

`find_orphans` rapproche le disque et le registre. Elle suppose donc que le registre décrit **tout** ce qui vit sous `UPLOAD_ROOT`.

Cette hypothèse est fausse dès qu'un autre composant écrit là sans inscrire.

!!! danger "Un écrivain qui n'inscrit pas voit ses fichiers déclarés orphelins"
    C'est arrivé entre deux opt-ins officiels : `forge-mvc-images` écrivait sous cette racine sans rien inscrire, et la purge signalait ses images et leurs vignettes (`IMAGES-REGISTRY-RECORD-001`).

    Le refus sur registre vide ne couvre pas ce cas : il ne se déclenche que si le registre est **entièrement** vide.
    Un projet qui inscrit une partie de ses fichiers a un registre peuplé, et tout le reste passe pour orphelin.

    Tout composant qui écrit sous `UPLOAD_ROOT` doit appeler `record_file`.
    C'est ce que `forge-mvc-images` fait désormais, et ce que votre application doit faire pour ce qu'elle écrit elle même.

!!! info "Regardez avant de supprimer"
    `forge files:orphans` affiche par défaut et ne supprime que sur `--delete`.

    Lancez la commande sans l'option une première fois : la liste dit ce que le registre ignore, et c'est le meilleur moyen de découvrir un écrivain qui n'inscrit pas.

## Ce que Forge purge, et ce qu'il ne purge pas

`files:orphans` supprime des fichiers **que rien ne réclame** : le registre ne les connaît pas, ou il les connaît alors qu'ils ont disparu du disque.

Il n'existe **pas** de purge par ancienneté, et c'est délibéré (`DOC-FILES-RETENTION-SCOPE-001`).

!!! info "Une durée de conservation est une règle métier"
    Forge ne sait pas qu'une facture se garde dix ans et une vignette trente jours.

    D'autres opt-ins purgent bien par âge, `audit:gc --days`, `stats:gc --days`, `iot:gc --days`. La différence n'est pas de principe : ils suppriment des lignes **dont ils connaissent le sens**, un événement de journal ou une mesure de capteur.
    Un fichier appartient au domaine de l'application, et supprimer par date sans savoir ce qu'on supprime est le geste qu'il ne faut pas offrir.

!!! tip "L'écrire soi même est court"
    Le registre porte `created_at` : une application qui veut une rétention interroge `forge_files` sur ce critère, appelle `delete_upload` puis `forget_file`, et garde la décision de ce qu'elle efface.

    Le faire elle même la force à nommer sa règle, ce qui est le bon endroit pour cette décision.


## Supprimer un fichier le retire aussi du registre

Les suppressions retiraient le fichier du disque sans toucher au registre.

La ligne restait, et `owner_usage_bytes` somme les tailles inscrites : le quota comptait donc des fichiers qui n'existaient plus (`FILES-DELETE-FORGETS-001`).

!!! danger "Un quota qui comptait des fichiers supprimés"
    Mesuré : trois dépôts d'un mégaoctet, puis trois suppressions par le chemin documenté, et le quota annonçait toujours trois mégaoctets.

    Un utilisateur qui dépose et supprime finit refusé pour un espace qu'il n'occupe pas, avec un message « quota dépassé » impossible à diagnostiquer de l'extérieur : son stockage est vide.

!!! info "Trois chemins, un seul défaut"
    `delete_upload`, `delete_media_file` et `purge_orphan_variants` suppriment tous des fichiers sous `UPLOAD_ROOT`, et aucun ne désinscrivait.

    Le dernier est le plus ironique : c'est le nettoyage, et il faisait grossir le quota à chaque passage.

    Un garde-fou lu sur l'arbre syntaxique refuse qu'une fonction publique supprime un fichier sans le désinscrire.

!!! info "L'oubli est au mieux, et il a lieu quel que soit le sort du fichier"
    La table `forge_files` est optionnelle (ADR-094), et faire échouer une suppression parce qu'un registre n'est pas provisionné **empêcherait de supprimer**, ce qui est pire que le défaut corrigé.

    Une inscription qui décrit un fichier absent est fausse dans tous les cas : la corriger ne dépend pas de la réussite de la suppression sur disque.
