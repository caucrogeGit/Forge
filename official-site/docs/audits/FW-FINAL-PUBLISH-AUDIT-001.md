# Rapport final — FW-FINAL-PUBLISH-AUDIT-001

## Résumé

Audit final de publication Forge-web validé.

Le site officiel Forge est publié en HTTPS sur :

`https://forgemvc.com/`

La documentation est publiée sur :

`https://forgemvc.com/docs/`

## Publication publique

Validations publiques :

- `https://forgemvc.com/` : 200.
- `https://forgemvc.com/docs/` : 200.
- `https://forgemvc.com/docs/forge/` : 200.
- `https://forgemvc.com/docs/forge/installation/` : 200.
- `https://forgemvc.com/robots.txt` : 200.
- `https://forgemvc.com/sitemap.xml` : 200.
- `https://forgemvc.com/nonexistent/` : 404.

## Redirections

- `http://forgemvc.com/` : 308 vers HTTPS.
- `https://www.forgemvc.com/` : 308 vers `https://forgemvc.com/`.
- `https://www.forgemvc.com/docs/` : 308 vers `https://forgemvc.com/docs/`.

## DNS

- `forgemvc.com` pointe vers `93.26.201.177`.
- `www.forgemvc.com` est un CNAME vers `forgemvc.com`.
- Cloudflare reste en `DNS only`.

## Sécurité publique

- Proxmox `8006/tcp` est inaccessible publiquement.
- SSH `22/tcp` est inaccessible publiquement.
- Proxmox n’est pas exposé.

## VM forge-web

- Caddy est `active` et `enabled`.
- Ports actifs : 80 et 443.
- API admin Caddy limitée à `127.0.0.1:2019`.
- Caddy sert `/srv/forge-web/current`.

## Logs et statistiques

- Logs Caddy JSON actifs : `/var/log/caddy/forge-web-access-json.log`.
- Rotation Caddy configurée.
- GoAccess installé et validé localement.
- Rapport GoAccess local : `/home/roger/forge-web-stats/forge-web-goaccess.html`.
- Les statistiques ne sont pas publiées dans `/srv/forge-web/current`.

## Vie privée

Aucun tracker actif détecté :

- pas de Google Analytics ;
- pas de Google Tag Manager ;
- pas de Matomo ;
- pas de Plausible ;
- pas de Cookiebot ;
- pas de Facebook Pixel.

Les mentions textuelles dans les rapports ou la documentation ne sont pas des trackers actifs.

## Build final

Build final validé :

- `scripts/build-site.sh` : OK.
- 277 fichiers générés.
- 222 fichiers HTML.
- 19 478 liens locaux analysés.
- 0 lien local cassé.
- `git diff --check` : OK.

## État Git

Dernier commit validé :

`477ed48 Prepare local GoAccess statistics`

`HEAD` est aligné avec `origin/main` au moment de l’audit final.

## Hors périmètre respecté

- Pas de proxy Cloudflare orange.
- Pas de DNSSEC ajouté.
- Pas de CAA ajouté.
- Pas de mail configuré.
- Pas de publication publique des statistiques.
- Pas de modification Proxmox.

## Décision

`FW-FINAL-PUBLISH-AUDIT-001` est validé.

Forge-web est publié proprement en HTTPS, avec documentation publique, logs serveur, statistiques locales non publiques et Proxmox non exposé.

## Prochain ticket recommandé

`FW-POST-PUBLISH-MAINTENANCE-001 — Définir la maintenance post-publication Forge-web`.
