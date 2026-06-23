# Rapport final — FW-DEPLOY-PREP-001

## Résumé

Le déploiement contrôlé vers la VM `forge-web` a été préparé sans remplacer le site actuellement servi par Caddy.

Le script `scripts/deploy-to-forge-web.sh` a été créé. Il permet de copier le contenu local `dist/` vers un dossier de staging distant, avec un mode dry-run actif par défaut.

Aucun fichier de `/srv/forge-web/current` n’a été remplacé dans ce ticket.

## Machines concernées

Machine locale :

- hostname : `devstation`
- projet : `/home/roger/Projets/Forge-web`
- rôle : génération du site, préparation du script, contrôle Git

Machine distante :

- hostname : `forge-web`
- IP : `192.168.1.98`
- utilisateur SSH : `roger`
- rôle : cible future de publication LAN

Proxmox :

- non concerné dans ce ticket

## Build local

Le dossier `dist/` existe et contient le site Forge-web généré :

- `dist/index.html`
- `dist/docs/index.html`

Le dry-run rsync a estimé la taille totale du site à envoyer à environ `26,2 Mo`.

## Accès SSH

L’accès SSH par clé depuis `devstation` vers `forge-web` est fonctionnel.

Commande validée :

- `ssh roger@192.168.1.98 'hostname && whoami'`

Résultat :

- hostname : `forge-web`
- utilisateur : `roger`

## Rsync local et distant

`rsync` est présent côté local :

- `/usr/bin/rsync`

`rsync` est présent côté distant :

- `/usr/bin/rsync`

Les dossiers distants existent :

- `/srv/forge-web`
- `/srv/forge-web/current`

Ils appartiennent à `root:root`, ce qui impose une procédure contrôlée pour le remplacement final.

## Script de déploiement préparé

Script créé :

- `scripts/deploy-to-forge-web.sh`

Comportement :

- utilise `set -euo pipefail`
- cible par défaut : `roger@192.168.1.98`
- staging distant par défaut : `/tmp/forge-web-deploy-staging`
- mode dry-run par défaut : `DRY_RUN=1`
- vérifie que `dist/index.html` existe
- vérifie que `dist/docs/index.html` existe
- copie uniquement vers le staging distant
- ne remplace jamais `/srv/forge-web/current`

## Test dry-run

Commande exécutée :

- `DRY_RUN=1 scripts/deploy-to-forge-web.sh`

Résultat :

- rsync fonctionne
- SSH fonctionne
- la liste des fichiers à copier est affichée
- aucun fichier n’est réellement copié
- `/srv/forge-web/current` n’est pas modifié

Le dry-run annonce notamment :

- `index.html`
- `robots.txt`
- `sitemap.xml`
- `docs/`
- `static/`
- documentation Forge générée
- assets MkDocs
- assets landing

Taille totale annoncée :

- `26.247.914` octets

## État de la VM après préparation

Caddy sert toujours la page placeholder :

- URL : `http://192.168.1.98`
- statut : `HTTP/1.1 200 OK`
- taille : `257` octets
- titre : `Forge-web — test local`

Fichier encore servi :

- `/srv/forge-web/current/index.html`

Taille confirmée :

- `257` octets

Le staging distant existe mais reste vide après dry-run :

- `/tmp/forge-web-deploy-staging`

C’est normal : le script crée le dossier avant d’exécuter rsync en mode simulation.

## Risques identifiés

1. `/srv/forge-web/current` appartient à `root:root`, donc le remplacement réel nécessitera `sudo`.
2. Le script actuel ne fait que préparer le staging, il ne publie pas encore.
3. Il faudra sauvegarder la page placeholder avant remplacement.
4. Il faudra vérifier le contenu du staging avant bascule.
5. Le déploiement public HTTPS/DNS reste hors périmètre.
6. Le firewall local n’est pas encore traité.
7. Les logs/statistiques ne sont pas encore configurés.

## Limites restantes

- Aucun déploiement réel effectué.
- Aucun remplacement de `/srv/forge-web/current`.
- Aucun changement Caddy.
- Aucun changement DNS.
- Aucun HTTPS public.
- Aucun firewall modifié.
- Pas encore de rollback automatisé.

## Décision proposée

La préparation est validée.

Le prochain ticket peut effectuer le déploiement LAN réel, à condition de :

1. relancer le build local ;
2. copier réellement `dist/` vers le staging distant ;
3. vérifier le staging ;
4. sauvegarder le placeholder actuel ;
5. remplacer `/srv/forge-web/current` de manière contrôlée ;
6. vérifier `http://192.168.1.98/` et `/docs/`.

## Prochain ticket recommandé

`FW-DEPLOY-GO-001 — Déployer Forge-web sur la VM forge-web en LAN`

Ce ticket devra remplacer réellement `/srv/forge-web/current` après sauvegarde et vérification du staging.
