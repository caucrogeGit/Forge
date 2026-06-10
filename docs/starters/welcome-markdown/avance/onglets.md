# Offrir des variantes avec les onglets

**Objectif** : présenter l'installation selon le système d'exploitation, sans allonger la page.

**Ce que vous allez apprendre :** les onglets de contenu (extension `pymdownx.tabbed`).

!!! info "Dernier niveau"
    Vous reprenez votre `prise-en-main.md` enrichi au niveau intermédiaire.
    Le niveau avancé lui donne une finition professionnelle ; ce palier transforme l'installation en onglets par système.

## Des onglets

Chaque onglet s'ouvre par `===` suivi du libellé entre guillemets, son contenu indenté de quatre espaces.

~~~md
=== "Linux / macOS"
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

=== "Windows"
    ```bat
    python -m venv .venv
    .venv\Scripts\activate
    ```
~~~

Rendu :

=== "Linux / macOS"
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

=== "Windows"
    ```bat
    python -m venv .venv
    .venv\Scripts\activate
    ```

## Ajoutez à votre page

Remplacez la commande d'activation de la section « Installation » par des onglets par système, dans `prise-en-main.md`.
Le reste de l'installation (`pip install`, `forge new`) est commun et peut rester sous les onglets.

## À retenir

- Un onglet s'ouvre par `=== "Libellé"`, contenu indenté de quatre espaces.
- On y met n'importe quel contenu : code, texte, listes.
- Idéal pour des variantes : systèmes, langages, niveaux de configuration.

[Continuer avec Diagrammes et inclusions](diagrammes-et-inclusions.md)
