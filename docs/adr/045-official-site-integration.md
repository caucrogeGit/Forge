# ADR-045 : Intégrer la publication du site officiel dans Forge

## Statut

Proposé — bêta publique 1.0 (`1.0.0-beta.x`).

---

## Date

2026-06-23

---

## Contexte

La documentation publique de Forge (forgemvc.com) est aujourd'hui publiée par
**deux** chaînes distinctes :

1. **GitHub Pages** — `.github/workflows/pages.yml` : à chaque push sur `main`,
   la CI exécute `mkdocs build --strict` et publie `site/`. Entièrement dans le
   dépôt `forge`, automatique.

2. **VM forge-web** (`forgemvc.com` auto-hébergé) — via un dépôt **séparé**,
   `Forge-official-site`. Ce dépôt :
   - **importe** la documentation de Forge dans `docs/forge/`
     (`scripts/import_forge_docs.py`, liste blanche) ;
   - ajoute du contenu propre (landing `public/`, `robots.txt`, `sitemap.xml`,
     un runbook d'exploitation, une doc secrets, et l'historique d'audits
     `FW-*` de la mise en place de la VM) ;
   - **assemble** un `dist/` (landing à `/`, site MkDocs sous `/docs/`) ;
   - **déploie** par `rsync` vers `roger@192.168.1.98:/srv/forge-web/`
     (staging distant, backups datés, lock, `DRY_RUN=1` par défaut).

Cette seconde chaîne est un **intermédiaire** : la documentation doit être
importée d'un dépôt vers l'autre avant publication, ce qui crée un risque de
dérive (le site peut retarder sur la doc canonique) et une charge manuelle.
L'audit beta12 garde aussi la trace d'un `rsync` lancé **par erreur** depuis
`~/Projets/Forge`, qui a failli écraser la VM.

L'ADR-044 a fait de `docs/` (landing canonique incluse) la **source unique**
de la documentation. L'import depuis `forge` vers `Forge-official-site` n'a
donc plus de raison d'être : la source est déjà dans `forge`.

---

## Décision

1. **Décommissionner `Forge-official-site`.** Sa fonction de publication est
   rapatriée dans `forge`. Le dépôt séparé est abandonné (l'import
   `import_forge_docs.py` disparaît : `forge` est la source).

2. **forgemvc.com sert directement le site MkDocs de Forge.** Le `site/`
   produit par `mkdocs build --strict` est servi tel quel à la racine du
   domaine. La landing (`docs/index.html`, ADR-044) est l'accueil ; les pages
   de doc sont servies à `/install/`, `/reference/`, etc. Il n'y a **plus
   d'assemblage** (`build-site.sh`) ni de préfixe `/docs/`.

   Conséquence : les URLs changent (la doc quitte `/docs/forge/…` pour `/…`).
   Des **redirections** des anciennes URLs clés sont posées côté serveur
   (Caddy/Nginx sur la VM) ; `site_url` de `mkdocs.yml` est fixé pour que le
   `sitemap.xml` (généré par MkDocs) porte les URLs canoniques.

3. **Un dossier `official-site/` porte l'outillage de publication.** Il
   contient, hors du site publié :
   - le script de déploiement (`mkdocs build --strict` puis `rsync` de `site/`
     vers la VM), avec staging distant, backups datés, lock et **`DRY_RUN=1`
     par défaut** (repris de `deploy-to-forge-web.sh`) ;
   - le `robots.txt` et tout réglage SEO non géré par MkDocs ;
   - le runbook d'exploitation et la doc de gestion des secrets (adaptés) ;
   - l'historique d'audits `FW-*` de forge-web, en archive brute.

   `official-site/` **n'est pas** inclus dans le site MkDocs (`docs_dir` reste
   `docs/`) : c'est de l'outillage et de la mémoire d'exploitation, pas de la
   documentation du framework.

4. **Deux voies de publication.** Conformément au besoin :
   - **Script local** `official-site/deploy.sh` : `DRY_RUN=1` par défaut,
     confirmation explicite obligatoire pour le mode réel, jamais de cible VM
     par défaut silencieuse (anti-récidive de l'incident beta12) ;
   - **Workflow CI** `deploy-forge-web.yml` : `workflow_dispatch` manuel,
     clé SSH en **secret CI**, `environment` GitHub protégé.

5. **Aucun secret committé.** Accès SSH, identifiants VM et clés vivent dans
   les secrets CI ou la configuration locale ignorée par `.gitignore`, jamais
   dans le dépôt.

---

## Conséquences

### Positives

- Source unique : la doc publiée est toujours la doc canonique de `forge`,
  sans import ni dérive possible.
- Un dépôt de moins à maintenir et à synchroniser.
- Publication facilitée : un script (ou un clic CI) build + déploie.
- Le footgun `rsync` est encadré : `DRY_RUN` par défaut, confirmation
  explicite, voie CI privilégiée.

### Limites

- **Rupture d'URL** : la doc passe de `/docs/forge/…` à `/…`. Nécessite des
  redirections serveur pour préserver le SEO et les liens entrants ; à auditer
  et poser au déploiement.
- `forge` gagne un dossier d'outillage d'exploitation (`official-site/`) :
  c'est du release/ops pour le site **du framework lui-même**, pas une
  application métier (cohérent avec ADR-044), mais à garder clairement cantonné.
- La VM et ses accès restent hors dépôt : la CI doit porter les secrets.

---

## Alternatives écartées

### A — Garder le dépôt `Forge-official-site` séparé

Statu quo. Rejeté : c'est précisément l'intermédiaire (import + dérive +
charge manuelle) que cette décision supprime.

### B — Conserver la structure landing `/` + docs `/docs/`

Reproduire l'assemblage (`build-site.sh`) dans `forge` pour garder les URLs
actuelles. Rejeté (décision 2) : maintient une étape d'assemblage et un
préfixe `/docs/` artificiel alors que le `site/` de MkDocs se sert directement.
Le coût est une rupture d'URL, traitée par redirections.

### C — Publier uniquement via GitHub Pages

Abandonner la VM forge-web au profit de GitHub Pages seul. Hors périmètre :
la VM (domaine, Caddy/Nginx, contrôle d'hébergement) est un choix
d'infrastructure distinct, non tranché ici.

---

## Hors périmètre de cet ADR

- Le détail des redirections d'URL (inventaire des anciennes URLs, règles
  Caddy/Nginx) : à traiter à l'implémentation du déploiement.
- La configuration serveur de la VM (Caddy/Nginx, TLS) : vit sur la VM, pas
  dans le dépôt.
- Le sort de `pages.yml` (GitHub Pages) : conservé tel quel pour l'instant
  (miroir), sa coexistence avec forge-web sera réévaluée séparément.

---

## Référence

- ADR-043 Documentation embarquée cœur/CLI : `docs/adr/043-core-cli-doc-embedding.md`.
- ADR-044 Le dépôt ne porte que le framework : `docs/adr/044-framework-only-repo.md`.
- Workflow Pages existant : `.github/workflows/pages.yml`.
- Dépôt décommissionné : `Forge-official-site` (scripts `build-site.sh`,
  `import_forge_docs.py`, `deploy-to-forge-web.sh`, `sync-forge-docs-and-deploy.sh`).
- Charte : `CHARTE_DOC.md` (principes 1, 11).
