# Le chargement de configuration projet dans Forge

Ce document décrit le chargement explicite de la configuration du projet courant.

Le fichier de code correspondant est `cli/project/project_config.py`.

## 1. À quoi sert ce module ?

Il charge la configuration du projet Forge courant de façon **explicite**, sans magie cachée (principe 3).
Plusieurs commandes du CLI s'appuient sur lui pour lire la configuration applicative.

En cas de configuration absente ou invalide, il lève une exception dédiée plutôt que d'échouer silencieusement.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `load_project_config(root=None)` | charge et retourne le module de configuration du projet |
| `ProjectConfigError` | exception levée si la configuration est introuvable ou invalide |

## 3. Contextes d'utilisation

- **Commandes projet** : accéder à la configuration applicative.
- **Diagnostic** : signaler clairement une configuration manquante.

## 4. Voir aussi

- [La commande doctor](doctor.md) : diagnostic qui vérifie la configuration.
- [Les profils de projet](project_profiles.md) : contrat des profils officiels.
