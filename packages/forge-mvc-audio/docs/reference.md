# L'audio dans Forge (forge-mvc-audio)

Ce document explique ce que fait l'opt-in `forge-mvc-audio`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-audio` est une chaîne audio **complète et sans état** : ingérer un fichier, le sonder, le transcoder en MP3, le lire en streaming HTTP Range.

Volontairement sobre : aucune base de données, aucune file de transcodage, des opérations synchrones, des fichiers retrouvés par `uuid` sur le disque.

??? note "1. Rôle du module"

    L'opt-in couvre le cycle d'un fichier audio sans rien imposer en base : on ingère des octets, on les range sur disque sous un `uuid`, on peut les sonder (`ffprobe`), les convertir en MP3 (`ffmpeg`), et les servir.

    Il branche ses **routes** de lecture sur le routeur du projet via `register_audio_routes` (modèle opt-in de type route).

    Sa sobriété est un choix : pas de table SQL, pas de suivi de jobs ; tout est synchrone et le service retrouve les fichiers par `uuid`.

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
    pip install --pre forge-mvc-audio
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-audio"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-audio`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-audio==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable audio --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    Rien à faire : cet opt-in n'apporte aucune table.

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
    forge opt-in:disable audio
    pip uninstall forge-mvc-audio
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre et débranche les routes de `mvc/routes/__init__.py`, sans toucher au paquet.
    `forge opt-in:remove audio` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-audio` ajoute une commande :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `audio:doctor` | Diagnostic (paquet, config, `ffmpeg`/`ffprobe`). | `forge audio:doctor` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-audio` |
    | Module | `forge_mvc_audio` |
    | Catégorie | Médias et fichiers (ADR-055) |
    | Couche | opt-in de type route (couche `optins/`) |
    | Dépend de | `forge-mvc`, et `ffmpeg` / `ffprobe` (binaires système) |
    | API publique | `ingest_audio`, `probe_audio`, `transcode_to_mp3`, `register_audio_routes`, `load_audio_config` |
    | Objets | `AudioConfig`, `AudioMetadata` |
    | Configuration | `load_audio_config` (contrat `AudioConfig`) |
    | Commandes | `audio:doctor` |
    | Lecture | streaming HTTP Range, fichiers indexés par `uuid` |
    | État | **sans état** : pas de base de données, opérations synchrones |
    | Exceptions | `AudioIngestError`, `AudioProbeError`, `FfmpegError` |
    | Installation | `pip install --pre forge-mvc-audio` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre les modules, les objets et les dépendances externes.

    Le diagramme de séquence montre l'ingestion, le transcodage et la lecture.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre une chaîne sans base de données : les fichiers vivent sur disque sous un `uuid`, et `ffmpeg` / `ffprobe` font le travail média.

    ```mermaid
    classDiagram
        direction LR

        class ingest {
            <<module>>
            +ingest_audio(data, filename, title, config, uuid) dict
        }

        class probe {
            <<module>>
            +probe_audio(path, config, runner) AudioMetadata
        }

        class transcode {
            <<module>>
            +transcode_to_mp3(input_path, output_path, ...)
        }

        class http {
            <<module>>
            +register_audio_routes(router, config)
        }

        class AudioMetadata {
            <<dataclass>>
            +float duration
            +str codec
            +int bitrate
            +int channels
        }

        class ffmpeg {
            <<binaire externe>>
            +ffmpeg
            +ffprobe
        }

        ingest --> Disk : range par uuid
        probe --> ffmpeg : ffprobe
        transcode --> ffmpeg : ffmpeg
        probe --> AudioMetadata : renvoie
        http --> Disk : sert par uuid (HTTP Range)

    ```

    À retenir :

    - aucune table : les fichiers sont rangés et retrouvés par `uuid` ;
    - `ffprobe` sonde, `ffmpeg` transcode ;
    - `probe_audio` renvoie un `AudioMetadata` typé ;
    - la lecture sert le fichier par son `uuid`, en streaming.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre une ingestion suivie d'un transcodage, puis la lecture.

    ```mermaid
    sequenceDiagram
        actor Op as Code applicatif
        participant Ingest as ingest_audio
        participant Disk as Disque (uuid)
        participant Probe as probe_audio
        participant Trans as transcode_to_mp3
        participant Routes as register_audio_routes
        actor Navigateur

        Op->>Ingest: ingest_audio(data, "cours.wav")
        Ingest->>Disk: range le fichier sous un uuid
        Ingest-->>Op: dict (uuid, chemin, ...)
        Op->>Probe: probe_audio(chemin)
        Probe-->>Op: AudioMetadata (durée, codec...)
        Op->>Trans: transcode_to_mp3(src, dst)
        Trans-->>Op: MP3 écrit
        Navigateur->>Routes: GET l'audio (avec Range)
        Routes-->>Navigateur: flux MP3 (206 Partial Content)

    ```

    À retenir :

    - l'ingestion valide et range les octets sous un `uuid` ;
    - le sondage et le transcodage sont des appels **synchrones** ;
    - la lecture honore l'en-tête `Range` ;
    - rien n'est suivi en base : l'application gère ses propres références d'`uuid`.

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `ingest_audio` | `ingest_audio(data, filename, title=None, config=None, uuid=None) -> dict` | valide et range un fichier audio |
    | `probe_audio` | `probe_audio(path, config=None, runner=None) -> AudioMetadata` | métadonnées via `ffprobe` |
    | `transcode_to_mp3` | `transcode_to_mp3(input_path, output_path, ffmpeg_bin="ffmpeg", bitrate_kbps=192, ...)` | conversion MP3 via `ffmpeg` |
    | `register_audio_routes` | `register_audio_routes(router, config=None) -> Any` | branche les routes de lecture |
    | `load_audio_config` | `load_audio_config(source=None) -> AudioConfig` | charge la configuration |
    | `AudioConfig` | dataclass | contrat de configuration |
    | `AudioMetadata` | dataclass | durée, codec, bitrate, canaux |
    | `AudioIngestError`, `AudioProbeError`, `FfmpegError` | exceptions | erreurs d'ingestion, de sondage, de transcodage |

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Vérifier l'installation | `forge audio:doctor` |
    | Ingérer un fichier | `ingest_audio(data, filename)` |
    | Lire les métadonnées | `probe_audio(path)` |
    | Convertir en MP3 | `transcode_to_mp3(src, dst)` |
    | Brancher la lecture | `register_audio_routes(router)` |
    | Configurer le module | `load_audio_config(...)` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Ingérer puis transcoder

    ```python
    from forge_mvc_audio import ingest_audio, transcode_to_mp3

    stored = ingest_audio(data, "cours.wav", title="Cours 1")
    transcode_to_mp3(stored["path"], stored["path"].replace(".wav", ".mp3"))
    ```

    L'ingestion range le fichier sous un `uuid` ; le transcodage est synchrone.

    ### 8.2 Brancher les routes de lecture

    ```python
    # optins/audio/routes.py (couche optins du projet)
    from forge_mvc_audio import register_audio_routes


    def register(router) -> None:
        register_audio_routes(router)

    ```

    !!! tip "Aide-mémoire"
        Une chaîne en quatre temps :

        - `ingest_audio` pour entrer ;
        - `probe_audio` pour inspecter ;
        - `transcode_to_mp3` pour convertir ;
        - `register_audio_routes` pour lire.

??? note "11. Sobriété, uuid et dépendances"

    Le module est **sans état** : pas de table, pas de file de jobs.
    L'application garde elle-même la trace des `uuid` qu'elle a ingérés.

    `ffmpeg` et `ffprobe` sont des binaires système (pas des dépendances pip) ; `forge audio:doctor` vérifie leur présence.

    !!! warning "ffmpeg / ffprobe requis"
        Sans ces binaires, le sondage et le transcodage échouent (`AudioProbeError`, `FfmpegError`).

        Lancez `forge audio:doctor` après installation.

    !!! note "Opérations synchrones"
        Le transcodage est synchrone : pour de gros fichiers, déclenchez-le hors requête (par exemple via `forge-mvc-jobs`).

        La sobriété est assumée : pas de file intégrée, pas de suivi en base.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-audio` : la dépendance va de l'opt-in vers le cœur.

??? note "12. Lire les métadonnées d'un fichier"

    `ffprobe` rendait déjà ces étiquettes, le paquet les jetait (`AUDIO-ID3-001`) : le sondage lisait la durée, le codec et le débit, et laissait tomber le titre, l'artiste et l'album.

    Une application devait donc rappeler `ffprobe` elle même pour afficher le nom d'un morceau qu'elle venait de recevoir.

    ```python
    from forge_mvc_audio import probe_audio

    meta = probe_audio(chemin)
    meta.duration_seconds        # déjà présent
    meta.tags.title              # « Le Sacre du printemps »
    meta.tags.display_title      # « Stravinsky - Le Sacre du printemps »
    meta.tags.year               # 2019
    meta.tags.track_number       # 3, sur meta.tags.track_total
    ```

    `meta.tags` n'est jamais `None` : un fichier sans étiquette donne un objet vide, de sorte qu'un appelant n'ait pas à tester avant de lire. C'est d'ailleurs le cas courant d'un enregistrement brut, ou d'un fichier transcodé par le paquet, qui pose `-map_metadata -1`.

    !!! danger "Une étiquette vient du fichier envoyé"
        Elle est écrite par qui a produit le fichier, ou par qui l'a modifié avant de l'envoyer, et elle finit affichée dans une page.

        Trois précautions sont donc appliquées ici plutôt que laissées à l'appelant, qui les oublierait une fois sur deux. Les caractères de contrôle sont retirés, y compris `U+2028` que `str.strip` laisse passer et qui casse une chaîne JavaScript. La longueur est bornée à 300 caractères, rien n'empêchant un titre d'un mégaoctet. Et rien n'est interprété.

    !!! warning "L'échappement reste au gabarit"
        Le module ne décode aucune entité et n'échappe rien.

        Le faire ici et dans le gabarit afficherait `&amp;amp;`, et Jinja échappe déjà.

    !!! info "Les noms d'étiquettes varient selon le conteneur"
        ID3 dit `tit2`, Vorbis dit `TITLE`, et la casse change d'un outil à l'autre.

        Les clés sont donc cherchées en minuscules, par ordre de préférence. Un conteneur sans bloc de format, comme le WAV, voit ses étiquettes lues sur le flux audio.

    Une année implausible ou un « piste 5 sur 2 » sont écartés : afficher une valeur manifestement fausse vaut moins que ne rien afficher.

    Le module ne **réécrit** jamais les étiquettes d'un fichier. Les lire et les écrire sont deux gestes, et le second appartiendrait à un autre ticket.

??? note "13. Découper un fichier"

    Extraire un extrait, retirer un silence de tête, produire un aperçu de trente secondes : le paquet savait transcoder un fichier entier, pas en prendre un morceau (`AUDIO-TRIM-001`).

    ```bash
    forge audio:trim source.wav extrait.mp3 --from 1:30 --to 2:00
    forge audio:trim source.wav apercu.mp3 --to 30 --reencode
    ```

    Les trois écritures d'un instant sont acceptées, `90`, `1:30` et `0:01:30.5`, parce que les trois se rencontrent et que refuser l'une d'elles n'apporterait rien.

    ```python
    from forge_mvc_audio import trim_audio

    trim_audio("source.wav", "extrait.mp3", start=90, end=120)
    ```

    !!! danger "La sortie ne peut pas être la source"
        Une découpe sur place n'existe pas côté `ffmpeg`, qui lit et écrit en même temps : le fichier serait tronqué à zéro et le travail perdu.

        La comparaison porte sur le chemin résolu, `a.mp3` et `./a.mp3` désignant le même fichier.

    !!! warning "Un fichier de sortie existant n'est pas écrasé"
        C'est le mode « Forge génère » de la charte, write-if-new.

        Un extrait produit deux fois avec des bornes différentes doit dire lequel gagne, d'où `--force`.

    !!! info "Sans réencodage, les bornes sont approchées"
        Les flux sont copiés tels quels : la découpe est instantanée et sans perte, mais elle se cale sur l'image clé la plus proche, à quelques dixièmes de seconde près.

        `--reencode` rend les bornes exactes, au prix d'un transcodage complet.

    Un intervalle vide ou renversé est refusé plutôt que joué : `ffmpeg` écrirait un fichier de zéro seconde sans se plaindre.

    L'option `-ss` est placée **avant** `-i`, ce qui fait sauter `ffmpeg` directement à l'instant demandé au lieu de décoder tout ce qui précède. Sur un long fichier, cela change une découpe de plusieurs minutes en une opération immédiate.

??? note "14. Alignement avec le module vidéo"

    `audio:doctor` et `video:doctor` étaient **déjà** alignés quand ce ticket a été ouvert : même dataclass de résultat, mêmes statuts minuscules, mêmes contrôles (`AUDIO-DOCTOR-HARMONISE-001`).

    Le ticket livre donc ce qui manquait vraiment, un garde-fou qui refuse que les deux surfaces divergent, à un contrôle près : la migration, que l'audio n'a pas puisqu'il est sans état.

    La comparaison a en revanche fait apparaître une divergence réelle, ailleurs.

    !!! danger "Une valeur de configuration illisible lève désormais"
        `FORGE_AUDIO_MAX_DURATION_SECONDS=7200x` retombait sur le défaut en silence : les fichiers plus longs étaient refusés, et rien ne l'expliquait.

        Le paquet suit maintenant `forge-mvc-video`, `forge-mvc-files` et `forge-mvc-images` : une limite mal écrite se signale au démarrage. Pour ne pas borner, retirez la variable.

    L'harmonisation de deux paquets porte d'abord sur ce que fait leur code, pas seulement sur ce qu'affiche leur diagnostic.

## Voir aussi

- [Configuration (config.py)](references/config.md) : contrat `AudioConfig`.
- [Ingestion (ingest.py)](references/ingest.md) : `ingest_audio`, stockage par uuid.
- [Sondage (probe.py)](references/probe.md) et [Transcodage MP3 (transcode.py)](references/transcode.md).
- [Lecture HTTP (http.py)](references/http.md) : routes et streaming.
- [Welcome-Audio](welcome/debutant/audio-welcome.md) : parcours d'apprentissage.
