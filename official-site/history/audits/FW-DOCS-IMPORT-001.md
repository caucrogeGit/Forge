# Rapport final — FW-DOCS-IMPORT-001

> Date : 2026-05-23
> Branche : `main`
> Périmètre exécuté : strictement celui du ticket. Forge core lu en seule lecture, jamais modifié. Aucun secret copié. Aucun code applicatif copié.

---

## Résumé

La documentation publique de Forge est désormais importée dans `docs/forge/` (200 fichiers : 196 `.md` + 4 assets `static/`) via un script Python reproductible (`scripts/import_forge_docs.py`) à liste blanche stricte.

`mkdocs build --strict` passe sans warning (7 INFO non bloquants sur des chemins shell/dossiers informatifs). La navigation MkDocs expose désormais 7 entrées de doc Forge (vue d'ensemble, installation, premiers pas, concepts, référence, déploiement, roadmap) en plus de la doc interne Forge-web et des audits.

Deux adaptations factuelles par rapport à la « liste blanche initiale proposée » du ticket :

1. Ajout de `entities/` (10 fichiers) et `security/` (2 fichiers) à la whitelist : ce sont des dossiers de **documentation publique réelle** fortement référencés par les fichiers racine ; les exclure aurait cassé une cinquantaine de liens internes sans bénéfice.
2. Ajout d'une **passe de sanitisation `index.html` → `index.md`** dans le script. Forge core utilise une landing HTML (`docs/index.html`) référencée par 52 pages Markdown ; côté Forge-web ce rôle revient à `docs/forge/index.md`. La passe rewrite localement les liens dans les `.md` importés (jamais dans la source).

Aucun commit n'a été créé par ce ticket.

---

## Source documentaire

```text
/home/roger/Projets/Forge/docs/
```

Vérifications en lecture seule au démarrage :

| Vérification | Résultat |
|---|---|
| Source existe | OK (`test -d` positif) |
| Forge core sur `main` | OK |
| Forge core working tree propre | OK (`git -C /home/roger/Projets/Forge status --short` vide) |
| Secrets `.env*`, `*.key`, `*.pem`, `*.crt` dans la source | **Aucun** |
| Volume total de la source | ~4,3 Mo |
| Fichiers `.md` racine | 47 |
| Sous-dossiers présents | 13 (`adr`, `contributing`, `entities`, `history`, `project`, `quarkdown`, `reference`, `roadmap`, `security`, `starters`, `static`, `stylesheets`, `testing`) |

Forge core est resté **strictement intact** à la fin du ticket (`git status --short` côté Forge confirme working tree vide).

---

## Script d'import

Fichier : `scripts/import_forge_docs.py` (mode exécutable, 9,4 ko).

Caractéristiques :

- Source par défaut : `/home/roger/Projets/Forge/docs/`, surchargeable via `--source`.
- Destination par défaut : `docs/forge/` (résolue par rapport au script), surchargeable via `--dest`.
- Mode `--dry-run` disponible.
- **Garde-fou « destination dans Forge-web »** (`assert_dest_within_forgeweb`) refuse tout import vers un chemin hors du dépôt.
- **Vidage contrôlé** de la destination avant import (`clear_destination`) pour garantir un état reproductible.
- **Whitelist explicite** des sous-dossiers (`WHITELISTED_SUBDIRS`).
- **Whitelist d'extensions** : `.md`, `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`, `.gif`, `.ico`.
- **Blacklist de noms** : `cert.pem`, `key.pem`, `.envrc`, et tout fichier dont le nom finit par `.env`, `.key`, `.pem`, `.crt`, `.pyc`.
- **Blacklist de dossiers** : `.git`, `.venv`, `venv`, `__pycache__`, `node_modules`, `.cache`, `site`, `core`, `mvc`, `packages`, `tests`, `env`, `secrets` (ceinture de sécurité même si la source n'en contient pas).
- **Passe de sanitisation** post-copie (`sanitize_imported_markdown`) : rewrite des liens Markdown `(…/index.html)` et `href="…/index.html"` en `index.md` équivalent.
- **Régénération de `docs/forge/index.md`** comme page d'accueil de la section.
- **Vérification finale anti-fuite** : balayage récursif de la destination ; sortie code 3 si un fichier interdit s'y trouvait, build aborté.

Ce que le script ne fait **pas** :

- pas de `rsync -a`, pas de `cp -a`, pas de `shutil.copytree` aveugle ;
- aucune écriture en dehors de `dest` ;
- aucune écriture sous `/home/roger/Projets/Forge/` (vérifiable : le script n'ouvre la source qu'en lecture).

---

## Liste blanche appliquée

Sous-dossiers de `/home/roger/Projets/Forge/docs/` autorisés :

| Sous-dossier | Inclus ? | Justification |
|---|---|---|
| `adr/` | ✅ | Décisions d'architecture publiques (ADR-001 à ADR-014) |
| `reference/` | ✅ | Référence API/CLI/modules officiels |
| `starters/` | ✅ | Documentation des starters publics |
| `contributing/` | ✅ | Conventions de contribution publiques |
| `roadmap/` | ✅ | Roadmaps Forge, Design, Field test |
| `history/` | ✅ | Releases, audits archivés, historique |
| `testing/` | ✅ | Documentation des tests terrain |
| `entities/` | ✅ (ajouté) | Doc publique des entités (10 fichiers) référencée 50× par les .md racine |
| `security/` | ✅ (ajouté) | Doc RBAC publique (2 fichiers) |
| `static/` | ✅ | Assets (images, favicon) |
| `project/` | ❌ | 1 fichier (`github-repository-settings.md`) — interne au dépôt Forge |
| `stylesheets/` | ❌ | `extra.css` non utilisé par `mkdocs.yml` de Forge-web (à ajouter si on importe le hook MkDocs version) |
| `quarkdown/` | ❌ | 1 fichier expérimental, hors périmètre publication |

Extensions de fichiers autorisées : `.md`, `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`, `.gif`, `.ico`.

Extensions ignorées (silencieusement) : `.css`, `.js` (4 fichiers ignorés dans `static/` : `tailwind.css`, `src/input.css`, `js/app.js`, `js/landing.js`). Justification : Forge-web a sa propre toolchain Tailwind côté landing (`public/static/`) et n'a pas besoin de réimporter les assets de la doc Forge core ; en revanche les favicons/logos SVG/PNG sont conservés.

---

## Fichiers importés

Total : **200 fichiers** dans `docs/forge/` (en plus de `docs/forge/index.md` régénéré).

| Origine | Comptés | Notes |
|---|---|---|
| `*.md` racine | 47 | tous les guides, références, politiques, etc. |
| `adr/` | 14 | ADR-001 à ADR-014 |
| `reference/` | 12 | CLI, API, modules, sessions, RBAC… |
| `starters/` | 14 | 7 starters × index + rebuild |
| `contributing/` | 1 | conventions |
| `roadmap/` | 4 | Forge, Design, Field test, contrats JSON Schema |
| `history/` | 76 | audits/releases/historique |
| `testing/` | 15 | tests terrain + tickets FT |
| `entities/` | 10 | JSON canonique, schémas, types |
| `security/` | 2 | rbac-contract, rbac-usage |
| `static/` | 4 | favicon.ico, favicon.svg, logo PNG, etc. (images uniquement) |

Bilan exécuté par le script :

```text
Markdown racine importés : 47
Sous-dossiers :
  - adr            OK     copiés=  14 ignorés=   0
  - reference      OK     copiés=  12 ignorés=   0
  - starters       OK     copiés=  14 ignorés=   0
  - contributing   OK     copiés=   1 ignorés=   0
  - roadmap        OK     copiés=   4 ignorés=   0
  - history        OK     copiés=  76 ignorés=   0
  - testing        OK     copiés=  15 ignorés=   0
  - entities       OK     copiés=  10 ignorés=   0
  - security       OK     copiés=   2 ignorés=   0
  - static         OK     copiés=   4 ignorés=   4
Sanitisation index.html → index.md : 52 fichiers réécrits.
Total : 47 .md racine + 152 dans sous-dossiers (4 ignorés, 0 fuite).
```

---

## Fichiers exclus

### Dossiers refusés (par whitelist)

- `/home/roger/Projets/Forge/docs/project/` (1 fichier — interne au dépôt)
- `/home/roger/Projets/Forge/docs/stylesheets/` (1 fichier — non utilisé)
- `/home/roger/Projets/Forge/docs/quarkdown/` (1 fichier — expérimental)
- `/home/roger/Projets/Forge/docs/index.html` (landing Forge core — Forge-web utilise `public/index.html` séparément, déjà transformée)

### Fichiers refusés par extension (dans `static/` whitelisté)

- `static/tailwind.css`
- `static/src/input.css`
- `static/js/app.js`
- `static/js/landing.js`

### Catégories absolument exclues (vérifiées absentes de l'import)

- Code applicatif Forge : `core/`, `mvc/`, `packages/`, `tests/`, `forge_cli/`, `integrations/`, `schemas/`, `forge.py`, `app.py`, etc.
- Artefacts : `node_modules/`, `__pycache__/`, `.venv/`, `forge_mvc.egg-info/`
- Métadonnées : `.git/`, `.github/`, `.vscode/`, `.kilo/`, `.codex`
- Configuration build : `pyproject.toml`, `package.json`, `mkdocs.yml` (Forge-web a le sien), `requirements*.txt`
- Secrets / clés : `cert.pem`, `key.pem`, tout `*.env`, `*.key`, `*.crt`
- Hook MkDocs : `tools/mkdocs_version_hook.py` (non importé ; le `mkdocs.yml` de Forge-web n'a pas de section `hooks`)

---

## Modifications MkDocs

`mkdocs.yml` — section `nav` enrichie :

```diff
 nav:
   - Accueil: index.md
-  - Forge:
+  - Documentation Forge:
       - Vue d'ensemble: forge/index.md
+      - Installation: forge/installation.md
+      - Premiers pas: forge/getting-started.md
+      - Concepts: forge/concepts.md
+      - Référence: forge/reference.md
+      - Déploiement: forge/deployment.md
+      - Roadmap: forge/roadmap/forge-roadmap.md
   - Projet Forge-web:
       - Architecture générale: meta/01-architecture-generale-forge-web.md
       - Création du dépôt: meta/02-creation-depot-forge-web.md
   - Audits:
       - FW-AUDIT-EXISTING-001: audits/FW-AUDIT-EXISTING-001.md
       - FW-REPO-STRUCTURE-001: audits/FW-REPO-STRUCTURE-001.md
+      - FW-MKDOCS-INIT-001: audits/FW-MKDOCS-INIT-001.md
```

Tous les fichiers ajoutés dans la nav ont été vérifiés existants avant insertion.

Note : la nav ne couvre **pas encore l'intégralité** des 196 pages importées (volontairement, conformément au ticket : « Ne pas essayer de tout ranger parfaitement dans ce ticket. »). MkDocs Material affiche les pages absentes de la nav comme « accessibles uniquement par lien direct », ce qui suffit pour FW-DOCS-IMPORT-001. Un futur ticket d'organisation éditoriale (`FW-NAV-COMPLETE-XXX`) pourra structurer finement la nav.

`docs/forge/index.md` a été régénéré par le script avec un contenu adapté à Forge-web (signale la source canonique et l'absence d'édition directe).

---

## Corrections de liens

### Sanitisation automatique (script, post-copie)

52 fichiers Markdown réécrits par `sanitize_imported_markdown` :

- Pattern Markdown : `[texte](…/index.html#?)` → `[texte](…/index.md#?)`
- Pattern HTML : `href="…/index.html"` / `src="…/index.html"` → `href="…/index.md"`

Justification : Forge core publie sa doc avec une landing `index.html` à la racine de `docs/`. Côté Forge-web, le rôle « accueil de la section Forge » est tenu par `docs/forge/index.md` (régénéré par le script). MkDocs résout les liens internes vers `index.md`, pas `index.html`.

La sanitisation est **idempotente** (rejouer le script ne change rien si la source est inchangée) et **localisée** : elle ne touche que les fichiers copiés dans `dest`, jamais la source.

### Corrections manuelles côté Forge-web

Aucune correction manuelle n'a été nécessaire. La whitelist étendue (avec `entities/` + `security/`) et la sanitisation automatique ont suffi à éliminer les 53 warnings initiaux du premier build.

### Corrections côté Forge

**Aucune.** Forge core n'a pas été modifié. `git -C /home/roger/Projets/Forge status --short` retourne une sortie vide en fin de ticket.

---

## Vérifications sécurité

| Vérification | Commande | Résultat |
|---|---|---|
| Aucune fuite par nom de fichier | `find docs/forge -type f \( -name '.env*' -o -name 'cert.pem' -o -name 'key.pem' -o -name '*.key' -o -name '*.pem' -o -name '*.crt' \)` | **vide** (rien) |
| Aucun dossier exclu importé | `find docs/forge -type d \| grep -E '(^\|/)(core\|mvc\|packages\|tests\|env)(/\|$)'` | **vide** (rien) |
| Garde-fou final du script | balayage interne `sanitize_imported_markdown` puis vérif fuite | **0 fuite signalée** |
| Forge core intact | `git -C /home/roger/Projets/Forge status --short` | **vide** |

---

## Vérifications MkDocs

### `mkdocs build --strict`

```text
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /home/roger/Projets/Forge-web/site
INFO    -  Doc file 'audits/FW-AUDIT-EXISTING-001.md' contains an unrecognized relative link '../../../Forge/', it was left as is.
INFO    -  Doc file 'audits/FW-AUDIT-EXISTING-001.md' contains an unrecognized relative link '../../../Forge/docs/', it was left as is.
INFO    -  Doc file 'audits/FW-AUDIT-EXISTING-001.md' contains an unrecognized relative link '../../', it was left as is.
INFO    -  Doc file 'audits/FW-AUDIT-EXISTING-001.md' contains an unrecognized relative link '.', it was left as is.
INFO    -  Doc file 'forge/reference.md' contains an unrecognized relative link 'adr/', it was left as is.
INFO    -  Doc file 'forge/starters/welcome/index.md' contains an unrecognized relative link '../01-contact-simple/', it was left as is.
INFO    -  Doc file 'forge/starters/welcome/index.md' contains an unrecognized relative link '../', it was left as is.
INFO    -  Documentation built in 8.43 seconds
```

**0 WARNING** (7 INFO non bloquants pour `--strict`).

Les 7 INFO concernent des liens vers des **dossiers** (et non des fichiers), que MkDocs ne sait pas résoudre mais laisse passer. Elles n'affectent ni le build ni l'expérience utilisateur (le serveur HTTP résout naturellement les URLs de dossier si un `index.html` est présent).

### Build artifact

```text
$ ls site/
404.html  assets/  audits/  forge/  index.html  meta/  search/  sitemap.xml  sitemap.xml.gz
$ find site/forge -name '*.html' | wc -l
[~200 pages HTML]
```

Site complet, sitemap généré.

---

## État Git

```text
 D docs/forge/.gitkeep                 (supprimé : le dossier n'est plus vide)
 M docs/forge/index.md                  (régénéré par le script avec contenu adapté)
 M mkdocs.yml                           (nav enrichie)
?? docs/forge/15-minutes.md             (et 195 autres .md + 4 assets dans docs/forge/)
?? docs/forge/adr/                      (14 .md)
?? docs/forge/contributing/             (1 .md)
?? docs/forge/entities/                 (10 .md)
?? docs/forge/history/                  (76 .md)
?? docs/forge/reference/                (12 .md)
?? docs/forge/roadmap/                  (4 .md)
?? docs/forge/security/                 (2 .md)
?? docs/forge/starters/                 (14 .md)
?? docs/forge/static/                   (4 assets)
?? docs/forge/testing/                  (15 .md)
?? docs/audits/FW-DOCS-IMPORT-001.md    (ce rapport)
?? scripts/import_forge_docs.py         (script d'import, exécutable)
```

`git diff --check` = 0. `.claude/` **absent** de git status.

Branche : `main`. Aucun commit créé.

Commande de commit suggérée (à exécuter manuellement) :

```bash
git add scripts/import_forge_docs.py mkdocs.yml docs/forge/ \
        docs/audits/FW-DOCS-IMPORT-001.md
git commit -m "feat(docs): import Forge documentation (FW-DOCS-IMPORT-001)"
```

---

## Limites restantes

1. **Navigation incomplète** : seules 7 pages Forge sont structurées dans la nav (vue d'ensemble, installation, premiers pas, concepts, référence, déploiement, roadmap). Les 189 autres pages sont accessibles par lien direct mais non listées. → futur `FW-NAV-COMPLETE-XXX`.
2. **Lien dossier non résolu** dans `forge/reference.md` (`adr/`) et `forge/starters/welcome/index.md` (`../01-contact-simple/`, `../`) : 3 INFO non bloquants. À corriger lorsque la nav couvrira ces sections.
3. **Hook `mkdocs_version_hook.py`** non importé : la version Forge n'est pas injectée dans le rendu (Forge core l'injecte automatiquement). À traiter si la cohérence de version devient critique → futur `FW-MKDOCS-VERSION-001`.
4. **`docs/stylesheets/extra.css`** non importé : si Forge core ajoute des styles personnalisés à sa doc, ils manqueront ici. À évaluer visuellement.
5. **Sous-dossier `static/` partiellement importé** : seuls les assets image sont copiés. Si la doc Forge fait référence à `static/js/app.js` ou `static/tailwind.css`, ces liens cassent silencieusement (non vu dans les warnings actuels).
6. **`docs/forge/index.md` régénéré** : tout contenu manuel précédemment ajouté à ce fichier serait écrasé à chaque ré-import. Si une vraie page d'accueil personnalisée pour la section Forge est souhaitée, elle devrait vivre sous un autre nom (et `forge/index.md` rester un placeholder géré par le script).
7. **Aucune CI** : le script doit être lancé manuellement. Une CI GitHub Actions pourrait automatiser l'import + build à chaque release Forge → futur ticket.
8. **`landing/` (vide) et `notes/` (vide)** : non touchés, conformément au ticket.
9. **`public/index.html`** et `sources/forge-landing/` : non touchés, conformément au ticket.
10. **Aucun déploiement** ni configuration Caddy/DNS, conformément au ticket.
11. **Aucun commit créé.**

---

## Prochain ticket recommandé

**FW-LANDING-FINALIZE-001 — Finaliser la landing page Forge-web**

Pré-requis désormais satisfaits :

- doc Forge importée sous `docs/forge/` ;
- nav MkDocs fonctionnelle ;
- build strict vert ;
- les liens relatifs `./docs/...` de `public/index.html` ont maintenant une cible potentielle (la doc est en place).

Périmètre suggéré (à confirmer dans le ticket lui-même) :

1. Décider du sous-chemin de publication (`/`, `/docs/`, `docs.forgemvc.com`).
2. Ajuster `site_url` dans `mkdocs.yml` en cohérence.
3. Vérifier que tous les liens `./docs/...` de `public/index.html` résolvent vers une page MkDocs réelle après build.
4. Écrire `scripts/build-site.sh` qui assemble `public/` + `site/` (MkDocs) dans un seul `dist/` prêt à servir.
5. Ne pas déployer.
