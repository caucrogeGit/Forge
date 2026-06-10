# Replier le détail

**Objectif** : ajouter une section de dépannage repliable, pour ne pas alourdir la page.

**Ce que vous allez apprendre :** les blocs dépliables (extension `pymdownx.details`), repliés ou dépliés par défaut.

Votre page met en avant les prérequis.

Nous ajoutons une rubrique « Dépannage », repliée par défaut : le lecteur ne l'ouvre qu'en cas de besoin.

## Un bloc replié

Remplacez `!!!` par `???` pour obtenir un encadré **replié**, que le lecteur ouvre d'un clic.

~~~md
??? note "Voir les détails"
    Le contenu reste caché tant qu'on ne clique pas.
~~~

Rendu :

??? note "Voir les détails"
    Le contenu reste caché tant qu'on ne clique pas.

## Déplié par défaut

Ajoutez un `+` (`???+`) pour afficher le bloc déjà ouvert, tout en le laissant repliable.

~~~md
???+ tip "Bon à savoir"
    Visible au chargement, refermable d'un clic.
~~~

Rendu :

???+ tip "Bon à savoir"
    Visible au chargement, refermable d'un clic.

## Ajoutez à votre page

Ajoutez une rubrique « Dépannage » repliable à `prise-en-main.md` :

~~~md
## Dépannage

??? question "« commande forge introuvable »"
    Vérifiez que l'environnement virtuel est activé,
    puis que Forge est bien installé avec `pip show forge-mvc`.

??? question "Erreur de connexion à la base"
    Contrôlez que MariaDB est démarré et que les accès du fichier d'environnement sont corrects.
~~~

## À retenir

- `???` ouvre un encadré **replié** ; `???+` un encadré **déplié** mais refermable.
- Même syntaxe que les admonitions (types, titre entre guillemets).
- Idéal pour le détail secondaire : dépannage, notes, exemples longs.

[Continuer avec Montrer du code](code.md)
