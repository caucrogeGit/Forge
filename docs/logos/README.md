# Logos Forge

Ce dossier contient les logos Forge déclinés en plusieurs tailles, au format PNG transparent.

Chaque sous-dossier correspond à une taille de référence, exprimée par le plus grand côté :

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
Ils sont générés à partir des exports Canva transparents, détourés au plus près du contenu avec ImageMagick (`-trim`), avec une marge transparente uniforme d'environ 5 pour cent.
Le rapport d'aspect propre à chaque logo est préservé : les visuels ne sont donc pas carrés, et la taille de référence borne le plus grand côté (sortie `PNG32:`, fond `none`, aucun agrandissement).

La méthode complète est décrite dans la documentation, page « ImageMagick (guide complet) », chapitre « Générer un jeu de tailles carrées (cas logos) ».
