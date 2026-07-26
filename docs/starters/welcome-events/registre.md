# Le registre

Objectif : écrire le cœur du mécanisme, un dictionnaire d'abonnés et deux fonctions.

**Ce que vous allez apprendre :** qu'un système d'événements tient en une trentaine de lignes, et que tout le reste n'est que politique de conception.

## Là où nous en sommes

Votre projet a un contrôleur d'inscription qui appelle trois fonctions à la suite.
Nous posons le mécanisme qui permettra de les découpler, sans encore l'utiliser.

## L'ajout

Créez le dossier `mvc/events/`, puis `mvc/events/_registry.py` :

```python
# mvc/events/_registry.py
"""Registre d'événements applicatif : abonnement et émission explicites."""

from collections.abc import Callable
from typing import Any

Listener = Callable[[dict[str, Any]], None]

_LISTENERS: dict[str, list[Listener]] = {}


def subscribe(event_name: str, listener: Listener) -> None:
    """Abonne un écouteur à un nom d'événement."""
    _LISTENERS.setdefault(event_name, []).append(listener)


def emit(event_name: str, payload: dict[str, Any] | None = None) -> int:
    """Appelle tous les écouteurs abonnés, dans l'ordre d'abonnement.

    Retourne le nombre d'écouteurs appelés.
    """
    data = payload or {}
    listeners = _LISTENERS.get(event_name, [])
    for listener in listeners:
        listener(data)
    return len(listeners)


def listeners_for(event_name: str) -> list[Listener]:
    """Retourne les écouteurs abonnés, pour inspection et pour les tests."""
    return list(_LISTENERS.get(event_name, []))
```

## Comprendre ce code

- **`_LISTENERS` est un simple dictionnaire.**
  Une clé est un nom d'événement, la valeur est la liste ordonnée des fonctions à appeler.
  Il n'y a pas d'autre état, pas de classe, pas de métaclasse, pas de décorateur.
- **`emit` est une boucle `for`.**
  C'est important de le voir en face : « émettre un événement » signifie exactement « parcourir une liste et appeler chaque élément ».
  Toute la difficulté des systèmes d'événements est ailleurs, dans les questions que ce palier n'a pas encore posées.
- **`emit` retourne un entier.**
  Ce choix n'est pas décoratif : sans lui, une faute de frappe dans un nom d'événement serait totalement silencieuse.
  Nous y reviendrons au palier des angles morts.
- **`listeners_for` existe pour vos tests.**
  Un registre que l'on ne peut pas inspecter est un registre que l'on ne peut pas tester ; le rendre lisible de l'extérieur est le minimum vital.
- **Le préfixe `_` de `_registry.py`** signale que ce module est interne au paquet `mvc.events` : les autres modules passeront par `mvc.events`, pas par lui.

## Tester

Dans un shell Python du projet :

```python
>>> from mvc.events._registry import emit, subscribe
>>> subscribe("user.registered", lambda data: print("bonjour", data["email"]))
>>> emit("user.registered", {"email": "ada@example.org"})
bonjour ada@example.org
1
>>> emit("user.registred")
0
```

Regardez bien la dernière ligne.
Le nom est mal orthographié, et il ne se passe **rien** : pas d'erreur, pas d'avertissement, juste un `0` que personne ne lit en production.
Vous venez de rencontrer le premier défaut structurel du patron.

## À retenir

- Un registre d'événements, c'est un dictionnaire de listes et une boucle `for`.
- Le mécanisme est trivial ; ce sont les décisions autour de lui qui sont difficiles.
- Un nom d'événement est une chaîne, donc une faute de frappe ne se voit pas.

Au palier suivant, nous posons le fichier qui fait toute la différence entre un registre auditable et un bus magique.

[Continuer avec Le câblage visible](cablage.md)
