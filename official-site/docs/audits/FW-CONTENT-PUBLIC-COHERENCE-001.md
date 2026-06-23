# Rapport final — FW-CONTENT-PUBLIC-COHERENCE-001

> Date : 2026-05-23
> Branche : `main`
> Périmètre exécuté : strictement celui du ticket. Aucune modification de Forge core, aucun déploiement, aucun touch DNS/Caddy/Proxmox.

---

## Résumé

Trois familles d'incohérences publiques corrigées :

1. **Version landing** : 4 occurrences de `1.0.0-beta.1` → `1.0.0-beta.8` (puce de version, terminal workflow, paragraphe info, titre de section).
2. **Lien PyPI explicite** : ajout d'un `<a href="https://pypi.org/project/forge-mvc/">` autour du texte « Disponible sur PyPI » (auparavant un `<span>` non cliquable).
3. **Lien charte** : `https://github.com/caucrogeGit/Forge/blob/main/CHARTE_DOC.md` → `/docs/forge/charter/` (la charte est désormais publiée sur forgemvc.com via MkDocs).

**Bug systémique majeur corrigé** : 52 occurrences du macro Forge core `{{forge_version}}` (+ `{{forge_tag}}`, `{{python_min}}`) fuyaient dans le HTML publié faute du hook Forge core importé. Le script d'import a été étendu pour substituer ces macros statiquement à l'import (variables figées : `1.0.0b8`, `v1.0.0-beta.8`, `3.12`). 28 fichiers `docs/forge/*` ont changé après ré-import (substitution + sanitisation `index.html` → `index.md` étendue à 65 fichiers vs 52).

**Cohérence licence** : aucun bug. La licence Forge-web (`LICENSE` racine) est explicitement distincte de la licence Forge (« The Forge framework itself is licensed separately »). `docs/forge/licence.md` documente proprement la licence propriétaire de Forge.

**Vérifications finales** :
- `mkdocs build --strict` : 0 warning, 5 INFO non bloquants (inchangé).
- `scripts/build-site.sh` : OK (259 fichiers).
- `scripts/check_local_links.py dist` : **0 lien cassé** sur 18 078 liens locaux.
- 7 sondes HTTP critiques (incluant `/docs/forge/charter/`, `/docs/forge/installation-pipx/`) : toutes **HTTP 200**.

Aucun commit créé.

---

## Incohérences détectées

| # | Cible | Symptôme | Source | Statut |
|---|---|---|---|---|
| 1 | `public/index.html` ligne 79 (puce version) | `v1.0.0-beta.1` alors que Forge est en `beta.8` (CHANGELOG 2026-05-22) | Landing figée à la première bêta | **Corrigé** |
| 2 | `public/index.html` ligne 119 (terminal) | `workflow Forge 1.0.0-beta.1` | Idem | **Corrigé** |
| 3 | `public/index.html` ligne 618 (paragraphe info) | `Forge 1.0.0-beta.1 est une préversion` | Idem | **Corrigé** |
| 4 | `public/index.html` ligne 717 (titre section) | `<h2>Forge 1.0.0-beta.1</h2>` | Idem | **Corrigé** |
| 5 | `public/index.html` (puce « Disponible sur PyPI ») | Texte non cliquable, aucun lien PyPI explicite ailleurs dans la landing | Oubli | **Corrigé** — lien ajouté vers `https://pypi.org/project/forge-mvc/` |
| 6 | `public/index.html` ligne 777 (bouton « Charte ») | Lien externe vers GitHub `CHARTE_DOC.md` alors que la charte est publiée sur forgemvc.com | Héritage Forge core | **Corrigé** → `/docs/forge/charter/` |
| 7 | `docs/forge/*.md` × 52 occurrences | `{{forge_version}}` apparaît littéralement dans le HTML publié | Hook Forge core (`tools/mkdocs_version_hook.py`) non importé en FW-AUDIT-EXISTING-001 (volontairement, périmètre filesystem) | **Corrigé** — substitution statique à l'import |
| 8 | `docs/forge/*.md` × 8 occurrences | `{{forge_tag}}` idem | Idem | **Corrigé** |
| 9 | `docs/forge/*.md` × 10 occurrences | `{{python_min}}` idem | Idem | **Corrigé** |
| 10 | `docs/forge/installation.md`, `rbac.md`, `release-local.md` | Mentions « source-only » pour `forge-mvc-mfa` / `forge-mvc-rbac` | **Forge core dit explicitement** : « non publié PyPI en 1.0.0b8 » | **Non corrigé** — divergence éditoriale entre le ticket (« publié en 1.0.0b8 ») et la documentation officielle Forge core. Le ticket demande de corriger Forge-web seulement et de noter la divergence ; or modifier le contenu publié de Forge core de façon unilatérale risque de publier une affirmation factuellement fausse. Voir « Limites restantes ». |

---

## Corrections landing

`public/index.html` — 4 transformations + 1 ajout + 1 remplacement de lien :

### 1. Version (replace_all)

```diff
- v1.0.0-beta.1                          (puce)
- workflow Forge 1.0.0-beta.1            (terminal)
- Forge 1.0.0-beta.1 est une préversion  (paragraphe)
- <h2>Forge 1.0.0-beta.1</h2>            (titre)
+ ... 1.0.0-beta.8 partout (4 occurrences)
```

### 2. Lien PyPI

```diff
- <span>Disponible sur PyPI</span>
+ <a href="https://pypi.org/project/forge-mvc/" target="_blank" rel="noopener noreferrer" class="hover:underline">Disponible sur PyPI</a>
```

### 3. Lien Charte

```diff
- <a href="https://github.com/caucrogeGit/Forge/blob/main/CHARTE_DOC.md"
-    target="_blank" rel="noopener noreferrer" class="...">Charte</a>
+ <a href="/docs/forge/charter/"
+    class="...">Charte</a>
```

Note : `target="_blank" rel="noopener noreferrer"` retirés car la cible est maintenant interne au site — pas besoin d'ouvrir dans un nouvel onglet.

### Liens conservés intacts

- `https://github.com/caucrogeGit/Forge` (×4, bouton et liens « Voir GitHub ») — pointent bien vers le dépôt source.
- `git clone https://github.com/caucrogeGit/Forge.git` (×2, snippet et data-copy) — correct.
- Les 6 liens externes vers Python.org, MariaDB, Jinja, HTMX, Alpine.js, Tailwind — corrects.

---

## Corrections documentation

Les modifications du contenu importé passent **toujours par `scripts/import_forge_docs.py`** pour rester reproductibles (un ré-import écrase docs/forge/).

### Extension `scripts/import_forge_docs.py`

Ajout d'un dictionnaire `FORGE_MACROS` substitué dans `sanitize_imported_markdown` :

```python
FORGE_MACROS: dict[str, str] = {
    "{{forge_version}}": "1.0.0b8",
    "{{ forge_version }}": "1.0.0b8",
    "{{forge_tag}}": "v1.0.0-beta.8",
    "{{ forge_tag }}": "v1.0.0-beta.8",
    "{{python_min}}": "3.12",
    "{{ python_min }}": "3.12",
}
```

Source de vérité : `pyproject.toml` de Forge core (version `1.0.0b8` au 2026-05-22). Si Forge core release une nouvelle version, **il faudra mettre à jour ce dictionnaire et re-importer**.

Ce que le script ne touche **pas** :

- `{{ csrf_token }}` (14 occurrences) — code Jinja dans les exemples
- `{{ value }}` / `{{ label }}` / `{{ key }}` / `{{ var }}` / `{{ v }}` — variables Jinja dans les exemples
- Autres patterns `{{ ... }}` quelconques

Seuls les 3 macros officiels du hook Forge core sont substitués.

### Bilan import

```text
$ python scripts/import_forge_docs.py
Markdown racine importés : 47
Sous-dossiers : 10 dossiers OK, 4 ignorés
Sanitisation index.html → index.md : 65 fichiers réécrits  ← était 52 avant
Fixups ciblés appliqués : 1
Total : 47 .md racine + 152 dans sous-dossiers (4 ignorés, 0 fuite).
```

28 fichiers `.md` sous `docs/forge/` ont changé de contenu par rapport à l'ancienne version importée (cf. `git status` ci-dessous).

### Pages publiques prioritaires — vérifications après import

| Page | Macro `{{...}}` résiduelle ? | beta.8 cohérent ? | Notes |
|---|---|---|---|
| `docs/forge/index.md` | Non (régénéré par script) | N/A | OK |
| `docs/forge/installation.md` | Non | Oui (`Forge 1.0.0b8`, `v1.0.0-beta.8`) | Mentionne `forge-mvc-mfa` Alpha non publié PyPI — voir Limites |
| `docs/forge/installation-pipx.md` | Non | Oui | OK |
| `docs/forge/release-and-compatibility.md` | Non | OK | OK |
| `docs/forge/compatibility.md` | Non | OK | OK |
| `docs/forge/release-policy.md` | Non | OK | Modules listés en `4 - Beta` (cohérent) |
| `docs/forge/charter.md` | Non | N/A | Page philo, pas de version |
| `docs/forge/licence.md` | Non | N/A | Cohérent avec LICENSE racine |
| `docs/forge/reference.md` | Non | OK (`Forge 1.0.0b8`) | OK |
| `docs/forge/auth.md` | Non | OK | OK |
| `docs/forge/reference/auth-mfa.md` | Non | OK | Mentionne statut MFA — voir Limites |

---

## Versions et statuts publics

État cohérent **affiché publiquement après ce ticket** :

| Élément | Forge-web (après) | Source |
|---|---|---|
| Version annoncée sur la landing | `v1.0.0-beta.8` | aligné sur `CHANGELOG.md` Forge core (2026-05-22) |
| Forge `{{forge_version}}` dans les docs | `1.0.0b8` (PEP 440) | substitution statique |
| Forge `{{forge_tag}}` dans les docs | `v1.0.0-beta.8` (SemVer) | substitution statique |
| Python minimum | `3.12` | `pyproject.toml` |
| Package PyPI principal | `forge-mvc` | landing + docs |
| Statut Forge core | bêta publique (`--pre` requis) | landing + `installation-pipx.md` |
| Modules opt-in (RBAC / Workflow / Stats) | `4 - Beta` selon `release-policy.md` | cohérent avec ticket |
| Module MFA | « Alpha — non publié PyPI en `1.0.0b8` » (Forge core dit ainsi) | **divergent vs ticket** — voir Limites |
| Module Media | (statut non révisé dans ce ticket) | — |

---

## Liens GitHub / PyPI / Charte

### Landing (`public/index.html`)

| Lien | Cible après ticket | Statut |
|---|---|---|
| Bouton « Voir GitHub » (×2) | `https://github.com/caucrogeGit/Forge` | OK (dépôt source) |
| Snippet `git clone` × 2 (bloc + data-copy) | `https://github.com/caucrogeGit/Forge.git` | OK |
| « Disponible sur PyPI » | `https://pypi.org/project/forge-mvc/` | **nouveau** |
| « Charte » (footer) | `/docs/forge/charter/` | **modifié** (avant : GitHub) |
| Dropdown « Projet > GitHub » | `https://github.com/caucrogeGit/Forge` | OK |
| Doc liens internes `./docs/forge/...` × 41 | `/docs/forge/...` | OK (FW-LANDING-FINALIZE-001) |

### `mkdocs.yml`

- `repo_url: https://github.com/caucrogeGit/Forge-web` — OK (dépôt Forge-web)
- `site_url: https://forgemvc.com/docs/` — OK
- Aucun lien CHARTE_DOC.md vers GitHub

### Docs importées (`docs/forge/`)

Les pages Forge importées conservent leurs liens internes Markdown vers `charter.md` (relative), qui résolvent vers `/docs/forge/charter/` après build. Cohérent avec la landing.

---

## Licence

Vérifié :

- `LICENSE` racine Forge-web : **« All rights reserved unless explicitly stated otherwise. »** + mention explicite « The Forge framework itself is licensed separately in its own repository. »
- `LICENSE` racine Forge core : **« Forge — Licence propriétaire / source disponible »**, copyright Roger Cauchon, tous droits réservés
- `docs/forge/licence.md` (importé) : documente clairement « licence propriétaire / source disponible » de Forge

**Cohérence** : OK. Aucun risque de laisser croire que Forge-web change la licence de Forge core. Aucun emploi de « open source » ni « FOSS » dans les pages publiques.

**Aucune correction nécessaire**.

---

## Vérifications MkDocs

```text
$ mkdocs build --strict
INFO    -  Documentation built in 8.99 seconds
```

**0 WARNING**, 5 INFO non bloquants — strictement les mêmes que FW-NAV-DOCS-STRUCTURE-001 et FW-LOCAL-QA-001 (liens « dossier » dans deux pages).

Aucune régression introduite. La substitution des macros (×52) n'a généré aucun nouveau warning.

---

## Vérifications liens

```text
$ python3 scripts/check_local_links.py dist

Racine          : /home/roger/Projets/Forge-web/dist
Fichiers HTML   : 208
Liens analysés  : 40524
Liens externes  : 22446
Liens locaux    : 18078
Cibles uniques  : 129
Liens cassés    : 0

OK — aucun lien local cassé.
```

Évolution depuis FW-NAV-DOCS-STRUCTURE-001 :

| Métrique | FW-NAV-DOCS-STRUCTURE-001 | FW-CONTENT-PUBLIC-COHERENCE-001 | Δ |
|---|---|---|---|
| Fichiers HTML | 207 | 208 | +1 (ce rapport) |
| Liens analysés | 40 377 | 40 524 | +147 |
| Liens locaux | 17 993 | 18 078 | +85 |
| Liens cassés | **0** | **0** | 0 |

Le nouveau lien PyPI ajouté dans la landing (externe) et le lien charte interne (`/docs/forge/charter/`) sont tous deux propres.

---

## Sondes HTTP

```text
200 | /
200 | /docs/
200 | /docs/forge/charter/
200 | /docs/forge/installation/
200 | /docs/forge/release-and-compatibility/
200 | /docs/forge/licence/
200 | /docs/forge/installation-pipx/
```

7 URLs critiques testées via `python3 -m http.server -d dist`. Toutes répondent **HTTP 200**.

Extrait du HTML servi à `/` :

```text
v1.0.0-beta.8
<a href="https://pypi.org/project/forge-mvc/" ...>Disponible sur PyPI</a>
workflow Forge 1.0.0-beta.8
Forge 1.0.0-beta.8 est une préversion
<h2>Forge 1.0.0-beta.8</h2>
<a href="/docs/forge/charter/"
```

Confirmation visuelle que toutes les transformations sont bien rendues.

---

## État Git

30 fichiers modifiés, dont 28 sous `docs/forge/*` du fait du ré-import avec substitution des macros :

```text
 M public/index.html                                       (5 changements : version × 4 + PyPI + charte)
 M scripts/import_forge_docs.py                            (+ FORGE_MACROS + substitution dans sanitize)
 M docs/forge/15-minutes.md                                (substitution macros)
 M docs/forge/app-complete-tutorial.md
 M docs/forge/auth.md
 M docs/forge/compatibility.md
 M docs/forge/deploy-advanced.md
 M docs/forge/deployment.md
 M docs/forge/guide.md
 M docs/forge/history/audits/findings-tracker.md
 M docs/forge/installation-github.md
 M docs/forge/installation-pipx.md
 M docs/forge/installation-windows.md
 M docs/forge/installation.md
 M docs/forge/lts-policy.md
 M docs/forge/media.md
 M docs/forge/profiles.md
 M docs/forge/rbac.md
 M docs/forge/reference.md
 M docs/forge/reference/api.md
 M docs/forge/reference/auth-mfa.md
 M docs/forge/reference/cli-commands.md
 M docs/forge/release-local.md
 M docs/forge/release-policy.md
 M docs/forge/stability-contract.md
 M docs/forge/starters/01-contact-simple/index.md
 M docs/forge/starters/02-utilisateurs-auth/index.md
 M docs/forge/starters/03-carnet-contacts/index.md
 M docs/forge/starters/04-suivi-comportement-eleves/index.md
 M docs/forge/testing/tickets/ft-01-install-version-check-001.md
?? docs/audits/FW-CONTENT-PUBLIC-COHERENCE-001.md          (ce rapport)
```

Vérifications négatives :

- `git diff --check` = 0
- `.claude/` : **absent** de git status (correctement ignoré)
- Forge core : **intact** (`git -C /home/roger/Projets/Forge status --short` vide)
- `dist/`, `site/`, `.venv/` : tous ignorés

Branche : `main`. Aucun commit créé.

Commande de commit suggérée :

```bash
git add public/index.html scripts/import_forge_docs.py docs/forge/ \
        docs/audits/FW-CONTENT-PUBLIC-COHERENCE-001.md
git commit -m "docs(public): align version + PyPI + charter + macros (FW-CONTENT-PUBLIC-COHERENCE-001)"
```

---

## Limites restantes

1. **Divergence éditoriale ticket vs Forge core (MFA / RBAC / Media « source-only »)**

   Le ticket affirme : « `forge-mvc-mfa` publié en `1.0.0b8` mais statut Alpha », « `forge-mvc-rbac` publié en `1.0.0b8` ».

   Forge core (dernière édition 2026-05-22) dit :

   - `docs/forge/installation.md` : « `forge-mvc-mfa` … **Alpha** — non publié PyPI en `1.0.0b8` »
   - `docs/forge/rbac.md` × 2 : « `forge-mvc-rbac` (source-only en `1.0.0b8` — voir … ) »
   - `docs/forge/release-local.md` : « Prérequis : `forge-mvc-mfa` installé (source-only — `pip install -r requirements-dev.txt` depuis le dépôt). »
   - `docs/forge/stability-contract.md` : « `forge-mvc-mfa` (Alpha) … Non publié PyPI en `1.0.0b8` — publication future. »

   **Décision prise dans ce ticket** : NE PAS appliquer une réécriture automatique « source-only » → « publié sur PyPI ». Raisons :

   - L'imposer via `KNOWN_FIXUPS` réécrirait un message éditorial Forge core nuancé, avec un fort risque de publier une affirmation factuellement fausse si MFA/RBAC ne sont effectivement pas (encore) sur PyPI au moment du déploiement.
   - La divergence demande une vérification de fait (présence réelle sur `pypi.org/project/forge-mvc-mfa/`) et un alignement éditorial **côté Forge core** avant que Forge-web ne le reflète.

   **À faire dans un ticket suivant** : vérifier l'état PyPI réel des modules opt-in et, selon le résultat :
   - soit ouvrir un ticket Forge (hors ce projet) pour mettre à jour les docs de Forge core (recommandé) ;
   - soit, si la divergence est confirmée pérenne, ajouter des `KNOWN_FIXUPS` ciblés en `scripts/import_forge_docs.py`.

2. **Macros figées dans le script** : `FORGE_MACROS` contient des valeurs littérales (`1.0.0b8`, `v1.0.0-beta.8`, `3.12`). À chaque nouvelle release Forge core, il faudra mettre à jour le dictionnaire et re-importer. Une alternative serait de lire dynamiquement `/home/roger/Projets/Forge/pyproject.toml` au moment de l'import — non fait pour ce ticket (couplage filesystem). À évaluer plus tard.

3. **`history/audits/findings-tracker.md` modifié** : contient des macros `{{forge_version}}` historiques (ancien rapport d'audit Forge core). Le fichier a été substitué avec la version courante, ce qui peut introduire une légère incohérence narrative dans le rapport d'audit historique. Effet jugé mineur (rapport interne historique, peu consulté). Non corrigé.

4. **Mention « MariaDB » seule** sur la landing (puce verticale) : Forge supporte aussi SQLite via profils. Non modifié dans ce ticket (hors périmètre version/PyPI/charte). À traiter dans un ticket éditorial dédié si souhaité.

5. **`{{ forge_version }}` avec espaces** (2 occurrences) : prises en charge par `FORGE_MACROS` (paire avec et sans espaces).

6. **Auth MFA marqué « Pre-Alpha » dans le `mkdocs.yml` original de Forge core** : non reporté dans notre nav (ticket FW-NAV-DOCS-STRUCTURE-001 a simplifié en « Auth MFA »). Décision à confirmer.

7. **Pages non corrigées (volume) dans `docs/forge/history/`** : la sanitisation des macros a touché 28 fichiers ; les autres mentions de versions historiques (`beta.5`, `beta.6`, etc.) sont conservées telles quelles dans `history/releases/` car elles sont effectivement historiques.

8. **Aucun commit créé**.

---

## Prochain ticket recommandé

**FW-PUBLISH-READINESS-001 — Préparer la checklist de publication locale avant serveur**

Pré-requis désormais satisfaits :

- contenu public cohérent (version, PyPI, charte) ;
- macros Forge substituées (pas de `{{forge_version}}` qui fuit en HTML) ;
- 0 lien cassé, 7 sondes HTTP critiques OK ;
- ré-import + rebuild reproductibles via scripts ;
- licence claire et distincte (Forge / Forge-web).

Périmètre suggéré pour `FW-PUBLISH-READINESS-001` (à préciser dans son propre ticket) :

1. Liste de contrôle pré-publication : version, dates, captures écran landing, robots.txt/sitemap, headers HTTP attendus, taille `dist/`.
2. Vérification réseau des liens externes critiques (GitHub, PyPI, Python.org, MariaDB) — par sondes HTTP/HEAD ponctuelles.
3. Évaluer si `mkdocs.yml` doit aussi exposer `forge/entities/`, `forge/security/{rbac-contract,rbac-usage}`, ADR-009→014 avant publication.
4. Vérifier la cohérence MFA/RBAC PyPI (cf. Limite #1) — décider de la réécriture des mentions source-only.
5. Préparer un README « comment publier » pour la VM web (sans la déployer).
6. Inventaire des secrets et exigences DNS minimum (mémo, pas activation).
7. Ne **pas** déployer ni configurer Caddy / Proxmox dans ce ticket.
