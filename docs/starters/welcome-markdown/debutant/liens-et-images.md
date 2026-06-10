# Liens et images

**Objectif** : renvoyer vers des ressources et illustrer la page.

**Ce que vous allez apprendre :** les liens internes et externes, les liens automatiques (extension `magiclink`) et les images.

Votre page est presque complète.

Nous ajoutons une section « Liens utiles » et montrons comment insérer une image.

## Liens

Un lien associe un libellé entre crochets à une cible entre parenthèses.
Pour une page de la documentation, pointez vers le **fichier** `.md` : MkDocs vérifie ces liens au build `--strict`.

~~~md
Voir l'[aide-mémoire Markdown](../../../reference/markdown/aide-memoire.md).
Le site officiel de [Python](https://www.python.org).
~~~

Rendu :

Voir l'[aide-mémoire Markdown](../../../reference/markdown/aide-memoire.md).
Le site officiel de [Python](https://www.python.org).

## Liens automatiques

Avec `magiclink`, une URL écrite en clair devient cliquable sans syntaxe particulière.

~~~md
La documentation vit sur https://www.python.org et le contact est doc@example.com.
~~~

Rendu :

La documentation vit sur https://www.python.org et le contact est doc@example.com.

## Images

Une image est un lien précédé d'un `!` ; le texte alternatif décrit l'image et s'affiche si elle manque.

~~~md
![Logo de Forge](assets/logo-forge.png)
~~~

Le chemin est relatif à la page ; placez vos fichiers dans un dossier `assets/` du projet.

## Ajoutez à votre page

Terminez `prise-en-main.md` par une section de liens :

~~~md
## Liens utiles

- La [documentation complète](https://example.com/forge).
- Le dépôt du code et le suivi des tickets.
- Contact : doc@example.com
~~~

## À retenir

- Lien : `[libellé](cible)` ; pour la doc, viser le fichier `.md`.
- `magiclink` transforme une URL ou un email en clair en lien.
- Image : `![texte alternatif](chemin)`, le `!` fait la différence.

[Voir le bilan du niveau débutant](bilan.md)
