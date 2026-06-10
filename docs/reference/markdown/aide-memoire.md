# Aide-mémoire Markdown

**Objectif** : retrouver d'un coup d'œil toute la syntaxe Markdown de la documentation Forge, son rendu et le nom de chaque signe.

**Ce que vous allez apprendre :** rien de neuf, c'est la synthèse. La syntaxe **en ligne** est donnée avec son **rendu** dans une colonne ; la syntaxe **en bloc** est dans des encadrés dépliables (source plus rendu) ; la dernière partie nomme les **signes**.

# Syntaxe en ligne

Chaque ligne montre la syntaxe, son effet et le **rendu** réel.

## Emphase et code

| Syntaxe | Effet | Rendu |
|---|---|---|
| `**gras**` | gras | **gras** |
| `_italique_` | italique | _italique_ |
| `***gras italique***` | gras et italique | ***gras italique*** |
| `` `code` `` | code en ligne | `Response.text()` |
| `` `#!python …` `` | code en ligne coloré | `#!python fetch_all()` |

## Texte enrichi

| Syntaxe | Effet | Rendu |
|---|---|---|
| `==texte==` | surlignage | ==surligné== |
| `^texte^` | exposant | m^2^ |
| `^^texte^^` | inséré | ^^inséré^^ |
| `~texte~` | indice | H~2~O |
| `~~texte~~` | barré | ~~barré~~ |
| `++ctrl+c++` | touches clavier | ++ctrl+c++ |
| `(c)` `-->` `+/-` | symboles | (c) --> +/- |
| `:material-check:` | icône | :material-check: |
| `:rocket:` | émoji | :rocket: |
| `[=60% "60 %"]` | barre de progression | [=60% "60 %"] |

## Liens, attributs et notes

| Syntaxe | Effet | Rendu |
|---|---|---|
| `[texte](cible)` | lien | [Python](https://www.python.org) |
| URL en clair | lien automatique | https://www.python.org |
| `**texte**{ .classe }` | classe ou attribut | **Objectif**{ .intro-label } |
| `**texte**{ title="…" }` | infobulle au survol | **mot**{ title="infobulle au survol" } |
| `texte[^clé]` | note de bas de page | un fait[^am] |
| `*[SIGLE]: …` | abréviation au survol | MVC |

[^am]: La note apparaît en bas de la page.

*[MVC]: Modèle Vue Contrôleur

## Relecture et maths en ligne

| Syntaxe | Effet | Rendu |
|---|---|---|
| `{++ajout++}` | ajout | {++ajout++} |
| `{--retrait--}` | suppression | {--retrait--} |
| `{~~a~>b~~}` | remplacement | {~~a~>b~~} |
| `{==surligné==}` | surlignage | {==surligné==} |
| `{>>note<<}` | commentaire | corrigé{>>commentaire<<} |
| `$O(1)$` | formule en ligne | $O(1)$ |

# Syntaxe en bloc

Ces éléments occupent plusieurs lignes : **dépliez** pour voir la source et le rendu.

??? note "Titres ( # )"
    ```md
    # Titre de la page
    ## Sous-titre
    ### Sous-sous-titre
    ```

    Le `#` donne le titre de la page ; `##` et `###` les sous-titres, repris dans le sommaire.

??? note "Listes (puces, numéros, tâches)"
    ```md
    - puce
    - autre puce

    1. premier
    2. second

    - [x] fait
    - [ ] à faire
    ```

    Rendu :

    - puce
    - autre puce

    1. premier
    2. second

    - [x] fait
    - [ ] à faire

??? note "Citation et règle horizontale"
    ```md
    > Une citation.

    ---
    ```

    Rendu :

    > Une citation.

    ---

??? note "Tableau"
    ```md
    | Gauche | Droite |
    |:---|---:|
    | a | 1 |
    ```

    Rendu :

    | Gauche | Droite |
    |:---|---:|
    | a | 1 |

??? note "Liste de définition"
    ```md
    Terme
    :   Sa définition.
    ```

    Rendu :

    Terme
    :   Sa définition.

??? note "Admonition ( !!! )"
    ```md
    !!! warning "Titre"
        Contenu de l'encadré.
    ```

    Rendu :

    !!! warning "Titre"
        Contenu de l'encadré.

??? note "Bloc dépliable ( ??? / ???+ )"
    ```md
    ??? note "Replié par défaut"
        Caché jusqu'au clic.

    ???+ note "Déplié par défaut"
        Visible, mais refermable.
    ```

    `???` est replié, `???+` est déplié ; même syntaxe que les admonitions.

??? note "Onglets ( === )"
    ```md
    === "Onglet A"
        Contenu A.

    === "Onglet B"
        Contenu B.
    ```

    Rendu :

    === "Onglet A"
        Contenu A.

    === "Onglet B"
        Contenu B.

??? note "Bloc de code"
    Source (clôture de quatre accents graves pour montrer celle de trois) :

    ~~~md
    ```python title="exemple.py" linenums="1" hl_lines="2"
    def index(request):
        return Response.text("Bonjour")
    ```
    ~~~

    Rendu :

    ```python title="exemple.py" linenums="1" hl_lines="2"
    def index(request):
        return Response.text("Bonjour")
    ```

??? note "Image (et lightbox)"
    ```md
    ![texte alternatif](chemin/image.png)
    ```

    Rendu (cliquez pour agrandir) :

    ![Logo de Forge](../../static/forge-logo.png)

    Au clic, l'image s'ouvre en grand dans une surimpression (plugin `mkdocs-glightbox`).

??? note "Diagramme Mermaid"
    ~~~md
    ```mermaid
    graph LR
        A[Requête] --> B[Réponse]
    ```
    ~~~

    Rendu :

    ```mermaid
    graph LR
        A[Requête] --> B[Réponse]
    ```

??? note "Inclusion de fichier"
    ```md
    --8<-- "chemin/extrait.py"
    ```

    Insère le contenu d'un fichier réel (plugin `snippets`), pour ne pas recopier une source.

??? note "Note de bas de page"
    ```md
    Un fait à sourcer[^1].

    [^1]: La précision correspondante.
    ```

    L'appel renvoie à une note affichée en bas de la page, avec un lien de retour.

??? note "Formule en bloc"
    ```md
    $$
    T(n) = T(n/2) + O(1)
    $$
    ```

    Rendu :

    $$
    T(n) = T(n/2) + O(1)
    $$

# Le nom des signes

L'exemple montre un usage courant.

## Ponctuation

| Signe | Nom et appellation | Exemple |
|---|---|---|
| `.` | point (*period*) | une phrase. |
| `,` | virgule (*comma*) | un, deux, trois |
| `;` | point-virgule (*semicolon*) | rouge ; vert |
| `:` | deux-points (*colon*) | trois couleurs : rouge, vert, bleu |
| `!` | point d'exclamation (*bang*) | attention ! |
| `?` | point d'interrogation (*question mark*) | vraiment ? |
| `…` | points de suspension (*ellipsis*) | et ainsi de suite… |
| `·` | point médian | auteur·rice |
| `•` | puce (*bullet*) | premier • deuxième |

## Tirets et traits

| Signe | Nom et appellation | Exemple |
|---|---|---|
| `-` | trait d'union (*hyphen*) | porte-clé |
| `–` | tiret demi-cadratin (*en dash*) | pages 10–20 |
| `—` | tiret cadratin (*em dash*, à éviter) | un aparté — comme ceci |
| `_` | tiret bas (*underscore*) | nom_de_variable |

## Guillemets et apostrophes

| Signe | Nom et appellation | Exemple |
|---|---|---|
| `«` `»` | guillemets français (chevrons) | « Bonjour Forge » |
| `"` | guillemet droit (*double quote*) | `"chaîne"` en code |
| `’` | apostrophe typographique | l’objet Request |
| `` ` `` | accent grave (*backtick*) | `forge serve` |

## Parenthèses, opérateurs et symboles

| Signe | Nom et appellation | Exemple |
|---|---|---|
| `(` `)` | parenthèses (*round brackets*) | une remarque (entre parenthèses) |
| `[` `]` | crochets (*square brackets*) | index `[0]` |
| `{` `}` | accolades (*curly braces*) | segment `/article/{id}` |
| `<` `>` | chevrons (*angle brackets*) | balise `<p>` |
| `\|` | barre verticale (*pipe*) | colonnes de tableau |
| `\` | barre oblique inverse (*backslash*) | échappement `\*` |
| `/` | barre oblique (*slash*) | chemin `a/b/c` |
| `#` | croisillon (*hash*, pas « dièse ») | titre `# Titre` |
| `&` | esperluette (*ampersand*) | `&` en HTML |
| `@` | arobase (*at*) | nom@example.com |
| `±` `×` `÷` | plus ou moins, multiplié, divisé | 20 ± 2, 6 × 7, 42 ÷ 6 |
| `≠` `≤` `≥` | comparateurs | a ≠ b, x ≤ y |
| `→` `←` `↔` | flèches | requête → réponse |
| `°` | degré | 20 °C |
| `§` | paragraphe (*section*) | voir § 2.1 |
| `µ` | micro (mu) | 5 µF |
| `©` `®` `™` | commerciaux | Forge © 2026 |

## Espaces

| Signe | Nom et appellation | Usage |
|---|---|---|
| (espace) | espace (sécable) | séparation ordinaire des mots |
| (espace insécable) | espace insécable (*no-break space*, U+00A0) | avant `: ; ? !` et autour des guillemets |
| (espace fine) | espace fine insécable (U+202F) | typographie soignée |

!!! warning "Le piège du « dièse »"
    En français courant, on appelle souvent `#` un « dièse ».
    C'est un abus : le vrai dièse est le signe musical `♯`.
    Le nom correct de `#` est **croisillon** (ou *hash* en informatique).

## Rappel de style

- Une **phrase par ligne** dans la source.
- Espaces **insécables** avant `: ; ? !` et autour des guillemets « ».
- **Pas** de tiret cadratin.
- Liens internes vers le **fichier** `.md`, vérifiés au build `--strict`.
