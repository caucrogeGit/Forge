# Présenter des données en tableau

**Objectif** : ajouter à la page un tableau des commandes essentielles de Forge.

**Ce que vous allez apprendre :** les tableaux (extension `tables`) et l'alignement de leurs colonnes.

!!! info "Le fil rouge continue"
    Vous reprenez votre `prise-en-main.md` du niveau débutant.
    Le niveau intermédiaire l'enrichit ; ce palier ajoute une section « Commandes ».

## Dessiner un tableau

Les barres verticales `|` séparent les colonnes ; la deuxième ligne sépare l'en-tête du corps.

~~~md
| Commande | Rôle |
|---|---|
| `forge new` | crée un projet |
| `forge serve` | lance le serveur de développement |
~~~

Rendu :

| Commande | Rôle |
|---|---|
| `forge new` | crée un projet |
| `forge serve` | lance le serveur de développement |

## Aligner les colonnes

Les deux-points dans la ligne de séparation fixent l'alignement.

~~~md
| Commande | Fréquence | Depuis la version |
|:---|:---:|---:|
| `forge new` | rare | 1.0 |
| `forge migration:apply` | souvent | 1.0 |
~~~

Rendu :

| Commande | Fréquence | Depuis la version |
|:---|:---:|---:|
| `forge new` | rare | 1.0 |
| `forge migration:apply` | souvent | 1.0 |

## Ajoutez à votre page

Ajoutez une section « Commandes » à `prise-en-main.md` :

~~~md
## Commandes

| Commande | Rôle |
|:---|:---|
| `forge new <nom>` | crée un nouveau projet |
| `forge serve` | lance le serveur de développement |
| `forge migration:apply` | applique les migrations en attente |
~~~

## À retenir

- Un tableau se dessine avec `|` et une ligne de séparation `|---|`.
- `:---`, `:---:`, `---:` alignent à gauche, au centre, à droite.
- Une cellule accepte du Markdown en ligne (`code`, **gras**, liens).

[Continuer avec Définir des termes](definitions.md)
