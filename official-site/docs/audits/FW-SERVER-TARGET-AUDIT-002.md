# Rapport final — FW-SERVER-TARGET-AUDIT-002

## Résumé

La VM `forge-web` existe, répond en SSH, exécute Debian 13 et dispose de Caddy installé, actif et opérationnel.

Caddy sert actuellement une page placeholder locale depuis `/srv/forge-web/current`.

La VM est prête pour un déploiement LAN contrôlé du site Forge-web généré dans `dist/`.

## VM cible

- Hostname : `forge-web`
- Utilisateur SSH : `roger`
- IP locale : `192.168.1.98/24`
- Interface : `ens18`
- Passerelle : `192.168.1.1`
- OS : Debian GNU/Linux 13 trixie 13.5
- Kernel : `6.12.88+deb13-amd64`

## Ressources

- CPU : 1 vCPU
- RAM : 1,9 GiB
- Swap : 1,2 GiB
- Disque : 24G
- Racine `/` : ext4, 22G, 19G libres

Ces ressources sont suffisantes pour un site statique Forge-web.

## Réseau et ports

Ports observés :

- `22/tcp` : SSH
- `80/tcp` : Caddy HTTP
- `127.0.0.1:2019` : API admin Caddy locale uniquement

Le port `443/tcp` n’est pas encore écouté. C’est normal tant que le domaine public et HTTPS ne sont pas configurés.

## Caddy

Version : `2.6.2`

Service :

- `enabled`
- `active`

Caddyfile actuel :

- site : `http://192.168.1.98`
- racine : `/srv/forge-web/current`
- serveur : `file_server`

Validation Caddy :

- résultat : `Valid configuration`
- avertissement attendu : Caddy écoute seulement en HTTP, donc HTTPS automatique non appliqué à ce stade.

Ce warning est normal en phase LAN.

## Contenu web actuel

Caddy sert une page placeholder :

- fichier : `/srv/forge-web/current/index.html`
- titre : `Forge-web — test local`
- contenu : page de test locale servie par Caddy
- IP affichée : `192.168.1.98`

Le vrai site Forge-web n’est pas encore déployé.

## Permissions

Chemin servi :

- `/srv/forge-web/current`

Propriétaire :

- `root:root`

Permissions :

- `/srv` : `755`
- `/srv/forge-web` : `755`
- `/srv/forge-web/current` : `755`

Le chemin est lisible par Caddy. Pour le futur déploiement, il faudra utiliser une procédure contrôlée, probablement avec `sudo rsync`.

## Firewall local

`ufw` n’est pas installé.

Aucune règle firewall locale exploitable n’a été relevée dans les sorties fournies.

Avant exposition publique, il faudra définir clairement :

- `80/tcp` public
- `443/tcp` public
- `22/tcp` privé uniquement LAN/VPN/Tailscale

## Vérification Proxmox

Aucun signal Proxmox détecté dans la VM :

- `pveproxy.service` absent
- pas de port `8006/tcp` observé
- pas de commande `pveversion` observée
- pas de paquet Proxmox visible dans les sorties fournies

La cible n’est donc pas le node Proxmox.

## Risques identifiés

1. SSH écoute sur IPv4/IPv6 : acceptable en LAN, à ne pas exposer publiquement.
2. Pas de firewall local actif : à traiter avant ouverture Internet.
3. Caddy est en HTTP-only : normal en LAN, HTTPS à traiter après DNS.
4. `/srv/forge-web/current` appartient à `root:root` : nécessite une procédure de déploiement contrôlée.
5. Le site réel Forge-web n’est pas encore déployé.
6. DNS public non configuré.
7. HTTPS public non configuré.

## Décision proposée

La VM `forge-web` et Caddy sont validés pour une phase de déploiement LAN contrôlé.

Ne pas modifier DNS ni HTTPS maintenant.

Prochaine étape : préparer une procédure reproductible pour copier le contenu local `dist/` vers `/srv/forge-web/current`.

## Limites restantes

- Test HTTP depuis un poste LAN externe à confirmer si nécessaire.
- Firewall local à définir plus tard.
- HTTPS public non testé.
- DNS non configuré.
- Pas encore de stratégie de rollback.
- Pas encore de logs/statistiques Caddy.

## Prochain ticket recommandé

`FW-DEPLOY-PREP-001 — Préparer le déploiement contrôlé vers la VM forge-web`

Puis :

- `FW-DEPLOY-GO-001`
- `FW-DNS-WEB-001`
- `FW-ACCESS-LOGS-STATS-001`
