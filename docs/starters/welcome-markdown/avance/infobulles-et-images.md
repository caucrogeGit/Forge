# Infobulles et agrandissement d'image

**Objectif** : ajouter à la page des infobulles au survol et permettre d'agrandir les captures d'écran.

**Ce que vous allez apprendre :** les **infobulles** (fonctionnalité Material `content.tooltips`) et la **lightbox** d'image (plugin `mkdocs-glightbox`).

!!! info "Au-delà du Markdown pur"
    Ces deux effets ne viennent pas de Markdown lui-même, mais du **thème Material** et d'un **plugin**.
    Ils s'activent dans `mkdocs.yml` (voir le [préambule](../installation.md#installer-markdown-et-ses-extensions)).

## Infobulles au survol

Avec la fonctionnalité `content.tooltips` activée, un attribut `title` (posé par `attr_list`) s'affiche dans une **bulle stylée** au survol.

~~~md
Survolez ce [lien](#){ title="Forge est un framework web Python" }.
Survolez ce **mot**{ title="explication au survol" }.
~~~

Rendu (survolez) :

Survolez ce [lien](#){ title="Forge est un framework web Python" }.
Survolez ce **mot**{ title="explication au survol" }.

Les **abréviations** (palier précédent) produisent aussi une infobulle, sans attribut `title` :

~~~md
Le jeton CSRF protège les écritures.

*[CSRF]: Cross-Site Request Forgery
~~~

Rendu (survolez le sigle) :

Le jeton CSRF protège les écritures.

*[CSRF]: Cross-Site Request Forgery

## Agrandir une image

Avec le plugin `mkdocs-glightbox`, **toute image de contenu** devient cliquable : un clic l'ouvre en grand dans une surimpression (lightbox), avec un fond sombre et un bouton de fermeture.

~~~md
![Logo de Forge](../../../static/forge-logo.png)
~~~

Rendu (cliquez sur l'image) :

![Logo de Forge](../../../static/forge-logo.png)

Aucune syntaxe particulière n'est nécessaire : le comportement est **automatique** pour les images de la documentation.

## Ajoutez à votre page

Dans `prise-en-main.md`, donnez une infobulle à un terme technique, et insérez une capture d'écran (elle s'agrandira au clic) :

~~~md
Le serveur de **développement**{ title="à n'utiliser qu'en local, jamais en production" } écoute sur le port 8000.

![Capture de la page d'accueil](assets/accueil.png)
~~~

## À retenir

- Une **infobulle** vient d'un attribut `title` (via `attr_list`) ou d'une abréviation, rendue par la fonctionnalité Material `content.tooltips`.
- La **lightbox** (plugin `mkdocs-glightbox`) agrandit toute image de contenu au clic, sans syntaxe particulière.
- Ces effets dépendent de la configuration `mkdocs.yml`, pas du Markdown seul.

[Continuer avec Relecture et maths](relecture-et-maths.md)
