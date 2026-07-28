# L'audio dans Forge (forge-mvc-audio)

Ce document explique ce que fait l'opt-in `forge-mvc-audio`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-audio` est une chaîne audio **complète et sans état** : ingérer un fichier, le sonder, le transcoder en MP3, le lire en streaming HTTP Range.

Volontairement sobre : aucune base de données, aucune file de transcodage, des opérations synchrones, des fichiers retrouvés par `uuid` sur le disque.

??? note "1. Rôle du module"

    L'opt-in couvre le cycle d'un fichier audio sans rien imposer en base : on ingère des octets, on les range sur disque sous un `uuid`, on peut les sonder (`ffprobe`), les convertir en MP3 (`ffmpeg`), et les servir.

    Il branche ses **routes** de lecture sur le routeur du projet via `register_audio_routes` (modèle opt-in de type route).

    Sa sobriété est un choix : pas de table SQL, pas de suivi de jobs ; tout est synchrone et le service retrouve les fichiers par `uuid`.

??? note "2. Installation"

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-audio
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-audio"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable audio --apply
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) et câble ses routes dans `mvc/routes/__init__.py`.
    `forge opt-in:install audio` affiche la commande `pip` sans l'exécuter.

    Ces gestes ne suffisent pas à rendre l'opt-in **opérationnel** : il reste à l'épingler dans
    `requirements.txt`, à provisionner sa base s'il en a une, à le brancher là où il agit et à le
    prouver par un premier usage réel.
    Voir la procédure canonique, [Rendre un opt-in opérationnel : les cinq points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

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

    #### 3. Poser sa base

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

## Voir aussi

- [Configuration (config.py)](references/config.md) : contrat `AudioConfig`.
- [Ingestion (ingest.py)](references/ingest.md) : `ingest_audio`, stockage par uuid.
- [Sondage (probe.py)](references/probe.md) et [Transcodage MP3 (transcode.py)](references/transcode.md).
- [Lecture HTTP (http.py)](references/http.md) : routes et streaming.
- [Welcome-Audio](welcome/debutant/audio-welcome.md) : parcours d'apprentissage.
