# L'aide par commande dans Forge

Ce document décrit l'interception centrale de `--help` et `-h` pour les commandes du CLI.

Le fichier de code correspondant est `cli/_support/help_dispatch.py`.

## 1. À quoi sert ce module ?

Certaines commandes Forge ne gèrent pas elles-mêmes le drapeau `--help`.
Ce module fournit une aide **centralisée** pour ces commandes, sans toucher à leur `main()`.

Les commandes qui possèdent déjà une aide native (cas `argparse`, ou check manuel de `--help`) ne sont **pas** listées ici.
Leur propre `main()` reste responsable d'afficher leur aide détaillée.

L'architecture repose sur deux dictionnaires :

- `HELP_TEXTS_RICH` : aide longue par commande (Usage, Description, Effets, Prérequis, Options, Limites).
- `HELP_DESCRIPTIONS` : description d'une seule ligne, servant de filet de sécurité.

Si une commande figure dans `HELP_DESCRIPTIONS` sans entrée riche correspondante, un gabarit générique est produit automatiquement.
Aucune commande n'est ainsi laissée sans aide.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `HELP_FLAGS` | ensemble figé des drapeaux reconnus (`--help`, `-h`) |
| `wants_help(args)` | retourne `True` si un drapeau d'aide figure dans `args` |
| `format_command_help(command)` | retourne le texte d'aide d'une commande, ou `None` si non gérée |

`format_command_help` cherche d'abord l'aide riche.
À défaut, il construit un texte court depuis la description.
Il renvoie `None` quand la commande n'est connue d'aucun des deux dictionnaires.

## 3. Contextes d'utilisation

- **`forge <commande> --help`** : interception avant l'exécution de la commande.
- **Commandes sans aide native** : bénéficient d'une aide cohérente sans modifier leur code.
- **Garde-fou de classification** : une commande dispatchée par `forge.py` mais absente des deux dictionnaires ET sans aide native déclenche une erreur de test (`tests/meta/test_cli_help_flags_closing_audit_001.py`).

## 4. Voir aussi

- [L'aide générale du CLI](help.md) : sommaire global des commandes.
- [Les erreurs CLI](errors.md) : sortie d'erreur et code retour.
