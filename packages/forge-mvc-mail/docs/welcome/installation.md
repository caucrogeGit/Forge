# Installation : welcome-mail

Le parcours **welcome-mail** découvre l'opt-in `forge-mvc-mail` : composer,
transporter, mettre en forme et configurer l'envoi d'emails.

Ce préambule installe le module dans un projet Forge existant.
La progression se réalise ensuite **à la main** : chaque palier décrit les
fichiers à créer et la route à câbler.

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  Installer Forge.
- **Python 3.12+**.

## 1. Installer le module opt-in Mail

```bash
pip install --pre forge-mvc-mail
```

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-mail
```

Le détail de la création d'un projet est décrit dans
Installer Forge.
Aucun starter n'est généré : les fichiers du parcours se créent à la main au
fil des paliers.

## Après l'installation

Vous pouvez attaquer le premier palier de code, où vous créerez vous-même le
contrôleur, la vue et la route `/mail-welcome`.

[Continuer sur le starter Welcome Mail](debutant/mail-welcome.md)
