# FW-AUDIT-EXISTING-001 — Audit initial de l'existant Forge-web

> Date de l'audit : 2026-05-23
> Auteur : audit automatisé sous contrôle utilisateur
> Périmètre : lecture seule. Aucun fichier de Forge core n'a été modifié. Seul ce rapport et son dossier `docs/audits/` ont été créés dans Forge-web.

---

## 1. Résumé

L'audit confirme que **Forge-web est déjà initialisé** (structure de base, README, .gitignore, premier commit Git, dépôt distant `caucrogeGit/Forge-web` configuré), mais il est **vide côté documentation et incomplet côté landing**.

Constats principaux :

1. Les sources nommées dans le ticket (`Forge-main.zip`, `forge-docs.zip`, `notes-infrastructure-proxmox.md`, `notes-dns-domaine-forgemvc-com.md`, `conversations-projet-forge-web.md`) **n'existent pas sous forme de fichiers** sur la machine. Les équivalents vivants sont accessibles dans le dépôt Forge core (`/home/roger/Projets/Forge/`).
2. La **source documentaire canonique** doit donc être le dépôt Forge core vivant — pas un zip — car il est le seul à jour (dernier remaniement docs : 2026-05-22, version annoncée `1.0.0-beta.8`).
3. La **landing page** existe en trois copies divergentes (Forge core, sources/, public/). La plus récente et la plus propre est `public/index.html`, mais elle conserve quelques liens GitHub absolus et des liens MkDocs relatifs qui présupposent que la doc sera publiée sous `/docs/` du même domaine.
4. Aucun `mkdocs.yml` n'existe encore dans Forge-web : il devra être adapté depuis `Forge/mkdocs.yml`, avec retrait du hook spécifique à Forge core et changement du `site_url`.
5. Aucun secret n'est présent dans Forge-web. Le `.gitignore` actuel couvre correctement `.env`, clés, certificats et `site/`.
6. La conversation `01-architecture-generale-forge-web.md` cite des documents (`conversations-projet-forge-web.md`, `notes-infrastructure-proxmox.md`, `notes-dns-domaine-forgemvc-com.md`, `CHARTE_DOC.md`) qui sont des **sources externes au dépôt** (probablement ChatGPT et un fichier Forge core). Cette dépendance documentaire externe doit être tracée.

Décision recommandée à l'issue de l'audit : ouvrir **FW-DOCS-IMPORT-001** avant toute autre opération d'infrastructure, puisque la structure du dépôt est déjà correcte mais la matière documentaire manque.

---

## 2. Sources auditées

| Source citée par le ticket | Présence locale | Emplacement réel utilisé pour l'audit |
|---|---|---|
| `Forge-main.zip` | **Absent** | Substitut : `/home/roger/Projets/Forge/` (arbre Forge core vivant) |
| `forge-docs.zip` | **Absent** | Substitut : `/home/roger/Projets/Forge/docs/` |
| `README.md` (Forge-web) | Présent | `README.md` |
| `mkdocs.yml` | **Absent dans Forge-web** | Présent dans Forge core : `Forge/mkdocs.yml` |
| `CHARTE_DOC.md` | Absent dans Forge-web | Présent dans Forge core : `Forge/CHARTE_DOC.md` |
| `notes-infrastructure-proxmox.md` | **Absent** | À recréer dans `notes/` |
| `notes-dns-domaine-forgemvc-com.md` | **Absent** | À recréer dans `notes/` |
| `conversations-projet-forge-web.md` | **Absent** | À recréer dans `notes/` |
| Dépôt local Forge-web | Présent | [/home/roger/Projets/Forge-web/](../../) |

Inventaire complet du dépôt Forge-web (état au 2026-05-23) :

```text
Forge-web/
├── README.md                                       (42 lignes, contenu validé)
├── .gitignore                                      (27 lignes, couvre secrets + site/)
├── docs/
│   ├── 01-architecture-generale-forge-web.md       (599 lignes, décisions cadre)
│   ├── 02-creation-depot-forge-web.md              (665 lignes, tutoriel de création)
│   └── .gitkeep
├── infra/                                          (vide sauf .gitkeep)
├── landing/
│   └── assets/{css,img,js}/.gitkeep                (vide)
├── notes/                                          (vide sauf .gitkeep)
├── public/
│   ├── index.html                                  (53 175 octets, landing transformée)
│   └── static/
│       ├── img/forge-logo.png                      (~825 Ko)
│       ├── js/landing.js                           (27 lignes)
│       └── tailwind.css                            (36 Ko)
├── scripts/                                        (vide sauf .gitkeep)
└── sources/
    └── forge-landing/
        ├── index.original.html                     (53 714 octets, snapshot Forge core)
        └── index.before-forge-web-links.html       (53 714 octets, identique à index.original.html)
```

Historique Git (3 commits sur `main`) :

```text
689219f docs: ajouter les premiers contenus Forge-web
52110fd docs: update landing after Forge PyPI publication
a9e962e init: create Forge-web project structure
```

---

## 3. État de Forge-main.zip

**Le fichier `Forge-main.zip` n'a pas été trouvé** sur le poste. La recherche a couvert `/home/roger/` jusqu'à 6 niveaux de profondeur et n'a remonté aucun ZIP.

Substitut audité : l'arbre de travail vivant `/home/roger/Projets/Forge/`. C'est un dépôt Git complet (branche `main` à jour, 28 dossiers racines), correspondant au framework Forge en cours de développement.

Inventaire de Forge core pertinent pour Forge-web :

| Dossier / fichier Forge core | Pertinent pour Forge-web ? |
|---|---|
| `docs/` (50+ fichiers .md, 1 index.html, sous-dossiers entities/, history/, reference/, starters/, etc.) | **Oui** — source documentaire canonique à importer |
| `docs/index.html` | **Oui** — landing page d'origine (déjà partiellement copiée) |
| `docs/static/`, `docs/stylesheets/`, `docs/img/` | **Oui** — assets de la documentation |
| `docs/quarkdown/` | À évaluer (probablement non) |
| `mkdocs.yml` | **Oui** — à dupliquer/adapter |
| `tools/mkdocs_version_hook.py` | À évaluer — hook référencé par `mkdocs.yml`, propre à Forge core |
| `requirements-docs.txt` | **Oui** — dépendances MkDocs (3 lignes : mkdocs, mkdocs-material, pymdown-extensions) |
| `CHARTE_DOC.md` | À discuter — pertinent comme contenu, mais sous licence/canonicité Forge core |
| `static/` racine, `core/`, `mvc/`, `forge_cli/`, `packages/`, `tests/`, `integrations/`, `forge.py`, `app.py`, `schemas/` | **Non** — code applicatif Forge |
| `cert.pem`, `key.pem`, `storage/`, `env/`, `.venv/`, `node_modules/`, `__pycache__/`, `forge_mvc.egg-info/`, `TestForge101/` | **Non — exclusion absolue** |

Statut : Forge core est l'unique source à jour. Il est plus récent que tout ZIP potentiellement archivé.

---

## 4. État de forge-docs.zip

**Le fichier `forge-docs.zip` n'a pas été trouvé** non plus.

Substitut audité : `/home/roger/Projets/Forge/docs/`.

Contenu (synthèse) :

- ~50 fichiers Markdown racines (installation, guide, getting-started, 15-minutes, concepts, crud, front, auth, security, deployment, release-policy, faq, mail, media, pdf, etc.)
- Sous-dossiers thématiques : `adr/` (14 ADR), `entities/`, `reference/`, `starters/` (7 starters), `history/` (audits + releases archivés), `testing/` (tests terrain), `roadmap/`, `project/`, `contributing/`, `security/`, `stylesheets/`.
- `index.html` : landing page (55 884 octets, 46 références à `caucrogegit.github.io/Forge/`)
- `static/` : favicon, logo, JS, src, tailwind.css

Comparaison avec les copies locales Forge-web :

| Fichier | Taille | Refs `caucrogegit.github.io/Forge/` ou `caucrogeGit/Forge` |
|---|---|---|
| `Forge/docs/index.html` (source vive) | 55 884 o | **46** |
| `Forge-web/sources/forge-landing/index.original.html` | 53 714 o | **26** |
| `Forge-web/sources/forge-landing/index.before-forge-web-links.html` | 53 714 o | **26** |
| `Forge-web/public/index.html` | 53 175 o | **6** (toutes restantes vers `github.com/caucrogeGit/Forge`) |

Conclusion : la source Forge core est **plus volumineuse et plus à jour que le snapshot pris dans `sources/`**. Cela signifie que la copie dans `sources/forge-landing/` est légèrement obsolète. Il faudra rafraîchir le snapshot ou bien décider de considérer `public/index.html` comme la nouvelle source de travail et abandonner `sources/`.

---

## 5. Comparaison des sources documentaires

| Critère | Forge core `docs/` (substitut Forge-main.zip / forge-docs.zip) | Snapshot Forge-web `sources/` |
|---|---|---|
| Fraîcheur (date la plus récente) | 2026-05-22 | 2026-05-15 |
| Complétude (volume) | ~50 fichiers .md + 8 sous-dossiers | 1 fichier HTML seulement (landing) |
| Cohérence avec PyPI publié | Oui (`1.0.0-beta.8` dans CHANGELOG) | Inconnue / partielle |
| Compatibilité MkDocs prête à l'emploi | Oui (`mkdocs.yml` testé) | Non (aucun `mkdocs.yml`) |
| Liens externes corrects pour forgemvc.com | Non — pointent vers `caucrogegit.github.io/Forge/` | Partiellement corrigés dans `public/index.html` |

**Décision proposée : la source documentaire canonique est `/home/roger/Projets/Forge/docs/`** (équivalent vivant de Forge-main.zip / forge-docs.zip).

Justification :
- C'est la version la plus récente.
- C'est la seule cohérente avec le code Forge publié sur PyPI.
- C'est celle qui est testée localement par les contributeurs Forge.
- Toute autre source serait par construction obsolète.

Conséquence : la prochaine étape (FW-DOCS-IMPORT-001) doit définir une procédure d'import claire et **idéalement automatisable** (script `scripts/sync-docs.sh`) plutôt qu'une copie manuelle, pour pouvoir resynchroniser à chaque release Forge core.

---

## 6. État de la landing page

### 6.1 Emplacement actuel

Trois copies coexistent :

1. **Source d'origine** : `Forge/docs/index.html` — 55 884 octets, 46 liens GitHub Pages. C'est la landing servie par MkDocs comme `index.html` de la doc Forge core.
2. **Snapshot importé** : `sources/forge-landing/index.original.html` — 53 714 octets, 26 liens. Préservé tel quel pour traçabilité.
3. **Landing de travail** : `public/index.html` — 53 175 octets, 6 liens GitHub absolus restants.

`index.original.html` et `index.before-forge-web-links.html` sont **identiques au bit près** (`diff -q` muet) — la deuxième copie n'apporte rien et peut être supprimée pour éviter la confusion (à décider en FW-REPO-STRUCTURE-001).

### 6.2 Extraction propre vers Forge-web

L'extraction est **déjà entamée** (commit `52110fd`). La landing de travail `public/index.html` a déjà :

- remplacé les `https://caucrogegit.github.io/Forge/...` par des chemins relatifs `./docs/...` (présupposant publication sous `forgemvc.com/docs/`) ;
- supprimé les liens redondants ;
- conservé les liens absolus vers GitHub (raisonnable, car le dépôt source reste sur GitHub).

### 6.3 Liens obsolètes restants dans `public/index.html`

```text
public/index.html:47    https://github.com/caucrogeGit/Forge
public/index.html:107   https://github.com/caucrogeGit/Forge
public/index.html:636   git clone https://github.com/caucrogeGit/Forge.git
public/index.html:648   data-copy="git clone https://github.com/caucrogeGit/Forge.git"
public/index.html:777   https://github.com/caucrogeGit/Forge/blob/main/CHARTE_DOC.md
public/index.html:780   https://github.com/caucrogeGit/Forge
```

Aucun lien `caucrogegit.github.io/Forge/` ne subsiste dans `public/index.html`. Les 6 liens restants pointent vers le dépôt GitHub de Forge — **c'est correct** : le code source reste sur GitHub, seule la documentation publique migre vers forgemvc.com.

### 6.4 Mention de GitHub Pages

Aucune mention résiduelle de GitHub Pages dans `public/index.html`. La transition fonctionnelle est faite ; il reste à valider que les chemins relatifs `./docs/...` résolvent correctement une fois MkDocs en place.

---

## 7. État de MkDocs

### 7.1 Constat

**Aucun `mkdocs.yml` n'existe dans Forge-web.** Aucune dépendance MkDocs n'est déclarée. Le dossier `docs/` de Forge-web ne contient pour l'instant que de la documentation **interne au projet Forge-web** (architecture, création du dépôt), pas la documentation publique de Forge.

### 7.2 `mkdocs.yml` de Forge core (à adapter)

Source : `Forge/mkdocs.yml`. Éléments à transformer si on duplique ce fichier dans Forge-web :

| Clé | Valeur actuelle (Forge core) | Adaptation Forge-web recommandée |
|---|---|---|
| `site_name` | `Forge` | Inchangé |
| `site_description` | `Framework web MVC pur Python` | Inchangé |
| `site_url` | `https://caucrogegit.github.io/Forge/` | **`https://forgemvc.com/docs/`** (à confirmer selon le sous-chemin retenu) |
| `repo_name` | `caucrogeGit/Forge` | Inchangé (le code reste sur GitHub Forge) |
| `repo_url` | `https://github.com/caucrogeGit/Forge` | Inchangé |
| `edit_uri` | `edit/main/docs/` | Inchangé **si** les docs restent éditées dans Forge core ; à modifier si elles deviennent éditables dans Forge-web |
| `theme.favicon` / `theme.logo` | `static/favicon.svg` / `static/forge-logo.png` | Inchangé si on importe `docs/static/` |
| `extra_css` | `stylesheets/extra.css` | Inchangé si on importe `docs/stylesheets/` |
| `hooks` | `tools/mkdocs_version_hook.py` | **À retirer ou à porter** — fichier hors `docs/`, propre au build Forge core (probablement injecte la version Forge depuis le pyproject) |
| `plugins.search` | activé, langue `fr` | Inchangé |
| `markdown_extensions` (pymdownx, admonition, etc.) | complet | Inchangé |
| `docs_dir` / `site_dir` | `docs` / `site` | Inchangé |
| `nav` | ~200 entrées | À garder tel quel **si on importe toute la doc**, sinon à élaguer |

### 7.3 Dépendances

`Forge/requirements-docs.txt` :

```text
mkdocs>=1.6
mkdocs-material>=9.7
pymdown-extensions>=10.0
```

C'est minimal et directement réutilisable dans Forge-web (à créer comme `requirements-docs.txt` à la racine).

### 7.4 Compatibilité forgemvc.com

Pas de blocage technique. Trois décisions doivent être prises explicitement avant import :

1. **Sous-chemin de publication** : `https://forgemvc.com/docs/` ou `https://forgemvc.com/` (doc à la racine, landing sous `/`) ou `https://docs.forgemvc.com/` (sous-domaine séparé). Cela conditionne `site_url` et les chemins relatifs de la landing.
2. **Source de vérité éditoriale** : la doc reste-t-elle éditée dans Forge core puis synchronisée vers Forge-web, ou bien Forge-web devient le dépôt éditorial avec rapatriement inverse ? **Recommandation : édition dans Forge core, import unidirectionnel vers Forge-web** (cohérent avec la séparation framework/site).
3. **Sort du hook `tools/mkdocs_version_hook.py`** : à inspecter avant import ; soit le porter, soit le remplacer par une injection statique de la version.

---

## 8. Liens à corriger pour forgemvc.com

### 8.1 Dans la landing `public/index.html`

Aucun lien `caucrogegit.github.io/Forge/` à corriger (déjà fait). Les 6 liens `github.com/caucrogeGit/Forge` sont **à conserver** : ils pointent vers le dépôt source.

À valider une fois MkDocs en place : tous les liens `./docs/...` (chemins relatifs vers la doc) :

```text
./docs/guide/
./docs/roadmap/forge-roadmap/
./docs/installation/
./docs/installation-developpement/
./docs/deployment/
./docs/installation-windows/
./docs/starters/01-contact-simple/
./docs/starters/02-utilisateurs-auth/
./docs/starters/03-carnet-contacts/
./docs/starters/04-suivi-comportement-eleves/
./docs/15-minutes/
./docs/app-complete-tutorial/
./docs/reference/
./docs/api-json/
./docs/production-security/
./docs/release-policy/
./docs/contributing/
```

### 8.2 Dans la documentation interne Forge-web

[docs/meta/02-creation-depot-forge-web.md](../meta/02-creation-depot-forge-web.md) contient 13 références à `https://github.com/caucrogeGit/Forge-web.git` — toutes correctes (instructions de création du dépôt Forge-web sur GitHub).

[docs/meta/01-architecture-generale-forge-web.md](../meta/01-architecture-generale-forge-web.md) : 1 référence à `forgemvc.com` (correcte).

Aucune correction nécessaire dans la documentation interne.

### 8.3 Dans la documentation Forge core (avant import éventuel)

`Forge/docs/index.html` contient encore 46 références à `caucrogegit.github.io/Forge/`. Si la landing était re-importée depuis Forge core, il faudrait rejouer la transformation déjà appliquée à `public/index.html`. C'est un argument fort pour ne **pas** réimporter la landing : la version `public/index.html` est déjà bonne.

Pour les `*.md` de Forge core : un import en masse devra inclure un audit/sed des liens internes Markdown (`[texte](path)`) pour s'assurer qu'aucun n'est ancré sur `caucrogegit.github.io/Forge/`. À traiter dans FW-DOCS-IMPORT-001.

---

## 9. Fichiers à importer dans Forge-web

Liste consolidée des éléments à importer depuis Forge core (`/home/roger/Projets/Forge/`) :

| Source Forge core | Cible Forge-web | Adaptation |
|---|---|---|
| `mkdocs.yml` | `mkdocs.yml` (racine) | Voir §7.2 : adapter `site_url`, retirer/porter le hook |
| `requirements-docs.txt` | `requirements-docs.txt` (racine) | Aucune |
| `docs/*.md` (tous sauf `index.html`) | `docs/forge/` (sous-dossier pour éviter le mélange avec la doc interne Forge-web) | Auditer liens internes |
| `docs/adr/` | `docs/forge/adr/` | Idem |
| `docs/entities/` | `docs/forge/entities/` | Idem |
| `docs/reference/` | `docs/forge/reference/` | Idem |
| `docs/starters/` | `docs/forge/starters/` | Idem |
| `docs/history/` | `docs/forge/history/` | Idem (gros volume, à confirmer si tout est public) |
| `docs/testing/` | `docs/forge/testing/` | À confirmer (peut-être interne) |
| `docs/roadmap/` | `docs/forge/roadmap/` | Idem |
| `docs/project/` | `docs/forge/project/` | À confirmer (probablement interne) |
| `docs/contributing/` | `docs/forge/contributing/` | Idem |
| `docs/security/` | `docs/forge/security/` | Idem |
| `docs/static/` | `docs/forge/static/` | Aucune |
| `docs/stylesheets/` | `docs/forge/stylesheets/` | Aucune |
| `CHARTE_DOC.md` | `docs/forge/charter-canonical.md` | À discuter — duplication d'un document canonique de Forge core ; alternative : lien externe |
| `tools/mkdocs_version_hook.py` | À évaluer | Inspecter avant import |

Éléments déjà présents dans Forge-web (à conserver tels quels) :

- `public/index.html` (landing déjà transformée — ne pas réimporter)
- `public/static/img/forge-logo.png`, `public/static/js/landing.js`, `public/static/tailwind.css`
- `docs/01-architecture-generale-forge-web.md`, `docs/02-creation-depot-forge-web.md`
- `README.md`, `.gitignore`

Notes externes à recréer manuellement (pas trouvées localement) :

- `notes/notes-infrastructure-proxmox.md` — à reconstituer depuis le projet ChatGPT
- `notes/notes-dns-domaine-forgemvc-com.md` — idem
- `notes/conversations-projet-forge-web.md` — idem

---

## 10. Fichiers à exclure

Exclusion stricte. Aucun de ces éléments ne doit jamais être copié dans Forge-web :

**Code applicatif Forge** :
- `core/`, `mvc/`, `forge_cli/`, `packages/`, `integrations/`, `schemas/`
- `forge.py`, `app.py`, `config.py`, `conftest.py`
- `pyproject.toml`, `package.json`, `package-lock.json`, `MANIFEST.in`, `pytest.ini`, `requirements.txt`, `requirements-dev.txt`
- `tests/`, `TestForge101/`, `deploy/`, `tools/` (sauf hook MkDocs à étudier), `scripts/`, `translations/`, `static/`

**Artefacts et runtime** :
- `node_modules/`, `__pycache__/`, `forge_mvc.egg-info/`, `.venv/`, `.pyenv`, `storage/`, `env/`, `site/` (généré)

**Secrets et certificats** :
- `cert.pem`, `key.pem`
- Tout `.env`, `.envrc`, `*.key`, `*.crt`, `*.pem`
- Toute clé SSH ou token GitHub/Cloudflare

**Métadonnées de dépôt Forge core** :
- `.git/`, `.github/`, `.vscode/`, `.kilo/`, `.codex`, `.agents/`, `.claude/`, `.python-version`

**Documents de gouvernance Forge core** (à juger au cas par cas) :
- `CHANGELOG.md` (interne Forge), `CONTRIBUTING.md`, `SECURITY.md`, `CLAUDE.md`, `LICENSE` (à dupliquer pour Forge-web), `README.md` (existe déjà côté Forge-web), `sample.json`

Le `.gitignore` actuel de Forge-web protège déjà la majorité de ces cas (`.env*`, clés, certificats, `site/`, `__pycache__`, `.venv/`). Il pourrait être renforcé pour bloquer aussi `node_modules/`, `.vscode/`, `.idea/` (déjà fait) et explicitement `cert.pem`, `key.pem`.

---

## 11. Risques identifiés

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **Documentation obsolète** importée à partir d'un ZIP archivé au lieu de Forge core vivant | Élevée | Élevé (incohérence avec le code publié) | Décision §5 : source canonique = arbre vivant Forge core. Pas de ZIP. |
| 2 | **Liens GitHub Pages persistants** dans la doc importée (`caucrogegit.github.io/Forge/`) | Élevée | Moyen (liens cassés) | Audit/sed systématique en FW-DOCS-IMPORT-001 ; build MkDocs avec `--strict` |
| 3 | **Confusion entre doc interne Forge-web** (`docs/0X-...md`) et doc publique Forge | Moyenne | Moyen | Isoler la doc Forge importée dans `docs/forge/` ; ne pas la mélanger avec `docs/audits/` ou `docs/0X-...md` |
| 4 | **Copie excessive du dépôt Forge** (import accidentel de `core/`, `mvc/`, etc.) | Moyenne | Élevé (gonflage, duplication, charge maintenance) | Script d'import explicite avec liste blanche, pas d'un `rsync -a` aveugle |
| 5 | **Secrets / .env accidentellement importés** (`cert.pem`, `key.pem` traînent à la racine Forge core) | Moyenne | Très élevé (compromission) | `.gitignore` durci ; liste noire explicite dans le script d'import ; `git status` + relecture avant chaque commit |
| 6 | **Documentation publiée incohérente avec PyPI/GitHub** (version, liens vers releases inexistantes) | Moyenne | Moyen | Synchroniser l'import avec une release Forge identifiée (tag) ; mentionner la version Forge dans le footer |
| 7 | **Déploiement prématuré sans firewall ni sauvegarde** | Faible (ticket suivant l'interdit) | Très élevé | Respecter la roadmap §13 ; ne pas court-circuiter les phases |
| 8 | **Snapshot `sources/forge-landing/` divergent de la source vive** | Constatée | Faible | Décision : soit rafraîchir le snapshot, soit le supprimer comme obsolète (à traiter en FW-REPO-STRUCTURE-001) |
| 9 | **Hook MkDocs `tools/mkdocs_version_hook.py` manquant** après import partiel | Élevée si import naïf | Moyen (build cassé) | Inspecter le hook avant import ; soit le porter, soit retirer la clé `hooks:` du `mkdocs.yml` adapté |
| 10 | **Notes externes (`notes-*.md`, `conversations-*.md`) jamais matérialisées** | Constatée | Faible mais traçabilité perdue | Recréer les fichiers vides dans `notes/` avec frontmatter pointant vers la source originale (ChatGPT, Forge core) |
| 11 | **Boucle d'édition double** : modifications de la doc faites dans Forge-web puis perdues au prochain import depuis Forge core | Moyenne | Élevé | Décision claire §7.4 : Forge core = source unique éditoriale ; Forge-web = consommateur en lecture seule |
| 12 | **Mélange avec Forge Design** | Faible si discipline respectée | Moyen | Règle §3.3 du document architecture déjà actée : Forge Design hors périmètre |

---

## 12. Structure cible proposée

Structure recommandée à l'issue de l'audit (objectif FW-REPO-STRUCTURE-001 + FW-DOCS-IMPORT-001) :

```text
Forge-web/
├── README.md                         (existant, à enrichir avec section MkDocs/build)
├── .gitignore                        (existant, à durcir : cert.pem, key.pem, node_modules/)
├── LICENSE                           (à ajouter, distinct de Forge core)
├── mkdocs.yml                        (à créer — adapté de Forge core)
├── requirements-docs.txt             (à créer — copie de Forge/requirements-docs.txt)
│
├── docs/                             (sources MkDocs publiées)
│   ├── index.md                      (à créer — accueil de la doc, court)
│   ├── audits/                       (audits Forge-web — ce rapport ici)
│   │   └── FW-AUDIT-EXISTING-001.md
│   ├── meta/                         (doc interne Forge-web, déplacée depuis docs/0X-…md)
│   │   ├── 01-architecture-generale-forge-web.md
│   │   └── 02-creation-depot-forge-web.md
│   └── forge/                        (doc Forge importée, intacte)
│       ├── installation.md, guide.md, …
│       ├── adr/
│       ├── entities/
│       ├── reference/
│       ├── starters/
│       ├── static/
│       └── stylesheets/
│
├── public/                           (landing statique servie à /)
│   ├── index.html                    (existant, à laisser tel quel)
│   └── static/
│       ├── img/
│       ├── js/
│       └── tailwind.css
│
├── sources/                          (snapshots de traçabilité)
│   └── forge-landing/
│       └── index.original.html       (un seul fichier ; supprimer le doublon)
│
├── infra/                            (notes d'infrastructure sans secrets)
│   └── README.md                     (à créer — index des notes)
│
├── notes/                            (notes de travail, recréées)
│   ├── notes-infrastructure-proxmox.md
│   ├── notes-dns-domaine-forgemvc-com.md
│   └── conversations-projet-forge-web.md
│
├── scripts/                          (scripts de build/import/déploiement)
│   ├── sync-docs-from-forge.sh       (à créer — import contrôlé depuis Forge core)
│   └── build-site.sh                 (à créer — mkdocs build --strict + assemblage public/+site/)
│
└── site/                             (généré, ignoré par git)
```

Décisions structurelles incluses dans cette cible :

1. La doc interne Forge-web (`01-…md`, `02-…md`) **déménage** dans `docs/meta/` pour libérer `docs/` au profit de MkDocs et clarifier qu'elle n'est pas la doc publique.
2. La doc Forge importée vit **intégralement sous `docs/forge/`**, jamais mélangée avec autre chose.
3. Le doublon `sources/forge-landing/index.before-forge-web-links.html` est supprimé.
4. Un `LICENSE` propre à Forge-web est ajouté (Forge core a la sienne ; il faut décider laquelle pour le site — `CC-BY` pour le contenu, `MIT` pour le code, à trancher).
5. Un dossier `infra/` est doté d'un `README.md` d'index (vide aujourd'hui).
6. `scripts/` reçoit deux scripts clés (`sync-docs-from-forge.sh`, `build-site.sh`) pour rendre la chaîne reproductible.

---

## 13. Roadmap Forge-web proposée

Tickets courts, séquentiels, chacun avec une responsabilité unique. Numérotation `FW-…-NNN`.

| Ticket | Titre | Durée estimée | Dépend de |
|---|---|---|---|
| **FW-REPO-STRUCTURE-001** | Aligner la structure du dépôt sur la cible §12 (créer `docs/meta/`, déplacer `01-/02-…md`, créer `docs/forge/` vide, créer `LICENSE`, supprimer doublon `sources/`, durcir `.gitignore`) | 1 h | FW-AUDIT-EXISTING-001 |
| **FW-MKDOCS-INIT-001** | Créer `mkdocs.yml` minimal et `requirements-docs.txt`, vérifier `mkdocs serve` localement (avec une page de test) | 1 h | FW-REPO-STRUCTURE-001 |
| **FW-DOCS-IMPORT-001** | Écrire `scripts/sync-docs-from-forge.sh`, importer `docs/*.md`, `docs/adr/`, `docs/entities/`, `docs/reference/`, `docs/starters/`, `docs/static/`, `docs/stylesheets/` dans `docs/forge/`, auditer/corriger les liens `caucrogegit.github.io` | 2-3 h | FW-MKDOCS-INIT-001 |
| **FW-LANDING-FINALIZE-001** | Valider que tous les liens relatifs `./docs/...` de `public/index.html` résolvent, ajuster `site_url` MkDocs, choisir le sous-chemin (`/`, `/docs/`, `docs.forgemvc.com`) | 1 h | FW-DOCS-IMPORT-001 |
| **FW-NOTES-RECREATE-001** | Recréer `notes/notes-infrastructure-proxmox.md`, `notes/notes-dns-domaine-forgemvc-com.md`, `notes/conversations-projet-forge-web.md` depuis les sources externes ChatGPT (contenu, pas re-cadrage) | 1 h | indépendant |
| **FW-BUILD-SCRIPT-001** | Écrire `scripts/build-site.sh` : `mkdocs build --strict` + assemblage avec `public/` → `site/` prêt à déployer | 1 h | FW-LANDING-FINALIZE-001 |
| **FW-DEPLOY-PREP-001** | Préparer la VM web (notes dans `infra/`, sans toucher Proxmox) ; produire un README de déploiement Caddy | 2 h | FW-BUILD-SCRIPT-001 |
| **FW-DNS-PREP-001** | Documenter dans `notes/` les enregistrements DNS minimaux ; ne rien activer | 30 min | indépendant |
| **FW-CADDY-CONFIG-001** | Rédiger un `Caddyfile` modèle dans `infra/`, sans déployer | 1 h | FW-DEPLOY-PREP-001 |
| **FW-DEPLOY-GO-001** | Premier déploiement réel (séparé, à ne déclencher qu'après validation manuelle) | hors audit | tout ce qui précède |

Note : l'ordre respecte la règle du document architecture §15 (cadrer → créer → générer → contenu → publier → sécuriser).

---

## 14. Prochain ticket recommandé

**FW-REPO-STRUCTURE-001 — Aligner la structure du dépôt Forge-web sur la cible**

Justification :
- L'audit a confirmé que la structure actuelle est **proche mais pas alignée** sur la cible (`docs/meta/` manquant, doublon dans `sources/`, pas de `LICENSE`, `mkdocs.yml` absent, `notes/` vide).
- Aucune importation documentaire ne devrait commencer avant d'avoir la bonne arborescence cible, sinon le rangement sera douloureux a posteriori.
- C'est un ticket court (1 h) qui débloque toute la suite.

Le ticket suivant immédiat sera **FW-MKDOCS-INIT-001** (créer `mkdocs.yml` minimal), puis seulement après **FW-DOCS-IMPORT-001** (import depuis Forge core).

L'ordre **NE doit PAS être** : structure → import docs → MkDocs. Il doit être : structure → MkDocs vide → import docs **dans** MkDocs déjà valide.

---

## Annexe A — Fichiers explicitement absents (recherche locale 2026-05-23)

```text
Forge-main.zip                             ABSENT
forge-docs.zip                             ABSENT
notes-infrastructure-proxmox.md            ABSENT
notes-dns-domaine-forgemvc-com.md          ABSENT
conversations-projet-forge-web.md          ABSENT
Forge-web/mkdocs.yml                       ABSENT
Forge-web/LICENSE                          ABSENT
Forge-web/requirements-docs.txt            ABSENT
```

## Annexe B — Fichiers Forge core modifiés par cet audit

**Aucun.** Conformément au périmètre du ticket, aucun fichier de Forge core (`/home/roger/Projets/Forge/`) n'a été lu en écriture, modifié, déplacé ou supprimé. Toutes les opérations sur Forge core ont été des lectures (`Read`, `grep`, `ls`).

Seuls fichiers créés par cet audit :

- [docs/audits/FW-AUDIT-EXISTING-001.md](FW-AUDIT-EXISTING-001.md) (ce rapport)
- [docs/audits/](.) (dossier parent)
