# Rapport final — FW-HTTPS-PORT-443-001

## Résumé

HTTPS public a été activé avec succès pour `forgemvc.com`.

Le site Forge-web est maintenant accessible publiquement en HTTPS.

URL validée : `https://forgemvc.com/`.

## Redirection routeur

La box SFR redirige maintenant :

- `80/tcp -> 192.168.1.98:80`.
- `443/tcp -> 192.168.1.98:443`.

La redirection Proxmox `8006/tcp` reste désactivée.

## Caddy

Caddy a été modifié pour activer HTTPS automatique :

- `forgemvc.com` sert `/srv/forge-web/current`.
- `www.forgemvc.com` redirige vers `https://forgemvc.com{uri}`.
- `http://192.168.1.98` reste disponible en LAN.

Sauvegarde créée sur la VM : `/etc/caddy/Caddyfile.before-https-forgemvc`.

## Tests HTTPS

Résultats validés :

- `https://forgemvc.com/` : 200.
- `https://forgemvc.com/docs/` : 200.
- `https://forgemvc.com/docs/forge/` : 200.
- `https://forgemvc.com/docs/forge/installation/` : 200.
- `https://forgemvc.com/robots.txt` : 200.
- `https://forgemvc.com/sitemap.xml` : 200.
- `https://forgemvc.com/nonexistent/` : 404.

## Redirections

- `http://forgemvc.com/` : 308 vers `https://forgemvc.com/`.
- `https://www.forgemvc.com/` : 308 vers `https://forgemvc.com/`.
- `https://www.forgemvc.com/docs/` : 308 vers `https://forgemvc.com/docs/`.

## Certificat TLS

Certificat obtenu automatiquement par Caddy via Let’s Encrypt.

- Sujet : `CN=forgemvc.com`.
- Émetteur : `Let's Encrypt E7`.
- Début : `May 23 19:38:26 2026 GMT`.
- Fin : `Aug 21 19:38:25 2026 GMT`.

## Sécurité

- `forgemvc.com:8006` est inaccessible.
- Proxmox n’est pas exposé.
- Aucun SSH public n’a été configuré.
- Cloudflare reste en `DNS only`.

## Hors périmètre respecté

- Pas de proxy Cloudflare orange.
- Pas de DNSSEC.
- Pas de CAA.
- Pas de mail.
- Pas de modification Proxmox.
- Pas de configuration logs/statistiques.

## Décision

`FW-HTTPS-PORT-443-001` est validé.

Forge-web est maintenant publié en HTTPS sur `https://forgemvc.com/`.

## Prochain ticket recommandé

`FW-ACCESS-LOGS-STATS-001 — Mettre en place les logs d’accès et statistiques simples`.
