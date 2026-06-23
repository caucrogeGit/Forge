# OFFICIAL-SITE-LOCAL-DOCS-LINKS-001 — Liens documentaires locaux pour forgemvc.com

## Objectif

Le site officiel `forgemvc.com` doit servir sa propre documentation locale,
pas un miroir GitHub Pages.

## Règle de contrat public

Le site officiel `forgemvc.com` **ne doit pas** utiliser GitHub Pages
(`caucrogegit.github.io/Forge`) pour sa documentation interne.

Les liens internes de documentation doivent cibler :

- des chemins relatifs au domaine : `/docs/forge/...` ;
- ou l'URL canonique complète : `https://forgemvc.com/docs/forge/...`.

GitHub Pages peut continuer d'exister comme miroir technique, mais la
landing publique et la documentation publiée par MkDocs ne doivent plus
en dépendre pour leur navigation interne.

## Constat avant ticket

`public/index.html` contenait **49 occurrences** de
`https://caucrogegit.github.io/Forge/...` dans les attributs `href` de la
landing publique (menu de navigation, sections Installation, Starters,
Référence API, Architecture, Déploiement, etc.).

Conséquence : la navigation interne du site officiel renvoyait
l'utilisateur vers un autre domaine pour consulter sa propre
documentation.

## Correction appliquée

1. Substitution mécanique dans `public/index.html` :

   ```text
   https://caucrogegit.github.io/Forge/   →   /docs/forge/
   ```

   Le préfixe de chemin reste identique (`install/windows-wsl/`,
   `starters/01-contact-simple/`, etc.), seul l'hôte change. Toutes les
   cibles existent localement sous `docs/forge/` et sont déclarées dans
   `mkdocs.yml`.

2. Les attributs `target="_blank" rel="noopener noreferrer"` sont
   conservés tels quels : le ticket impose de ne pas modifier le design
   de la landing. Un ticket de suivi pourra réévaluer l'ouverture en
   nouvel onglet pour une navigation interne.

3. Les liens externes légitimes restent inchangés :

   - GitHub : `https://github.com/caucrogeGit/Forge`
   - PyPI et autres ressources externes assumées.

## Garde-fou de régression

`scripts/check_no_github_pages_docs.py` audite récursivement la landing
et la documentation, et échoue dès qu'un lien actif (`href`/`src` HTML,
lien Markdown `](...)`) cible `caucrogegit.github.io/Forge`.

Périmètre scanné : `public/`, `landing/`, `docs/`, `dist/`, `site/`.

Exclusions justifiées :

- `sources/forge-landing/` — archive de la landing pré-migration ;
- `docs/audits/` — audits du site officiel décrivant la migration ;
- `docs/forge/history/` — audits historiques de Forge core importés ;
- `site/search/` — index de recherche MkDocs.

Dans ces zones, l'URL apparaît en texte ou en code (`<code>…</code>`),
comme référence d'incidents ou de tickets clos. Aucune navigation
interne ne dépend de ces mentions.

Usage :

```bash
python3 scripts/check_no_github_pages_docs.py
```

## Validation

```bash
.venv/bin/python -m mkdocs build --strict
python -m py_compile scripts/*.py
bash -n scripts/*.sh
git diff --check
python3 scripts/check_no_github_pages_docs.py
```

Toutes les validations passent (exit 0). Le grep de contrôle global
défini dans le ticket :

```bash
grep -RIn "caucrogegit.github.io/Forge" dist site docs landing public . \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__
```

ne retourne plus aucun lien actif dans la landing ou dans
`dist/`/`site/` hors des zones explicitement archivées.

## Hors-scope (à traiter séparément)

- **Venv obsolète** : `.venv/bin/*` contient encore des shebangs vers
  l'ancien chemin du projet (`/home/roger/Projets/Forge-web/...`), suite
  au renommage `Forge-web` → `Forge-official-site`. Conséquence :
  `scripts/build-site.sh` échoue à l'étape `mkdocs build` car le
  binaire `mkdocs` ne s'exécute pas via son shebang. Workaround utilisé
  pour ce ticket : `.venv/bin/python -m mkdocs build --strict`. Une
  recréation du venv (`python -m venv .venv && .venv/bin/pip install -r
  requirements-docs.txt`) restaurera des shebangs corrects.

- **Formulaire de recherche** : `public/index.html` ligne 49 cible
  `action="search/"`. Depuis `/`, cela résout vers `/search/` alors que
  l'index MkDocs est sous `/docs/search/`. Hors-scope du présent
  ticket — à corriger dans un ticket dédié au formulaire de recherche.
