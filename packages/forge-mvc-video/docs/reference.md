# La vidéo dans Forge (forge-mvc-video)

Ce document explique ce que fait l'opt-in `forge-mvc-video`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-video` gère l'upload de vidéos, leur transcodage en MP4 (H.264/AAC) et leur lecture en streaming HTTP Range.

Le travail lourd (transcodage) se fait **hors requête HTTP**, via des commandes `video:*`, jamais pendant que le serveur répond.

??? note "1. Rôle du module"

    Servir une vidéo demande de la normaliser : un fichier source hétérogène devient un MP4 lisible par tous les navigateurs, avec une image d'affiche (poster).

    L'opt-in enchaîne un **pipeline** : ingérer le fichier, le sonder (`ffprobe`), le transcoder en MP4 (`ffmpeg`), générer un poster, puis le servir en streaming.

    Il branche aussi ses **routes** de lecture sur le routeur du projet, via la couche `optins/` (modèle opt-in de type route).

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
    pip install --pre forge-mvc-video
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-video"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-video`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-video==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable video --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    ```bash
    forge video:init
    forge migration:apply
    ```

    `video:init` copie la migration embarquée dans `mvc/migrations/` ;
    `migration:apply` l'exécute et la trace (ADR-071).
    Sans cette étape, le premier appel échoue sur une table absente.

    #### 4. Le brancher là où il agit

    Ses routes montent avec celles des autres opt-ins, par l'appel
    `register_optins(router)` déjà présent dans `mvc/routes/__init__.py`.
    Rien de plus à écrire.

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
    forge opt-in:disable video
    pip uninstall forge-mvc-video
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre et débranche les routes de `mvc/routes/__init__.py`, sans toucher au paquet.
    `forge opt-in:remove video` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-video` ajoute ces commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `video:doctor` | Diagnostic (paquet, config, `ffmpeg`/`ffprobe`). | `forge video:doctor` |
    | `video:init` | Copie la migration vidéo vers `mvc/migrations/`. | `forge video:init` |
    | `video:upload` | Dépose une vidéo source. | `forge video:upload film.mov --title "Démo"` |
    | `video:process` | Transcode une vidéo (par `id` ou `--pending`). | `forge video:process --pending` |
    | `video:cleanup` | Purge les vidéos `failed` et fichiers orphelins. | `forge video:cleanup` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-video` |
    | Module | `forge_mvc_video` |
    | Catégorie | Médias et fichiers (ADR-055) |
    | Couche | opt-in de type route (couche `optins/`) |
    | Dépend de | `forge-mvc`, `forge-mvc-files`, et `ffmpeg` / `ffprobe` (binaires externes) |
    | API publique | `register_video_routes` (branchement des routes) |
    | Configuration | `FORGE_VIDEO_*` (`load_video_config`) |
    | Pipeline | `ingest_video`, `probe_video`, `transcode_to_mp4`, `generate_poster`, `process_video` |
    | Commandes | `video:doctor`, `video:init`, `video:upload`, `video:process`, `video:cleanup` |
    | Lecture | streaming HTTP Range |
    | Modèle d'exécution | worker-CLI : transcodage hors requête HTTP |
    | Installation | `pip install --pre forge-mvc-video` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre le pipeline, les routes et les dépendances externes.

    Le diagramme de séquence montre l'upload, le traitement différé, puis la lecture.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le pipeline s'appuie sur `ffmpeg` / `ffprobe` et sur `forge-mvc-files`, et que les routes se branchent explicitement sur le routeur.

    ```mermaid
    classDiagram
        direction LR

        class pipeline {
            <<module>>
            +ingest_video(...)
            +probe_video(...) VideoMetadata
            +transcode_to_mp4(...)
            +generate_poster(...)
            +process_video(...)
        }

        class http {
            <<module>>
            +register_video_routes(router)
        }

        class config {
            <<module>>
            +load_video_config(source) VideoConfig
        }

        class ffmpeg {
            <<binaire externe>>
            +ffmpeg
            +ffprobe
        }

        class files {
            <<opt-in>>
            +save_upload()
            +serve_media_file()
        }

        pipeline --> ffmpeg : sonde / transcode
        pipeline --> files : stocke
        http --> files : sert (HTTP Range)
        pipeline --> config : lit FORGE_VIDEO_*

    ```

    À retenir :

    - le pipeline transforme une source en MP4 + poster ;
    - `ffmpeg` / `ffprobe` sont des binaires externes requis ;
    - les routes de lecture se branchent via `register_video_routes` ;
    - le stockage et le service viennent de `forge-mvc-files`.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre l'upload, le traitement par un worker, puis la lecture.

    ```mermaid
    sequenceDiagram
        actor Op as Opérateur / contrôleur
        participant Up as video:upload
        participant Proc as video:process (worker)
        participant FF as ffmpeg / ffprobe
        participant Routes as register_video_routes
        actor Navigateur

        Op->>Up: dépose une vidéo source
        Up-->>Op: vidéo en statut "uploaded"
        Proc->>FF: probe (métadonnées)
        Proc->>FF: transcode MP4 + poster
        Proc-->>Op: vidéo "ready"
        Navigateur->>Routes: GET la vidéo (avec Range)
        Routes-->>Navigateur: flux MP4 (206 Partial Content)

    ```

    À retenir :

    - l'upload et le traitement sont **séparés** : la requête ne transcode jamais ;
    - `video:process` (worker-CLI) fait probe + transcode + poster ;
    - la lecture honore l'en-tête `Range` (streaming) ;
    - une vidéo n'est lisible qu'une fois `ready`.

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `register_video_routes` | `register_video_routes(router) -> None` | branche les routes de lecture sur le routeur |
    | `load_video_config` | `load_video_config(source=None) -> VideoConfig` | lit la configuration `FORGE_VIDEO_*` |
    | `process_video` | `process_video(...)` | pipeline complet : probe + transcode + poster |
    | `probe_video` | `probe_video(...) -> VideoMetadata` | sonde une vidéo (`ffprobe`) |
    | `transcode_to_mp4` | `transcode_to_mp4(...)` | transcode en MP4 (`ffmpeg`) |
    | `generate_poster` | `generate_poster(...)` | génère l'image d'affiche |
    | `ingest_video` | `ingest_video(...)` | entre une source dans le pipeline |

    Les fonctions de pipeline sont surtout appelées par les commandes `video:*` (worker), pas pendant une requête.

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Vérifier l'installation | `forge video:doctor` |
    | Préparer la table | `forge video:init` |
    | Déposer une vidéo | `forge video:upload <fichier>` |
    | Transcoder (hors requête) | `forge video:process --pending` |
    | Brancher la lecture | `register_video_routes(router)` |
    | Configurer le module | `FORGE_VIDEO_*` / `load_video_config` |
    | Nettoyer | `forge video:cleanup --apply` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Brancher les routes de lecture

    ```python
    # optins/video/routes.py (couche optins du projet)
    from forge_mvc_video import register_video_routes


    def register(router) -> None:
        register_video_routes(router)

    ```

    `forge opt-in:enable video --apply` crée cette couche ; le branchement reste explicite.

    ### 8.2 Traiter les vidéos en attente (worker)

    ```bash
    forge video:upload ma_video.mov --title "Cours 1"
    forge video:process --pending     # probe + transcode MP4 + poster
    ```

    Le transcodage tourne dans la commande, pas dans le serveur web.

    !!! tip "Aide-mémoire"
        Trois temps :

        - déposer (`video:upload`) ;
        - traiter hors requête (`video:process`) ;
        - lire en streaming (routes branchées par `register_video_routes`).

??? note "11. Dépendances externes et exécution différée"

    `ffmpeg` et `ffprobe` doivent être installés sur la machine ; `forge video:doctor` le vérifie.

    Le transcodage est lourd : il se fait via `video:process` (worker-CLI), idéalement déclenché par cron ou un service, jamais pendant une requête HTTP.

    !!! warning "ffmpeg / ffprobe requis"
        Sans ces binaires, le sondage et le transcodage échouent.

        Lancez `forge video:doctor` après installation pour confirmer leur présence.

    !!! note "Lecture en streaming"
        La lecture s'appuie sur `forge-mvc-files` (HTTP Range) : le navigateur peut chercher dans la vidéo sans tout télécharger.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-video` : la dépendance va de l'opt-in vers le cœur.

??? note "12. Montrer l'état de traitement"

    Une vidéo passe par quatre états, `uploaded`, `processing`, `ready` et `failed`.

    Le paquet les enregistrait sans jamais donner de quoi les montrer (`VIDEO-STATUS-UI-001`) : après l'envoi, la page ne savait pas dire où en était le transcodage, et chaque application réécrivait sa table de correspondance vers un libellé français.

    ```python
    from forge_mvc_video import describe_video_status

    vue = describe_video_status(repository.get_by_uuid(uuid))
    vue.label            # « Transcodage en cours »
    vue.is_pending       # faut il redemander l'état ?
    vue.public_message   # ce que le visiteur peut lire
    ```

    La route `GET /videos/{uuid}/status` rend la même chose en JSON, de quoi rafraîchir une page sans la recharger. Elle suit la règle d'accès de la lecture : protégée par le même jeton, ou ouverte comme elle.

    !!! danger "La sortie d'erreur de ffmpeg ne sort jamais"
        `error_message` porte le message de ffmpeg, qui contient les **chemins absolus** des fichiers d'entrée et de sortie.

        Le rendre à un visiteur publierait l'arborescence du serveur, et un gabarit qui affiche « la raison de l'échec » le fait sans y penser.

        `VideoStatusView` sépare donc `public_message`, destiné à l'écran, de `technical_detail`, destiné au journal. `as_public_dict()` ne peut pas rendre le second : la séparation est portée par le type, non par une consigne, et un gabarit ne peut pas afficher par accident un champ qui n'est pas là.

    !!! info "Un état inconnu ne lève pas"
        Une ligne absente ou un état que le paquet ne connaît pas donnent « État inconnu ».

        Une exception ici remplacerait une page dégradée par une page d'erreur, ce qui est pire pour la personne qui regarde.

??? note "13. Plafonner la vidéothèque entière"

    Le paquet bornait déjà **un** fichier, par sa taille (`FORGE_VIDEO_MAX_UPLOAD_MB`) et par sa durée (`FORGE_VIDEO_MAX_DURATION_SECONDS`). Ces deux contrôles existaient et fonctionnaient.

    Rien ne bornait leur **somme** (`VIDEO-QUOTA-001`) : cinq cents vidéos d'une heure et de 999 Mo passent chacune le contrôle, et remplissent le disque de cinq cents gigaoctets.

    | Variable | Ce qu'elle borne |
    |---|---|
    | `FORGE_VIDEO_MAX_UPLOAD_MB` | un fichier, déjà présente |
    | `FORGE_VIDEO_MAX_DURATION_SECONDS` | un fichier, déjà présente |
    | `FORGE_VIDEO_MAX_TOTAL_MB` | la somme des tailles |
    | `FORGE_VIDEO_MAX_TOTAL_DURATION_SECONDS` | la somme des durées |

    Sans les deux dernières, rien n'est cumulé, et la base n'est même pas interrogée : un déploiement sans quota ne paye pas une requête par envoi.

    !!! warning "La durée se vérifie au traitement, pas à l'envoi"
        La taille est connue avant d'écrire, la durée seulement après le sondage.

        Un dépassement fait donc échouer le traitement et laisse le fichier source, que l'application supprime si elle le souhaite. Sonder avant d'écrire demanderait un fichier temporaire et un appel à `ffprobe` de plus par envoi, pour déplacer le problème sans le résoudre.

    !!! danger "Une valeur de configuration illisible lève"
        `FORGE_VIDEO_MAX_DURATION_SECONDS=7200x` **interrompt** le chargement de la configuration.

        Elle retombait auparavant sur le défaut en silence : les vidéos de deux heures étaient refusées, et rien n'expliquait pourquoi. Le paquet suit maintenant `forge-mvc-files` et `forge-mvc-images`.

    `library_totals()` rend l'état courant sans rien refuser, de quoi afficher une jauge. Les restants valent `None` quand aucun plafond n'est déclaré, jamais zéro, qui voudrait dire le contraire.

??? note "14. Associer des sous-titres"

    Une vidéo sans sous-titres est inaccessible aux personnes sourdes ou malentendantes, illisible dans un environnement bruyant, et introuvable par une recherche textuelle (`VIDEO-SUBTITLES-001`).

    ```python
    from forge_mvc_video import store_subtitle

    chemin = store_subtitle(donnees, video["uuid"], "fr", storage_root=config.storage_root)
    repository.add_subtitle(video["id"], lang="fr", path=chemin,
                            label="Français", is_default=True)
    ```

    ```html
    <video controls src="/videos/{{ uuid }}">
      <track kind="subtitles" srclang="fr" label="Français" default
             src="/videos/{{ uuid }}/subtitles/fr">
    </video>
    ```

    !!! info "Un seul format, WebVTT"
        C'est le seul que la balise `<track>` lit nativement, sans script ni conversion.

        En accepter d'autres, SRT ou ASS, demanderait de convertir à la volée ou de faire porter la conversion au navigateur, qui ne sait pas la faire. Le principe 11 veut une seule façon officielle.

    !!! danger "Ce qui n'est pas du WebVTT est refusé à l'entrée"
        Le contrôle porte sur la signature `WEBVTT`, que la spécification exige en tête de fichier.

        Sans lui, n'importe quel fichier pourrait être stocké et servi depuis le domaine de l'application sous un nom rassurant. Le refuser à l'écriture vaut mieux que de le filtrer à chaque lecture : la ligne ne doit pas exister.

    !!! info "Le chemin ne prend rien de l'utilisateur"
        Il est bâti depuis l'UUID de la vidéo et l'étiquette de langue, tous deux validés.

        Le nom du fichier envoyé n'entre pas dans le chemin, et aucune traversée n'est donc possible.

    L'étiquette de langue est normalisée en minuscules : `FR` et `fr` créeraient sinon deux pistes que la contrainte d'unicité laisserait passer et que le lecteur afficherait deux fois. Poser une nouvelle piste par défaut retire le drapeau des autres, deux pistes par défaut laissant le navigateur choisir.

    La piste est servie avec la même règle d'accès que la vidéo : une piste dit ce que la vidéo raconte, la protéger moins n'aurait pas de sens.

    Ajouter la table demande `forge video:init` puis `forge migration:apply`, comme la table `videos`.

## Voir aussi

- [Configuration (config.py)](references/config.md) : contrat `FORGE_VIDEO_*`.
- [Sondage (probe.py)](references/probe.md) et [Transcodage MP4 (transcode.py)](references/transcode.md) : le pipeline.
- [Traitement (process.py)](references/process.md) : orchestration complète.
- [Lecture HTTP (http.py)](references/http.md) : routes et streaming.
- [Welcome-Vidéo](welcome/debutant/video-welcome.md) : parcours d'apprentissage.
