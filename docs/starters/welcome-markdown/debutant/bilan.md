# Bilan : niveau débutant

Vous avez posé le **squelette** de la page « Prise en main de Forge » : titre, introduction, présentation, principes, citation, prérequis et liens.

## Les notions acquises

- Palier 1 : titres `#`, paragraphes, une phrase par ligne, échappement `\`.
- Palier 2 : emphase `**gras**` / `_italique_`, code en ligne, code en ligne coloré.
- Palier 3 : listes à puces, numérotées et de tâches.
- Palier 4 : citations `>` et règle horizontale `---`.
- Palier 5 : liens, liens automatiques et images.

## État de votre page

??? note "prise-en-main.md à ce stade"
    ```md
    # Prise en main de Forge

    Forge est un framework web Python explicite, pédagogique et testable.
    Cette page vous guide pour installer Forge et créer votre premier projet.

    ## Présentation

    Forge est **explicite** : le `SQL` reste visible et il n'y a pas de _magie cachée_.
    Le noyau est **minimal** ; les fonctions avancées s'ajoutent en modules opt-in.

    ## Principes

    - **Explicite** : le SQL reste visible.
    - **Minimal** : un noyau réduit, des modules opt-in.
    - **Testable** : on teste avant d'élargir.

    > Forge préfère un code explicite et durable à la facilité immédiate.
    > (Charte philosophique, principe 3)

    ---

    ## Prérequis

    - [ ] Python 3.12 ou plus
    - [ ] Une base MariaDB
    - [ ] Le gestionnaire de paquets `pip`

    ## Liens utiles

    - La [documentation complète](https://example.com/forge).
    - Le dépôt du code et le suivi des tickets.
    - Contact : doc@example.com
    ```

## Et ensuite

Votre page est lisible mais encore plate.

Le niveau intermédiaire l'enrichit : tableaux, listes de définition, encadrés, blocs dépliables et blocs de code colorés.

[Niveau intermédiaire : Présenter des données en tableau](../intermediaire/tableaux.md)
