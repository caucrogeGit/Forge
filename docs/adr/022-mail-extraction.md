# ADR-022 : Extraction de l'email vers `forge-mvc-mail`

## Statut

Acceptée

Amende [ADR-004](004-core-perimeter.md) (périmètre du core minimal) et prolonge [ADR-021](021-pivot-extraction.md) : poursuite du dégraissage du core vers des opt-ins.

---

## Contexte

`core/mail/` (composition de messages, transports, templates Jinja, journalisation, CLI `mail:*`) **échoue au test de légitimité d'ADR-004** : « si je retire cette brique du core, une application Forge basique tourne-t-elle encore ? » → oui.
L'email est un besoin fréquent mais **n'est pas une primitive générale** du framework, et `core/mail/` est **autonome** (aucun autre module du core ne l'importe ; sa seule dépendance core est `core.forge` pour la config et `core.database.db` pour le journal, disponibles via `forge-mvc`).

Le module relève donc d'un opt-in, comme stats, workflow ou pivot.

---

## Décision

**`core/mail/` et la CLI `cli/mail.py` sont extraits vers l'opt-in `forge-mvc-mail`.**

| Avant | Après |
|---|---|
| `core/mail/<module>.py` | `forge_mvc_mail.<module>` (API réexportée par `forge_mvc_mail`) |
| `cli/mail.py` | `forge_mvc_mail.cli` |
| `from core.mail import …` | `from forge_mvc_mail import …` |

- La famille CLI `mail:init / test / render / doctor / logs` reste exposée par la CLI cœur, **routée vers le paquet** via `try / except ImportError` (même mécanisme que `iot:*` / `video:*` / `make:pivot-crud`).
- Le starter `send-email` (palier avancé de `welcome-forge`) importe désormais `forge_mvc_mail`.
  Ce n'est **pas** une nouveauté de périmètre : `welcome-forge` comporte déjà un palier avancé qui dépend d'un opt-in (`file-upload` → `forge_mvc_files`).
  `send-email` reste donc en place ; un parcours dédié `welcome-mail` est créé séparément (suite de ce chantier) pour approfondir l'usage de l'email.

**Pré-1.0 (convention bêta)** : extraction sans alias déprécié dans le core.
Les anciens chemins `core.mail` et `cli.mail` sont supprimés.

---

## Conséquences

- Nouveau paquet `packages/forge-mvc-mail/` (distribution PyPI séparée, dépend de `forge-mvc` et `jinja2`).
- Garde-fou d'extraction `MAIL-EXTRACT-001` : le core ne contient plus `mail`, le paquet expose l'API publique et la CLI.
- Tests mail protégés par `pytest.importorskip("forge_mvc_mail")` (core autonome, garde-fou `TESTS-OPTIN-IMPORTORSKIP-001`).
- `forge_mvc_mail` ajouté aux listes opt-in transverses (importorskip, core-only-contract, classifiers PyPI, sweep imports docs) + `release-policy.md`.

---

## Suite

- **`WELCOME-MAIL`** : parcours pédagogique `welcome-mail` (premier envoi, composition, transports, templates, config, diagnostic), chantier dédié.
