# Le câblage visible

Objectif : poser le fichier qui liste **tous** les abonnements à la main, et comprendre pourquoi c'est lui, et non le registre, qui fait la valeur de ce parcours.

**Ce que vous allez apprendre :** la différence entre un registre auditable et un bus magique, et pourquoi elle tient à un seul fichier.

## Là où nous en sommes

Le palier précédent a posé `mvc/events/_registry.py`.
Le mécanisme existe, mais personne ne s'abonne encore.
La question est : **où** les abonnements sont-ils déclarés ?

C'est la seule question qui compte vraiment.

## L'ajout

D'abord, l'API publique du paquet, `mvc/events/__init__.py` :

```python
# mvc/events/__init__.py
"""Événements applicatifs : émission et abonnement explicites."""

from mvc.events._registry import emit, listeners_for, subscribe

__all__ = ["emit", "subscribe", "listeners_for"]
```

Ensuite le fichier central, `mvc/events/wiring.py` :

```python
# mvc/events/wiring.py
"""Câblage des événements : la liste complète des abonnements.

Ce fichier est la SEULE source de vérité des réactions de l'application.
Le lire de haut en bas répond entièrement à la question
« que se passe-t-il quand tel événement est émis ? ».
"""

from mvc.events._registry import subscribe


def wire_events() -> None:
    """Déclare tous les abonnements. Appelée une fois, au démarrage."""
    # Aucun abonnement pour l'instant : le palier suivant en ajoute.
    return
```

Enfin, l'appel au démarrage, dans `app.py`, à côté de la construction de l'`Application` :

```python
# app.py (extrait, à ajouter à la main)
from mvc.events.wiring import wire_events

wire_events()
```

## Comprendre ce code

- **`wire_events()` est appelée explicitement.**
  Rien ne la découvre, rien ne la déclenche : si vous ne l'appelez pas, aucun événement n'a d'effet.
  C'est voulu.
  Un système dont on peut couper tout le comportement en commentant une ligne est un système que l'on comprend.
- **Le câblage vit dans `app.py`, pas dans `mvc/`.**
  Ce n'est pas arbitraire : c'est déjà la convention Forge pour les middlewares, que le squelette câble au même endroit avec le même argument.
  `mvc/` porte le code métier, `app.py` porte l'assemblage.
- **Un seul fichier répond à « qui écoute quoi ».**
  Ouvrez `wiring.py`, vous savez tout.
  C'est exactement la propriété que la découverte automatique détruit.

## La variante refusée, et pourquoi

Presque tous les frameworks proposent plutôt ceci :

```python
# Contre-exemple : ce que Forge refuse. Ne l'écrivez pas.
@events.on("user.registered")
def send_welcome_mail(data):
    ...
```

C'est plus court, et c'est le problème.
Avec le décorateur, l'abonnement est déclaré **là où la fonction est définie**, donc éparpillé dans tout le projet.
Pour savoir ce qui se passe à l'inscription, il faut désormais chercher dans l'ensemble du code, en espérant que le module contenant le décorateur ait bien été importé.
Cette dernière condition est la source de bugs classique du patron : un écouteur qui ne se déclenche pas parce que son module n'a jamais été chargé, sans la moindre erreur pour vous le dire.

Le `wiring.py` échange trois lignes de verbosité contre une garantie : **si ce n'est pas écrit ici, ça n'arrive pas**.

C'est la raison pour laquelle l'[ADR-052](../../adr/052-optin-strategy.md) place le bus auto-découvert hors trajectoire tout en jugeant recevable « une forme explicite et minimale, registre câblé dans un fichier visible, `emit` manuel ».
Vous venez d'écrire cette forme-là.

## Tester

```python
>>> from mvc.events import listeners_for
>>> from mvc.events.wiring import wire_events
>>> wire_events()
>>> listeners_for("user.registered")
[]
```

La liste est vide et c'est normal : nous n'avons encore abonné personne.

## À retenir

- Le registre est banal ; le fichier de câblage est ce qui rend le système auditable.
- Le câblage est appelé explicitement au démarrage, dans `app.py`, comme les middlewares.
- Le décorateur `@events.on` est plus court mais rend le comportement introuvable : Forge le refuse par écrit.

Au palier suivant, nous branchons enfin un cas réel.

[Continuer avec Le cas réel](cas-reel.md)
