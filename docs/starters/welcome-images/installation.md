# Installation — Progression « Bonjour Forge Images »

Ce préambule installe le module **opt-in** `forge-mvc-images` et génère le projet
de départ de la progression images. C'est la **seule page du parcours** qui
contient des commandes de création : tous les paliers suivants supposent le
projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core et des autres parcours, voir
    [Installer Forge](../../install/index.md).

!!! warning "Module pas encore publié sur PyPI"
    `forge-mvc-images` n'est pas encore publié sur PyPI (cible : release
    beta.13). On l'installe donc **depuis les sources**. Une fois publié, la
    commande deviendra `pip install --pre forge-mvc-images`.

## Prérequis

- **Forge installé** (core `forge-mvc`). Si ce n'est pas encore fait, suivre
  d'abord [Installer Forge](../../install/index.md).
- **Python 3.12+**.
- Les premiers paliers (premier contact, dérivation des variantes) fonctionnent
  **sans base de données**. La couche médias en base n'intervient qu'au niveau
  intermédiaire.

## 1. Installer le module opt-in Images

Le cœur de Forge ne dépend pas de l'image : c'est une brique que l'on ajoute à la
demande. `forge-mvc-images` dépend de `forge-mvc-files` (l'upload générique) ;
on installe les deux depuis les sources du dépôt :

```bash
pip install -e packages/forge-mvc-files/
pip install -e packages/forge-mvc-images/
```

## 2. Générer le projet de départ

La progression démarre sur le starter `images-welcome` (Bonjour Forge Images) :

```bash
forge starter:build images-welcome
```

## 3. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/images-welcome` : la page affiche
**« Bonjour Forge Images »**. La route `/images-welcome/inspect` renvoie en JSON
les formats acceptés et les tailles de variantes.

## 4. Vérifier l'installation

`forge-mvc-images` est une brique **bibliothèque** (pas de CLI dédiée). On
vérifie qu'elle est bien vue par Forge avec :

```bash
forge opt-in:list
```

Le module `images` doit apparaître comme installé.

## Après l'installation

Le module répond : vous pouvez attaquer le premier palier de code.

[Continuer avec Bonjour Forge Images](debutant/images-welcome.md)
