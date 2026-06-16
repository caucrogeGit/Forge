# Conventions internes de Forge

> **Document opérationnel.** Cette page consolide les patterns émergents
> de la refonte Forge 3.0 (phase 14). Elle complète la charte philosophique
> (`CHARTE_DOC.md`) et les ADR (`docs/adr/`) avec des techniques de travail
> concrètes éprouvées sur le terrain.
>
> **Audience** : contributeurs (humains et agents IA) qui rédigent du code,
> écrivent des tests, modifient la documentation ou structurent le projet.

## Organisation

Quatre sections thématiques :

- **A. Audit avant action** — 5 patterns
- **B. Tests : conventions et patterns** — 6 patterns
- **C. Code : architecture** — 6 patterns
- **D. Documentation : structure** — 3 patterns

Total : 19 patterns documentés.

Chaque pattern présente son énoncé court, le contexte d'apparition (ticket
d'origine) et un exemple ou une règle pratique.

Une **annexe « Glossaire »** (en fin de page) fixe le vocabulaire canonique
de Forge — quel mot pour quel objet — et n'entre pas dans le décompte des
19 patterns.

---

## A. Audit avant action

### A.1 — Audit 5 racines pour renommages et extractions

Pour tout renommage massif d'API ou extraction modulaire, grep sur les
**5 racines productives** :

```
core/   mvc/   forge_cli/   tests/   integrations/
```

Manquer une racine cause des call sites oubliés qui ne se révèlent
qu'au premier `pytest`. Pour les déplacements de fichiers de
**documentation**, ajouter aussi les `*.md` à plat (6e source).

Utiliser `--exclude=<garde_fou>.py` pour éviter les faux positifs du test
qui vérifie l'absence.

Origine : `WORKFLOW-EXTRACT-001` (consommateur dans `integrations/` manqué
au grep initial).

### A.2 — Vérifier `.gitignore` avant de refondre un fichier

Avant d'éditer un fichier de configuration ou de briefing, vérifier qu'il
n'est pas dans `.gitignore`. Un fichier ignoré peut être un brouillon
personnel qui devient partagé au moment de la refonte — décision explicite
à prendre.

Origine : `CLAUDE-MD-UPDATE-001` (le fichier était dans `.gitignore`
depuis longtemps, retiré et commité pour la première fois).

### A.3 — Vérifier l'historique git pour les suppressions

Avant de supprimer un ensemble cohérent de fichiers (shims d'une
extraction, fichiers d'une feature retirée), faire :

```bash
git log --diff-filter=A --name-only -- core/<dir>/
```

Cela identifie tous les fichiers créés à la période de l'extraction,
pas seulement ceux qu'on devine par nom. Un fichier oublié laisse un
résidu invisible.

Origine : `EXTRACTION-CLEANUP-SHIMS-001` (3e shim `totp_replay.py`
oublié, identifié grâce à l'historique git).

### A.4 — Vérifier la production interne avant suppression nette

Avant toute suppression d'une API publique, vérifier que du code
applicatif déjà déployé ne dépend pas de cette API. La note pré-3.0
ne protège que des utilisateurs externes — le code propre du mainteneur
peut être en production interne.

Si oui : suppression partielle (création supprimée, vérification conservée)
+ mécanisme de migration au prochain usage. Si non : suppression nette.

Origine : `HASHING-PBKDF2-REMOVE-001` (proposition initiale de suppression
nette corrigée parce que des hashes PBKDF2 vivaient en production interne).

### A.5 — Audit étendu pour la documentation référencée par les tests

Quand un fichier de documentation est déplacé ou découpé, vérifier qu'aucun
test ne le référence par chemin codé en dur (lecture de contenu, recherche
de mots-clés). Ce sont des dépendances silencieuses faciles à oublier au
grep initial.

Origine : `DOCS-REFERENCE-SPLIT-001` (8 fichiers de tests redirigés après
le découpage de `docs/reference.md` en 11 sous-fichiers).

---

## B. Tests : conventions et patterns

### B.1 — Helper local pour formats legacy

Pour tester un format dont l'API de création publique a été supprimée
(par exemple : hash PBKDF2 dont la création a disparu), créer un helper
privé dans le fichier de test qui recrée le format au niveau bytes (avec
`hashlib`, `os.urandom`, etc.) plutôt que d'importer depuis le code de
production.

```python
# Dans le fichier de test
def _make_legacy_pbkdf2_hash(password: str) -> str:
    import hashlib, os
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260000)
    return f"pbkdf2:sha256:260000:{salt.hex()}:{dk.hex()}"
```

Origine : `HASHING-PBKDF2-REMOVE-001`, `LANG-MIGRATION-001`.

### B.2 — Inspection du code source via `module.__file__`

Un test qui inspecte le contenu source d'un module doit accéder au fichier
via `module.__file__` plutôt qu'un chemin codé en dur :

```python
# Robuste au déplacement
from forge_mvc_mfa import mfa as mfa_mod
content = Path(mfa_mod.__file__).read_text()

# Fragile
content = Path("core/auth/mfa.py").read_text()
```

Origine : `EXTRACTION-CLEANUP-SHIMS-001`.

### B.3 — `PROJECT_ROOT` partagé dans les tests

Éviter `Path(__file__).parents[N]` codé en dur dans les tests. Si un
fichier de test est déplacé dans un sous-dossier, le `N` doit changer —
potentiellement dans des dizaines de fichiers.

Recommandation : exporter une constante depuis `tests/conftest.py` ou
utiliser une heuristique stable (chercher un marqueur comme `pyproject.toml`).

Origine : `TESTS-CLASSIFY-001`.

### B.4 — Classification sémantique des tests `_001`

La convention `test_<TICKET>_001.py` n'est **pas** un signal de
classification automatique en `tests/meta/`. Critère sémantique :

- Test qui vérifie un **contrat d'absence** (X n'existe plus) ou une
  **migration** (Y a bien été déplacé) → `tests/meta/`
- Test qui valide un **comportement applicatif normal**, même si le nom
  suit le pattern `_001` → reste à plat dans `tests/`

Origine : `TESTS-CLASSIFY-001` (3 fichiers `_001` identifiés comme
fonctionnels et laissés à plat).

### B.5 — Généraliser plutôt que supprimer

Si un test valide un mécanisme via un cas concret qui disparaît, préférer
**généraliser** le test (pour qu'il continue à valider le mécanisme via un
autre cas) plutôt que de le supprimer.

Origine : `CMD-LEGACY-REMOVE-001` (`test_deprecation_policy.py` généralisé
après la suppression de `cmd/`).

### B.6 — Cohérence des noms de fonctions de tests lors d'un renommage d'API

Lors d'un renommage massif d'API publique, **inclure aussi les noms de
fonctions de tests** dans le sed. Un test `def test_creer_session_X():` n'a
plus de sens après le renommage de `creer_session` en `create_session` —
il faut renommer la fonction de test aussi.

```bash
# Inclure les définitions de fonctions de test
sed -i 's/\btest_creer_session\b/test_create_session/g' tests/test_*.py
```

Origine : `LANG-MIGRATION-001` (6 noms de fonctions de tests renommés en
passant).

---

## C. Code : architecture

### C.1 — Pattern `lock + delegate`

Pour les opérations qui doivent être thread-safe **et** réutilisables en
interne (sans acquérir le lock deux fois), séparer en deux fonctions :

```python
def purge_old(self) -> None:
    with self._lock:
        self._do_purge_old()

def _do_purge_old(self) -> None:
    # Logique réelle, sans acquérir le lock
    ...
```

La fonction publique acquiert le lock et délègue. La fonction privée fait
le travail. Réutilisation possible depuis une autre fonction qui détient
déjà le lock.

Origine : Découvert dans l'écosystème Forge (sessions, rate-limit).

### C.2 — Convention `register_<module>_routes(router)`

Les opt-ins Forge exposent une **fonction d'enregistrement**
plutôt qu'un objet `router` à importer puis attacher :

```python
# Dans mvc/routes_<module>.py généré
def register_mfa_routes(router):
    router.add_route("/mfa/setup", controller.setup, methods=["GET", "POST"])
    ...
```

Plus naturel à Python, plus extensible, plus testable que
`from mvc.routes_mfa import router; app.include_router(router)`.

Origine : `MODULES-EXPLICIT-ROUTES-001`.

### C.3 — Note « Module extrait » en tête des pages de référence

Pour chaque module extrait du core (MFA, RBAC, Workflow, Stats), la page
de référence correspondante commence par une note :

```markdown
> **Module extrait** : depuis Forge X.Y, ce code vit dans
> `forge-mvc-<module>`. Voir `packages/forge-mvc-<module>/README.md`
> pour l'installation et l'API. Cette page documente l'API publique
> pour mémoire.
```

Évite la confusion sur "où est le vrai code".

Origine : `DOCS-REFERENCE-SPLIT-001`.

### C.4 — Tests garde-fous pour tickets documentaires

Pour un ticket à profil documentaire structurant (ADR, refonte de fichier
de référence, déduplication), les tests garde-fous vérifient la **présence
des concepts clés** dans le contenu, pas juste l'existence du fichier :

```python
@pytest.mark.parametrize("keyword", ["principe X", "ADR-Y", ...])
def test_mentions_concept(self, keyword):
    assert keyword in content
```

Un fichier dont les concepts disparaissent au fil des éditions serait
silencieusement ineffectif.

Origine : `AUTH-AUDIT-CLARIFY-ARCHITECTURE-001`, `CLAUDE-MD-UPDATE-001`.

### C.5 — Renommage massif avec word boundaries

Pour un sed massif sur des identifiants, **toujours utiliser les word
boundaries `\b`** (GNU sed, Linux) :

```bash
sed -i 's/\best_limite\b/is_rate_limited/g' tests/test_*.py
```

Sans `\b`, `est_limite` matcherait aussi `est_limite_upload` — bug
silencieux. Sur BSD/macOS : `[[:<:]]` et `[[:>:]]` ou installer `gsed`.

Vérifier après par grep :

```bash
grep -r "est_limite" core/ mvc/ tests/ | grep -v "est_limite_upload"
```

Origine : `LANG-MIGRATION-001`.

---

### C.6 — Validation précoce des arguments critiques (anti-erreur-différée)

Une entrée publique du cœur appelée par le code applicatif (contrôleur,
`mvc/routes.py`, boot) doit **valider tôt** ses arguments positionnels critiques,
avec un `TypeError` au message **actionnable**, plutôt que de laisser passer une
valeur invalide qui ne casse que plus loin.

Motivation : l'**erreur différée**. Une valeur fautive fabriquée à un endroit
(ex. `Response("texte")` : le 1er argument positionnel est le `status`) mais
consommée ailleurs (l'envoi de la réponse) produit un traceback qui pointe le
**point de consommation**, pas le code fautif. Valider au moment de la
construction/enregistrement remet l'erreur dans le frame de l'appelant.

Entrées du cœur couvertes (le message nomme le bon usage) :

| Entrée | Argument validé | Ticket |
|---|---|---|
| `Response(status, …)` | `status` entier | `CORE-RESPONSE-STATUS-TYPE-001` |
| `html()` / `BaseController.render()` | `status` entier (2e positionnel ≠ contexte) | `CORE-RENDER-STATUS-TYPE-001` |
| `router.add(…, handler)` | `handler` appelable (à l'enregistrement) | `CORE-ROUTE-HANDLER-CALLABLE-001` |

Critère pour appliquer (et **ne pas** sur-valider, principe 8) : entrée publique,
appelée par le code applicatif, dont un argument positionnel critique mal typé
provoque une erreur **différée**. Le contrat est verrouillé par le test méta
`tests/meta/test_core_early_validation_contract_001.py` — y ajouter une ligne
quand on couvre une nouvelle entrée.

Origine : retours de tests terrain (ADR-009), cycle b17.

---

## D. Documentation : structure

### D.1 — MkDocs strict + liens hors `docs/`

Pour référer depuis une page MkDocs à un fichier situé hors du dossier
`docs/` (par exemple `CHARTE_DOC.md` à la racine du dépôt), utiliser des
**backticks** plutôt qu'un hyperlien :

```markdown
Voir `CHARTE_DOC.md` à la racine du dépôt.
```

Et non :

```markdown
Voir [CHARTE_DOC.md](../CHARTE_DOC.md).  ← warning mkdocs --strict
```

Les backticks rendent le fichier identifiable sans déclencher de résolution
de lien.

Origine : `DOCS-CHARTER-DEDUP-001`.

### D.2 — `docs/history/` comme mémoire brute

Quand un fichier de roadmap ou de documentation devient obsolète, le
déplacer dans `docs/history/` via `git mv` sans fusion ni synthèse. Le
dossier `docs/history/` est une **mémoire brute** du projet, pas une
documentation curée.

La synthèse vit ailleurs : `CHANGELOG.md` pour l'historique des livraisons,
ADR pour les décisions architecturales.

Origine : `DOCS-CONSOLIDATE-ROADMAPS-001`.

### D.3 — Section « Historique » dans la nav MkDocs

Pour les fichiers déplacés dans `docs/history/`, créer (ou enrichir) une
section "Historique" dans `mkdocs.yml` qui les expose. Évite de les retirer
du site (rupture de liens externes potentiels) tout en les marquant
clairement comme historiques.

```yaml
- Historique:
    - Roadmap Forge 1.5 → 2.0: history/forge-roadmap-history-2.0.md
    - Charte v1: history/charte-v1.md
    - Archives post-2.0: history/forge_post_2_0_consolidation_roadmap.md
```

Origine : `DOCS-CONSOLIDATE-ROADMAPS-001`.

---

## Glossaire — vocabulaire canonique

Forge emploie plusieurs mots proches (`module`, `package`, `opt-in`,
`extension`). Ils ne sont **pas** interchangeables : chacun désigne une
facette précise. Cette annexe fixe l'usage. Un audit (juin 2026) a montré
que la confusion supposée entre ces termes était en réalité faible — d'où le
choix de **clarifier par le vocabulaire plutôt que de renommer du code** (un
renommage toucherait le contrat public 1.0 et la charte pour un gain
cosmétique).

| Terme | Sens canonique | À ne pas confondre avec |
|---|---|---|
| **module opt-in** | Paquet pip officiel installé dans l'environnement (`forge-mvc-mfa`, `forge-mvc-images`…), dans `packages/`. C'est le sens de « Modules officiels » (CLAUDE.md) et « modules opt-in » (charte, Principe 8). | le « module de projet » ci-dessous |
| **module de projet** | Brique copiée **dans un projet utilisateur** via `forge module:install` (manifeste `module.json`, registre `forge_modules.json`, dossier `modules/`). | le « module opt-in » pip |
| **package** | Réservé à la **facette distribution PyPI** (`pip install forge-mvc-images`, `pyproject.toml`, dossier `packages/`). Ne pas l'employer pour désigner l'unité fonctionnelle — dire « module opt-in ». | — |
| **opt-in** | **Propriété**, pas un objet : « jamais activé automatiquement » (Principes 7 et 8). Adjectif, pas synonyme de module/package. | un nom d'objet |
| **extension** | Uniquement « **extension de fichier** » (`.png`, validation d'upload) ou une extension d'IDE tierce. **Jamais** synonyme de module/brique. | un module Forge |

**Règle pratique** : quand le mot « module » seul serait ambigu, le qualifier
— « module opt-in » (pip) ou « module de projet » (`forge module:install`).

Origine : arbitrage vocabulaire (juin 2026, consolidation bêta 1.0).

---

## Évolution du document

Ce document s'enrichit au fil des sessions de développement. Quand un
nouveau pattern émerge d'un ticket structurant, l'ajouter dans la section
thématique correspondante avec son ticket d'origine.

À chaque tag majeur (1.0, 2.0…), revoir l'ensemble pour retirer les
patterns devenus obsolètes ou les conventions intégrées automatiquement
au code.

---

## Voir aussi

- `CHARTE_DOC.md` — Charte philosophique (principes non négociables)
- `docs/adr/` — Architecture Decision Records (décisions structurantes)
- `CLAUDE.md` — Briefing pour agents IA
- `CHANGELOG.md` — Historique des livraisons
