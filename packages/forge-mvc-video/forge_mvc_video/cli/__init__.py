# pyright: strict
"""Commandes CLI du module vidéo (``forge video:*``).

Commandes disponibles :
- ``video:doctor``  — diagnostic (package, config, migration, ffmpeg/ffprobe, routes) ;
- ``video:init``    — copie la migration ``videos`` vers ``mvc/migrations/`` ;
- ``video:upload``  — entrée d'upload (valide, stocke, insère au statut ``uploaded``) ;
- ``video:process`` — worker (probe + poster + transcodage MP4) ;
- ``video:cleanup`` — purge (vidéos ``failed`` / fichiers orphelins), dry-run par défaut.
"""
