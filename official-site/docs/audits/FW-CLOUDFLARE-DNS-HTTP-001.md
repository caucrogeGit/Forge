# Rapport final — FW-CLOUDFLARE-DNS-HTTP-001

## Résumé

Les enregistrements DNS Cloudflare minimaux pour `forgemvc.com` ont été créés en mode `DNS only`.

Le site Forge-web est accessible en HTTP via le domaine racine après résolution vers `93.26.201.177`.

## Enregistrements créés

- `A forgemvc.com -> 93.26.201.177`.
- `CNAME www.forgemvc.com -> forgemvc.com`.

Les deux enregistrements sont en `DNS only`, nuage gris.

## Tests DNS

- `dig A forgemvc.com` retourne `93.26.201.177` sur les résolveurs publics.
- `dig CNAME www.forgemvc.com` retourne `forgemvc.com` sur les résolveurs déjà propagés.
- Le cache DNS local de la box SFR peut rester temporairement en retard.

## Tests HTTP

Tests avec résolution forcée vers `93.26.201.177` :

- `http://forgemvc.com/` : 200, landing Forge visible.
- `http://www.forgemvc.com/` : 308 vers `http://forgemvc.com/`.
- `http://www.forgemvc.com/docs/` : 308 vers `http://forgemvc.com/docs/`.

## Sécurité

- `forgemvc.com:8006` est inaccessible.
- La redirection Proxmox `8006/tcp` reste désactivée côté box.
- Aucun port SSH public n’a été ouvert.

## Hors périmètre respecté

- HTTPS public non activé.
- Port 443 non traité.
- Cloudflare proxy orange non activé.
- DNSSEC non modifié.
- CAA non créé.
- Mail non traité.
- Proxmox non modifié.

## Décision

Le DNS HTTP minimal est validé.

Forge-web est prêt pour le prochain ticket HTTPS.

## Prochain ticket recommandé

`FW-HTTPS-PORT-443-001 — Rediriger 443 vers forge-web et préparer HTTPS Caddy`.
