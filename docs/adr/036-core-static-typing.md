# ADR-036 — Typage statique du cœur, vérifié en CI

## Statut

Accepté — Forge 1.0.0-beta.17 (ticket `ADR-CORE-STATIC-TYPING-001`).

Issu d'un retour de tests terrain (ADR-009) : en mode strict, Pylance/Pyright
noie l'utilisateur sous des `reportUnknown*` sur les symboles du cœur, car
celui-ci est partiellement typé et n'expose pas ses types (pas de `py.typed`).

---

## Date

2026-06-16

---

## Contexte

Le cœur de Forge est **partiellement typé** : ~66 % des fonctions de `core/`
portent une annotation de retour, mais beaucoup de conteneurs sont nus
(`dict` au lieu de `dict[str, X]`), des paramètres ne sont pas annotés, et
aucun vérificateur n'est exécuté. Mesure initiale : `pyright core/` en mode
**basic** relève **41 erreurs** (dont 32 `reportArgumentType`).

Deux conséquences :

1. **Côté utilisateur.** Aucun paquet ne ship le marqueur `py.typed` (PEP 561).
   Pyright (via Pylance) traite donc `forge-mvc` comme **non typé** : même les
   annotations existantes sont ignorées dans un projet `forge new`. D'où le bruit
   `reportUnknown*` en mode strict (mitigé provisoirement par un override dans le
   squelette, `SKELETON-VSCODE-STRICT-NOISE-001`).
2. **Côté cœur.** Les 41 erreurs basic révèlent de vraies incohérences de type
   non détectées (le contrat public n'est pas vérifié par machine).

Pour un framework, les types **font partie du contrat public** (principe 10 :
« une API publique est un contrat de complétude »).

---

## Décision

Le cœur de Forge est **typé et vérifié statiquement en intégration continue**.

- **Vérificateur : Pyright.** C'est le moteur de Pylance : la CI voit exactement
  ce que voit l'éditeur de l'utilisateur (cohérence terrain). Configuration dans
  `pyproject.toml` (`[tool.pyright]`).
- **Marqueur `py.typed`** ajouté à chaque paquet distribué exposant une API
  importée par le code utilisateur (`core`, `integrations`, et les douze
  `forge_mvc_*`), et inclus dans les wheels (PEP 561). Sans lui, typer le cœur
  ne sert pas l'utilisateur.
- **Stricte par cliquet, pas en big-bang.** On adopte d'abord un niveau qui passe
  au vert (baseline `basic` sur `core/`, après correction des 41 erreurs), puis
  on bascule **module par module** en strict (`# pyright: strict` en tête de
  fichier, en commençant par la surface publique `core/http`), avec une **règle
  de non-régression** en CI (aucune nouvelle erreur).
- **Critère de sortie partiel.** Quand la surface publique (`core/http`,
  `BaseController`) est stricte et `py.typed` publié, l'**override
  `reportUnknown*` du squelette est retiré** (la cause étant traitée).

---

## Conséquences

**Positives :**

- Contrat public vérifié par machine ; meilleure DX (autocomplétion, détection
  d'erreurs dans le code utilisateur) ; bugs de type du cœur attrapés.
- Boucle terrain bouclée : l'override `reportUnknown*` deviendra inutile.

**Coûts :**

- Effort de finition d'annotations + correction des 41 erreurs basic, puis du
  delta strict module par module (chantier multi-tickets, étalé sur la b17).
- Dépendance de développement supplémentaire (`pyright`), exécutée en CI.

---

## Plan (tickets b17)

1. `CORE-TYPING-PYRIGHT-BASELINE-001` — config `[tool.pyright]` (basic),
   `py.typed` (core + integrations + 12 opt-ins, + package-data), correction des
   41 erreurs basic de `core/`, **gate CI** (job pyright), garde-fou méta.
2. `CORE-TYPING-STRICT-HTTP-001` — `core/http` en `# pyright: strict`, conteneurs
   paramétrés ; puis retrait de l'override `reportUnknown*` du squelette.
3. Tickets suivants — cliquet strict sur les autres modules de `core/`
   (`mvc`, `database`, `sessions`, `security`, `forms`, `auth`…).

---

## ADR liés

- Retour terrain encadré par l'**ADR-009** (consolidation bêta, tests terrain).
- Concrétise le **principe 10** (contrat de complétude) appliqué aux types.
- Remplace à terme la mitigation `SKELETON-VSCODE-STRICT-NOISE-001`.

---

## Charte appliquée

- Principe 1 — explicite, testable, durable (types = contrat vérifié).
- Principe 10 — une API publique est un contrat de complétude.
- Principe 2 — petits tickets : cliquet module par module, pas de big-bang.
- Règle A — retirer la cause (cœur non typé), pas seulement le symptôme
  (override de diagnostics).
