# Préambule : apprendre Markdown en documentant Forge

**Objectif** : apprendre Markdown et toutes les extensions de la documentation Forge, en construisant une vraie page de documentation.

**Ce que vous allez apprendre :** la syntaxe Markdown, palier après palier, en rédigeant vous-même un document qui grandit du simple titre à la page de référence complète.

!!! info "Le mini-projet du parcours"
    Comme les autres progressions `welcome-*`, ce parcours suit un **fil rouge** unique.
    Ici, vous rédigez à la main une seule page de documentation : **« Prise en main de Forge »**, dans un fichier `prise-en-main.md`.

    Elle part d'un titre et d'un paragraphe, puis s'enrichit à chaque palier : listes, tableaux, encadrés, code, onglets, diagrammes, notes.
    À la fin, vous obtenez une page de documentation complète, et vous maîtrisez tout le Markdown de Forge.

## Comment lire ce parcours

Chaque palier présente d'abord la **source** Markdown dans un bloc de code, puis son **rendu** réel.
Vous reproduisez ensuite la syntaxe dans votre fichier `prise-en-main.md`, section après section.

~~~md
Un mot en **gras**, un autre en _italique_.
~~~

Rendu :

Un mot en **gras**, un autre en _italique_.

## Le style d'écriture attendu

La documentation Forge suit une typographie française stricte (directive §2.1) :

- une **phrase par ligne** dans la source Markdown ;
- des **espaces insécables** avant `: ; ? !` et autour des guillemets « » ;
- **pas** de tiret cadratin ; on préfère la virgule, le point-virgule ou les deux-points.

## Installer Markdown et ses extensions

Markdown n'est pas un outil que l'on installe seul.
Dans la documentation Forge, il est rendu par **MkDocs** et le thème **Material** ; les extensions viennent du paquet **pymdown-extensions** (quelques-unes sont fournies directement par Markdown).

Trois paquets suffisent. Le dépôt les déclare dans `requirements-docs.txt` :

```text
mkdocs>=1.6
mkdocs-material>=9.7
pymdown-extensions>=10.0
```

Installez-les dans votre environnement :

```bash
pip install -r requirements-docs.txt
# ou directement :
pip install "mkdocs>=1.6" "mkdocs-material>=9.7" "pymdown-extensions>=10.0"
```

### Activer les extensions

Une extension installée n'agit que si elle est **déclarée** dans `mkdocs.yml`, sous la clé `markdown_extensions`.
Voici la configuration de Forge, à recopier :

```yaml
markdown_extensions:
  - admonition          # encadrés !!!
  - attr_list           # attributs en ligne { .classe }
  - def_list            # listes de définition
  - footnotes           # notes de bas de page
  - md_in_html          # Markdown dans du HTML
  - tables              # tableaux
  - toc:                # sommaire + ancres
      permalink: true
  - pymdownx.details    # blocs dépliables ???
  - pymdownx.highlight:  # coloration des blocs de code
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.superfences:  # blocs imbriqués + fence mermaid
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.inlinehilite  # code en ligne coloré
  - pymdownx.snippets      # inclusion de fichiers --8<--
  - pymdownx.tabbed:       # onglets ===
      alternate_style: true
  - pymdownx.tasklist:     # cases à cocher
      custom_checkbox: true
  - pymdownx.mark          # ==surlignage==
  - pymdownx.caret         # ^exposant^, ^^inséré^^
  - pymdownx.tilde         # ~indice~, ~~barré~~
  - pymdownx.keys          # touches ++ctrl+c++
  - pymdownx.magiclink     # liens automatiques
  - pymdownx.emoji:        # icônes :material-...: et émojis
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  - pymdownx.smartsymbols  # (c), -->, +/- ...
  - pymdownx.critic        # annotations de relecture
  - pymdownx.arithmatex:   # formules mathématiques
      generic: true
  - pymdownx.progressbar   # barres de progression
  - pymdownx.betterem      # emphase plus fine
  - abbr                   # abréviations *[SIGLE]:
  - sane_lists             # règles de listes strictes
  - meta                   # métadonnées de page
  - wikilinks              # liens [[Page]]
  - legacy_attrs           # compatibilité d'attributs
```

Les extensions sans préfixe (`admonition`, `attr_list`, `tables`, `abbr`…) sont fournies par **Markdown** lui-même ; celles en `pymdownx.*` viennent de **pymdown-extensions** ; l'index d'émojis `material.extensions.emoji` vient du thème **Material**.

### Le CSS et le JavaScript d'appoint

Quelques fonctionnalités ont besoin d'un fichier compagnon, déclaré lui aussi dans `mkdocs.yml` :

```yaml
extra_css:
  - stylesheets/extra.css

extra_javascript:
  - javascripts/mathjax.js
  - https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js
```

- `extra.css` porte les styles maison, par exemple la classe `.intro-label`.
- `mathjax.js` configure le rendu des formules (`arithmatex`), complété par la bibliothèque MathJax.

### Plugins et fonctionnalités du thème

Deux effets interactifs ne viennent pas des extensions, mais d'un **plugin** et d'une **fonctionnalité du thème** :

- la **lightbox** d'image (agrandissement au clic) est fournie par le plugin `mkdocs-glightbox`, ajouté à `requirements-docs.txt` et déclaré sous `plugins` ;
- les **infobulles** au survol viennent de la fonctionnalité Material `content.tooltips`, déclarée sous `theme.features`.

```yaml
theme:
  features:
    - content.tooltips   # infobulles au survol

plugins:
  - search
  - glightbox            # lightbox d'image
```

## Lancer le serveur de prévisualisation

Pendant la rédaction, lancez le serveur local de MkDocs : il sert la documentation et la **recharge** à chaque enregistrement.

```bash
mkdocs serve
```

Ouvrez ensuite http://127.0.0.1:8000 dans votre navigateur : chaque sauvegarde d'un fichier `.md` met la page à jour automatiquement.

!!! warning "Port déjà utilisé"
    Par défaut, MkDocs écoute sur le port 8000, comme le serveur de développement de Forge (`forge serve`).
    Si les deux tournent en même temps, donnez un autre port à MkDocs :

    ```bash
    mkdocs serve -a 127.0.0.1:8001
    ```

Pour produire le site final (les fichiers HTML, dans `site/`) et contrôler la documentation :

```bash
mkdocs build --strict
```

L'option `--strict` transforme le moindre avertissement (lien mort, page absente de la navigation) en **erreur** : c'est le contrôle utilisé pour toute la documentation Forge.

## Les trois niveaux

| Niveau | Ce que vous construisez | Markdown abordé |
|---|---|---|
| [Débutant](debutant/titre-et-intro.md) | le squelette de la page | titres, texte, listes, citations, liens |
| [Intermédiaire](intermediaire/tableaux.md) | une page riche | tableaux, définitions, encadrés, blocs dépliables, code |
| [Avancé](avance/onglets.md) | une page de niveau professionnel | onglets, diagrammes, texte enrichi, notes, relecture, maths |

[Commencer le niveau débutant](debutant/titre-et-intro.md)
