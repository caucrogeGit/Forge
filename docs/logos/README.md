# Logos Forge

Ce dossier contient les logos Forge déclinés en plusieurs tailles carrées, au format PNG transparent.

Chaque sous-dossier correspond à une taille :

- `1024x1024/`
- `512x512/`
- `256x256/`
- `128x128/`
- `64x64/`
- `32x32/`
- `16x16/`

Chaque taille contient les mêmes logos :

- `forge-1` à `forge-7` : variantes du logo principal ;
- `forge-bandeau-1` et `forge-bandeau-2` : versions en bandeau ;
- `serveur-forge` : illustration du serveur Forge.

Les fichiers sont nommés `<logo>-<taille>.png`, par exemple `forge-1-512.png`.

Tous les fichiers sont de vrais PNG transparents : canal alpha présent et fond réellement transparent.
Ils sont générés à partir des exports Canva transparents, puis redimensionnés avec ImageMagick en toile carrée stricte (sortie `PNG32:`, fond `none`).

La méthode complète est décrite dans la documentation, section « Outils », page « ImageMagick (logos transparents) ».
