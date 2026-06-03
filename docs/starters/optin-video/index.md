# Vidéo (opt-in)

Le sujet **Vidéo (opt-in)** regroupe les starters d'entrée dans
l'écosystème [`forge-mvc-video`](../../video/parcours.md), le module
opt-in de Forge dédié à l'upload, au transcodage MP4 et à la lecture
vidéo en streaming HTTP Range.

Comme tout opt-in Forge, Vidéo n'est **jamais** chargé automatiquement :
le projet le branche explicitement via la couche `optins/`, sans
découverte magique (voir
[structure des opt-ins](../../architecture/optins-project-structure.md)).

## Parcours

| Niveau | Starter | Objectif |
|--------|---------|----------|
| Premier contact | [Bonjour Vidéo — `welcome-optin-video`](welcome-optin-video.md) | Trois routes pédagogiques + la route de lecture officielle `GET /videos/{uuid}`, configuration inspectée (token masqué), branchement opt-in explicite — sans ffmpeg ni table créée. |

Un seul niveau pour l'instant ; le parcours s'étoffera au fil des
tickets vidéo (voir [Forge Video — parcours complet](../../video/parcours.md)).

## Pour aller plus loin

- [Forge Video — parcours complet](../../video/parcours.md)
- [Référence CLI `forge video:*`](../../reference/cli-commands.md)
