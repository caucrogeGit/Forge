# Rapport final — FW-ROUTER-PORTS-AUDIT-001

## Résumé

Audit des redirections routeur SFR réalisé.

La règle Proxmox exposant `8006/tcp` vers `192.168.1.188:8006` a été désactivée.

La règle HTTP Forge-web a été créée et activée : `80/tcp -> 192.168.1.98:80`.

## État routeur

- Box : SFR.
- IP publique détectée : `93.26.201.177`.
- Règle `proxmox` : désactivée.
- Règle `forge-web-http` : active.

## Redirections

- `8006/tcp -> 192.168.1.188:8006` : désactivé.
- `80/tcp -> 192.168.1.98:80` : activé.
- `443/tcp -> 192.168.1.98:443` : non encore créé.

## Tests publics

- `http://93.26.201.177/` : réponse Caddy `200`.
- `https://93.26.201.177:8006/` : connexion impossible, attendu.
- `Host: 192.168.1.98` sur IP publique : landing Forge visible.
- `Host: forgemvc.com` sur IP publique : réponse Caddy `200`, mais contenu non servi correctement car Caddyfile pas encore configuré pour le domaine.

## Décision

La redirection publique HTTP fonctionne.

Proxmox n’est plus exposé sur `8006/tcp`.

Il faut maintenant configurer Caddy pour `forgemvc.com` avant de modifier Cloudflare.

## Hors périmètre respecté

- Aucun DNS Cloudflare modifié.
- Aucun HTTPS public activé.
- Aucun changement Proxmox.
- Aucun serveur mail.

## Prochain ticket recommandé

`FW-CADDY-DOMAIN-HTTP-001 — Configurer Caddy pour servir forgemvc.com en HTTP avant DNS`.
