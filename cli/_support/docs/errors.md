# Les erreurs CLI dans Forge

Ce document décrit les helpers d'erreur standardisés du CLI.

Le fichier de code correspondant est `cli/_support/errors.py`.

## 1. À quoi sert ce module ?

Les commandes Forge signalent leurs erreurs de façon uniforme.
Le message part toujours sur `stderr`, jamais sur `stdout`.
La convention de rendu est constante :

```
Erreur : <message>
Conseil : <suggestion>   (optionnel)
```

Le code de sortie par défaut est `1` (erreur utilisateur).

## 2. L'API

| Fonction | Rôle |
|---|---|
| `cli_error(message, hint="")` | affiche l'erreur sur `stderr` sans terminer le processus |
| `cli_fail(message, hint="", code=1)` | affiche l'erreur sur `stderr` puis termine le processus (`sys.exit`) |

Le `hint` est facultatif : s'il est vide, la ligne `Conseil :` n'est pas émise.

## 3. Contextes d'utilisation

- **Validation d'arguments** : signaler une saisie invalide sans interrompre brutalement (`cli_error`).
- **Échec irrécupérable** : interrompre la commande avec un code retour non nul (`cli_fail`).
- **Scénarios CI** : le code de sortie non nul permet à un pipeline de détecter l'échec.

## 4. Voir aussi

- [Le formatage de sortie CLI](output.md) : tags de statut sur la sortie standard.
