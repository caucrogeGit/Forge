# Aide-mémoire Markdown

**Objectif** : retrouver d'un coup d'œil toute la syntaxe Markdown de la documentation Forge, et le nom de chaque signe.

**Ce que vous allez apprendre :** rien de neuf, c'est la synthèse. La première partie récapitule la **syntaxe** ; la seconde nomme les **signes**.

# Partie 1 : la syntaxe

## Bases

| Syntaxe | Effet |
|---|---|
| `# Titre` … `###### Titre` | titres de niveau 1 à 6 |
| `**gras**`, `_italique_` | emphase |
| `- élément` | liste à puces |
| `1. élément` | liste numérotée |
| `- [ ]` / `- [x]` | liste de tâches |
| `> citation` | bloc de citation |
| `[libellé](cible.md)` | lien |
| `![alt](image.png)` | image |
| `---` | règle horizontale |
| `\*` | échapper un caractère |

## Tableaux et définitions

| Syntaxe | Effet |
|---|---|
| `\| a \| b \|` + ligne `\|---\|---\|` | tableau |
| `:---`, `:---:`, `---:` | alignement gauche, centré, droite |
| terme puis `:   définition` | liste de définition |

## Admonitions et onglets

| Syntaxe | Effet |
|---|---|
| `!!! note "Titre"` | encadré (note, tip, warning, danger…) |
| `??? note "Titre"` | encadré dépliable, replié |
| `???+ note "Titre"` | encadré dépliable, déplié |
| `=== "Onglet"` | onglets de contenu |

## Code et diagrammes

| Syntaxe | Effet |
|---|---|
| `` `code` `` | code en ligne |
| `` `#!python …` `` | code en ligne coloré |
| clôture ```` ``` ```` + langage | bloc de code coloré |
| `linenums="1"`, `hl_lines="2 3"`, `title="…"` | options de bloc |
| clôture `mermaid` | diagramme |
| `--8<-- "fichier"` | inclure un fichier |

## Texte enrichi

| Syntaxe | Effet |
|---|---|
| `==texte==` | surlignage |
| `^exposant^`, `^^inséré^^` | exposant, insertion |
| `~indice~`, `~~barré~~` | indice, barré |
| `++ctrl+c++` | touches clavier |
| `(c)`, `(tm)`, `-->`, `+/-` | symboles typographiques |
| `:material-check:`, `:smile:` | icônes et émojis |
| `[=85% "85 %"]` | barre de progression |

## Notes, abréviations, attributs

| Syntaxe | Effet |
|---|---|
| `texte[^clé]` + `[^clé]: …` | note de bas de page |
| `*[SIGLE]: signification` | abréviation avec infobulle |
| `**texte**{ .classe }` | classe, identifiant ou attribut |
| URL ou email en clair | lien automatique |
| `[[NomDePage]]` | lien wiki |

## Relecture et maths

| Syntaxe | Effet |
|---|---|
| `{++ajout++}`, `{--retrait--}` | ajout, suppression |
| `{~~ancien~>nouveau~~}` | remplacement |
| `{==surligné==}`, `{>>note<<}` | surlignage, commentaire |
| `$O(n)$`, `$$ … $$` | formule en ligne, en bloc |

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

## Voir aussi

Le parcours qui construit tout cela, palier après palier :

- [Préambule](installation.md) : le fil rouge « Prise en main de Forge ».
- [Niveau débutant](debutant/titre-et-intro.md) : structure de base.
- [Niveau intermédiaire](intermediaire/tableaux.md) : enrichir la page.
- [Niveau avancé](avance/onglets.md) : finition professionnelle.
