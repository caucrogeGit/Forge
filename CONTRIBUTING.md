# Contribuer à Forge

Merci de l'intérêt que vous portez à Forge.

## Cadre philosophique

Avant de contribuer, lisez la [charte philosophique](CHARTE_DOC.md) — elle
définit les principes de Forge et les règles d'évolution qui s'appliquent à
toute modification du framework.

Les décisions architecturales structurantes sont documentées dans
[`docs/adr/`](docs/adr/). Toute contribution qui touche au périmètre du
`core/`, à l'API publique ou aux conventions de code doit s'appuyer sur un
principe de la charte ou faire l'objet d'une nouvelle ADR.

## Comment contribuer

1. Forkez le dépôt
2. Créez une branche depuis `main` : `git checkout -b ma-contribution`
3. Committez vos changements avec un message clair
4. Ouvrez une Pull Request en décrivant ce que vous avez fait et pourquoi

## Cession de droits

En soumettant une contribution (Pull Request, patch, suggestion de code), vous
acceptez de céder l'intégralité des droits de propriété intellectuelle sur
cette contribution à Roger Lequette, sans restriction et sans compensation.

Votre contribution sera intégrée sous la même licence propriétaire que le
reste du projet (voir [LICENSE](LICENSE)).

## Ce que nous acceptons

- Corrections de bugs
- Améliorations de performances
- Documentation

## Ce que nous n'acceptons pas

- Ajout de dépendances externes au runtime
- Changements qui cassent la compatibilité ascendante sans discussion préalable

## Lancer les tests

### Première installation (clone frais)

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# ou : .venv\Scripts\activate      # Windows

# Installer le core + les outils de dev + les 11 modules opt-in
pip install -e .
pip install -r requirements-dev.txt

# Vérifier : les 11 modules opt-in sont importables
python -c "import forge_mvc_mfa, forge_mvc_rbac, forge_mvc_workflow, forge_mvc_stats, forge_mvc_files, forge_mvc_images, forge_mvc_audio, forge_mvc_iot, forge_mvc_video, forge_mvc_pivot, forge_mvc_mail; print('OK')"

# Lancer la suite complète
pytest
```

Résultat attendu : **~9 349 passed, 2 skipped**.

### Cycle de développement

Une fois l'environnement initial créé :

```bash
source .venv/bin/activate
pytest                       # toute la suite (~2 minutes)
pytest -m "not meta"         # tests fonctionnels uniquement (plus rapide)
pytest -m meta               # tests de cohérence projet uniquement
```

### Dépannage : `ModuleNotFoundError: forge_mvc_mfa` (ou autre)

Cause typique : la commande `pip install -r requirements-dev.txt` n'a pas
été lancée, ou un module opt-in vient d'être ajouté/déplacé.

Solution :

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
```

---

## Checklist release

Avant de préparer une release ou de fusionner un changement de fond, exécuter :

```bash
python -m pytest tests/ -q
forge check:model
python -m mkdocs build --strict
python -m pip install -e . --no-deps             # rafraîchit l'entry point forge
python -m pip install -r requirements-dev.txt   # garantit que les 11 modules opt-in sont à jour
```

Pour lancer uniquement les tests fonctionnels du framework (plus rapide) :

```bash
python -m pytest -m "not meta" -q
```

Pour lancer uniquement les tests de cohérence projet (doc, versions, charte) :

```bash
python -m pytest -m meta -q
```

Les tests dans `tests/meta/` vérifient la cohérence de la documentation, des ADR
et de la structure du projet. Ils ne testent pas le comportement du framework
lui-même (cf. charte 3.E).

Pour le modèle d'entités, vérifier aussi que :

- les JSON invalides bloquent la génération ;
- les fichiers manuels existants ne sont pas écrasés ;
- les contraintes SQL avancées restent dans des scripts applicatifs séparés, jamais dans les fichiers générés sous `mvc/entities/`.

## Synchronisation du venv avec le code source

Forge est installé dans le venv local et via pipx à partir d'un wheel
précompilé (`dist/forge_mvc-X.Y.Z-py3-none-any.whl`). Après tout bump
de version dans `pyproject.toml`, il faut régénérer ce wheel et le
réinstaller :

```bash
# Régénérer le wheel à partir du code source actuel
python -m build --wheel

# Réinstaller dans le venv local (adapter X.Y.Z à la version cible)
source .venv/bin/activate
pip install --force-reinstall --no-deps dist/forge_mvc-X.Y.Z-py3-none-any.whl
deactivate

# Mettre à jour l'installation pipx
pipx install --force dist/forge_mvc-X.Y.Z-py3-none-any.whl
```

Vérifier ensuite :

```bash
forge --version
# Doit afficher la version cible
```

**Pourquoi cette étape manuelle ?** Forge utilise `forge.py` comme module
standalone (`py-modules = ["forge"]` dans `pyproject.toml`). Cette structure
ne supporte pas le mode édition (`pip install -e .`) de façon fiable —
les modifications du source ne se reflètent pas automatiquement dans le venv.

Les deux invocations suivantes sont équivalentes et supportées :

```bash
python forge.py --version    # script direct (développement)
python -m forge --version    # module Python (recommandé en production)
forge --version              # après pip install (entry point déclaré)
```

La restructuration en package `forge/` a été évaluée (`PACKAGING-FORGE-MODULE-001`)
et écartée : `forge.py` et `forge/` ne peuvent pas coexister, et 236 imports
`forge_cli` dans les tests empêchent une migration sans risque.

## Modifier la landing page

La landing page de Forge a deux sources canoniques distinctes :

| Source | Cible générée |
|---|---|
| `mvc/views/landing/index.html` | `docs/index.html` |
| `static/` (CSS, JS, images) | `docs/static/` |

**Workflow complet de modification** :

```bash
# 1. Éditer le HTML
$EDITOR mvc/views/landing/index.html

# 2. Si modification de classes Tailwind, régénérer le CSS
npm run build:css

# 3. Synchroniser vers docs/
forge sync:landing
```

La commande `forge sync:landing` copie :
- `mvc/views/landing/index.html` → `docs/index.html`
- `static/*` → `docs/static/*` (récursif)

**Vérification** : `mkdocs build --strict` doit passer sans warning. Le
site déployé reflètera les modifications après le prochain push.

**Prérequis Tailwind** : `node_modules/` doit être à jour. Si `npm run
build:css` échoue avec *"tailwindcss: not found"*, lancer `npm install`
d'abord.

## Contact

Pour toute question avant de contribuer : forgemvc@gmail.com
