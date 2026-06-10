# Mettre en avant avec les admonitions

**Objectif** : signaler un prérequis important et un point de vigilance dans la page.

**Ce que vous allez apprendre :** les admonitions (extension `admonition`), leurs types et leurs titres.

Votre page contient des commandes et un glossaire.

Nous attirons l'attention sur la version de Python requise et sur un piège courant.

## Une admonition

Elle s'ouvre par `!!!` suivi d'un **type**, puis d'un contenu indenté de quatre espaces.

~~~md
!!! note
    Forge vise un runtime Python volontairement limité.
~~~

Rendu :

!!! note
    Forge vise un runtime Python volontairement limité.

## Les types et un titre personnalisé

Le texte entre guillemets remplace le titre par défaut.

~~~md
!!! warning "Version de Python"
    Forge exige Python 3.12 ou plus récent.

!!! tip "Astuce"
    Travaillez dans un environnement virtuel dédié.
~~~

Rendu :

!!! warning "Version de Python"
    Forge exige Python 3.12 ou plus récent.

!!! tip "Astuce"
    Travaillez dans un environnement virtuel dédié.

## Ajoutez à votre page

Insérez ces encadrés dans la section « Prérequis » de `prise-en-main.md` :

~~~md
!!! warning "Version de Python"
    Forge exige Python 3.12 ou plus récent.
    Vérifiez avec `python --version`.

!!! tip "Environnement virtuel"
    Créez un environnement dédié avant d'installer Forge.
~~~

## À retenir

- Une admonition s'ouvre par `!!! type`, contenu indenté de quatre espaces.
- Types courants : `note`, `tip`, `warning`, `danger`, `info`.
- Un texte entre guillemets personnalise le titre ; `""` le supprime.

[Continuer avec Replier le détail](blocs-depliables.md)
