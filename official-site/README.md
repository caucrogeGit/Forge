# official-site — publication de forgemvc.com (ADR-045)

Ce dossier porte **l'outillage de publication** du site officiel
[forgemvc.com](https://forgemvc.com). Il a remplacé le dépôt séparé
`Forge-official-site` (décommissionné, ADR-045) : la documentation n'est plus
importée d'un dépôt à l'autre, elle est publiée **directement depuis ce dépôt**.

Ce dossier **n'est pas** de la documentation du framework : il n'est pas inclus
dans le site MkDocs (`docs_dir` reste `docs/`). C'est de l'outillage et de la
mémoire d'exploitation.

## Ce qui est publié

`forgemvc.com` sert **directement** le `site/` produit par `mkdocs build` :

- `/` — la landing (`docs/index.html`, canonique depuis l'ADR-044) ;
- `/install/`, `/reference/`, … — les pages de documentation ;
- `/sitemap.xml` et `/robots.txt` — générés/copiés par MkDocs.

Il n'y a **plus** de préfixe `/docs/` ni d'assemblage : la source est `docs/`.

## Déployer

Le script construit le site (`mkdocs build --strict`) puis le pousse sur la VM
forge-web par `rsync`, avec backup daté et bascule via un staging vérifié.

```bash
# Aperçu sans rien écrire sur la VM (DRY_RUN=1 par défaut) :
bash official-site/deploy.sh

# Déploiement réel (demande une confirmation interactive « DEPLOY ») :
DRY_RUN=0 bash official-site/deploy.sh
```

Sécurité (anti-incident de déploiement) : `DRY_RUN=1` par défaut, confirmation
explicite obligatoire en mode réel, backup distant daté avant toute bascule.
Voir aussi le workflow CI `.github/workflows/deploy-forge-web.yml` (publication
déclenchée à la main, clé SSH en secret).

Variables surchargeables : `REMOTE_HOST`, `REMOTE_CURRENT`, `REMOTE_BACKUPS`,
`REMOTE_STAGE`. Les accès SSH/secrets ne sont **jamais** committés.

## Redirections d'URL (rupture héritée)

L'ancien site servait la doc sous `/docs/forge/…`. Désormais elle est à la
racine (`/…`). Des redirections `301` des anciennes URLs vers les nouvelles
sont à poser **côté serveur** (Caddy/Nginx sur la VM) pour préserver le SEO et
les liens entrants. Cette configuration vit sur la VM, hors dépôt.

## history/

`history/` archive la mémoire d'exploitation héritée de `Forge-official-site`
(runbook, audits `FW-*`, gestion des secrets, préparation au déploiement).
Ces documents décrivent l'ancien flux (import + structure `/docs/`) et sont
conservés **à titre d'archive** ; ils ne décrivent plus le fonctionnement
courant, qui est celui de ce README et de l'ADR-045.
