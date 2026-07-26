# Le cas réel : l'inscription

Objectif : brancher l'inscription utilisateur sur le registre, et mesurer ce que le contrôleur y gagne.

**Ce que vous allez apprendre :** écrire des écouteurs, les câbler, et repérer un piège de nommage bien réel si vous relayez vers `forge-mvc-stats`.

## Là où nous en sommes

Le registre existe, le câblage existe et il est vide.
Nous reprenons le contrôleur d'inscription du préambule, celui qui alignait trois appels.

## L'ajout

Créez `mvc/events/listeners/__init__.py` (vide), puis `mvc/events/listeners/user.py` :

```python
# mvc/events/listeners/user.py
"""Réactions à l'inscription d'un utilisateur."""

from typing import Any

from mvc.services.mail import send_welcome
from mvc.services.notifications import notify_admins
from mvc.services.stats import record_registration


def send_welcome_mail(data: dict[str, Any]) -> None:
    send_welcome(data["email"])


def track_registration(data: dict[str, Any]) -> None:
    record_registration(data["user_id"])


def warn_admins(data: dict[str, Any]) -> None:
    notify_admins(data["user_id"])
```

Complétez ensuite `mvc/events/wiring.py` :

```python
# mvc/events/wiring.py (extrait)
from mvc.events._registry import subscribe
from mvc.events.listeners.user import (
    send_welcome_mail,
    track_registration,
    warn_admins,
)


def wire_events() -> None:
    subscribe("user.registered", send_welcome_mail)
    subscribe("user.registered", track_registration)
    subscribe("user.registered", warn_admins)
```

Le contrôleur peut enfin maigrir :

```python
# mvc/controllers/register_controller.py (extrait, après)
from mvc.events import emit


def store(self, request):
    user_id = create_user(request.form["email"])
    emit("user.registered", {"user_id": user_id, "email": request.form["email"]})
    return self.redirect("/login")
```

## Comprendre ce code

- **Le contrôleur ne connaît plus les réactions.**
  Il annonce un fait métier, « un utilisateur s'est inscrit », et s'arrête là.
  C'est le gain, et il est réel : ajouter une quatrième réaction ne touchera plus jamais ce fichier.
- **Les écouteurs ne connaissent pas le contrôleur.**
  Ils reçoivent un dictionnaire et travaillent.
  Chacun est une fonction ordinaire, testable seule, sans requête HTTP ni base de données.
- **La charge utile est un contrat implicite.**
  `data["user_id"]` suppose que l'émetteur l'a mis dedans.
  Rien ne le vérifie.
  C'est la contrepartie du découplage : vous avez remplacé un appel typé par un dictionnaire libre.
  Sur un projet qui dure, documentez la charge utile de chaque événement en commentaire dans `wiring.py`.
- **Les écouteurs délèguent à `mvc/services/`.**
  Ils ne contiennent pas de logique : ils traduisent un événement en appel de service.
  Un écouteur qui grossit est un service déguisé, à extraire.

## Le piège du nommage

Nos événements s'appellent `user.registered`, avec un point.
C'est la convention habituelle et elle est bonne : elle groupe par domaine.

Mais si votre `record_registration` relaie vers l'opt-in `forge-mvc-stats`, attention : cet opt-in impose ses propres noms en `snake_case` et **refuse** le point.

```python
>>> from forge_mvc_stats import validate_event_name
>>> validate_event_name("user_registered")
'user_registered'
>>> validate_event_name("user.registered")
StatsEventError: Le nom d'événement 'user.registered' contient des caractères non autorisés.
```

Le nom de votre événement applicatif et le nom de l'événement statistique sont **deux choses différentes**.
C'est l'écouteur qui fait la traduction, explicitement :

```python
def track_registration(data: dict[str, Any]) -> None:
    record_registration(data["user_id"])   # relaie sous le nom « user_registered »
```

Ne soyez pas tenté de renommer vos événements applicatifs pour plaire à un opt-in.
La frontière entre votre vocabulaire métier et celui d'une brique tierce se tient dans l'adaptateur, pas dans le vocabulaire.

## Tester

```python
>>> from mvc.events import emit, listeners_for
>>> from mvc.events.wiring import wire_events
>>> wire_events()
>>> len(listeners_for("user.registered"))
3
>>> emit("user.registered", {"user_id": 1, "email": "ada@example.org"})
3
```

## À retenir

- Le contrôleur annonce un fait, les écouteurs décident quoi en faire.
- La charge utile est un dictionnaire libre : ce contrat n'est vérifié par rien, documentez-le.
- Le vocabulaire de vos événements vous appartient ; traduisez dans l'écouteur quand une brique tierce impose le sien.

Au palier suivant, nous cassons tout cela volontairement.

[Continuer avec Les angles morts](angles-morts.md)
