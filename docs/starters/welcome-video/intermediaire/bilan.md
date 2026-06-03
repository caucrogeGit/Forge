# Bilan — niveau intermédiaire (Vidéo)

Récapitulatif des compétences acquises au **niveau intermédiaire** de la
progression *Bonjour Forge Vidéo*. Ce niveau fait passer de la lecture à une
petite chaîne **alimenter → servir → suivre**, toujours sans transcodage.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 — [Téléverser une vidéo](video-upload.md) | Ingérer un fichier (`ingest_video`), stockage sous UUID + ligne `videos` au statut `uploaded`, **sans ffmpeg**. |
| 2 — [Lire une vidéo](video-playback.md) | Brancher la lecture officielle (`register_video_routes`), `GET /videos/{uuid}` en streaming Range. |
| 3 — [Suivre l'état d'une vidéo](video-status.md) | Observer le cycle de vie par statut (`list_by_status`) : `uploaded → processing → ready`. |

Vous savez maintenant enregistrer une vidéo, la servir en streaming et suivre son
cycle de vie, sans transcodage.

## Et ensuite

Le récapitulatif rassemble toutes les API vidéo de la progression sur une seule
page.

[Récapitulatif de la progression Vidéo](../recapitulatif.md)
