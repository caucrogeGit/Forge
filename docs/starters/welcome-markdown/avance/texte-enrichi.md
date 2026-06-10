# Le texte enrichi

**Objectif** : ajouter des touches fines à la page : termes surlignés, touches clavier, symboles et icônes.

**Ce que vous allez apprendre :** les extensions `mark`, `caret`, `tilde`, `keys`, `smartsymbols`, `emoji` et `progressbar`.

Votre page est complète sur le fond.

Nous soignons la forme avec quelques enrichissements ponctuels.

## Surligner, exposant, indice, barré

~~~md
Un terme ==important==.
Une surface en m^2^ et la formule H~2~O.
Un prix ~~barré~~.
~~~

Rendu :

Un terme ==important==.
Une surface en m^2^ et la formule H~2~O.
Un prix ~~barré~~.

## Touches clavier et symboles

~~~md
Interrompez le serveur avec ++ctrl+c++.
Copyright (c), tolérance +/- 1, flèche -->.
~~~

Rendu :

Interrompez le serveur avec ++ctrl+c++.
Copyright (c), tolérance +/- 1, flèche -->.

## Icônes, émojis et progression

~~~md
Installation réussie :material-check: ou échec :material-alert:.
Avancement du tutoriel :

[=66% "2 niveaux sur 3"]
~~~

Rendu :

Installation réussie :material-check: ou échec :material-alert:.
Avancement du tutoriel :

[=66% "2 niveaux sur 3"]

## Ajoutez à votre page

Enrichissez la section « Dépannage » ou « Commandes » de `prise-en-main.md`, par exemple :

~~~md
Pour arrêter le serveur de développement, utilisez ++ctrl+c++.
Une commande réussie affiche une coche :material-check: dans la sortie.
~~~

## À retenir

- `==surligné==`, `^exposant^`, `~indice~`, `~~barré~~`.
- `++ctrl+c++` rend de vraies touches ; `(c)`, `-->`, `+/-` deviennent des symboles.
- `:nom:` insère une icône Material ou un émoji ; `[=66% "…"]` une barre de progression.

[Continuer avec Notes, abréviations et attributs](notes-et-attributs.md)
