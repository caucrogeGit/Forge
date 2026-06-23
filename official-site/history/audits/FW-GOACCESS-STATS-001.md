# Rapport final — FW-GOACCESS-STATS-001

## Résumé

GoAccess a été installé et validé sur la VM `forge-web` pour produire des statistiques locales à partir des logs Caddy.

Aucun tracker JavaScript, aucun cookie, aucun Google Analytics et aucune publication publique des statistiques n’ont été ajoutés.

## Installation

GoAccess installé via `apt` sur la VM `forge-web`.

Version validée : `GoAccess 1.9.3`.

## Logs source

Log Caddy source :

`/var/log/caddy/forge-web-access-json.log`

Le format JSON Caddy natif n’a pas été directement accepté par GoAccess avec `--log-format=CADDY`.

Erreur observée : `IPv4/6 is required`.

## Solution retenue

Un convertisseur local JSON Caddy vers format Combined a été créé sur la VM :

`/home/roger/bin/forge_web_caddy_json_to_combined.py`

Un script de génération a été créé :

`/home/roger/bin/forge-web-generate-stats.sh`

Il produit :

`/home/roger/forge-web-stats/forge-web-goaccess.html`

## Validation

Le script a été contrôlé :

- contenu vérifié ;
- `bash -n` OK ;
- exécution OK ;
- rapport HTML généré ;
- taille du rapport : environ 695K.

## Non-publication

Le rapport GoAccess n’est pas publié dans le site web.

Vérifications OK :

- pas de `/srv/forge-web/current/forge-web-goaccess.html` ;
- pas de `/srv/forge-web/current/stats`.

## Vie privée

Décision maintenue :

- pas de Google Analytics ;
- pas de Matomo ;
- pas de tracker JavaScript ;
- pas de cookie de tracking ;
- pas de bannière RGPD inutile à ce stade.

Les statistiques restent basées uniquement sur les logs serveur.

## Limites restantes

- Rapport GoAccess généré manuellement, pas encore automatisé.
- Rapport non accessible depuis un navigateur distant.
- Pas encore de tâche cron.
- Pas encore d’accès protégé à une page stats.

## Hors périmètre respecté

- Aucun DNS modifié.
- Aucun Cloudflare proxy orange activé.
- Aucun fichier stats publié publiquement.
- Aucun changement Proxmox.
- Aucun mail configuré.

## Décision

`FW-GOACCESS-STATS-001` est validé.

Forge-web dispose maintenant de statistiques locales non publiques générées avec GoAccess.

## Prochain ticket recommandé

`FW-FINAL-PUBLISH-AUDIT-001 — Audit final de publication Forge-web`.
