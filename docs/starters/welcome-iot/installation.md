# Installation — Progression « Bonjour Forge IoT »

Ce préambule installe le module **opt-in** `forge-mvc-iot` et génère le projet
de départ de la progression IoT. C'est la **seule page du parcours** qui
contient des commandes de création : tous les paliers suivants supposent le
projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core et des autres parcours, voir
    [Installer Forge](../../install/poste-linux.md). Pour la configuration MQTT,
    voir [Configuration IoT](../../iot/configuration.md).

## Prérequis

- **Forge installé** (core `forge-mvc`). Si ce n'est pas encore fait, suivre
  d'abord [Installer Forge](../../install/poste-linux.md).
- **Python 3.12+**.
- **Aucun broker MQTT n'est requis** pour les premiers paliers : ils
  fonctionnent sans broker ni base de données. Le broker n'intervient qu'au
  niveau avancé (palier « Le subscriber MQTT »).

## 1. Installer le module opt-in IoT

Le cœur de Forge ne dépend pas de l'IoT : c'est une brique que l'on ajoute à la
demande. Installation directe depuis PyPI (`forge-mvc-iot` est publié depuis
`1.0.0-beta.12`) :

```bash
pip install --pre forge-mvc-iot
```

Équivalent via la CLI Forge depuis un projet existant :

```bash
forge opt-in:install iot
```

## 2. Générer le projet de départ

La progression démarre sur le starter `iot-welcome` (Bonjour Forge IoT) :

```bash
forge starter:build iot-welcome
```

## 3. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/iot-welcome` : la page affiche
**« Bonjour Forge IoT »**. La route `/iot-welcome/inspect` renvoie la
configuration MQTT en JSON, mot de passe masqué.

## 4. Vérifier l'installation

```bash
forge iot:doctor
```

`forge iot:doctor` contrôle de façon non invasive que le module est branché
(paquet, configuration, API), sans toucher au broker ni à la base.

## Après l'installation

Le module répond : vous pouvez attaquer le premier palier de code.

[Continuer avec Bonjour Forge IoT](debutant/iot-welcome.md)
