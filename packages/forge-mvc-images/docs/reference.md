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
    pip install --pre forge-mvc-images
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-images"
    ```

    </div>

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

    #### 3. Poser ce dont il a besoin

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
    | Variantes | `variant_presets()`, déclarées par `IMAGE_VARIANTS` |
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
    | `save_image_upload` | `save_image_upload(file, category="images", *, variants=True, focal=None) -> SavedUpload` | vérifie, écrit, génère les variantes |
    | `save_image` | `save_image(file, *, category="images", entity_name=None, entity_id=None, usage="main", position=0, is_main=True) -> MediaRecord` | enregistre une image liée à une entité |
    | `generate_image_variants` | `generate_image_variants(path, *, root=None, focal=None, presets=None) -> dict[str, str]` | génère les variantes déclarées |
    | `verify_image_content` | `verify_image_content(data) -> None` | garde anti-bombe, lève si non-image |
    | constantes | `ALLOWED_IMAGE_EXTENSIONS`, `ALLOWED_IMAGE_MIME_TYPES` | formats autorisés |
    | `variant_presets` | `variant_presets() -> tuple[VariantPreset, ...]` | préréglages applicables, lus de la configuration |
    | `image_limits` | `image_limits() -> ImageLimits` | bornes de dimensions et de poids |
    | `find_orphan_variants` | `find_orphan_variants(*, root=None) -> VariantOrphanReport` | variantes que plus rien ne sert |

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
        attach_media_to_entity(saved, entity_name="article", entity_id=7, role="gallery")
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

    Les variantes sont déclarées par `IMAGE_VARIANTS` et lues par `variant_presets()` ; l'original est conservé tel quel.

    !!! warning "Le MIME annoncé ne suffit pas"
        Un fichier non-image peut se présenter avec une extension et un `Content-Type` d'image.

        `save_image_upload` (et `save_image`) appellent `verify_image_content` avant d'écrire : ne court-circuitez pas cette étape.

    !!! note "Pillow vit dans l'opt-in"
        `Pillow` est une dépendance de `forge-mvc-images`, retirée du cœur (ADR-018).

        Le cœur ne sait pas traiter d'images ; tout l'image vit ici.

    !!! note "S'appuie sur forge-mvc-files"
        L'écriture disque, le service (HTTP Range) et l'anti-traversal viennent de `forge-mvc-files`.

        `forge-mvc-images` ajoute le traitement (Pillow) et la couche applicative.

??? note "12. Déclarer ses variantes"

    Les deux variantes du paquet, `medium` et `thumbnail`, vivaient dans une constante de module accordée à la main avec deux dictionnaires littéraux (`presets.py`).

    Ajouter une taille demandait donc d'éditer le paquet en trois endroits, et l'ADR-018 avait relevé la conséquence sans la corriger : « non extensible sans éditer le code » (`IMAGES-PRESETS-DECLARATIFS-001`).

    ```bash
    IMAGE_VARIANTS=thumbnail:300x300,medium:1280x1280,banniere:1920x1080:crop
    ```

    Chaque entrée porte un nom, des dimensions, et un mode facultatif.

    | Mode | Effet |
    |---|---|
    | `fit` (défaut) | l'image tient dans la boîte, son rapport est conservé |
    | `crop` | la boîte est remplie exactement, le débord est rogné |

    Sans déclaration, les deux préréglages historiques s'appliquent : un projet existant ne change pas de comportement.

    ```python
    from forge_mvc_images import preset_by_name, preset_names, variant_presets

    variant_presets()          # (VariantPreset('thumbnail', 300, 300, 'fit'), ...)
    preset_names()             # ('thumbnail', 'medium', 'banniere')
    preset_by_name("banniere") # VariantPreset(..., mode='crop')
    ```

    !!! info "Les préréglages sont lus, jamais figés"
        `variant_presets()` relit la configuration à chaque appel.

        La constante précédente était un instantané pris au chargement du module, aveugle à toute variable posée ensuite.

    !!! danger "Le nom devient un dossier sur le disque"
        Un nom hors de `[a-z0-9_-]` est refusé, et `original` est **réservé** : il désigne le fichier source, et une variante portant ce nom l'écraserait.

        Un préréglage déclaré deux fois est refusé lui aussi. Garder la dernière déclaration en silence produirait une taille que personne n'a lue.

    !!! warning "Retirer un préréglage laisse ses fichiers"
        Les images déjà produites restent sur le disque, et rien ne les régénérera.

        `forge images:orphans` les nomme, voir la section 14.

??? note "13. Rogner autour d'un point d'intérêt"

    Une variante en mode `crop` remplit exactement sa boîte, ce qu'un rognage centré fait mal (`IMAGES-FOCAL-CROP-001`).

    Sur une photo de groupe cadrée large, le centre géométrique tombe souvent entre deux personnes, et une bannière de 1920 sur 1080 taillée dans un portrait vertical coupe la tête.

    ```python
    from forge_mvc_images import FocalPoint, save_image_upload

    depot = save_image_upload(
        request.files["photo"],
        focal=FocalPoint(x=0.5, y=0.15),   # le sujet est en haut
    )
    ```

    Le point est exprimé en fractions de la largeur et de la hauteur, de sorte qu'il reste valable quelles que soient les dimensions de la source et de la cible. `FocalPoint(0.5, 0.5)` est le centre, et c'est ce qui s'applique par défaut.

    !!! info "Forge ne détecte aucun point d'intérêt"
        La détection de visages ou de saillance demande un modèle, donc une dépendance lourde et des résultats à surveiller.

        Le point est une donnée de l'application, posée par la personne qui téléverse ou par un service qu'elle choisit. Le stocker à côté du média est le motif habituel.

    !!! info "Forge n'invente pas de pixels"
        Si la source est plus petite que la boîte demandée, la variante garde le rapport de la boîte mais reste à la taille disponible.

        Agrandir produirait une image floue en se faisant passer pour la taille déclarée. Un portrait de 800 sur 1200 donne ainsi une bannière de 800 sur 450, au bon rapport.

    !!! warning "La fenêtre est ramenée dans l'image"
        Un point proche d'un bord donnerait une fenêtre à cheval sur le vide, que Pillow comblerait par du noir.

        `crop_box` recale la fenêtre pour qu'elle tienne dans la source, le point restant au plus près de son centre.

??? note "14. Nettoyer les variantes inutiles"

    Deux situations laissent des fichiers que plus rien ne sert, et la seconde n'existait pas avant que les préréglages deviennent déclarables (`IMAGES-ORPHAN-VARIANTS-001`).

    ```bash
    forge images:orphans                        # affiche seulement
    forge images:orphans --delete                # applique
    forge images:orphans --only prereglage-retire
    ```

    | Situation | Cause habituelle |
    |---|---|
    | Variante sans original | image supprimée sans passer par `delete_media` |
    | Variante d'un préréglage retiré | `IMAGE_VARIANTS` ne déclare plus ce nom |

    !!! info "Aucune base n'est consultée"
        Une variante est orpheline si son original n'est pas sur le disque, ce qui se lit du disque seul.

        Contrairement à `files:orphans`, aucun registre n'est nécessaire, et le garde-fou du registre vide n'a donc pas lieu d'être ici.

    !!! warning "Un dossier applicatif peut ressembler à un dossier de variantes"
        La reconnaissance repose sur la forme `parent/nom/photo.jpg` en face de `parent/photo.jpg`.

        Un dossier portant par hasard un nom de préréglage et contenant un fichier homonyme de son voisin du dessus serait pris pour un dossier de variantes. C'est précisément pourquoi la commande affiche avant de supprimer.

    !!! info "La commande ne régénère rien"
        Reproduire une variante manquante demanderait de décider quand, et une purge qui écrit serait deux gestes sous un seul nom.

    Un orphelin cumulant les deux motifs n'apparaît qu'une fois, dans la catégorie la plus grave.

??? note "15. Borner les dimensions et le poids"

    Le paquet portait une seule limite, la surface en pixels, pensée contre la bombe de décompression (`IMAGES-LIMITS-CONFIG-001`).

    Elle laisse passer une image de 12000 sur 2000, qui tient sous les 24 mégapixels et qui est pourtant impossible à afficher, coûteuse à redimensionner et volumineuse à servir.

    | Variable | Ce qu'elle borne |
    |---|---|
    | `IMAGE_MAX_WIDTH` | largeur en pixels |
    | `IMAGE_MAX_HEIGHT` | hauteur en pixels |
    | `IMAGE_MAX_BYTES` | poids du fichier image |
    | `UPLOAD_MAX_IMAGE_PIXELS` | surface, garde anti bombe, déjà présente |

    Sans déclaration, aucune des trois nouvelles n'est appliquée. Le contrôle de surface reste en place, il protégeait contre autre chose.

    !!! danger "Une valeur illisible interrompt"
        `IMAGE_MAX_WIDTH=5MB` **lève** au lieu d'être ignoré, comme le quota de `forge-mvc-files`.

        Retomber en silence sur « aucune limite » à cause d'une faute de frappe irait exactement dans le mauvais sens. Pour ne pas borner, retirez la variable.

    !!! info "Le poids d'une image se borne à part"
        `IMAGE_MAX_BYTES` est distinct d'`upload_max_size`, qui borne **tout** envoi.

        Une application peut accepter un PDF de 20 Mo et refuser une photo de 5 Mo, les deux n'ayant ni le même usage ni le même coût de traitement.

    Les dimensions sont contrôlées sur l'en-tête, avant tout décodage, et le poids avant même l'ouverture du fichier.

??? note "16. Choisir les variantes depuis un contrat d'entité"

    Une entité déclarant un média pouvait dire `variants: true` ou `variants: false`, c'est à dire toutes ou aucune (`IMAGES-ENTITY-FIELD-001`).

    Une fois les préréglages déclarables, ce booléen ne suffit plus : un avatar n'a pas besoin de la bannière de 1920 sur 1080, dont la génération coûte à chaque envoi.

    ```json
    {
      "media": [
        {"name": "avatar", "field": "image", "role": "avatar",
         "variants": ["thumbnail"]}
      ]
    }
    ```

    Le contrat vérifie la **forme** de la liste, pas l'existence des préréglages : ceux ci vivent dans la configuration de `forge-mvc-images`, qu'un opt-in ne peut pas importer depuis un autre.

    !!! danger "Un nom non déclaré lève à la génération"
        `generate_image_variants(presets=["hero"])` refuse si `hero` n'est pas dans `IMAGE_VARIANTS`.

        L'ignorer laisserait l'entité réclamer une déclinaison inexistante, et la page finirait avec une image cassée sans que rien n'ait signalé la cause.

    !!! info "Seules les variantes produites sont rendues"
        Le dictionnaire de retour ne porte que l'original et ce qui a été généré.

        Rendre le chemin d'une variante non produite ferait stocker à l'appelant une adresse qui ne répond pas.

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


## Inscription au registre des fichiers

`forge-mvc-images` écrit sous `UPLOAD_ROOT`, la racine que `forge-mvc-files` connaît.

Il inscrit désormais au registre de ce dernier tout ce qu'il écrit, l'original comme chaque variante (`IMAGES-REGISTRY-RECORD-001`).

!!! danger "La purge d'orphelins supprimait les images"
    `forge files:orphans` rapproche le disque et le registre : une image absente du registre y était **un orphelin**, et `--delete` la supprimait.

    Le garde-fou du registre vide ne protégeait pas ce cas.
    Il ne se déclenche que si le registre est **entièrement** vide, et un projet qui inscrit ses documents, comme la documentation de `forge-mvc-files` l'enseigne, avait un registre peuplé et des images signalées orphelines.

    Mesuré sur un projet portant un document inscrit et une image non inscrite : l'original **et sa vignette** étaient signalés.

!!! info "L'inscription est au mieux"
    La table `forge_files` est optionnelle (ADR-094), et faire échouer une sauvegarde d'image parce qu'un registre n'est pas provisionné serait disproportionné.

    L'échec est journalisé sur une ligne, sans pile : ce chemin se déclenche une fois par fichier écrit, et une trace complète par vignette noierait le journal.

    Ce n'est pas une dégradation silencieuse pour autant : sans cette table, `find_orphans` lève aussi, et la purge ne peut pas tourner.
    Les deux cas s'alignent, il n'y a pas de fenêtre où l'inscription manque pendant que la purge supprime.
