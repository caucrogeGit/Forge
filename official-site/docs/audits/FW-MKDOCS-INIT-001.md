# Rapport final — FW-MKDOCS-INIT-001

> Date : 2026-05-23
> Branche : `main`
> Périmètre exécuté : strictement celui du ticket. Aucun import documentaire. Aucune doc Forge copiée. Aucun fichier Forge core touché.

---

## Résumé

Le socle MkDocs minimal est en place. `mkdocs build --strict` passe sans avertissement. `mkdocs serve -a 127.0.0.1:8001` démarre et répond HTTP 200. La navigation expose 6 pages : accueil Forge-web, vue d'ensemble Forge (placeholder), 2 documents internes Forge-web (`meta/01-…`, `meta/02-…`), et les 2 rapports d'audit (`audits/FW-AUDIT-EXISTING-001`, `audits/FW-REPO-STRUCTURE-001`).

Une modification additionnelle (justifiée) a été nécessaire dans `docs/audits/FW-AUDIT-EXISTING-001.md` : 11 liens Markdown pointaient vers des chemins hors `docs_dir` (filesystem) et faisaient échouer `--strict`. Ils ont été convertis en `` `inline code` `` qui conserve l'information sans prétendre à être cliquable. La modification est purement cosmétique et préserve intégralement le contenu et la sémantique de l'audit.

Aucun commit n'a été créé par ce ticket.

---

## Précondition .claude

`.claude/` était déjà ignoré par `.gitignore` (entrée ajoutée hors-session — section `# Local Claude/AI tooling`).

Vérification au début du ticket :

```bash
git status --short | grep -E '\.claude'
→ aucune sortie
→ CLAUDE_HIDDEN_OK
```

Vérification finale identique. `.claude/` n'apparaît à aucun moment dans la zone de staging ni dans les fichiers non suivis Git. Aucune action supplémentaire n'a été nécessaire.

---

## Fichiers créés

| Fichier | Rôle |
|---|---|
| `mkdocs.yml` | Configuration MkDocs (site_name, theme material, nav, extensions, plugins) |
| `requirements-docs.txt` | Dépendances Python pour le build documentaire (3 lignes) |
| `docs/index.md` | Page d'accueil de la documentation Forge-web (avec admonition `warning`) |
| `docs/forge/index.md` | Placeholder pour la doc Forge à importer plus tard |
| `docs/audits/FW-MKDOCS-INIT-001.md` | Ce rapport |

Dossiers : aucun nouveau dossier créé. `docs/forge/` existait déjà depuis FW-REPO-STRUCTURE-001.

---

## Fichiers modifiés

| Fichier | Nature | Justification |
|---|---|---|
| `docs/audits/FW-AUDIT-EXISTING-001.md` | 11 liens `[texte](chemin-hors-docs)` convertis en `` `texte` `` | Nécessaire pour faire passer `mkdocs build --strict` (les chemins relatifs vers `Forge/`, `public/`, `sources/`, `README.md`, etc. sont hors `docs_dir` et MkDocs les considère comme cassés) |

Aucun autre fichier n'a été modifié par ce ticket. `.gitignore` apparaît dans `git status` comme `M` mais cette modification est l'ajout de `.claude/` effectué hors session et déjà acquis avant le démarrage du ticket.

`docs/forge/.gitkeep` est laissé en place (n'interfère pas avec MkDocs : seuls les `.md` sont indexés).

---

## Configuration MkDocs

Points clés du `mkdocs.yml` créé :

| Clé | Valeur |
|---|---|
| `site_name` | `Forge` |
| `site_description` | `Site officiel du framework web Python Forge` |
| `site_author` | `Roger Cauchon` |
| **`site_url`** | **`https://forgemvc.com/`** (jamais GitHub Pages) |
| `repo_name` | `caucrogeGit/Forge-web` |
| `repo_url` | `https://github.com/caucrogeGit/Forge-web` |
| `edit_uri` | `""` (désactivé — la doc Forge-web n'est pas éditable depuis le site) |
| `theme.name` | `material` |
| `theme.language` | `fr` |
| `theme.palette` | scheme `default`, primary `black`, accent `deep orange` |
| `markdown_extensions` | 12 extensions (admonition, attr_list, def_list, footnotes, md_in_html, tables, toc, 5 pymdownx) |
| `plugins.search` | activé, langue `fr`, séparateur étendu |
| `docs_dir` | `docs` |
| `site_dir` | `site` |
| `hooks` | **aucun** (le hook Forge core n'est pas réutilisé, conformément à l'analyse §7.2 de FW-AUDIT-EXISTING-001) |

Dépendances (`requirements-docs.txt`) :

```text
mkdocs>=1.6,<2
mkdocs-material>=9.5,<10
pymdown-extensions>=10,<11
```

Versions effectivement installées :

```text
mkdocs 1.6.1
mkdocs-material installé (série 9.x conforme aux bornes)
```

---

## Navigation

Six entrées, toutes vérifiées existantes avant insertion dans `nav` :

```yaml
nav:
  - Accueil: index.md                                                    # créé par ce ticket
  - Forge:
      - Vue d'ensemble: forge/index.md                                   # créé par ce ticket
  - Projet Forge-web:
      - Architecture générale: meta/01-architecture-generale-forge-web.md  # déplacé par FW-REPO-STRUCTURE-001
      - Création du dépôt: meta/02-creation-depot-forge-web.md             # déplacé par FW-REPO-STRUCTURE-001
  - Audits:
      - FW-AUDIT-EXISTING-001: audits/FW-AUDIT-EXISTING-001.md           # créé par FW-AUDIT-EXISTING-001
      - FW-REPO-STRUCTURE-001: audits/FW-REPO-STRUCTURE-001.md           # créé par FW-REPO-STRUCTURE-001
```

Note : ce rapport (`FW-MKDOCS-INIT-001.md`) n'est intentionnellement **pas** ajouté à la nav par ce ticket — la nav doit être ajoutée par le ticket qui l'ouvre afin que la nav reste un fait constaté, pas une auto-promotion. À ajouter dans un futur ticket (typiquement le suivant) si souhaité.

---

## Vérifications

### `mkdocs build --strict`

```text
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /home/roger/Projets/Forge-web/site
INFO    -  Doc file 'audits/FW-AUDIT-EXISTING-001.md' contains an unrecognized relative link '../../../Forge/', it was left as is.
INFO    -  Doc file 'audits/FW-AUDIT-EXISTING-001.md' contains an unrecognized relative link '../../../Forge/docs/', it was left as is.
INFO    -  Doc file 'audits/FW-AUDIT-EXISTING-001.md' contains an unrecognized relative link '../../', it was left as is. Did you mean '../index.md'?
INFO    -  Doc file 'audits/FW-AUDIT-EXISTING-001.md' contains an unrecognized relative link '.', it was left as is. Did you mean 'FW-AUDIT-EXISTING-001.md'?
INFO    -  Documentation built in 0.51 seconds
```

**0 WARNING**, 4 INFO non bloquants. `--strict` valide.

Les 4 INFO restantes concernent des chemins shell purement informatifs dans des tableaux (`../../../Forge/`, `../../`, `.`) qui sont laissés tels quels par MkDocs sans transformation. Elles ne bloquent pas le build et ne justifient pas une nouvelle ronde d'édition.

### `mkdocs serve -a 127.0.0.1:8001`

```text
INFO    -  Watching paths for changes: 'docs', 'mkdocs.yml'
INFO    -  Serving on http://127.0.0.1:8001/
```

Sonde HTTP :

```text
HTTP/1.0 200 OK
Server: WSGIServer/0.2 CPython/3.12.13
Content-Type: text/html
Content-Length: 19646
```

Page d'accueil servie correctement (≈ 19 ko HTML). Processus arrêté proprement.

### `git diff --check`

```text
EXITCODE=0
```

Aucun problème de whitespace ni de conflit.

### Site généré

```text
$ ls site/
404.html  assets/  audits/  forge/  index.html  meta/  search/  sitemap.xml  sitemap.xml.gz
```

Build complet, sitemap généré, toutes les pages de la nav présentes.

---

## État Git

```text
 M .gitignore                                              (déjà acquis, ajout .claude/ hors-session)
 M docs/audits/FW-AUDIT-EXISTING-001.md                    (11 liens cassés convertis en inline code)
?? docs/forge/index.md                                     (créé par ce ticket)
?? docs/index.md                                           (créé par ce ticket)
?? mkdocs.yml                                              (créé par ce ticket)
?? requirements-docs.txt                                   (créé par ce ticket)
```

Vérifications négatives :

- `.claude/` : **absent** de git status (correctement ignoré).
- `.venv/` : **absent** (`git check-ignore` confirme `.gitignore:4:.venv/`).
- `site/` : **absent** (`git check-ignore` confirme `.gitignore:8:site/`).
- Aucun fichier sous `/home/roger/Projets/Forge/` modifié.
- Aucune doc Forge copiée vers `docs/forge/`.

Branche : `main`. Aucun commit créé. Commande de commit suggérée (à exécuter manuellement) :

```bash
git add mkdocs.yml requirements-docs.txt docs/index.md docs/forge/index.md \
        docs/audits/FW-AUDIT-EXISTING-001.md docs/audits/FW-MKDOCS-INIT-001.md \
        .gitignore
git commit -m "feat(docs): init MkDocs skeleton (FW-MKDOCS-INIT-001)"
```

---

## Limites restantes

Ce qui n'est volontairement **pas** fait dans ce ticket :

1. La documentation Forge n'est pas importée — `docs/forge/` ne contient qu'un `index.md` placeholder + `.gitkeep`. → FW-DOCS-IMPORT-001.
2. La landing `public/index.html` n'est pas servie par MkDocs (elle reste un artefact statique distinct, à assembler au moment du déploiement). → FW-LANDING-FINALIZE-001 + FW-BUILD-SCRIPT-001.
3. `site_url: https://forgemvc.com/` est posé mais la décision exacte sur le sous-chemin de publication de la doc (`/`, `/docs/`, `docs.forgemvc.com`) reste ouverte → FW-LANDING-FINALIZE-001.
4. Aucun favicon ni logo n'est défini dans le thème — sera fait à l'import des assets Forge (`docs/forge/static/`) en FW-DOCS-IMPORT-001.
5. `docs/.gitkeep` et `docs/forge/.gitkeep` sont laissés en place : inoffensifs pour MkDocs, retirés trivialement plus tard si désiré.
6. `extra_css` n'est pas activé : sera ajouté à l'import du `docs/stylesheets/extra.css` Forge core.
7. Aucun build CI/CD configuré.
8. Aucun déploiement.
9. Ce rapport `FW-MKDOCS-INIT-001.md` n'a pas été ajouté à la nav (à faire dans le ticket suivant si désiré — voir Navigation §note).
10. Le rapport FW-AUDIT-EXISTING-001 a été modifié pour rendre `--strict` vert. Si une autre lecture de l'audit hors MkDocs est souhaitée (par exemple dans un éditeur Markdown standard), les liens transformés ne sont plus cliquables. Acceptable car les chemins restent visibles en clair.
11. Aucun commit créé.

---

## Prochain ticket recommandé

**FW-DOCS-IMPORT-001 — Importer en liste blanche la documentation Forge**

Pré-requis désormais satisfaits :

- `mkdocs.yml` opérationnel ;
- `requirements-docs.txt` figé ;
- venv `.venv/` fonctionnel (ignoré par Git) ;
- `docs/forge/` réservé et prêt à recevoir l'import ;
- source documentaire identifiée et vérifiée : `/home/roger/Projets/Forge/docs/`.

Règle déjà fixée et à respecter strictement :

```text
Source       : /home/roger/Projets/Forge/docs/
Méthode      : import contrôlé par liste blanche
Interdit     : copie globale du dépôt Forge
Interdit     : import de cert.pem, key.pem, .env*, core/, mvc/, etc.
Cible        : docs/forge/ uniquement
Validation   : mkdocs build --strict doit toujours passer après import
```

Périmètre recommandé pour FW-DOCS-IMPORT-001 :

1. Écrire `scripts/sync-docs-from-forge.sh` avec liste blanche explicite des sous-dossiers et fichiers à importer.
2. Importer une **première vague restreinte** (`installation.md`, `getting-started.md`, `15-minutes.md`, `guide.md`, `concepts.md`) pour valider la mécanique.
3. Auditer les liens internes pour `caucrogegit.github.io/Forge/` et les transformer en liens MkDocs relatifs (`./`).
4. Étendre la navigation `mkdocs.yml` pour exposer les pages importées.
5. Rebuild `mkdocs build --strict` à zéro warning.
6. Documenter la liste blanche et l'ordre des futures vagues d'import.
