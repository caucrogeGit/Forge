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
de la documentation. L'import inter-dépôts n'a donc plus lieu d'être : en
rapatriant l'outillage dans `forge`, l'import devient une simple copie
**locale** (`docs/` → `official-site/docs/forge/` au build), sans dépôt
intermédiaire ni dérive possible.

---

## Décision

1. **Décommissionner `Forge-official-site` ; sa fonction de publication est
   rapatriée dans `forge`, sous `official-site/`, réduite à un tuyau.** Le
   dépôt séparé est abandonné. `official-site/` conserve : les scripts de
   build/déploiement (`build-site.sh`, `deploy-to-forge-web.sh`,
   `sync-forge-docs-and-deploy.sh`, validateurs `check_*`, `audit-secrets.sh`),
   `public/` (`robots.txt`, `sitemap.xml`), `infra/`, et la mémoire
   d'exploitation (`docs/` propre : runbook, audits `FW-*`, doc secrets, en
   archive non publiée).

2. **`official-site` construit avec le `mkdocs.yml` CANONIQUE de Forge — plus
   d'import ni de nav propre.** `build-site.sh` lance `mkdocs build --strict`
   sur `forge/mkdocs.yml` (qui agrège déjà `docs/` + les docs « par module »
   d'ADR-043 via `!include`, et passe `--strict`). Sont **supprimés**
   `official-site/mkdocs.yml` et `import_forge_docs.py` : ils dupliquaient la
   nav et la structure de Forge et **dérivaient** (nav figée pointant dans le
   vide, docs de module manquantes). La doc a une **source unique** (`docs/`),
   sans copie ni synchronisation.

3. **La structure publique de forgemvc.com est conservée.** `build-site.sh`
   assemble la landing canonique (`docs/index.html`) à `/`, et le site MkDocs
   de Forge sous `/docs/forge/`. **Aucune rupture d'URL** ; les docs « par
   module » sont incluses (elles viennent du `mkdocs.yml` de Forge).

4. **`official-site/` n'est pas inclus dans le site MkDocs du framework.**
   Le `docs_dir` de `forge` reste `docs/` ; `official-site/` est de
   l'outillage et de la mémoire d'exploitation, exclu des scans documentaires
   (par ex. garde-fou des versions périmées).

5. **Deux voies de publication, `DRY_RUN=1` par défaut.**
   - **Script local** : `bash official-site/scripts/sync-forge-docs-and-deploy.sh`
     (dry-run par défaut ; `DRY_RUN=0` pour le réel). Build (mkdocs de Forge) →
     validations → `rsync` vers la VM avec backup daté, staging vérifié,
     bascule contrôlée et lock (anti-récidive de l'incident beta12).
   - **Workflow CI** `deploy-forge-web.yml` : `workflow_dispatch` manuel,
     runner self-hosted sur le réseau de la VM (IP privée), secrets SSH.

6. **Aucun secret committé.** Accès SSH, identifiants VM et clés vivent dans
   les secrets CI ou la configuration locale ignorée par `.gitignore`.

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

- **Aucune rupture d'URL** (la structure `/docs/forge/…` est conservée), au
  prix d'une étape d'assemblage (`build-site.sh`) qui imbrique le site MkDocs
  de Forge sous `/docs/forge/` et pose la landing à `/`. Pas de second
  `mkdocs.yml` : on réutilise celui de Forge.
- `forge` gagne un dossier d'outillage d'exploitation (`official-site/`) :
  c'est du release/ops pour le site **du framework lui-même**, pas une
  application métier (cohérent avec ADR-044), mais à garder clairement cantonné.
- La VM et ses accès restent hors dépôt : la CI doit porter les secrets.

---

## Alternatives écartées

### A — Garder le dépôt `Forge-official-site` séparé

Statu quo. Rejeté : c'est précisément l'intermédiaire (import inter-dépôts +
dérive + charge manuelle) que cette décision supprime.

### B — Servir le site MkDocs de `forge` directement à la racine

Abandonner l'assemblage et le préfixe `/docs/`, servir le `site/` de la build
`forge` tel quel. Rejeté : casse les URLs publiques existantes (`/docs/forge/…`
→ `/…`), impose des redirections SEO, et jette une machinerie de publication
déjà éprouvée. Le rapatriement fidèle (décision 1) préserve l'acquis sans
rupture.

### C — Publier uniquement via GitHub Pages

Abandonner la VM forge-web au profit de GitHub Pages seul. Hors périmètre :
la VM (domaine, Caddy/Nginx, contrôle d'hébergement) est un choix
d'infrastructure distinct, non tranché ici.

---

## Hors périmètre de cet ADR

- La configuration serveur de la VM (Caddy/Nginx, TLS, racine servie) : vit
  sur la VM, pas dans le dépôt. La structure d'URL `/docs/` étant conservée,
  aucune redirection n'est requise.
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
