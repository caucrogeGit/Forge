# ADR-027 — Extraction de l'i18n vers `forge-mvc-i18n`

## Statut

Acceptée

Amende [ADR-004](004-core-perimeter.md) (périmètre du core minimal) et prolonge
[ADR-021](021-pivot-extraction.md) et [ADR-022](022-mail-extraction.md) :
poursuite du dégraissage du core vers des opt-ins.

---

## Contexte

`core/i18n/` (translator par catalogues JSON, locale par défaut et fallback,
cache, exceptions) **échoue au test de légitimité d'ADR-004** : « si je retire
cette brique du core, une application Forge basique tourne-t-elle encore ? » →
oui. La traduction est un besoin fréquent mais **n'est pas une primitive
générale** du framework, et `core/i18n/` est **autonome** (sa seule dépendance
core est `core.forge` pour les clés de configuration `i18n_default_locale` /
`i18n_fallback_locale` — disponible via `forge-mvc`).

Le module relève donc d'un opt-in, comme stats, workflow, pivot ou mail.

**Particularité — le couplage au générateur CRUD.** Contrairement à mail ou
pivot, `trans()` est tissé dans le **générateur CRUD du cœur** : `forge make:crud`
et les pages publiques émettent des templates qui appellent `{{ trans(...) }}`
(`crud.edit`, `common.save`, `crud.confirm_delete`…). Aujourd'hui le renderer
Jinja du cœur expose toujours `trans` comme global. Une extraction « en dur »
casserait au rendu tout CRUD généré tant que `forge-mvc-i18n` n'est pas installé.

---

## Décision

**Le translator runtime `core/i18n/` est extrait vers l'opt-in
`forge-mvc-i18n`, et le cœur conserve un repli `trans` no-op.**

| Avant | Après |
|---|---|
| `core/i18n/<module>.py` | `forge_mvc_i18n.<module>` (API réexportée par `forge_mvc_i18n`) |
| `from core.i18n import …` | `from forge_mvc_i18n import …` |
| renderer : `trans` = vraie fonction (toujours) | renderer : `trans` = repli no-op ; l'opt-in l'enrichit |

- **Repli no-op du noyau.** Le renderer Jinja (`integrations/jinja2/renderer.py`)
  expose toujours un global `trans` (`_default_trans`) qui **retourne la clé telle
  quelle**. Les templates générés rendent donc sans erreur, traduction ou non.
  Quand `forge-mvc-i18n` est installé, le renderer **remplace** ce repli par la
  vraie fonction `trans()` chargeant les catalogues. C'est exactement le pattern
  déjà utilisé pour `can()` (RBAC fournit un défaut `lambda: False`, l'opt-in
  l'enrichit), deux lignes plus haut dans le même renderer.
- **Clés de configuration conservées dans le noyau.** `i18n_default_locale` et
  `i18n_fallback_locale` restent dans le registre `_DEFAULTS` de `core.forge`,
  comme les clés `mail_*` après ADR-022 : le registre de configuration reste
  centralisé, seul le **code** migre.
- **CLI de scaffolding conservée dans le noyau.** `forge i18n:init` et
  `forge i18n:check` (`cli/assets/i18n.py`) sont **autonomes** : ils créent et
  vérifient `translations/fr.json` sans importer le translator runtime. Ils
  relèvent de l'outillage de projet du CLI cœur et restent disponibles sans
  installer `forge-mvc-i18n`. Seul le translator runtime est extrait.

**Pré-1.0 (convention bêta)** : extraction sans alias déprécié dans le core. Les
anciens chemins `core.i18n` sont supprimés.

---

## Conséquences

- Nouveau paquet `packages/forge-mvc-i18n/` (distribution PyPI séparée, dépend de
  `forge-mvc`).
- Garde-fou d'extraction `I18N-EXTRACT-001` : le core ne contient plus `i18n`, le
  paquet expose l'API publique, le renderer garde un repli no-op.
- Tests i18n protégés par `pytest.importorskip("forge_mvc_i18n")` (core autonome —
  garde-fou `TESTS-OPTIN-IMPORTORSKIP-001`).
- `forge_mvc_i18n` ajouté aux listes opt-in transverses (importorskip,
  core-only-contract, classifiers PyPI, sweep imports docs) + `release-policy.md`.
- DX : un CRUD généré sans `forge-mvc-i18n` affiche les clés brutes (`crud.edit`)
  au lieu du libellé traduit — dégradé mais lisible, jamais cassé.

---

## Suite

- Publication PyPI de `forge-mvc-i18n` (alignée sur la version du core) lors de la
  prochaine release des opt-ins.
