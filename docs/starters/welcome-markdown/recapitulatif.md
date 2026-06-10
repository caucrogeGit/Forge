# Aide-mémoire Markdown

**Objectif** : retrouver d'un coup d'œil toute la syntaxe Markdown de la documentation Forge, et le nom de chaque signe.

**Ce que vous allez apprendre :** rien de neuf, c'est la synthèse. La première partie récapitule la **syntaxe** (chaque ligne renvoie à la page qui la détaille) ; la seconde nomme les **signes**.

# Partie 1 : la syntaxe

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

# Partie 2 : le nom des signes

Rédiger une documentation claire suppose de désigner les signes par leur nom.
Écrire « le croisillon » ou « l'accent grave » est plus précis que « le petit carré » ou « la cédille à l'envers ».

## Ponctuation courante

| Signe | Nom français | Appellations et usage |
|---|---|---|
| `.` | point | point final ; séparateur décimal en anglais |
| `,` | virgule | séparateur décimal en français |
| `;` | point-virgule | *semicolon* |
| `:` | deux-points | *colon* |
| `!` | point d'exclamation | *bang*, *exclamation mark* |
| `?` | point d'interrogation | *question mark* |
| `…` | points de suspension | *ellipsis* (un seul caractère) |
| `·` | point médian | utilisé pour l'écriture inclusive |
| `•` | puce | *bullet* (listes) |

## Tirets et traits

La distinction est importante : la documentation Forge **proscrit le tiret cadratin**.

| Signe | Nom français | Appellations et usage |
|---|---|---|
| `-` | trait d'union | *hyphen* ; aussi signe moins et puce Markdown |
| `–` | tiret demi-cadratin | *en dash* ; intervalles (peu utilisé en français) |
| `—` | tiret cadratin | *em dash* ; **à éviter** dans la doc Forge (directive §2.1) |
| `_` | tiret bas | *underscore*, soulignement ; italique en Markdown |
| `‒` | tiret numéral | rare |

## Guillemets et apostrophes

| Signe | Nom français | Appellations et usage |
|---|---|---|
| `«` `»` | guillemets français | chevrons ; citations en français, avec espaces insécables |
| `"` | guillemet droit | *double quote* ; chaînes en code |
| `'` | apostrophe droite | *single quote*, apostrophe dactylographique |
| `“` `”` | guillemets courbes doubles | guillemets anglais ouvrant/fermant |
| `‘` `’` | guillemets courbes simples | apostrophe typographique `’` |
| `` ` `` | accent grave | *backtick*, *backquote* ; code en ligne en Markdown |

## Parenthèses, crochets, accolades, chevrons

| Signe | Nom français | Appellations et usage |
|---|---|---|
| `(` `)` | parenthèses | *parentheses*, *round brackets* |
| `[` `]` | crochets | *square brackets* ; libellé de lien Markdown |
| `{` `}` | accolades | *curly braces* ; attributs `attr_list`, segments de route `{id}` |
| `<` `>` | chevrons | inférieur et supérieur ; *angle brackets* ; balises HTML |

## Signes utilisés en Markdown et en code

| Signe | Nom français | Appellations et usage |
|---|---|---|
| `#` | croisillon | *hash*, *pound* ; titres en Markdown (à ne pas confondre avec le dièse `♯`) |
| `*` | astérisque | *star*, *splat* ; emphase et puces en Markdown |
| `~` | tilde | indice et barré en Markdown ; clôture de bloc alternative |
| `^` | accent circonflexe | *caret*, *chapeau* ; exposant en Markdown, puissance en code |
| `\|` | barre verticale | *pipe* ; colonnes de tableau Markdown |
| `\` | barre oblique inverse | *antislash*, *backslash* ; échappement |
| `/` | barre oblique | *slash* ; séparateur de chemin |
| `&` | esperluette | *et commercial*, *ampersand* ; entités HTML |
| `@` | arobase | *at* ; adresses et décorateurs |
| `=` | signe égal | *equals* ; onglets `===`, affectation en code |
| `+` | signe plus | *plus* ; bloc déplié `???+`, touches `++` |

## Opérateurs et symboles mathématiques

| Signe | Nom français | Appellations et usage |
|---|---|---|
| `%` | pour cent | *percent* ; modulo en code |
| `±` | plus ou moins | *plus-minus* |
| `×` | signe multiplié | croix de multiplication |
| `÷` | signe divisé | *obelus* |
| `≠` | différent de | *not equal* |
| `≤` `≥` | inférieur ou égal, supérieur ou égal | |
| `→` `←` `↔` | flèches | vers la droite, la gauche, double |
| `√` | radical | racine carrée |
| `∑` | sigma majuscule | symbole de somme |
| `°` | degré | *degree* ; angles et températures |

## Symboles divers et commerciaux

| Signe | Nom français | Appellations et usage |
|---|---|---|
| `§` | paragraphe | *section* ; renvoi à une section numérotée |
| `¶` | pied-de-mouche | *pilcrow* ; marque de paragraphe |
| `†` `‡` | obèle, double obèle | *dagger* ; appels de note |
| `$` | dollar | formules `arithmatex` en Markdown |
| `€` | euro | |
| `©` | copyright | droit d'auteur |
| `®` | marque déposée | *registered* |
| `™` | marque commerciale | *trademark* |
| `µ` | micro | lettre grecque mu, préfixe d'unité |

## Espaces

| Signe | Nom français | Appellations et usage |
|---|---|---|
| (espace) | espace | espace ordinaire, sécable |
| (espace insécable) | espace insécable | *no-break space* (U+00A0) ; avant `: ; ? !` et autour des guillemets |
| (espace fine) | espace fine insécable | U+202F ; typographie soignée |

## Séquences de signes en Markdown

Certains signes prennent un sens une fois **répétés ou combinés**.

| Séquence | Nom | Sens en Markdown |
|---|---|---|
| `#` … `######` | croisillons | titres de niveau 1 à 6 |
| `**texte**` | double astérisque | gras |
| `_texte_` | tiret bas | italique |
| `***texte***` | triple astérisque | gras italique |
| `` `code` `` | accents graves | code en ligne |
| ```` ``` ```` | clôture de code (trois accents graves) | bloc de code |
| `>` | chevron | citation |
| `- ` / `* ` / `+ ` | tiret, astérisque, plus | puce de liste |
| `- [ ]` / `- [x]` | tiret crochets | case à cocher |
| `---` | trois tirets | règle horizontale |
| `!!!` | triple point d'exclamation | admonition (encadré) |
| `???` | triple point d'interrogation | admonition dépliable, repliée |
| `???+` | triple point d'interrogation plus | admonition dépliable, dépliée |
| `=== "Onglet"` | triple signe égal | onglet de contenu |
| `==texte==` | double signe égal | surlignage |
| `~~texte~~` | double tilde | barré |
| `~texte~` | tilde | indice |
| `^texte^` | accent circonflexe | exposant |
| `^^texte^^` | double accent circonflexe | texte inséré |
| `++ctrl+c++` | doubles plus | touches clavier |
| `[texte](cible)` | crochets et parenthèses | lien |
| `![alt](source)` | exclamation, crochets, parenthèses | image |
| `[^1]` | crochets et accent circonflexe | appel de note de bas de page |
| `*[SIGLE]:` | astérisque et crochets | définition d'abréviation |
| `{ .classe }` | accolades | attribut en ligne (`attr_list`) |
| `{++ajout++}` `{--retrait--}` | accolades de relecture | annotations `critic` |
| `--8<--` | ciseaux | inclusion de fichier (`snippets`) |
| `$formule$` / `$$bloc$$` | dollars | formule mathématique (`arithmatex`) |
| `[[Page]]` | doubles crochets | lien wiki |
| `:nom:` | deux-points | émoji ou icône |
| `\` | barre oblique inverse | échappement du signe suivant |

!!! warning "Le piège du « dièse »"
    En français courant, on appelle souvent `#` un « dièse ».
    C'est un abus : le vrai dièse est le signe musical `♯`.
    Le nom correct de `#` est **croisillon** (ou *hash* en informatique).

## Rappel de style

- Une **phrase par ligne** dans la source.
- Espaces **insécables** avant `: ; ? !` et autour des guillemets « ».
- **Pas** de tiret cadratin.
- Liens internes vers le **fichier** `.md`, vérifiés au build `--strict`.

[Revenir au Préambule](installation.md)
