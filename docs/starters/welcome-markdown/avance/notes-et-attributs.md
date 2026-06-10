# Notes, abréviations et attributs

**Objectif** : expliciter les sigles, ajouter une note de bas de page et un libellé mis en forme.

**Ce que vous allez apprendre :** les extensions `footnotes`, `abbr`, `attr_list` et `wikilinks`.

Votre page emploie des sigles (MVC, CSRF) sans les définir.

Nous les explicitons, ajoutons une note de bas de page et un libellé en couleur.

## Notes de bas de page

Un appel `[^clé]` renvoie à une définition placée plus bas ; elle s'affiche en bas de page.

~~~md
Forge suit le patron MVC[^mvc].

[^mvc]: Modèle, Vue, Contrôleur : une séparation classique des responsabilités.
~~~

Rendu :

Forge suit le patron MVC[^mvc].

[^mvc]: Modèle, Vue, Contrôleur : une séparation classique des responsabilités.

## Abréviations

L'extension `abbr` associe un sigle à sa signification : au survol, une infobulle s'affiche.
On déclare la signification une fois, n'importe où dans la page.

~~~md
Le jeton CSRF protège les formulaires, et le SQL reste visible.

*[CSRF]: Cross-Site Request Forgery
*[SQL]: Structured Query Language
~~~

Rendu (survolez les sigles) :

Le jeton CSRF protège les formulaires, et le SQL reste visible.

*[CSRF]: Cross-Site Request Forgery
*[SQL]: Structured Query Language

## Attributs en ligne

L'extension `attr_list` ajoute une classe, un identifiant ou un attribut entre accolades.
La classe `.intro-label` colore un libellé, comme dans les paliers welcome-forge.

~~~md
**Objectif**{ .intro-label } : installer Forge en cinq minutes.
~~~

Rendu :

**Objectif**{ .intro-label } : installer Forge en cinq minutes.

## Ajoutez à votre page

Déclarez les abréviations en bas de `prise-en-main.md`, et donnez un libellé d'objectif à l'introduction :

~~~md
**Objectif**{ .intro-label } : installer Forge et créer un premier projet.

*[MVC]: Modèle Vue Contrôleur
*[CSRF]: Cross-Site Request Forgery
~~~

## À retenir

- Note de bas de page : appel `[^clé]` plus définition `[^clé]: …`.
- Abréviation : `*[SIGLE]: signification` ; infobulle au survol.
- `attr_list` ajoute classes et attributs, par exemple `{ .intro-label }`.

[Continuer avec Relecture et maths](relecture-et-maths.md)
