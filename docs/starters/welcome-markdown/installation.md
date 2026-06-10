# Préambule : le Markdown de la documentation Forge

**Objectif**{ .intro-label } : disposer d'une vitrine complète de toute la syntaxe Markdown disponible dans la documentation Forge.

**Ce que vous allez apprendre :**{ .intro-label } chaque page montre la **source** Markdown puis son **rendu**, pour que vous puissiez copier la syntaxe et voir immédiatement l'effet.

!!! info "À quoi sert cette progression"
    Contrairement aux autres `welcome-*`, cette progression ne construit pas un projet Forge.
    C'est un **catalogue de référence** : elle démontre toutes les extensions Markdown activées dans `mkdocs.yml`, telles qu'elles s'affichent dans cette documentation.

    Gardez-la sous la main quand vous rédigez un guide, un palier de tutoriel ou une page de référence.

## La convention « source puis rendu »

Dans chaque page, la syntaxe est présentée d'abord dans un bloc de code (la **source**), puis suivie de son **rendu** réel.

Par exemple, la source suivante :

~~~md
Un mot en **gras**, un autre en _italique_.
~~~

produit ce rendu :

Un mot en **gras**, un autre en _italique_.

## Style d'écriture attendu

La documentation Forge suit une typographie française stricte (directive §2.1) :

- une **phrase par ligne** dans la source Markdown ;
- des **espaces insécables** avant `: ; ? !` et autour des guillemets « » ;
- **pas** de tiret cadratin ; on préfère la virgule, le point-virgule ou les deux-points.

Le Markdown regroupe les lignes d'un même paragraphe au rendu : écrire une phrase par ligne ne change donc rien à l'affichage, mais facilite la relecture et les différences de version.

## Les familles d'extensions

| Page | Ce qu'elle couvre |
|---|---|
| [Les bases](bases.md) | titres, emphase, listes, citations, liens, images |
| [Tableaux et définitions](tableaux-et-definitions.md) | tableaux alignés, listes de définition |
| [Admonitions et onglets](admonitions-et-onglets.md) | encadrés, blocs dépliables, onglets |
| [Code et diagrammes](code-et-diagrammes.md) | coloration, blocs imbriqués, Mermaid, inclusions |
| [Texte enrichi](texte-enrichi.md) | surlignage, exposants, touches clavier, émojis, symboles |
| [Notes, abréviations, attributs](notes-abreviations-attributs.md) | notes de bas de page, abréviations, classes, liens automatiques |
| [Relecture et maths](relecture-et-maths.md) | annotations de relecture, formules mathématiques |
| [Aide-mémoire](recapitulatif.md) | toute la syntaxe et le nom des signes sur une seule page |

[Commencer avec Les bases](bases.md)
