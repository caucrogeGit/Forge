# official-site — publication de forgemvc.com

> **Intégré dans Forge (ADR-045).** Ce dossier est l'ancien dépôt
> `Forge-official-site` rapatrié dans le dépôt `forge`. La doc n'est plus
> importée d'un dépôt à l'autre : `import_forge_docs.py` lit désormais la doc
> canonique **locale** (`../docs`) et `official-site/docs/forge/` est un
> artefact de build non versionné. Publier :
> `bash official-site/scripts/sync-forge-docs-and-deploy.sh` (DRY_RUN par
> défaut), ou le workflow CI `.github/workflows/deploy-forge-web.yml`.
>
> **Statut connu (à régler avant le 1er déploiement réel post-intégration)** :
> `scripts/build-site.sh` lance `mkdocs build --strict` ; sur les docs Forge
> actuelles, des liens absolus `/docs/forge/…` (ex. `docs/testing/tickets/`,
> ajoutées depuis le dernier déploiement beta12) font échouer le mode strict.
> À traiter : corriger ces liens dans `docs/`, ajuster l'import, ou assouplir
> le strict. Sans rapport avec la santé du dépôt `forge` (sa propre build
> `mkdocs --strict` passe).

Site officiel du framework Forge.

Objectif du projet :

- publier https://forgemvc.com ;
- héberger la landing page publique ;
- héberger la documentation Forge générée avec MkDocs ;
- préparer un déploiement statique simple ;
- garder ce projet séparé du framework Forge.

## Périmètre

Ce dépôt concerne uniquement Forge-official-site :

- landing page ;
- documentation publique ;
- génération statique ;
- notes d'infrastructure ;
- scripts de build et de déploiement.

Ce dépôt ne doit pas modifier le cœur du framework Forge.

## Structure initiale

- landing/ : source de la landing page statique ;
- docs/ : documentation publique ou sources MkDocs ;
- site/ : site généré, non versionné ;
- infra/ : notes et fichiers d'infrastructure sans secrets ;
- notes/ : notes de travail du projet ;
- scripts/ : scripts locaux de génération ou déploiement.

## Décision initiale

Le site sera statique dans un premier temps.

MkDocs servira à générer la documentation.

Le reverse proxy et HTTPS seront traités plus tard, probablement avec Caddy.

Proxmox ne doit jamais être exposé directement au public.