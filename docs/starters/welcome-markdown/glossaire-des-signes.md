# Glossaire des signes

**Objectif** : nommer correctement les signes de ponctuation, de typographie et de programmation.

**Ce que vous allez apprendre :** le nom français de chaque signe, ses appellations courantes en informatique, et son usage en Markdown quand il en a un.

!!! tip "Pourquoi nommer les signes"
    Rédiger une documentation claire suppose de désigner les signes par leur nom.
    Écrire « le croisillon » ou « l'accent grave » est plus précis que « le petit carré » ou « la cédille à l'envers ».
    Cette page sert de référence partagée pour toute la documentation Forge.

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

!!! warning "Le piège du « dièse »"
    En français courant, on appelle souvent `#` un « dièse ».
    C'est un abus : le vrai dièse est le signe musical `♯`.
    Le nom correct de `#` est **croisillon** (ou *hash* en informatique).

## Séquences de signes en Markdown

Certains signes prennent un sens une fois **répétés ou combinés**.
Voici comment nommer et lire ces séquences.

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

## Voir aussi

- [Texte enrichi](texte-enrichi.md) : où plusieurs de ces signes (`==`, `^`, `~`, `++`) prennent un sens en Markdown.
- [Aide-mémoire](recapitulatif.md) : la syntaxe Markdown complète.

[Revenir au Préambule](installation.md)
