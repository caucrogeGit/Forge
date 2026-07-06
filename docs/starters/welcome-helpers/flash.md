# La façade Flash

Objectif : regrouper les **messages flash** (un message affiché une seule fois, puis consommé) sous une façade `Flash`.

**Ce que vous allez apprendre :** poser un message flash dans la session et le lire ; comprendre pourquoi le flash est une préoccupation **distincte** de la session brute, même s'il vit dans la session.

## Là où nous en sommes

Vous avez `_facade.py`, `session.py` et `cookies.py`.
Nous ajoutons la dernière façade du parcours.

## L'ajout

Créez `mvc/helpers/flash.py` :

```python
# mvc/helpers/flash.py
"""Façade de confort pour les messages flash (helper applicatif)."""

from core.security.session import get_flash as _get_flash
from core.security.session import set_flash as _set_flash
from mvc.helpers._facade import Facade


class Flash(Facade):

    @staticmethod
    def set(session_id: str, message: str, level: str = "success") -> None:
        _set_flash(session_id, message, level)

    @staticmethod
    def get(session_id: str) -> dict | None:
        return _get_flash(session_id)
```

## Comprendre ce code

- Un **message flash** est un message à usage unique : on le pose lors d'une action (« Enregistré », « Erreur »), il est affiché au chargement suivant, puis **supprimé** automatiquement.
  C'est le motif classique après un POST/redirect.
- **`set`** stocke `{message, level}` dans la session ; `level` (`"success"`, `"error"`, `"warning"`…) sert à choisir le style d'affichage.
- **`get`** lit **et supprime** le message d'un coup (lecture one-shot) : un second `get` renvoie `None`.
  C'est ce qui garantit qu'il n'apparaît qu'une fois.
- **Pourquoi une façade à part** : le flash vit *dans* la session, mais c'est une préoccupation différente (un message UI éphémère, pas l'état de session).
  Le séparer de `Session` garde chaque façade centrée sur un seul rôle ; c'est aussi pour ça qu'on ne l'avait pas mis dans `Session`.
- Le flash a besoin d'une **session existante** : on lui passe le `session_id` (obtenu via `Session.current_id` / `Session.new`).

## Tester

Dans un shell Python du projet :

```python
>>> from mvc.helpers.session import Session
>>> from mvc.helpers.flash import Flash
>>> sid = Session.new()
>>> Flash.set(sid, "Enregistré", "success")
>>> Flash.get(sid)
{'message': 'Enregistré', 'level': 'success'}
>>> Flash.get(sid)          # déjà consommé : plus rien
>>>
```

Le second appel ne renvoie rien (`None`) : le message est à usage unique.

## À retenir

- `Flash` gère des messages **à usage unique** : `set` pose, `get` lit **et supprime**.
- Le flash vit dans la session, mais reste une **façade distincte** (un rôle = une façade).
- Il exige un `session_id`, fourni par `Session`.

Au palier suivant, nous câblons tout : l'import unique et l'usage en contrôleur.

[Continuer avec Imports et usage](imports-usage.md)
