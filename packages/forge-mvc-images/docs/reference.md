# Les images et médias dans Forge (forge-mvc-images)

Ce document explique ce que fait l'opt-in `forge-mvc-images`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-images` est l'unique propriétaire de tout l'image dans Forge : le **traitement** (Pillow) et la **couche médias applicative** (associer des images à des entités, galerie, couverture).

Il s'appuie sur `forge-mvc-files` pour l'écriture disque et le service de fichiers.

??? note "1. Rôle du module"

    L'opt-in couvre deux niveaux complémentaires :

    - **traitement d'image** : vérifier qu'un upload est une vraie image, l'écrire, générer des variantes (miniature, medium) ;
    - **couche médias applicative** : relier une image à une entité (un article, un élève), lister une galerie, désigner une couverture.

    La vérification du contenu est une **sécurité** : on confirme que les octets sont bien une image avant toute écriture (garde anti-bombe de décompression), car le type MIME annoncé est falsifiable.

??? note "2. Installation"

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-images
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-images"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable images --apply
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
    `forge opt-in:install images` affiche la commande `pip` sans l'exécuter.

    La couche traitement (`save_image_upload`, `verify_image_content`, variantes) fonctionne dès l'installation.
    La couche médias applicative (`attach_media_to_entity`, `get_media_gallery`, `get_cover_media`) exige en plus une table `media`, prérequis dur.

    Créez-la avec la migration embarquée :

    ```bash
    forge images:init
    forge migration:apply
    ```

    `images:init` copie la migration embarquée dans `mvc/migrations/` ; `migration:apply` l'exécute.
    Sans cette table, tout appel de la couche médias échoue au premier `INSERT INTO media`.

    Ces gestes ne suffisent pas à rendre l'opt-in **opérationnel** : il reste à l'épingler dans
    `requirements.txt`, à provisionner sa base s'il en a une, à le brancher là où il agit et à le
    prouver par un premier usage réel.
    Voir la procédure canonique, [Rendre un opt-in opérationnel : les cinq points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-images`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-images==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable images --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser sa base

    ```bash
    forge images:init
    forge migration:apply
    ```

    `images:init` copie la migration embarquée dans `mvc/migrations/` ;
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
    forge opt-in:disable images
    pip uninstall forge-mvc-images
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove images` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    Cet opt-in n'expose aucune commande CLI : il s'utilise **par import** dans le code applicatif (voir l'API publique ci-dessous).

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-images` |
    | Module | `forge_mvc_images` |
    | Catégorie | Médias et fichiers (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc`, `forge-mvc-files`, `Pillow` |
    | Traitement | `save_image_upload`, `save_image`, `generate_image_variants`, `verify_image_content` |
    | Couche médias | `create_media_record`, `attach_media_to_entity`, `list_media_for_entity`, `get_media_gallery`, `get_cover_media` |
    | Objet renvoyé | `MediaRecord` (association fichier média / entité) |
    | Variantes | `IMAGE_VARIANT_SIZES` (miniature, medium) |
    | Formats autorisés | `ALLOWED_IMAGE_EXTENSIONS`, `ALLOWED_IMAGE_MIME_TYPES` |
    | Décision d'architecture | ADR-018 (remplace `forge-mvc-media`) |
    | Installation | `pip install --pre forge-mvc-images` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre les deux couches et leurs dépendances.

    Le diagramme de séquence montre l'enregistrement d'une image puis l'affichage d'une galerie.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le traitement s'appuie sur `forge-mvc-files` et Pillow, et que la couche médias persiste des associations via un exécuteur **injecté**.

    ```mermaid
    classDiagram
        direction LR

        class processing {
            <<module>>
            +save_image_upload(file, category, variants) SavedUpload
            +save_image(file, entity_name, entity_id, ...) MediaRecord
            +generate_image_variants(path, root) dict
            +verify_image_content(data) None
        }

        class media {
            <<module>>
            +create_media_record(entity_name, entity_id, path, ...) int
            +attach_media_to_entity(saved_upload, entity_name, entity_id, ...) int
            +list_media_for_entity(entity_name, entity_id, role) list
            +get_media_gallery(...) list
            +get_cover_media(...) dict
        }

        class MediaRecord {
            <<dataclass>>
            +str filename
            +str path
            +str category
        }

        class files {
            <<opt-in>>
            +save_upload()
            +serve_media_file()
        }

        class Pillow {
            <<dependance>>
        }

        processing --> files : écrit via
        processing --> Pillow : vérifie / redimensionne
        processing --> MediaRecord : renvoie
        media --> files : chemins / service
        processing ..> media : alimente
    ```

    À retenir :

    - la couche traitement produit des fichiers (original + variantes) ;
    - la couche médias relie ces fichiers à des entités ;
    - Pillow sert à vérifier et redimensionner, pas le cœur ;
    - l'écriture et le service passent par `forge-mvc-files`.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un upload d'image relié à une entité, puis l'affichage de sa galerie.

    ```mermaid
    sequenceDiagram
        actor Navigateur
        participant Ctrl as Contrôleur
        participant Img as forge_mvc_images
        participant Files as forge_mvc_files
        participant DB as Exécuteur BDD

        Navigateur->>Ctrl: POST image (multipart)
        Ctrl->>Img: save_image_upload(file)
        Img->>Img: verify_image_content (anti-bombe)
        Img->>Files: save_upload (écrit l'original)
        Img->>Img: generate_image_variants (miniature, medium)
        Img-->>Ctrl: SavedUpload
        Ctrl->>Img: attach_media_to_entity(saved, "article", 7)
        Img->>DB: insère l'association
        Navigateur->>Ctrl: GET page article
        Ctrl->>Img: get_media_gallery("article", 7)
        Img->>DB: lit les médias liés
        Img-->>Ctrl: galerie (URLs via media_url)
    ```

    À retenir :

    - le contenu est vérifié **avant** l'écriture disque ;
    - les variantes sont générées à l'enregistrement ;
    - l'association média / entité est persistée par la couche médias ;
    - la galerie et la couverture se lisent par entité.

??? note "8. API publique"

    ### Traitement d'image

    | Élément | Signature | Rôle |
    |---|---|---|
    | `save_image_upload` | `save_image_upload(file, category="images", *, variants=True) -> SavedUpload` | vérifie, écrit, génère les variantes |
    | `save_image` | `save_image(file, *, category="images", entity_name=None, entity_id=None, usage="main", position=0, is_main=True) -> MediaRecord` | enregistre une image liée à une entité |
    | `generate_image_variants` | `generate_image_variants(path, *, root=None) -> dict[str, str]` | génère miniature et medium |
    | `verify_image_content` | `verify_image_content(data) -> None` | garde anti-bombe, lève si non-image |
    | constantes | `ALLOWED_IMAGE_EXTENSIONS`, `ALLOWED_IMAGE_MIME_TYPES`, `IMAGE_VARIANT_SIZES` | formats et tailles |

    ### Couche médias applicative

    | Élément | Signature | Rôle |
    |---|---|---|
    | `create_media_record` | `create_media_record(entity_name, entity_id, path, ..., db=None) -> int` | enregistre une association média / entité |
    | `attach_media_to_entity` | `attach_media_to_entity(saved_upload, entity_name, entity_id, ..., db=None) -> int` | relie un `SavedUpload` à une entité |
    | `list_media_for_entity` | `list_media_for_entity(entity_name, entity_id, role=None, ...) -> list` | liste les médias d'une entité |
    | `get_media_gallery` | `get_media_gallery(...) -> list[dict]` | galerie d'une entité (avec URLs) |
    | `get_cover_media` | `get_cover_media(...) -> dict \| None` | média de couverture |
    | `media_url` | `media_url(path) -> str` | URL publique d'un média |
    | autres | `update_media_alt_text`, `update_media_position`, `delete_media`, `get_media_record` | gestion fine |

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Recevoir une image en sécurité | `save_image_upload(file)` |
    | Vérifier des octets image | `verify_image_content(data)` |
    | Générer miniature et medium | `generate_image_variants(path)` |
    | Relier une image à une entité | `attach_media_to_entity(...)` |
    | Afficher une galerie | `get_media_gallery(...)` |
    | Choisir une couverture | `get_cover_media(...)` |
    | Construire l'URL d'un média | `media_url(path)` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Recevoir une image et la relier à une entité

    ```python
    from forge_mvc_images import save_image_upload, attach_media_to_entity


    def add_photo(request):
        saved = save_image_upload(request.file("photo"))
        attach_media_to_entity(saved, "article", 7, role="gallery")
        return Response.text("Photo ajoutée.")
    ```

    `save_image_upload` vérifie le contenu, écrit l'original et génère les variantes.

    ### 8.2 Afficher la galerie d'une entité

    ```python
    from forge_mvc_images import get_media_gallery, get_cover_media

    gallery = get_media_gallery("article", 7)
    cover = get_cover_media("article", 7)
    ```

    !!! tip "Aide-mémoire"
        Deux couches, un même flux :

        - traitement : `save_image_upload` (vérifie, écrit, variantes) ;
        - médias : `attach_media_to_entity`, `get_media_gallery`, `get_cover_media`.

??? note "11. Sécurité, variantes et dépendances"

    `verify_image_content` confirme que les octets sont une vraie image avant toute écriture, et protège contre les bombes de décompression.

    Les variantes (miniature, medium) sont définies par `IMAGE_VARIANT_SIZES` ; l'original est conservé tel quel.

    !!! warning "Le MIME annoncé ne suffit pas"
        Un fichier non-image peut se présenter avec une extension et un `Content-Type` d'image.

        `save_image_upload` (et `save_image`) appellent `verify_image_content` avant d'écrire : ne court-circuitez pas cette étape.

    !!! note "Pillow vit dans l'opt-in"
        `Pillow` est une dépendance de `forge-mvc-images`, retirée du cœur (ADR-018).

        Le cœur ne sait pas traiter d'images ; tout l'image vit ici.

    !!! note "S'appuie sur forge-mvc-files"
        L'écriture disque, le service (HTTP Range) et l'anti-traversal viennent de `forge-mvc-files`.

        `forge-mvc-images` ajoute le traitement (Pillow) et la couche applicative.

## Voir aussi

- [Traitement d'image (processing.py)](references/processing.md) : `save_image`, variantes, vérification.
- [Dépôt de médias (media_repository.py)](references/media_repository.md) : associations média / entité.
- [Galerie (media_gallery.py)](references/media_gallery.md) : galerie, couverture, URLs.
- [Guide média](media.md) : vue d'ensemble applicative.
- [Welcome-Images](welcome/debutant/images-welcome.md) : parcours d'apprentissage.

## Déclaration de table

Le paquet ne livre plus de fichier SQL figé : il **déclare** sa table dans `tables.py`
(`MEDIA`, plus la liste `MIGRATIONS`).
Le DDL est rendu pour le backend installé par `core.database.table_ddl`, puis écrit
dans `mvc/migrations/` par `forge images:init` (chantier `OPTIN-DDL-DIALECTAL`).
Le SQL reste donc relisible avant `forge migration:apply`, mais il est correct pour
MariaDB, SQLite, PostgreSQL comme SQL Server.
