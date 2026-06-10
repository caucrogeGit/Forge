# Relecture et maths

**Objectif** : annoter une relecture de la page et, au besoin, écrire une formule.

**Ce que vous allez apprendre :** les extensions `critic` (annotations de relecture) et `arithmatex` (formules mathématiques rendues par MathJax).

Votre page est complète.

Avant de la publier, un relecteur peut y laisser des marques de correction ; et certaines pages techniques ont besoin d'une formule.

## Annotations de relecture

L'extension `critic` matérialise les changements proposés, à la manière du suivi de modifications.

| Syntaxe | Effet |
|---|---|
| `{++ajout++}` | ajout |
| `{--suppression--}` | suppression |
| `{~~ancien~>nouveau~~}` | remplacement |
| `{==surlignage==}` | surlignage |
| `{>>commentaire<<}` | commentaire en marge |

~~~md
Forge exige Python {--3.10--}{++3.12++} ou plus.{>>vérifier la version minimale<<}
~~~

Rendu :

Forge exige Python {--3.10--}{++3.12++} ou plus.{>>vérifier la version minimale<<}

!!! note "Usage"
    Ces marques servent à **discuter** une correction.
    Une fois la décision prise, on accepte ou rejette les annotations en nettoyant le texte.

## Formules mathématiques

L'extension `arithmatex` reconnaît la syntaxe LaTeX, et la documentation Forge charge **MathJax** : les formules sont donc rendues visuellement.

Formule en ligne, entre simples `$` :

~~~md
La recherche d'une route est en $O(1)$ grâce à la table de hachage.
~~~

Rendu :

La recherche d'une route est en $O(1)$ grâce à la table de hachage.

Formule en bloc, entre doubles `$$` :

~~~md
$$
T(n) = T(n/2) + O(1)
$$
~~~

Rendu :

$$
T(n) = T(n/2) + O(1)
$$

## Ajoutez à votre page

Les maths sont rarement utiles dans une page de prise en main : réservez-les aux pages qui en ont besoin.
En revanche, gardez le réflexe `critic` lors de vos relectures, par exemple :

~~~md
Le serveur écoute sur le port {~~5000~>8000~~} par défaut.
~~~

## À retenir

- `critic` annote une relecture : ajout, suppression, remplacement, commentaire.
- `arithmatex` plus MathJax rend les formules LaTeX, en ligne (`$…$`) ou en bloc (`$$…$$`).
- N'ajoutez des formules que là où elles servent vraiment.

[Voir le bilan du niveau avancé](bilan.md)
