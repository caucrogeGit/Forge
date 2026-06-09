# La base Facade

Objectif : créer la base commune `Facade`, un **namespace de méthodes statiques
qui ne s'instancie pas**, dont toutes nos façades hériteront.

**Ce que vous allez apprendre :** le patron « classe-namespace », pourquoi une
façade sans état ne doit pas s'instancier, et comment l'interdire proprement avec
`__new__`.

## Là où nous en sommes

Votre projet a un dossier `mvc/helpers/` avec un simple `__init__.py` vide. Nous
y posons le premier fichier, la base partagée par toutes les façades.

## L'ajout

Créez `mvc/helpers/_facade.py` :

```python
# mvc/helpers/_facade.py
"""Base des façades helper : namespace de méthodes statiques, non instanciable."""


class Facade:
    def __new__(cls, *args, **kwargs):
        raise TypeError(
            f"{cls.__name__} ne s'instancie pas : namespace de méthodes statiques."
        )
```

## Comprendre ce code

- Une façade ici n'a **pas d'état** : elle ne fait que regrouper des fonctions du
  noyau sous un nom. Il n'y a donc **rien à instancier** ; la session vit dans le
  store, le cookie dans la requête/réponse, pas dans un objet façade.
- `__new__` est appelé **avant** toute création d'instance. En y levant une
  `TypeError`, on rend la classe **non instanciable** : `Session()` échoue
  immédiatement, avec un message clair. C'est l'inverse de la magie : au lieu de
  laisser croire qu'on peut créer un objet, on l'interdit explicitement.
- Le `f"{cls.__name__}"` adapte le message à la sous-classe : `Session`,
  `Cookies` ou `Flash` afficheront chacune leur nom.
- On hérite de cette base pour **ne pas répéter** le garde dans chaque façade.

## Tester

Dans un shell Python du projet :

```python
>>> from mvc.helpers._facade import Facade
>>> Facade()
TypeError: Facade ne s'instancie pas : namespace de méthodes statiques.
```

L'erreur attendue confirme que la base est bien non instanciable.

## À retenir

- Une façade sans état est un **namespace**, pas un objet : on l'utilise par ses
  méthodes statiques (`Session.new()`), jamais en l'instanciant.
- `__new__` qui lève `TypeError` est la façon explicite d'interdire
  l'instanciation, sans surprise.
- Une base commune évite de répéter ce garde dans chaque façade.

Au palier suivant, nous écrivons notre première vraie façade : `Session`.

[Continuer avec La façade Session](session.md)
