# Aide-mémoire Markdown

**Objectif**{ .intro-label } : retrouver d'un coup d'œil toute la syntaxe Markdown disponible dans la documentation Forge.

**Ce que vous allez apprendre :**{ .intro-label } rien de neuf, c'est la synthèse : chaque ligne renvoie à la page qui détaille la syntaxe.

## Bases

| Syntaxe | Effet | Détail |
|---|---|---|
| `# Titre` … `###### Titre` | titres de niveau 1 à 6 | [Bases](bases.md) |
| `**gras**`, `_italique_` | emphase | [Bases](bases.md) |
| `- élément` | liste à puces | [Bases](bases.md) |
| `1. élément` | liste numérotée | [Bases](bases.md) |
| `- [ ]` / `- [x]` | liste de tâches | [Bases](bases.md) |
| `> citation` | bloc de citation | [Bases](bases.md) |
| `[libellé](cible.md)` | lien | [Bases](bases.md) |
| `![alt](image.png)` | image | [Bases](bases.md) |
| `---` | règle horizontale | [Bases](bases.md) |
| `\*` | échapper un caractère | [Bases](bases.md) |

## Tableaux et définitions

| Syntaxe | Effet | Détail |
|---|---|---|
| `\| a \| b \|` + ligne `\|---\|---\|` | tableau | [Tableaux et définitions](tableaux-et-definitions.md) |
| `:---`, `:---:`, `---:` | alignement gauche, centré, droite | [Tableaux et définitions](tableaux-et-definitions.md) |
| terme puis `:   définition` | liste de définition | [Tableaux et définitions](tableaux-et-definitions.md) |

## Admonitions et onglets

| Syntaxe | Effet | Détail |
|---|---|---|
| `!!! note "Titre"` | encadré (note, tip, warning, danger…) | [Admonitions et onglets](admonitions-et-onglets.md) |
| `??? note "Titre"` | encadré dépliable, replié | [Admonitions et onglets](admonitions-et-onglets.md) |
| `???+ note "Titre"` | encadré dépliable, déplié | [Admonitions et onglets](admonitions-et-onglets.md) |
| `=== "Onglet"` | onglets de contenu | [Admonitions et onglets](admonitions-et-onglets.md) |

## Code et diagrammes

| Syntaxe | Effet | Détail |
|---|---|---|
| `` `code` `` | code en ligne | [Code et diagrammes](code-et-diagrammes.md) |
| `` `#!python …` `` | code en ligne coloré | [Code et diagrammes](code-et-diagrammes.md) |
| clôture ```` ``` ```` + langage | bloc de code coloré | [Code et diagrammes](code-et-diagrammes.md) |
| `linenums="1"`, `hl_lines="2 3"`, `title="…"` | options de bloc | [Code et diagrammes](code-et-diagrammes.md) |
| clôture `mermaid` | diagramme | [Code et diagrammes](code-et-diagrammes.md) |
| `--8<-- "fichier"` | inclure un fichier | [Code et diagrammes](code-et-diagrammes.md) |

## Texte enrichi

| Syntaxe | Effet | Détail |
|---|---|---|
| `==texte==` | surlignage | [Texte enrichi](texte-enrichi.md) |
| `^exposant^`, `^^inséré^^` | exposant, insertion | [Texte enrichi](texte-enrichi.md) |
| `~indice~`, `~~barré~~` | indice, barré | [Texte enrichi](texte-enrichi.md) |
| `++ctrl+c++` | touches clavier | [Texte enrichi](texte-enrichi.md) |
| `(c)`, `(tm)`, `-->`, `+/-` | symboles typographiques | [Texte enrichi](texte-enrichi.md) |
| `:material-check:`, `:smile:` | icônes et émojis | [Texte enrichi](texte-enrichi.md) |
| `[=85% "85 %"]` | barre de progression | [Texte enrichi](texte-enrichi.md) |

## Notes, abréviations, attributs

| Syntaxe | Effet | Détail |
|---|---|---|
| `texte[^clé]` + `[^clé]: …` | note de bas de page | [Notes, abréviations, attributs](notes-abreviations-attributs.md) |
| `*[SIGLE]: signification` | abréviation avec infobulle | [Notes, abréviations, attributs](notes-abreviations-attributs.md) |
| `**texte**{ .classe }` | classe, identifiant ou attribut | [Notes, abréviations, attributs](notes-abreviations-attributs.md) |
| URL ou email en clair | lien automatique | [Notes, abréviations, attributs](notes-abreviations-attributs.md) |
| `[[NomDePage]]` | lien wiki | [Notes, abréviations, attributs](notes-abreviations-attributs.md) |

## Relecture et maths

| Syntaxe | Effet | Détail |
|---|---|---|
| `{++ajout++}`, `{--retrait--}` | ajout, suppression | [Relecture et maths](relecture-et-maths.md) |
| `{~~ancien~>nouveau~~}` | remplacement | [Relecture et maths](relecture-et-maths.md) |
| `{==surligné==}`, `{>>note<<}` | surlignage, commentaire | [Relecture et maths](relecture-et-maths.md) |
| `$O(n)$`, `$$ … $$` | formule en ligne, en bloc | [Relecture et maths](relecture-et-maths.md) |

## Rappel de style

- Une **phrase par ligne** dans la source.
- Espaces **insécables** avant `: ; ? !` et autour des guillemets « ».
- **Pas** de tiret cadratin.
- Liens internes vers le **fichier** `.md`, vérifiés au build `--strict`.

[Revenir au Préambule](installation.md)
