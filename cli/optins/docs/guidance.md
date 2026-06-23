# Les conseils d'activation des opt-ins dans Forge

Ce document décrit les messages de conseil affichés selon le *kind* d'un opt-in.

Le fichier de code correspondant est `cli/optins/guidance.py`.

## 1. À quoi sert ce module ?

Seuls les opt-ins de *kind* `route` (comme `iot`) ont un câblage projet réel (couche `optins/`).
Pour les bibliothèques et les transversaux, `opt-in:enable` et `opt-in:disable` n'écrivent rien.
Ils **informent** : ils expliquent comment utiliser ou retirer la brique.

Ce module produit ces messages, pour éviter toute cérémonie vide (principe 8).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `enable_guidance(optin)` | message d'activation pour un opt-in non routier |
| `disable_guidance(optin)` | message de désactivation pour un opt-in non routier |

## 3. Contextes d'utilisation

- **Opt-in bibliothèque** : guider l'utilisateur sans modifier son projet.
- **Cohérence d'expérience** : `enable`/`disable` répondent toujours, même sans câblage.

## 4. Voir aussi

- [Le catalogue des opt-ins](catalog.md) : source des *kinds*.
- [La commande opt-in:enable](enable.md) : branchement d'un opt-in routier.
