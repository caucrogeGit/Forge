# La lecture de l'environnement dans Forge

Ce document décrit comment Forge lit la variable `APP_ENV`.

`APP_ENV` désigne l'environnement actif d'une application Forge, `dev` par défaut et `prod` en production.
Plusieurs gardes du framework en dépendent, et une lecture approximative les désarme silencieusement.
Le fichier de code correspondant est `core/app/env.py`.

## 1. Rôle

Trois écritures de la même lecture coexistaient dans le dépôt.
Une lecture sans normalisation, une avec `.lower()` seul, et une avec `.strip().lower()`.

Les deux premières laissaient `APP_ENV=Prod` échouer une comparaison à `prod`.
Deux gardes de sécurité cessaient alors de se déclencher, sans le dire.

L'API IoT s'enregistrait sans jeton en production, ce que `SEC-IOT-TOKEN-PROD-001` interdit.
La commande `fixtures:load --run` acceptait de peupler la base de production sans `--force`, ce que l'ADR-074 interdit.

Ce module est la seule lecture officielle, conformément au principe 11.

## 2. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Module Python | `core.app.env` |
| Couche | bootstrap applicatif |
| Rôle | lire et normaliser `APP_ENV` |
| Dépend de | `os` et `collections.abc` seulement |
| API publique | `normalize_app_env`, `read_app_env`, `is_prod` |
| Constantes publiques | `APP_ENV_VAR`, `DEFAULT_APP_ENV`, `PROD` |
| Effet de bord | aucun, `read_app_env` lit `os.environ` sans l'écrire |

Le module ne dépend d'aucun autre module de Forge.
Il est donc importable au tout début du démarrage, y compris par la configuration du squelette.

## 3. Règle de normalisation

La forme canonique retire les blancs de bord et met en minuscules.

| Valeur lue | Forme canonique | Production |
|---|---|---|
| `"prod"` | `prod` | oui |
| `"Prod"` | `prod` | oui |
| `"  PROD  "` | `prod` | oui |
| `"dev"` | `dev` | non |
| `""` | `dev` | non |
| absente | `dev` | non |
| `"staging"` | `staging` | non |

Une valeur absente, vide ou blanche vaut `dev`.
C'est le côté sûr, car un environnement inconnu ne doit jamais être pris pour la production.

La normalisation porte sur la forme, jamais sur le sens.
`production` reste distinct de `prod`, parce qu'inventer un synonyme serait de la magie cachée que le principe 3 refuse.

## 4. API

### `normalize_app_env(value)`

Rend la forme canonique d'une valeur quelconque.
Accepte `object`, car la valeur peut venir du registre `core.forge`, qui n'est pas typé.

```python
from core.app.env import normalize_app_env

normalize_app_env(" Prod ")   # "prod"
normalize_app_env(None)       # "dev"
```

### `read_app_env(environ=None)`

Rend l'environnement actif, lu depuis l'environnement du processus.
Le paramètre `environ` permet de lire une autre source, ce dont les tests ont besoin sans toucher au processus.

```python
from core.app.env import read_app_env

read_app_env()                        # lit os.environ
read_app_env({"APP_ENV": "Prod"})     # "prod"
```

### `is_prod(value)`

Répond si la valeur désigne la production, une fois normalisée.
À préférer à une comparaison écrite à la main, car c'est l'écriture à la main qui avait laissé passer `Prod`.

```python
from core.app.env import is_prod

if is_prod(app_env):
    raise RuntimeError("configuration interdite en production")
```

## 5. Garde-fou

Le fichier `tests/meta/test_app_env_normalisation_001.py` refuse deux choses.

Une lecture de `APP_ENV` dans l'environnement du processus, hors de ce module.
Une comparaison à `prod` ou `dev` portant sur une lecture non normalisée.

Le détecteur travaille sur l'arbre syntaxique et non par expression régulière.
Un `grep` sur `prod` remonte le mot `produire`, et c'est exactement ce faux positif qui avait fait conclure à tort que `forge-mvc-fixtures` n'avait aucune garde.

## 6. Le cœur tolère, le pré-vol exige

Le cœur et le pré-vol de déploiement ne jouent pas le même rôle, et ils ne traitent pas `Prod` de la même façon.

Le cœur est permissif, parce qu'une garde de sécurité ne doit jamais rater une production à cause d'une majuscule.
`is_prod("Prod")` répond donc oui, et l'API IoT refuse de s'ouvrir.

La commande `forge deploy:check` est stricte, parce qu'elle vérifie une déclaration écrite par un exploitant dans `env/prod`.
Elle refuse `APP_ENV=Prod` et demande la forme canonique, pour qu'il n'existe qu'une seule écriture officielle, comme le veut le principe 11.

Les deux comportements se complètent.
Le pré-vol pousse vers la forme canonique avant le déploiement, et le cœur protège quand même si une variante passe.

## 7. Ce que le module ne fait pas

Il ne valide pas la liste des environnements autorisés.
`forge run --env` s'en charge pour son propre argument, et une application reste libre de nommer ses environnements.

Il ne charge aucun fichier `env/`.
C'est le rôle de la configuration du projet, qui utilise la valeur normalisée pour choisir le fichier à charger.
