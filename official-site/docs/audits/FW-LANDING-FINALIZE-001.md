# Rapport final — FW-LANDING-FINALIZE-001

> Date : 2026-05-23
> Branche : `main`
> Périmètre exécuté : strictement celui du ticket. Aucune modification de Forge core. Aucun déploiement. Aucun changement DNS / Caddy / Proxmox.

---

## Résumé

La landing publique est finalisée pour la stratégie `/` (landing) + `/docs/` (documentation). 41 liens documentation et 1 action de recherche ont été réécrits pour pointer vers les chemins MkDocs réels (`/docs/forge/…` et `/docs/search/`). Aucun lien `github.io` ne subsiste.

Un script de build unique [`scripts/build-site.sh`](#script-de-build) assemble la landing (`public/`) et le site MkDocs (`site/`) dans un dossier de sortie `dist/` prêt à servir. Le build passe ; un serveur HTTP statique local sert correctement `/`, `/docs/`, `/docs/forge/`, `/docs/forge/installation/`, `/docs/forge/concepts/`, `/docs/search/`, plus tous les assets `/static/...`.

Une modification incidente : deux liens cassés dans [docs/audits/FW-DOCS-IMPORT-001.md](FW-DOCS-IMPORT-001.md) (pointant vers `../../scripts/import_forge_docs.py` et `../../mkdocs.yml`, hors `docs_dir`) ont été convertis en inline code pour préserver `mkdocs build --strict` à zéro warning.

Aucun commit n'a été créé.

---

## Décision de publication

| Route HTTP | Contenu servi | Source |
|---|---|---|
| `/` | Landing page officielle Forge | `public/index.html` |
| `/static/...` | Assets de la landing (CSS, images, JS) | `public/static/...` |
| `/docs/` | Accueil de la documentation MkDocs (Forge-web) | `docs/index.md` → MkDocs |
| `/docs/forge/` | Accueil de la documentation Forge | `docs/forge/index.md` → MkDocs |
| `/docs/forge/<page>/` | Pages individuelles Forge | `docs/forge/<page>.md` → MkDocs |
| `/docs/meta/<page>/` | Doc interne Forge-web | `docs/meta/<page>.md` → MkDocs |
| `/docs/audits/<rapport>/` | Rapports d'audit | `docs/audits/<rapport>.md` → MkDocs |
| `/docs/search/` | Recherche MkDocs Material | générée par MkDocs |

Décision actée : **landing à la racine + documentation sous `/docs/`**. Pas de sous-domaine séparé (`docs.forgemvc.com`) — choix justifié par la simplicité du déploiement statique et un seul certificat HTTPS à gérer.

`site_url` dans `mkdocs.yml` reste `https://forgemvc.com/` (la valeur fixée par FW-MKDOCS-INIT-001 est compatible — MkDocs sait gérer un sous-chemin `/docs/` au moment de l'assemblage, et le script de build place le résultat au bon endroit).

---

## Fichiers modifiés

| Fichier | Nature | Justification |
|---|---|---|
| `public/index.html` | 41 réécritures `href="./docs/...` → `href="/docs/forge/...` + 1 réécriture `action="search/"` → `action="/docs/search/"` | Aligne la landing sur la doc importée (Forge dans `docs/forge/`) et sur la nouvelle stratégie de chemins absolus |
| `.gitignore` | Ajout de `dist/` après `site/` | Évite de versionner le dossier de sortie du build statique |
| `docs/audits/FW-DOCS-IMPORT-001.md` | 2 liens vers chemins hors `docs_dir` (`scripts/import_forge_docs.py`, `mkdocs.yml`) convertis en inline code | Nécessaire pour `mkdocs build --strict` à zéro warning |

Fichiers créés :

| Fichier | Rôle |
|---|---|
| `scripts/build-site.sh` | Assemble landing + MkDocs dans `dist/` (idempotent, `set -euo pipefail`) |
| `docs/audits/FW-LANDING-FINALIZE-001.md` | Ce rapport |

Fichiers **non** modifiés (interdits ou hors périmètre) :

- `/home/roger/Projets/Forge/` (Forge core intact — `git status` vide)
- `scripts/import_forge_docs.py` (aucun bug)
- `infra/`, `notes/`, `sources/`, `landing/` (hors périmètre)
- `mkdocs.yml` (aucun ajustement nécessaire pour ce ticket — `site_url` était déjà bon)

---

## Landing page

Inventaire de `public/index.html` après transformation :

| Catégorie de lien | Avant | Après |
|---|---|---|
| `caucrogegit.github.io/Forge/...` | 0 (déjà nettoyé en amont) | 0 |
| `./docs/...` (relatifs vers la doc) | 41 | 0 |
| `/docs/forge/...` (absolus vers Forge) | 0 | 41 |
| `action="search/"` (recherche relative cassée) | 1 | 0 |
| `action="/docs/search/"` (recherche correcte) | 0 | 1 |
| `https://github.com/caucrogeGit/Forge[.git]` | 6 | 6 (conservés — code source) |
| `https://github.com/caucrogeGit/Forge/blob/main/CHARTE_DOC.md` | 1 | 1 (conservé — charte canonique Forge core) |
| Liens PyPI / Python.org / MariaDB / Jinja / HTMX / Alpine.js / Tailwind | inchangés | inchangés |
| `href="./static/..."` (assets landing) | inchangés | inchangés (relatifs, OK à la racine) |

Volume : `public/index.html` = 795 lignes, ~53 ko.

---

## Liens corrigés

### Transformation 1 : `href="./docs/...` → `href="/docs/forge/...`

41 occurrences réécrites en une seule passe (`replace_all`). Couvre notamment :

```text
guide                           reference                      crud
roadmap/forge-roadmap           reference/crud                 reference/api
concepts                        reference/cli-commands         deployment
front                           reference/auth-mfa             api-json
migrations                      reference/workflow             installation
entity_architecture             reference/stats                installation-developpement
security                        installation-windows           starters/01-contact-simple
auth                            starters/02-utilisateurs-auth  starters/03-carnet-contacts
media                           starters/04-suivi-...          mail
15-minutes                      app-complete-tutorial          production-security
release-policy                  contributing                   rbac
```

Toutes les cibles ont été vérifiées présentes dans `docs/forge/` (import FW-DOCS-IMPORT-001).

### Transformation 2 : `action="search/"` → `action="/docs/search/"`

1 occurrence. La barre de recherche du header postait sur `forgemvc.com/search/` (cassé). Elle poste désormais sur `forgemvc.com/docs/search/` — l'interface Material générée par MkDocs.

### Liens conservés (corrects)

- 6 liens absolus vers `https://github.com/caucrogeGit/Forge[.git]` — pointent vers le dépôt source.
- 1 lien vers `https://github.com/caucrogeGit/Forge/blob/main/CHARTE_DOC.md` — la charte vit canoniquement dans Forge core, lien GitHub correct.
- Liens externes vers Python / MariaDB / Jinja / HTMX / Alpine / Tailwind / PyPI — inchangés.
- `href="./static/tailwind.css"`, `src="./static/img/forge-logo.png"` — relatifs au document racine, fonctionnent en servant la landing depuis `dist/`.

### Aucune modification côté MkDocs

Les liens internes à la doc Forge (`docs/forge/<X>.md` → autres pages Forge) n'ont pas eu besoin de modification dans ce ticket : ils avaient déjà été sanitisés en FW-DOCS-IMPORT-001 (52 fichiers réécrits pour `index.html` → `index.md`).

---

## Script de build

Fichier : `scripts/build-site.sh` (mode exécutable).

Caractéristiques :

- `set -euo pipefail` (échec strict)
- se positionne automatiquement à la racine du dépôt (`cd "$(dirname "$0")/.."`)
- active `.venv/` s'il existe (sinon attend `mkdocs` sur le `PATH`)
- vérifie la présence de `mkdocs` avant tout, sinon message d'erreur clair
- supprime entièrement `dist/` et `site/` au démarrage (build reproductible)
- copie `public/.` (landing + assets) vers `dist/`
- lance `mkdocs build --strict`
- intègre `site/.` (sortie MkDocs) sous `dist/docs/`
- affiche un bilan : nombre de fichiers et présence des 3 pages-clés (`dist/index.html`, `dist/docs/index.html`, `dist/docs/forge/index.html`)
- propose la commande d'exposition locale

Ce que le script **ne fait pas** :

- aucun déploiement distant ;
- aucune CI/CD ;
- aucun appel à Caddy / Nginx / rsync vers un serveur ;
- aucun build incrémental — toujours from-scratch (volonté de reproductibilité, durée actuelle ~9 s).

Exécution typique :

```text
==> Nettoyage de dist et site
==> Copie de la landing depuis public/
==> Génération MkDocs (mkdocs build --strict)
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /home/roger/Projets/Forge-web/site
INFO    -  Documentation built in 8.50 seconds
==> Intégration du site MkDocs sous dist/docs/

==> Bilan
  Fichiers totaux : 258
  Pages cibles :
    ok  dist/index.html
    ok  dist/docs/index.html
    ok  dist/docs/forge/index.html
```

---

## Vérifications locales

### Build

```text
mkdocs build --strict → 0 WARNING, 7 INFO non bloquants, 8.50 s
dist/ → 258 fichiers
```

### Sonde HTTP (python3 -m http.server 8080 -d dist)

| URL | HTTP | Taille | Notes |
|---|---|---|---|
| `/` | **200** | 53 386 o | landing transformée |
| `/docs/` | **200** | 20 493 o | accueil MkDocs (`docs/index.md`) |
| `/docs/forge/` | **200** | 20 357 o | accueil section Forge (`docs/forge/index.md`) |
| `/docs/forge/installation/` | **200** | 32 799 o | guide installation |
| `/docs/forge/concepts/` | **200** | 30 723 o | concepts Forge |
| `/docs/search/` | **200** | 270 o | interface Material search |
| `/static/tailwind.css` | **200** | 33 130 o | CSS landing |
| `/static/img/forge-logo.png` | **200** | 825 440 o | logo |
| `/static/js/landing.js` | **200** | 1 299 o | JS landing |
| `/nonexistent/` | **404** | – | 404 fonctionnel |

Aucune erreur côté serveur. Les chemins absolus définis dans la landing résolvent correctement quand `dist/` est servi à la racine HTTP.

### Liens critiques explicitement validés

- **Landing → docs Forge** : `/docs/forge/installation/` → HTTP 200 ✓
- **Recherche MkDocs** : `/docs/search/` → HTTP 200 ✓
- **Assets landing** : `/static/tailwind.css`, `/static/img/forge-logo.png` → HTTP 200 ✓
- **GitHub** : liens vers `github.com/caucrogeGit/Forge` (non testés côté HTTP — externes, OK structurellement)
- **PyPI** : pas de lien explicite vers `pypi.org` dans la landing, mais la mention « Disponible sur PyPI » et le nom `forge-mvc` sont conservés textuellement.

---

## État Git

```text
 M .gitignore                              (+ dist/)
 M docs/audits/FW-DOCS-IMPORT-001.md       (2 liens cassés → inline code)
 M public/index.html                        (42 réécritures de liens)
?? scripts/build-site.sh                    (nouveau)
?? docs/audits/FW-LANDING-FINALIZE-001.md   (ce rapport)
```

Vérifications négatives :

- `.claude/` : **absent** de `git status`.
- `dist/` : **ignoré** (`git check-ignore` confirme `.gitignore:9:dist/`).
- `site/` : **ignoré** (acquis avant ce ticket).
- `.venv/` : **ignoré**.
- Forge core : **intact** (`git -C /home/roger/Projets/Forge status --short` vide).

`git diff --check` = 0.

Commande de commit suggérée (à exécuter manuellement) :

```bash
git add public/index.html scripts/build-site.sh .gitignore \
        docs/audits/FW-DOCS-IMPORT-001.md \
        docs/audits/FW-LANDING-FINALIZE-001.md
git commit -m "feat(site): finalize landing + build script (FW-LANDING-FINALIZE-001)"
```

---

## Limites restantes

1. **Aucun audit exhaustif** des ~200 pages MkDocs servies — seuls les chemins critiques ont été sondés. Une vérification HTML/lien systématique (linkchecker, html-proofer, lychee) reste à faire → futur `FW-LOCAL-QA-001`.
2. **Pas de validation visuelle** : aucun screenshot, aucun test responsive mobile/desktop, aucun test d'accessibilité.
3. **`site_url` MkDocs** = `https://forgemvc.com/` au lieu de `https://forgemvc.com/docs/`. Conséquence : les balises canoniques `<link rel="canonical">` des pages MkDocs pointent vers une URL « pré-mount ». À évaluer en `FW-LOCAL-QA-001` si cela pose problème pour le SEO.
4. **Pas de réécriture des liens internes Markdown** qui pointent vers `/docs/...` absolus — mais aucun n'a été identifié comme cassé.
5. **Aucun déploiement** : `dist/` reste local. Pas de Caddyfile, pas de DNS, pas d'upload. Conformément au ticket.
6. **Pas de minification / pas d'optimisation d'assets** : la landing pèse 53 ko HTML (texte) et le logo 825 ko (PNG). Pourrait être optimisé en `FW-OPT-001` si pertinent.
7. **Pas de CI** : le build est lancé manuellement. Aucune intégration GitHub Actions configurée.
8. **`docs/.gitkeep`** subsiste alors que `docs/` n'est plus vide. Sans conséquence, sera retiré à la convenance.
9. **`landing/` (racine, créé en FW-REPO-STRUCTURE-001)** reste vide avec son `.gitkeep` — non utilisé par le build (qui consomme `public/`). À retirer/renommer dans un futur ticket de rangement.
10. **Aucun commit créé** par ce ticket.

---

## Prochain ticket recommandé

**FW-LOCAL-QA-001 — Vérifier localement le site complet Forge-web**

Pré-requis désormais satisfaits :

- `dist/` reproductible via `bash scripts/build-site.sh` ;
- landing servie à `/`, docs servies à `/docs/` ;
- nav MkDocs minimale fonctionnelle ;
- chemins absolus validés sur 9 URLs critiques.

Périmètre suggéré (à confirmer dans le ticket lui-même) :

1. Vérification exhaustive des liens internes du site complet (par exemple via `lychee dist/` ou `linkchecker http://127.0.0.1:8080`).
2. Sonde mobile/desktop : ouvrir la landing dans plusieurs viewports.
3. Vérification visuelle d'au moins une page de chaque grand groupe MkDocs (Forge, meta, audits, search).
4. Détection des images / fichiers manquants côté MkDocs (charges 404 sur la page d'accueil et 3 pages de référence).
5. Vérification de la cohérence du copyright, du logo, de la version affichée dans le footer entre landing et doc.
6. Rapport `FW-LOCAL-QA-001` listant les bugs visuels/structurels trouvés.
7. Ne **pas** corriger les bugs trouvés dans ce ticket de QA — un autre ticket les traite.
