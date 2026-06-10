# Relecture et maths

**Objectif**{ .intro-label } : annoter une relecture (ajouts, suppressions, commentaires) et écrire des formules mathématiques.

**Ce que vous allez apprendre :**{ .intro-label } les extensions `critic` (annotations de relecture) et `arithmatex` (formules LaTeX).

## Annotations de relecture

L'extension `critic` matérialise les changements d'une relecture, à la manière du suivi de modifications.

| Syntaxe | Effet |
|---|---|
| `{++texte++}` | ajout |
| `{--texte--}` | suppression |
| `{~~ancien~>nouveau~~}` | remplacement |
| `{==texte==}` | surlignage |
| `{>>commentaire<<}` | commentaire en marge |

Exemple de source :

~~~md
Le noyau reste {--volumineux--}{++minimal++} et {==explicite==}{>>point clé<<}.
~~~

Rendu :

Le noyau reste {--volumineux--}{++minimal++} et {==explicite==}{>>point clé<<}.

!!! note "Mode d'affichage"
    Par défaut, les annotations sont **visibles** (mode « view »).
    Elles servent à discuter une proposition d'édition ; une fois la décision prise, on accepte ou rejette les marques en nettoyant le texte.

## Formules mathématiques

L'extension `arithmatex` (configurée en mode `generic`) reconnaît la syntaxe LaTeX.

Formule **en ligne**, entre simples `$` :

~~~md
La complexité est en $O(n \log n)$ dans le cas moyen.
~~~

Formule **en bloc**, entre doubles `$$` :

~~~md
$$
\sigma = \sqrt{\frac{1}{N}\sum_{i=1}^{N}(x_i - \mu)^2}
$$
~~~

!!! warning "Rendu : un script est nécessaire"
    `arithmatex` produit le balisage des formules, mais leur **rendu visuel** exige une bibliothèque JavaScript (MathJax ou KaTeX) chargée via `extra_javascript`.
    La documentation Forge ne la charge pas par défaut : sans elle, les formules restent affichées en texte LaTeX brut.
    Activez MathJax seulement si une page a réellement besoin de mathématiques.

[Continuer avec l'Aide-mémoire](recapitulatif.md)
