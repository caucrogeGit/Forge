# Rapport final — FW-DEPLOY-GO-001

## Résumé

Déploiement LAN validé sur la VM `forge-web`.

URL validée : `http://192.168.1.98/`.

Caddy sert maintenant le vrai site Forge-web depuis `/srv/forge-web/current`.

## Déploiement

- Source locale : `/home/roger/Projets/Forge-web/dist/`.
- Staging : `/tmp/forge-web-deploy-staging`.
- Staging validé : `index.html`, `docs/index.html`, 269 fichiers, environ 26 Mo.
- Sauvegarde : `/srv/forge-web/backups/current-20260523-215252`.
- Bascule effectuée vers `/srv/forge-web/current`.

## Tests LAN

- `/` : 200.
- `/docs/` : 200.
- `/docs/forge/` : 200.
- `/docs/forge/installation/` : 200.
- `/robots.txt` : 200.
- `/sitemap.xml` : 200.
- `/nonexistent/` : 404.

## Hors périmètre

Pas de DNS public, pas de HTTPS public, pas de modification Proxmox, pas de modification Caddy, pas de mail.

## Décision

`FW-DEPLOY-GO-001` est validé.

## Prochain ticket

`FW-DNS-WEB-001 — Préparer la configuration DNS web pour forgemvc.com`.
