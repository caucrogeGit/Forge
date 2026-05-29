# Audit post-publication Forge 1.0.0-beta.12

> Ticket : `RELEASE-BETA12-POST-PUBLISH-VERIFY-001`. Smoke test
> **post-publication** réalisé **hors du dépôt de développement**, depuis
> PyPI, comme un utilisateur externe. Aucun bump, aucune publication,
> aucune modification fonctionnelle. Release auditée : commit `ac7f07b`,
> tag `v1.0.0-beta.12`, versions PyPI `1.0.0b12`.

## Verdict

**GO — release `1.0.0-beta.12` confirmée installable et utilisable.**

L'installation depuis PyPI (`forge-mvc` + `forge-mvc-iot` en `1.0.0b12`),
la création de projets neufs, le starter `welcome-iot`, les commandes IoT
et opt-ins, `forge optin:enable iot` / `forge optin:list` et
`forge iot:doctor` fonctionnent tous depuis la release publiée. Le core
reste indépendant de l'opt-in IoT.

## Environnement de test

```bash
mkdir -p /tmp/forge-b12-post-publish && cd /tmp/forge-b12-post-publish
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
```

Venv neuf, hors dépôt Forge, installation strictement depuis PyPI
(`--pre`). Python 3.12.13. `git`, `openssl`, `npm` présents.

## Installation core seule

`pip install --pre forge-mvc==1.0.0b12` → succès.

- `forge --version` → **`Forge 1.0.0b12`** ;
- `forge help` liste les commandes de base (`new`, `run`, `doctor`,
  `make:entity`, `db:init`, `starter:list`, …).

## Création projet neuf

`forge new forge-b12-core` → projet créé et initialisé (clone du tag
`v1.0.0-beta.12`, env, venv Python, dépendances, npm/Tailwind, certificats
SSL, git init), exit 0.

`forge doctor` dans le projet : **0 erreur**, 2 avertissements attendus
(MFA opt-in absent ; base non encore `db:init`). **Aucune mention ni
erreur liée à `forge-mvc-iot`** → le core reste **indépendant** de l'IoT.

## Installation forge-mvc-iot

`pip install --pre forge-mvc-iot==1.0.0b12` (même venv) → succès.
`pip show forge-mvc-iot` → **`1.0.0b12`**.

## Commandes IoT et optins

`forge help` (avec `forge-mvc-iot` installé) expose :

```
iot:doctor    iot:init    iot:simulate    iot:listen
optin:enable  optin:list
```

(Les commandes `optin:*` appartiennent au core ; les `iot:*` deviennent
fonctionnelles une fois `forge-mvc-iot` installé.)

## forge optin:enable iot

Dans `forge-b12-core` (dont `mvc/routes.py` contient `router = Router()`,
structure reconnue) :

- `forge optin:list` (avant) → **`iot absent`** ;
- `forge optin:enable iot` (dry-run par défaut) → annonce les 6 fichiers
  + le branchement `mvc/routes.py`, **n'écrit rien** (`optins/` non créé) ;
- `forge optin:enable iot --apply` → crée `optins/__init__.py`,
  `optins/registry.py`, `optins/iot/{__init__.py,routes.py,README.md,
  migrations/README.md}` et **branche** `mvc/routes.py`
  (`from optins.registry import register_optins` + `register_optins(router)`).

## forge optin:list

- Après `--apply` → **`iot activé`** (structure `optins/iot/`, registry
  `optins/registry.py`, `register_optins(router)` présent dans
  `mvc/routes.py`).
- Commande **lecture seule** : `Aucune modification effectuée.`

## Starter welcome-iot

`forge new forge-b12-iot --starter welcome-iot` → projet généré (exit 0).

- `optins/iot/` présent (mêmes 6 fichiers) ;
- `mvc/routes.py` branché via `optins/registry.py`
  (`register_optins(router)`) — injecté par le snippet du starter ;
- `forge doctor` → 0 erreur ;
- `forge iot:doctor` → OK hors DB/MQTT.

## forge iot:doctor

Diagnostic statique (sans `--db` ni `--mqtt`) :

```
[OK]    package forge-mvc-iot — installé (version 1.0.0b12)
[OK]    configuration IoT — chargée
[OK]    migration iot_events — présente (…_create_iot_events.sql)
[OK]    API HTTP IoT — register_iot_routes disponible
[SKIP]  broker MQTT — non testé par défaut
[SKIP]  base iot_events — non testée par défaut
0 avertissement(s), 0 erreur(s), 2 info(s).
```

## Visibilité PyPI

API JSON PyPI (source de vérité) : `forge-mvc` et `forge-mvc-iot`
exposent bien `1.0.0b12` (les 7 paquets ont été confirmés lors de la
publication). Note : `pip index versions` renvoie un **faux négatif**
(commande expérimentale) — non bloquant, l'installation `--pre` fonctionne.

## Limites du smoke test

- **MQTT (Mosquitto)** et **base (MariaDB)** ne sont **pas** testés en
  connexion réelle (hors périmètre ; `--mqtt` / `--db` restent en `SKIP`).
- Pas de démarrage de serveur applicatif (`forge run` / `python app.py`)
  ni de requête HTTP réelle vers `/api/iot/events`.
- Pas de test des autres opt-ins (`rbac`/`workflow`/`stats`/`mfa`/`media`)
  ni de leur activation.
- `pip index versions` non fiable ici — vérification via API JSON.

## Décision

**GO.** La release `Forge 1.0.0-beta.12` est publiée, installable depuis
PyPI et fonctionnelle de bout en bout pour le parcours IoT + opt-ins
côté utilisateur. Prochain ticket : `OFFICIAL-SITE-BETA12-UPDATE-001`
(mise à jour du site / doc publiée vers `1.0.0-beta.12`).
