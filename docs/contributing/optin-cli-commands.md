# Déclarer les commandes CLI d'un opt-in

Cette page explique comment un module opt-in ajoute ses commandes `forge <verbe>`
sans modifier le cœur.
Le mécanisme est décrit par l'[ADR-059](../adr/059-cli-command-dispatch-registry.md)
et implémenté dans `cli/commands/optin_dispatch.py`.

## Vue d'ensemble

Le lanceur `forge.py` résout une commande en trois temps.
D'abord les commandes natives du cœur (`new`, `run`, `doctor`, `db:*`, etc.).
Ensuite les commandes du cœur déléguées, via la table `CORE_COMMANDS`.
Enfin les commandes des opt-ins, via `dispatch_optin`.

Les commandes des opt-ins ne sont pas listées dans le cœur.
Elles sont **découvertes à l'exécution** par les entry points du groupe
`forge_mvc.commands`, à l'image des backends de base de données (ADR-054).
Le cœur ne connaît donc jamais la liste des commandes opt-in, et ajouter une
commande dans un opt-in ne touche pas le cœur.

## Déclarer les commandes d'un opt-in

Un opt-in déclare ses commandes en deux morceaux.

### 1. Une table déclarative légère

Créez `forge_mvc_<nom>/commands.py` avec un dictionnaire `COMMANDS`.
Ce fichier ne contient que des chaînes, il n'importe aucun handler.

```python
# pyright: strict
"""Commandes CLI de forge-mvc-exemple, découvertes par le cœur (ADR-059)."""
from __future__ import annotations

COMMANDS: dict[str, dict[str, str | bool]] = {
    "exemple:doctor": {"module": "forge_mvc_exemple.cli.doctor"},
    "exemple:init": {"module": "forge_mvc_exemple.cli.init"},
}
```

### 2. L'entry point dans le `pyproject.toml`

Exposez la table via le groupe `forge_mvc.commands`.

```toml
[project.entry-points."forge_mvc.commands"]
forge_mvc_exemple = "forge_mvc_exemple.commands:COMMANDS"
```

Le cœur charge cette table sans importer les handlers.
Le handler d'une commande n'est importé qu'au moment où la commande est invoquée
(import paresseux), donc installer l'opt-in ne ralentit pas le démarrage du cœur.

## Format d'une commande

Chaque entrée de `COMMANDS` associe un nom de commande à un descripteur.

| Clé | Rôle | Défaut |
|---|---|---|
| `module` | module à importer paresseusement | obligatoire |
| `attr` | attribut appelable dans le module | `main` |
| `full` | le handler reçoit les arguments complets, commande incluse | `False` |
| `exit_rc` | `sys.exit(rc)` si le handler renvoie un code non nul | `True` |

## Deux conventions d'appel

La plupart des handlers reçoivent les arguments **après** la commande et
renvoient un code de retour.
C'est la convention par défaut : `full` à `False`, `exit_rc` à `True`.

Certains handlers gèrent eux-mêmes plusieurs sous-commandes du même namespace.
Ils ont alors besoin des arguments complets pour savoir quelle sous-commande
exécuter, on pose donc `full` à `True`.

```python
_MAIL = {"module": "forge_mvc_mail.cli", "full": True, "exit_rc": False}

COMMANDS = {
    "mail:init": _MAIL,
    "mail:test": _MAIL,
}
```

## Rafraîchir les métadonnées

Les entry points sont lus depuis les métadonnées d'installation (`.dist-info`).
Après avoir édité un `pyproject.toml` ou un `commands.py`, réinstallez le paquet
pour que la découverte voie les changements.

```bash
pip install -e packages/forge-mvc-exemple --no-deps
```

## Commande d'un opt-in non installé

Si l'opt-in n'est pas installé, son entry point n'existe pas, la commande n'est
pas découverte.
`forge` répond alors « commande inconnue » avec un conseil qui oriente vers
l'installation du module opt-in.

## Voir aussi

- [ADR-059 : Registre de dispatch des commandes CLI](../adr/059-cli-command-dispatch-registry.md)
- [ADR-054 : Cœur agnostique BDD et backends opt-in](../adr/054-database-backend-optins.md), même mécanisme d'entry points.
- [Conventions internes](conventions.md), pattern B.7 pour les couches de test.
