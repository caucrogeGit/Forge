# Rapport final — FW-ACCESS-LOGS-STATS-001

## Résumé

Les access logs Caddy ont été activés pour Forge-web.

Aucun tracker JavaScript, aucun cookie de tracking et aucun outil externe type Google Analytics n’a été ajouté.

## Configuration

Fichier de logs : `/var/log/caddy/forge-web-access.log`.

Rotation native Caddy :

- `roll_size 10MiB`.
- `roll_keep 10`.
- `roll_keep_for 720h`.

Format : `console`.

## Validation

Accès générés :

- `https://forgemvc.com/`.
- `https://forgemvc.com/docs/`.
- `https://forgemvc.com/nonexistent/`.
- `https://www.forgemvc.com/`.

Résultats observés dans les logs :

- `200` pour la landing.
- `200` pour `/docs/`.
- `404` pour `/nonexistent/`.
- `308` pour la redirection `www`.

Le fichier `/var/log/caddy/forge-web-access.log` existe et se remplit correctement.

## Vie privée

Décision maintenue :

- pas de Google Analytics ;
- pas de tracker JavaScript ;
- pas de cookies de tracking ;
- pas de bannière RGPD inutile à ce stade.

Les statistiques seront basées sur les logs serveur.

## Rotation

La rotation native Caddy est suffisante pour ce stade.

Aucune configuration `logrotate` supplémentaire n’a été ajoutée afin d’éviter un doublon.

## Limites restantes

- Pas encore de tableau de bord statistiques.
- GoAccess non installé.
- Pas encore de rapport périodique de fréquentation.
- Les IP visibles dans les logs peuvent être celles de la box ou du NAT selon le chemin réseau.

## Hors périmètre respecté

- Cloudflare proxy orange non activé.
- DNS non modifié.
- Proxmox non modifié.
- Aucun outil de tracking externe ajouté.
- Mail non traité.

## Décision

`FW-ACCESS-LOGS-STATS-001` est validé.

Forge-web dispose maintenant de logs d’accès serveur simples et suffisants pour une première publication.

## Prochain ticket recommandé

`FW-GOACCESS-STATS-001 — Préparer des statistiques locales avec GoAccess`.
