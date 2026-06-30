# Bilan : niveau intermédiaire (Vidéo)

Récapitulatif des compétences acquises au **niveau intermédiaire** de la
progression *Welcome Vidéo*. Ce niveau fait passer de la lecture à une
petite chaîne **alimenter → servir → suivre**, toujours sans transcodage.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Téléverser une vidéo](video-upload.md) | Ingérer un fichier (`ingest_video`), stockage sous UUID + ligne `videos` au statut `uploaded`, **sans ffmpeg**. |
| 2 : [Lire une vidéo](video-playback.md) | Brancher la lecture officielle (`register_video_routes`), `GET /videos/{uuid}` en streaming Range. |
| 3 : [Suivre l'état d'une vidéo](video-status.md) | Observer le cycle de vie par statut (`list_by_status`) : `uploaded → processing → ready`. |

Vous savez maintenant enregistrer une vidéo, la servir en streaming et suivre son
cycle de vie, sans transcodage.

## Et ensuite

Place au **niveau avancé** : on bascule vers le réel, avec la sonde ffprobe, le
transcodage ffmpeg et le diagnostic du module.

[Niveau avancé : Sonder une vidéo](../avance/video-probe.md)
