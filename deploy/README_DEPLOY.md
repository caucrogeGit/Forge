# Déploiement Forge

Ce dossier contient les fichiers générés par `forge deploy:init`.

## Fichiers

| Fichier | Rôle |
|---------|------|
| `nginx/forge-app.conf` | Configuration Nginx (reverse proxy) |
| `systemd/forge-app.service` | Unité systemd (daemon applicatif) |

## Étapes d'installation

1. Créer `env/prod` avec les variables de production (voir `docs/deployment.md`).
   En production derrière Nginx, Forge écoute en HTTP local (`APP_SSL_ENABLED=false`).
2. Adapter `systemd/forge-app.service` : remplacer `User=www-data` si nécessaire.
3. Copier `nginx/forge-app.conf` dans `/etc/nginx/sites-available/`.
4. Activer le site Nginx :
   ```
   sudo ln -s /etc/nginx/sites-available/forge-app.conf /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```
5. Copier `systemd/forge-app.service` dans `/etc/systemd/system/`.
6. Activer le service :
   ```
   sudo systemctl daemon-reload
   sudo systemctl enable forge-app
   sudo systemctl start forge-app
   ```
7. Vérifier : `forge deploy:check`

> Ces fichiers sont des modèles. Adaptez-les à votre infrastructure.
