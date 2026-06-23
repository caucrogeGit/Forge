# Rapport final — FW-CADDY-DOMAIN-HTTP-001

## Résumé

Caddy a été configuré pour servir Forge-web en HTTP avec les hosts `forgemvc.com` et `www.forgemvc.com`.

Aucun DNS Cloudflare, aucun HTTPS public et aucune modification Proxmox n’ont été effectués.

## Configuration appliquée

Le Caddyfile contient maintenant :

- `http://192.168.1.98` : sert `/srv/forge-web/current`.
- `http://forgemvc.com` : sert `/srv/forge-web/current`.
- `http://www.forgemvc.com` : redirige vers `http://forgemvc.com{uri}` en 308.

Une sauvegarde a été créée : `/etc/caddy/Caddyfile.before-forgemvc-http`.

## Validations

- `caddy validate` : configuration valide.
- `systemctl reload caddy` : OK.
- `systemctl is-active caddy` : active.

## Tests HTTP

- `Host: forgemvc.com` local : 200, landing Forge visible.
- `Host: www.forgemvc.com` local : 308 vers `http://forgemvc.com/docs/`.
- `Host: forgemvc.com` via IP publique : 200, landing Forge visible.
- `Host: www.forgemvc.com` via IP publique : 308 vers `http://forgemvc.com/docs/`.

## Hors périmètre respecté

- DNS Cloudflare non modifié.
- HTTPS public non activé.
- Port 443 non traité.
- Proxmox non modifié.
- Firewall non modifié.
- Mail non traité.

## Décision

Caddy est prêt pour la création des enregistrements DNS HTTP de `forgemvc.com`.

## Prochain ticket recommandé

`FW-CLOUDFLARE-DNS-HTTP-001 — Créer les enregistrements DNS Cloudflare pour forgemvc.com en HTTP`.
