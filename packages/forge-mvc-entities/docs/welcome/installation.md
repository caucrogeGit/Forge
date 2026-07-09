# Installation : progression « Welcome Entités »

Ce préambule prépare la progression du **moteur d'entités**, l'opt-in `forge-mvc-entities`.
La progression se réalise ensuite à la main : chaque palier décrit la commande à lancer et le code généré à observer.

!!! info "Référence complète"
    Pour l'installation détaillée du cœur, voir Installer Forge.
    Pour la référence du moteur, voir [Moteur d'entités](../reference.md).

## Ce que couvre cette progression

Le moteur d'entités porte toute la chaîne de la couche de données.

- Niveau **débutant** : déclarer une entité (`make:entity`), la relier (`make:relation`), générer son SQL et son modèle (`build:model`), puis son CRUD (`make:crud`).
- Niveau **intermédiaire** : faire évoluer le schéma avec les migrations (`migration:make`, `migration:apply`).
- Niveau **avancé** : les tables pivot enrichies, une association `many_to_many` qui porte des attributs.

## Prérequis

- **Forge installé** (cœur `forge-mvc`).
  Sinon, suivre d'abord Installer Forge.
- **Python 3.12+**.
- **Un backend de base de données** pour les paliers qui touchent la base (`build:model`, migrations, CRUD).
  Le cœur est agnostique : installez le backend de votre choix, par exemple `pip install forge-mvc-sqlite` (fichier, sans serveur) ou `pip install forge-mvc-mariadb`.

## 1. Disposer d'un projet Forge

Le squelette est livré **sans** moteur d'entités : `forge new` produit un projet web nu.

```bash
forge new mon-projet-entites
```

## 2. Installer le moteur d'entités

La couche de données est un choix explicite (comme le backend).
Ajoutez l'opt-in au projet :

```bash
pip install --pre forge-mvc-entities
```

Le `requirements.txt` du projet documente déjà cet opt-in ; une application purement web n'en a pas besoin.

## 3. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte le moteur d'entités et les commandes qu'il fournit.

## Après l'installation

Vous pouvez attaquer le premier palier, où vous déclarez votre première entité et découvrez le contrat JSON qui la décrit.

[Continuer sur le starter Welcome Entités](debutant/entity-welcome.md)
