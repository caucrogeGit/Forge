# La fabrique d'application dans Forge

Ce document décrit la construction de l'`Application` Forge configurée.

La fabrique est la source unique d'initialisation : elle lit `config.py`, applique la configuration, branche le renderer Jinja2, charge les routes et construit l'`Application`.
Le fichier de code correspondant est `core/app/app_factory.py`.

## 1. Rôle

Assembler une application Forge demande plusieurs étapes : lire la configuration du projet, l'appliquer via `forge.configure(...)`, brancher le moteur de templates Jinja2, charger le routeur, puis instancier l'`Application`.

La fabrique regroupe ces étapes en un point unique.
Elle est réutilisée par le serveur de développement (`app.py`) et par le callable WSGI de production, pour qu'aucune divergence de configuration ne s'installe entre les deux voies.
Les fonctions sont idempotentes : un second appel reconfigure Forge sans casser l'état précédent.

## 2. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Module Python | `core.app.app_factory` |
| Couche | bootstrap applicatif |
| Rôle | construire l'`Application` configurée à partir de `config.py` |
| Dépend de | le module applicatif `config`, `core.forge`, le gestionnaire de templates, le renderer Jinja2 |
| API publique | `apply_forge_config()`, `build_application()` |
| Objet produit | une instance de `Application` (voir `application.md`) |
| Réutilisée par | le serveur de développement et le callable WSGI |

## 3. Schéma de séquence

Le module est un petit ensemble de fonctions de bootstrap : un diagramme de séquence éclaire mieux l'enchaînement qu'un diagramme de classe.

```mermaid
sequenceDiagram
    participant Appelant as app.py ou wsgi
    participant Factory as app_factory
    participant Config as config.py
    participant Forge as core.forge
    participant Tpl as template_manager
    participant App as Application

    Appelant->>Factory: build_application()
    Factory->>Config: lit les constantes de config
    Factory->>Forge: configure(**kwargs)
    Factory->>Tpl: register(Jinja2Renderer) si absent
    Factory->>Config: importe le module de routes
    Factory->>Forge: configure(router=...)
    Factory->>App: Application(router)
    App-->>Appelant: application prête à dispatcher
```

À retenir :

- `build_application()` exécute la même séquence d'initialisation que `app.py`, sans démarrer de serveur HTTP ;
- la configuration est lue depuis le module applicatif `config`, présent dans un projet généré ;
- le renderer Jinja2 n'est branché que si aucun renderer n'est déjà enregistré (idempotence) ;
- le routeur est chargé depuis le module désigné par `config.APP_ROUTES_MODULE`.

## 4. API publique

| Fonction | Signature | Rôle |
|---|---|---|
| `apply_forge_config` | `apply_forge_config() -> None` | applique la configuration Forge lue depuis `config.py` ; idempotent |
| `build_application` | `build_application() -> Application` | construit l'`Application` complète : config, Jinja2 et routes |

## 5. Contextes d'utilisation

| Besoin | Élément |
|---|---|
| Démarrer en développement ou en WSGI | `build_application()` |
| Initialiser la configuration sans serveur | `apply_forge_config()` |
| Obtenir une `Application` prête pour des tests | `build_application()` |

## 6. Exemples d'utilisation

Construire l'application complète :

```python
from core.app.app_factory import build_application

app = build_application()
```

Appliquer seulement la configuration, sans construire l'application :

```python
from core.app.app_factory import apply_forge_config

apply_forge_config()
```

## 7. Cohérence dev et production

!!! tip "Source unique d'initialisation"
    La fabrique existe pour éviter que le serveur de développement et le callable WSGI configurent Forge différemment.
    Toute évolution du `forge.configure(...)` central doit être miroitée des deux côtés.
    Cette parité est verrouillée par les tests du projet.

## Voir aussi

- [L'application](application.md) : l'objet construit par la fabrique.
- [Les callables WSGI](wsgi.md) : la voie de production qui appelle la fabrique.
- [Le chargeur de routes d'API](api_routes_loader.md) : branchement optionnel des routes d'API.
