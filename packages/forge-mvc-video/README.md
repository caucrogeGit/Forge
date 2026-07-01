# forge-mvc-video

Module **opt-in** Forge pour la vidéo applicative : upload contrôlé,
transcodage **MP4 H.264/AAC** et lecture en **streaming** (HTTP Range / 206).

Statut : **Beta**. Upload, transcodage MP4 et lecture en streaming HTTP Range
sont livrés.

## Principes

- **Opt-in** : le core Forge ne dépend pas de ce module.
- **Worker CLI → base → web lit** : le web ne transcode jamais pendant une
  requête. Le travail lourd se fait via `forge video:process`, le web ne fait
  que servir le résultat.
- **FFmpeg/ffprobe = binaires système** (pas des dépendances pip). Le module
  fonctionne en mode « serveur de médias » sans eux ; le transcodage les exige.
  `forge video:doctor` vérifie leur présence.

## Hors périmètre (v1)

Pas de HLS/DASH, pas de live, pas de WebRTC, pas de DRM, pas de 4K imposée,
pas d'AV1, pas de sous-titres avancés, pas de transcodage en requête HTTP.

## Installation

```bash
pip install --pre forge-mvc-video
forge video:doctor
```

Documentation : https://forgemvc.com/docs/forge/video/
