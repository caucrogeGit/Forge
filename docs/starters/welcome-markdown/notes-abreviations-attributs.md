# Notes, abréviations et attributs

**Objectif**{ .intro-label } : annoter le texte avec des notes de bas de page, des abréviations explicitées et des attributs HTML.

**Ce que vous allez apprendre :**{ .intro-label } les extensions `footnotes`, `abbr`, `attr_list`, `magiclink` et `wikilinks`.

## Notes de bas de page

Un appel `[^clé]` renvoie à une définition placée plus bas dans la page.

~~~md
Forge garde le SQL visible[^sql] et refuse la magie cachée.

[^sql]: Pas d'ORM : les requêtes sont écrites à la main et lisibles telles quelles.
~~~

Rendu :

Forge garde le SQL visible[^sql] et refuse la magie cachée.

[^sql]: Pas d'ORM : les requêtes sont écrites à la main et lisibles telles quelles.

Quel que soit l'endroit où vous écrivez la définition, elle s'affiche en **bas de page**, avec un lien de retour.

## Abréviations

L'extension `abbr` associe un sigle à sa signification : au survol, une infobulle s'affiche.
On déclare la signification une fois, n'importe où dans la page.

~~~md
Le protocole HTTP transporte la requête, et le jeton CSRF protège les écritures.

*[HTTP]: HyperText Transfer Protocol
*[CSRF]: Cross-Site Request Forgery
~~~

Rendu (survolez les sigles) :

Le protocole HTTP transporte la requête, et le jeton CSRF protège les écritures.

*[HTTP]: HyperText Transfer Protocol
*[CSRF]: Cross-Site Request Forgery

## Attributs en ligne

L'extension `attr_list` ajoute des classes, identifiants ou attributs à un élément, entre accolades.

### Une classe sur du texte

C'est ainsi qu'est posé le libellé orange des paliers welcome-forge.

~~~md
**Objectif**{ .intro-label } : la classe CSS `.intro-label` colore ce libellé.
~~~

Rendu :

**Objectif**{ .intro-label } : la classe CSS `.intro-label` colore ce libellé.

### Attributs sur un lien ou une image

~~~md
[Ouvrir dans un nouvel onglet](https://www.python.org){ target="_blank" rel="noopener" }

![Logo](../../assets/logo.png){ width="120" }
~~~

### Un identifiant d'ancre sur un titre

~~~md
## Ma section { #ancre-personnalisee }
~~~

Le titre devient atteignable via `#ancre-personnalisee` dans l'URL.

## Liens automatiques

L'extension `magiclink` transforme une URL ou une adresse écrite en clair en lien cliquable, sans syntaxe particulière.

~~~md
La page officielle est https://www.python.org et le contact doc@example.com.
~~~

Rendu :

La page officielle est https://www.python.org et le contact doc@example.com.

## Liens « wiki »

L'extension `wikilinks` transforme `[[NomDePage]]` en lien vers une page de même nom.

~~~md
Voir [[ReferenceHttp]] pour les détails.
~~~

Le libellé devient le texte du lien, et la cible est calculée à partir du nom.
Cette syntaxe est surtout utile pour des renvois internes rapides ; dans la doc Forge, on privilégie le lien explicite vers le fichier `.md` (vérifié au build `--strict`).

[Continuer avec Relecture et maths](relecture-et-maths.md)
