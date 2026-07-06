# ADR-065 : Le squelette de projet vit à la racine (`skeleton/`), paquet Python distinct

## Statut

Acceptée, Forge 1.0.0-rc.x (ticket `SKELETON-TOP-LEVEL-MOVE-001`).
Décision actée ; l'implémentation accompagne cet ADR.
Précise l'emplacement fixé par ADR-024 (bootstrap par squelette).

---

## Date

2026-07-06

---

## Contexte

Le squelette matérialisé par `forge new` vivait sous `skeleton/data/`.
Cet emplacement avait trois justifications techniques : le squelette était une **donnée du paquet** `cli` (`[tool.setuptools.package-data]`), il se **localisait** par le `__file__` du module `cli.skeleton`, et il n'est **consommé que par le CLI** (`forge new`).

Ces raisons sont réelles, mais elles relèvent de l'ingénierie du packaging, pas de l'ergonomie.
Retour terrain : un template de projet est un artefact de premier plan, on s'attend à le trouver en évidence.
Enfoui sous `cli/`, il est difficile à retrouver, ce qui contredit l'esprit de lisibilité de Forge (principe 3).

---

## Décision

Le squelette est déplacé à la racine du dépôt, `skeleton/`, tout en restant un **paquet Python autonome** (il conserve un `__init__.py`).

- `packages` inclut désormais `skeleton*` en plus de `core*`, `cli*`, `integrations*`.
- Les `package-data` (et `exclude-package-data`) sont re-clés sur le paquet `skeleton` (globs `data/**/*` relatifs à ce paquet).
- L'API passe de `from cli.skeleton import materialize, DATA_DIR` à `from skeleton import materialize, DATA_DIR`.
- La localisation reste `DATA_DIR = Path(__file__).resolve().parent / "data"` : elle fonctionne toujours puisque `skeleton` demeure un paquet installé.

Le squelette continue donc de voyager dans le wheel (donnée d'un paquet) et de se localiser par son module, mais il est désormais visible à la racine, à côté de `core/`, `cli/` et `integrations/`.
Le CLI (`forge new`) reste son seul consommateur : la responsabilité ne change pas, seul l'emplacement change.

Conformément à la convention pré-1.0 (bêta), le renommage se fait sans alias de compatibilité : il n'y a pas de code applicatif externe qui importe `cli.skeleton`.

---

## Conséquences

- Le squelette est découvrable immédiatement, à la racine, comme les autres troncs du dépôt.
- Le packaging reste correct : `skeleton/data/**` est empaqueté comme donnée du paquet `skeleton` et présent dans le wheel et le sdist ; `forge new` le matérialise depuis un `pip install`.
- Les imports internes changent (`cli.skeleton` → `skeleton`) ; les garde-fous et outils qui référençaient `cli/skeleton/data` sont repointés vers `skeleton/data`.
- Un garde-fou d'absence vérifie que `cli/skeleton` n'existe plus (anti-régression du déplacement).

### Alternatives écartées

- **Racine hors paquet (`/skeleton/` simple dossier)** : ne serait plus la donnée d'aucun paquet ; inclusion dans le wheel fragile (`data_files`/`force-include`) et plus aucune localisation par `__file__` une fois installé.
- **Laisser sous `cli/` avec un simple pointeur** (README/CLAUDE.md) : documente l'emplacement mais ne règle pas l'ergonomie ; le template reste enfoui.

---

## Charte appliquée

- **Principe 3 (refuser la magie cachée)** : un artefact de premier plan est visible à la racine, pas enfoui dans un sous-paquet.
- **Principe 11 (une seule façon officielle)** : un emplacement unique et évident pour le squelette.

Précise ADR-024 (bootstrap par squelette). Lié à ADR-036 (packaging typé) pour la cohérence des `package-data`.
