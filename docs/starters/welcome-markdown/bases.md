# Les bases

**Objectif**{ .intro-label } : maîtriser la syntaxe Markdown fondamentale, commune à toutes les pages.

**Ce que vous allez apprendre :**{ .intro-label } titres, emphase, listes, citations, liens, images, règles horizontales et échappement des caractères.

## Titres

Un titre commence par un à six `#`, suivis d'une espace.

~~~md
# Titre de niveau 1
## Titre de niveau 2
### Titre de niveau 3
~~~

Le titre de niveau 1 est réservé au **titre de la page** : n'en mettez qu'un.
Les titres de niveau 2 et 3 alimentent automatiquement le sommaire de droite (extension `toc`), chacun recevant une ancre cliquable.

## Paragraphes et emphase

Une ligne vide sépare deux paragraphes.
L'emphase est gérée finement par l'extension `betterem`.

~~~md
Du texte en **gras**, en _italique_, en **_gras italique_**.
On peut aussi _imbriquer **proprement** les marqueurs_.
~~~

Rendu :

Du texte en **gras**, en _italique_, en **_gras italique_**.
On peut aussi _imbriquer **proprement** les marqueurs_.

## Listes à puces

Une puce commence par `-` (tiret) suivi d'une espace ; l'indentation crée des sous-listes.

~~~md
- Premier élément
- Deuxième élément
    - Sous-élément
    - Autre sous-élément
- Troisième élément
~~~

Rendu :

- Premier élément
- Deuxième élément
    - Sous-élément
    - Autre sous-élément
- Troisième élément

## Listes numérotées

Les numéros réels importent peu : Markdown renumérote.
L'extension `sane_lists` impose des règles cohérentes (une liste numérotée ne démarre pas par accident sur un simple `1.` en milieu de paragraphe).

~~~md
1. Première étape
2. Deuxième étape
3. Troisième étape
~~~

Rendu :

1. Première étape
2. Deuxième étape
3. Troisième étape

## Listes de tâches

L'extension `tasklist` ajoute des cases à cocher.

~~~md
- [x] Étape réalisée
- [ ] Étape à faire
- [ ] Autre étape à faire
~~~

Rendu :

- [x] Étape réalisée
- [ ] Étape à faire
- [ ] Autre étape à faire

## Citations

Un `>` en début de ligne cite un texte.

~~~md
> Forge est un framework web Python explicite, pédagogique, testable et durable.
> On peut citer sur plusieurs lignes.
~~~

Rendu :

> Forge est un framework web Python explicite, pédagogique, testable et durable.
> On peut citer sur plusieurs lignes.

## Liens

Un lien associe un libellé entre crochets à une cible entre parenthèses.

~~~md
Un lien vers [le préambule de cette progression](installation.md).
Un lien externe vers [le site de Python](https://www.python.org).
~~~

Rendu :

Un lien vers [le préambule de cette progression](installation.md).
Un lien externe vers [le site de Python](https://www.python.org).

!!! tip "Liens internes"
    Pour une page de la documentation, pointez vers le **fichier** `.md` (chemin relatif), pas vers l'URL finale.
    MkDocs vérifie ces liens au build `--strict` : un lien cassé fait échouer la compilation, ce qui protège la documentation.

## Images

La syntaxe d'une image est celle d'un lien précédé d'un `!`.

~~~md
![Texte alternatif décrivant l'image](../../assets/logo.png)
~~~

Le texte alternatif est important pour l'accessibilité et s'affiche si l'image manque.

## Règle horizontale

Trois tirets seuls sur une ligne tracent une séparation.

~~~md
---
~~~

Rendu :

---

## Échapper un caractère

Pour afficher un caractère spécial littéralement, précédez-le d'un antislash.

~~~md
Afficher une étoile littérale : \*pas en italique\*.
~~~

Rendu :

Afficher une étoile littérale : \*pas en italique\*.

[Continuer avec Tableaux et définitions](tableaux-et-definitions.md)
