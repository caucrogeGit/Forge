# ADR-021, Extraction de pivot advanced vers `forge-mvc-pivot`

## Statut

Acceptée

Amende [ADR-004](004-core-perimeter.md) (périmètre du core minimal) et
s'inscrit dans la même logique que [ADR-018](018-image-module-extraction.md) /
[ADR-019](019-upload-extraction.md).

---

## Contexte

Après les extractions d'ADR-004 (MFA, OIDC supprimé, RBAC, workflow, stats) et
d'ADR-018/019 (images, files), un audit du `core/` a identifié des briques
encore présentes qui **échouent au test de légitimité d'ADR-004** : « si je
retire cette brique du core, une application Forge basique tourne-t-elle
encore ? ».

`core/pivot_advanced.py` est l'une d'elles :

- C'est une **fonctionnalité avancée** de données, la persistance
  d'associations `many_to_many` **enrichies** (lignes de jointure portant des
  attributs), avec son générateur `forge make:pivot-crud`.
- Elle n'est **pas** une primitive générale du framework : une application
  basique (HTTP, MVC, CRUD simple) tourne sans elle.
- Elle est **autonome** : aucun autre module du core ne l'importe ; ses accès
  base passent par les helpers injectables `core.database.db` (chargés
  paresseusement), comme les autres opt-ins (stats).

Elle relève donc d'un module opt-in, au même titre que stats ou workflow.

---

## Décision

**`core/pivot_advanced.py` et son générateur `cli/entities/make_pivot_crud.py`
sont extraits vers l'opt-in `forge-mvc-pivot`.**

| Élément avant | Élément après |
|---|---|
| `core/pivot_advanced.py` | `forge_mvc_pivot.service` (réexporté par `forge_mvc_pivot`) |
| `cli/entities/make_pivot_crud.py` | `forge_mvc_pivot.make_pivot_crud` |
| `from core.pivot_advanced import …` (code généré) | `from forge_mvc_pivot import …` |

- La commande `forge make:pivot-crud` reste exposée par la CLI cœur, mais est
  **routée vers le paquet** via `try / except ImportError` (même mécanisme que
  `iot:*` / `video:*`) : si `forge-mvc-pivot` n'est pas installé, un message
  invite à l'installer.
- Le code généré par `make:pivot-crud` importe désormais `forge_mvc_pivot` ;
  l'application doit donc installer l'opt-in pour utiliser un sous-CRUD pivot.

**Pré-1.0 (convention bêta)** : extraction sans alias déprécié dans le core
(pas d'utilisateurs externes à protéger). Les anciens chemins
`core.pivot_advanced` et `cli.entities.make_pivot_crud` sont supprimés.

---

## Conséquences

- Nouveau paquet `packages/forge-mvc-pivot/` (distribution PyPI séparée,
  dépend de `forge-mvc`).
- Les tests pivot importent `forge_mvc_pivot` et sont protégés par
  `pytest.importorskip("forge_mvc_pivot")` (core reste autonome, garde-fou
  `TESTS-OPTIN-IMPORTORSKIP-001`).
- Garde-fou d'extraction `PIVOT-EXTRACT-001` : le core ne contient plus
  `pivot_advanced`, le paquet expose l'API publique.
- Aucun starter gelé ni progression welcome n'est impacté (contrairement à une
  éventuelle extraction de `mail`, qui porte le starter `send-email` de la
  progression welcome-forge, traitée séparément si décidée).

---

## Pistes connexes (non tranchées ici)

Le même test de légitimité désigne deux autres candidats, à traiter par des
ADR dédiés s'ils sont retenus :

- **`core/mail/`**, autonome, non vital ; extraction plus lourde car elle
  déplace la famille CLI `mail:*` et sort le starter `send-email` de la
  progression welcome-forge gelée (réduction du contrat 1.0).
- **`core/i18n/`**, autonome mais de faible volume ; gain marginal.
