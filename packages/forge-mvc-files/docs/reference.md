# L'upload de fichiers dans Forge (forge-mvc-files)

Ce document explique ce que fait l'opt-in `forge-mvc-files`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-files` détient le pipeline d'upload générique : valider, écrire sur disque de façon sécurisée, servir un fichier en streaming, le supprimer, limiter le débit d'upload.

C'est le socle des médias : `forge-mvc-images`, `forge-mvc-video` et `forge-mvc-audio` s'appuient dessus.

??? note "1. Rôle du module"

    Recevoir un fichier d'un formulaire et le stocker en toute sécurité demande plusieurs étapes : valider l'extension, le type MIME et la taille, neutraliser le nom (anti-traversal), écrire sur disque, puis savoir le re-servir.

    L'opt-in regroupe ce pipeline derrière une API simple : `save_upload` pour entrer un fichier, `serve_media_file` pour le ressortir.

    La **validation pure** (extension, MIME, taille) reste dans le cœur (`core.forms.upload_validation`, ADR-019) et est réexportée ici : le cœur ne peut pas dépendre d'un opt-in (ADR-004).

??? note "2. Installation et désinstallation"

    ### Installation

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-files
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-files"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable files --apply
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
    `forge opt-in:install files` affiche la commande `pip` sans l'exécuter.

    Ces gestes ne suffisent pas à rendre l'opt-in **opérationnel** : il reste à l'épingler dans
    `requirements.txt`, à provisionner sa base s'il en a une, à le brancher là où il agit et à le
    prouver par un premier usage réel.
    Voir la procédure canonique, [Rendre un opt-in opérationnel : les cinq points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    ### Désinstallation

    ```bash
    forge opt-in:disable files
    pip uninstall forge-mvc-files
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove files` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Commandes"

    `forge-mvc-files` ajoute ces commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `upload:init` | Initialise les dossiers de stockage d'upload. | `forge upload:init` |
    | `media:init` | Initialise les dossiers de stockage média. | `forge media:init` |

??? note "4. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-files` |
    | Module | `forge_mvc_files` |
    | Catégorie | Médias et fichiers (ADR-055) |
    | Couche | opt-in (brique optionnelle), socle des médias |
    | Dépend de | `forge-mvc` (validation et exceptions restent au cœur) |
    | API publique | `save_upload`, `SavedUpload`, `serve_media_file`, `delete_upload`, `delete_media_file`, primitives de stockage, rate-limit |
    | Objet renvoyé | `SavedUpload` (métadonnées du fichier écrit) |
    | Service HTTP | `serve_media_file` (streaming, HTTP Range) |
    | Racine de stockage | variable d'environnement `UPLOAD_ROOT` (défaut `storage/uploads`) |
    | Exceptions | `UploadError` et ses sous-classes (extension, MIME, taille, stockage) |
    | Décisions d'architecture | ADR-019 (extraction), ADR-020 (primitives) |
    | Installation | `pip install --pre forge-mvc-files` |

??? note "5. Schémas UML"

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

??? note "6. API publique"

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

??? note "7. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Enregistrer un fichier reçu | `save_upload(file, category=...)` |
    | Servir un fichier | `serve_media_file(path, request=request)` |
    | Supprimer un fichier | `delete_upload(path)` |
    | Connaître la racine de stockage | `upload_root()` ou `UPLOAD_ROOT` |
    | Sécuriser un nom de fichier | `secure_filename(name)` |
    | Limiter les uploads abusifs | `is_upload_rate_limited(...)` |
    | Gérer un upload refusé | intercepter `UploadError` |

??? note "8. Exemples d'utilisation"

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

??? note "9. Sécurité, stockage et validation"

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

## Voir aussi

- [Upload générique (manager.py)](references/manager.md) : détail de `save_upload` / `serve_media_file`.
- [Primitives de stockage (storage.py)](references/storage.md) : anti-traversal, écriture bas niveau (ADR-020).
- [Rate-limit d'upload (rate_limit.py)](references/rate_limit.md) : limiter le débit.
- [Welcome-Files](welcome/debutant/files-welcome.md) : parcours d'apprentissage.
