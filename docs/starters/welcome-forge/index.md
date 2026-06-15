# Parcours Welcome Forge

Welcome Forge est la progression cœur du framework.

C'est un tutoriel continu : vous construisez à la main un seul projet qui grandit palier après palier, des premières routes jusqu'à une petite application avec base de données.
Contrairement aux starters opt-in, ce parcours n'installe aucune brique supplémentaire : il s'appuie uniquement sur le cœur de Forge, déjà présent dès qu'un projet est créé.

---

## Prérequis

Ce parcours suppose que vous avez déjà un projet Forge fonctionnel.

L'installation de Forge et la création d'un projet ne font pas partie du parcours : elles sont décrites une seule fois dans le guide d'installation.
Suivez d'abord l'un de ces guides, puis revenez ici :

* [Installer Forge sur Linux et créer un projet](../../install/poste-linux.md) ;
* [Installer Forge sur Windows avec WSL](../../install/windows-wsl.md) ;
* [Installer Forge depuis les sources GitHub](../../install/github.md).

À l'issue de cette procédure, vous disposez de Forge installé, d'un projet créé et d'un serveur de développement qui démarre avec `forge run`.

!!! note "Base de données"
    Les premiers paliers tournent sans base de données : ils n'ont pas besoin de `db:init`.
    MariaDB n'est nécessaire qu'à partir du palier « Première base SQL », voir [Préparer MariaDB](../../install/mariadb.md).

---

## Vérifier votre installation

Avant de commencer, contrôlez que votre poste et votre projet sont prêts.

La commande `forge` doit répondre :

```bash
forge --version
```

Dans le dossier de votre projet, `forge doctor` contrôle l'environnement sans rien modifier :

```bash
forge doctor
```

Si `forge` est introuvable ou si `forge doctor` signale un blocage, l'installation du poste ou du projet n'est pas terminée.
Reprenez alors le guide d'installation correspondant, par exemple [Installer Forge sur Linux et créer un projet](../../install/poste-linux.md), avant d'attaquer le premier palier.

---

## Les trois niveaux

Le parcours est organisé en trois niveaux qui se suivent.

Chaque niveau reprend le projet construit au niveau précédent.

### Débutant

Les fondamentaux du framework : routes, contrôleurs, vues, requête et réponse, formulaire POST, jeton CSRF, puis première base SQL en lecture et en écriture.

### Intermédiaire

La mise en forme et la manipulation de données : héritage de gabarit, liste, recherche, pagination, modification et suppression d'enregistrements, messages flash, état en session.

### Avancé

Les sujets plus riches : relations entre tables, écritures transactionnelles, téléversement de fichier, API JSON protégée.

---

## Commencer

Votre projet Forge est prêt et vérifié, vous pouvez attaquer le premier palier de code :

[Commencer avec Bonjour Forge](debutant/welcome.md)
