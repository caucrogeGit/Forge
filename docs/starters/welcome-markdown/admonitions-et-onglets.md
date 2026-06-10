# Admonitions et onglets

**Objectif**{ .intro-label } : mettre en valeur une information dans un encadré, la rendre dépliable, ou organiser du contenu en onglets.

**Ce que vous allez apprendre :**{ .intro-label } les admonitions (`admonition`), les blocs dépliables (`pymdownx.details`) et les onglets de contenu (`pymdownx.tabbed`).

## Admonitions

Une admonition s'ouvre par `!!!` suivi d'un **type**, puis d'un contenu indenté de quatre espaces.

~~~md
!!! note
    Une note d'information générale.
~~~

Rendu :

!!! note
    Une note d'information générale.

### Les types courants

Chaque type a sa couleur et son icône.

~~~md
!!! tip "Astuce"
    Un conseil pratique.

!!! warning "Attention"
    Un point de vigilance.

!!! danger "Danger"
    Une opération risquée.
~~~

Rendu :

!!! tip "Astuce"
    Un conseil pratique.

!!! warning "Attention"
    Un point de vigilance.

!!! danger "Danger"
    Une opération risquée.

### Titre personnalisé ou supprimé

Le texte entre guillemets remplace le titre par défaut ; un `""` vide supprime le titre.

~~~md
!!! info "Le mini-projet du niveau"
    Titre sur mesure.

!!! note ""
    Encadré sans titre.
~~~

Rendu :

!!! info "Le mini-projet du niveau"
    Titre sur mesure.

!!! note ""
    Encadré sans titre.

## Blocs dépliables

Remplacez `!!!` par `???` pour obtenir un bloc **replié** par défaut, que le lecteur ouvre d'un clic.
C'est le cœur du modèle de paliers de welcome-forge (sections par artefact MVC).

~~~md
??? note "Cliquez pour déplier"
    Le contenu reste caché tant qu'on ne clique pas.
~~~

Rendu :

??? note "Cliquez pour déplier"
    Le contenu reste caché tant qu'on ne clique pas.

Ajoutez un `+` (`???+`) pour afficher le bloc **déjà ouvert**, tout en le laissant repliable.

~~~md
???+ tip "Déplié par défaut"
    Visible au chargement, mais on peut le refermer.
~~~

Rendu :

???+ tip "Déplié par défaut"
    Visible au chargement, mais on peut le refermer.

## Imbriquer

Un encadré peut contenir un autre encadré, du code ou un tableau ; il suffit d'indenter davantage.

~~~md
!!! warning "Encadré parent"
    Texte du parent.

    ??? note "Encadré enfant dépliable"
        Contenu de l'enfant.
~~~

Rendu :

!!! warning "Encadré parent"
    Texte du parent.

    ??? note "Encadré enfant dépliable"
        Contenu de l'enfant.

## Onglets de contenu

L'extension `pymdownx.tabbed` regroupe des variantes sous des onglets, avec `===` suivi du libellé entre guillemets.

~~~md
=== "Python"
    ```python
    print("Bonjour Forge")
    ```

=== "Shell"
    ```bash
    echo "Bonjour Forge"
    ```
~~~

Rendu :

=== "Python"
    ```python
    print("Bonjour Forge")
    ```

=== "Shell"
    ```bash
    echo "Bonjour Forge"
    ```

[Continuer avec Code et diagrammes](code-et-diagrammes.md)
