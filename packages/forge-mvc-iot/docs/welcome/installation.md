# Installation : Progression « Welcome IoT »

Ce préambule installe le module **opt-in** `forge-mvc-iot` dans un projet Forge existant.
La progression IoT se réalise ensuite **à la main** : chaque palier décrit les fichiers à créer et la route à câbler.

!!! info "Référence complète"
    Pour l'installation détaillée du core et des autres parcours, voir Installer Forge.
    Pour la configuration MQTT, voir [Configuration IoT](../configuration.md).

## Prérequis

- **Forge installé** (core `forge-mvc`).
  Si ce n'est pas encore fait, suivre d'abord Installer Forge.
- **Python 3.12+**.
- **Aucun broker MQTT n'est requis** pour les premiers paliers : ils fonctionnent sans broker ni base de données.
  Le broker n'intervient qu'au niveau avancé (palier « Le subscriber MQTT »).

## 1. Installer le module opt-in IoT

Le cœur de Forge ne dépend pas de l'IoT : c'est une brique que l'on ajoute à la demande.
Installation directe depuis PyPI (`forge-mvc-iot` est publié depuis `1.0.0-beta.12`) :

```bash
pip install --pre forge-mvc-iot
```

Équivalent via la CLI Forge depuis un projet existant :

```bash
forge opt-in:install iot
```

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-iot
```

Le détail de la création d'un projet est décrit dans Installer Forge.
Aucun starter n'est généré : les fichiers du parcours se créent à la main au fil des paliers.

## 3. Vérifier l'installation

```bash
forge iot:doctor
```

`forge iot:doctor` contrôle de façon non invasive que le module est branché (paquet, configuration, API), sans toucher au broker ni à la base.

## Après l'installation

Le module répond : vous pouvez attaquer le premier palier de code, où vous créerez vous-même le contrôleur, la vue et la route `/iot-welcome`.

[Continuer sur le starter Welcome IoT](debutant/iot-welcome.md)
