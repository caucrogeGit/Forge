# Relecture et maths

**Objectif** : annoter une relecture (ajouts, suppressions, commentaires) et écrire des formules mathématiques.

**Ce que vous allez apprendre :** les extensions `critic` (annotations de relecture) et `arithmatex` (formules LaTeX).

## Annotations de relecture

L'extension `critic` matérialise les changements d'une relecture, à la manière du suivi de modifications.

| Syntaxe | Effet |
|---|---|
| `{++texte++}` | ajout |
| `{--texte--}` | suppression |
| `{~~ancien~>nouveau~~}` | remplacement |
| `{==texte==}` | surlignage |
| `{>>commentaire<<}` | commentaire en marge |

Exemple de source :

~~~md
Le noyau reste {--volumineux--}{++minimal++} et {==explicite==}{>>point clé<<}.
~~~

Rendu :

Le noyau reste {--volumineux--}{++minimal++} et {==explicite==}{>>point clé<<}.

!!! note "Mode d'affichage"
    Par défaut, les annotations sont **visibles** (mode « view »).
    Elles servent à discuter une proposition d'édition ; une fois la décision prise, on accepte ou rejette les marques en nettoyant le texte.

## Formules mathématiques

L'extension `arithmatex` (configurée en mode `generic`) reconnaît la syntaxe LaTeX.

Formule **en ligne**, entre simples `$` :

~~~md
La complexité est en $O(n \log n)$ dans le cas moyen.
~~~

Rendu :

La complexité est en $O(n \log n)$ dans le cas moyen.

Formule **en bloc**, entre doubles `$$` :

~~~md
$$
\sigma = \sqrt{\frac{1}{N}\sum_{i=1}^{N}(x_i - \mu)^2}
$$
~~~

Rendu :

$$
\sigma = \sqrt{\frac{1}{N}\sum_{i=1}^{N}(x_i - \mu)^2}
$$

!!! info "MathJax est chargé"
    La documentation Forge charge **MathJax** via `extra_javascript` (le fichier `docs/javascripts/mathjax.js` plus la bibliothèque officielle).
    Les formules ci-dessus sont donc rendues visuellement, et non laissées en texte brut.
    Le script n'agit que sur les éléments de classe `arithmatex` produits par `arithmatex` : le reste du texte n'est jamais réinterprété.

[Continuer avec l'Aide-mémoire](aide-memoire.md)
