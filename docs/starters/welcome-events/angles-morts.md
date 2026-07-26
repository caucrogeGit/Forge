# Les angles morts

Objectif : casser volontairement ce que vous venez de construire, pour découvrir les décisions que le patron vous impose de prendre.

**Ce que vous allez apprendre :** les quatre questions qu'un système d'événements pose et auxquelles il faut répondre une fois pour toutes.

## Là où nous en sommes

Le mécanisme marche.
C'est précisément le moment de chercher ce qui, dedans, ne va pas.

## 1. Un écouteur qui lève emporte les suivants

Reprenez le shell et abonnez un écouteur défaillant en premier :

```python
>>> from mvc.events import emit, subscribe
>>> def boom(data):
...     raise RuntimeError("serveur SMTP injoignable")
>>> subscribe("demo", boom)
>>> subscribe("demo", lambda data: print("moi je voulais travailler"))
>>> emit("demo")
RuntimeError: serveur SMTP injoignable
```

Le second écouteur n'a jamais tourné.
Traduit en métier : le serveur de courriel est tombé, donc la statistique n'a pas été enregistrée et l'administrateur n'a pas été notifié.
Pire, comme `emit` est appelé dans le contrôleur, l'inscription entière remonte une erreur 500, alors que l'utilisateur **a bien été créé**.

Deux politiques possibles, et il faut choisir :

```python
# Politique A : isoler. Un écouteur qui tombe n'empêche pas les autres.
import logging

logger = logging.getLogger(__name__)


def emit(event_name: str, payload: dict[str, Any] | None = None) -> int:
    data = payload or {}
    listeners = _LISTENERS.get(event_name, [])
    for listener in listeners:
        try:
            listener(data)
        except Exception:
            logger.exception("écouteur %s en échec sur %s", listener, event_name)
    return len(listeners)
```

La politique B est celle que vous avez déjà : laisser remonter, et donc échouer vite.

Aucune des deux n'est « la bonne ».
Isoler protège le parcours utilisateur mais transforme les pannes en lignes de log que personne ne lit.
Laisser remonter rend les pannes visibles mais couple la réussite de l'inscription à la disponibilité du serveur SMTP.
Ce que vous ne pouvez pas faire, c'est ne pas choisir.

## 2. L'ordre est celui de wiring.py, et rien ne le dit

Vos trois écouteurs tournent dans l'ordre où `wire_events()` les a abonnés.
Ce n'est écrit nulle part dans le contrat, seulement dans l'implémentation.

Le jour où quelqu'un réordonne les lignes de `wiring.py` pour « ranger par ordre alphabétique », il change le comportement de l'application sans le savoir.
Si l'ordre compte pour vous, écrivez-le en commentaire dans `wiring.py`.
S'il ne doit pas compter, alors aucun écouteur ne doit dépendre d'un autre, et cela se vérifie en relecture.

## 3. Une faute de frappe est silencieuse

Vous l'avez vu au palier du registre : `emit("user.registred")` retourne `0` sans broncher.

En développement, tirez parti de la valeur de retour :

```python
# En mode développement uniquement : signale un événement sans écouteur.
count = emit("user.registered", payload)
if count == 0:
    logger.warning("événement 'user.registered' émis sans aucun écouteur")
```

Vous pouvez aussi déclarer les noms d'événements comme constantes dans un module, pour que l'éditeur rattrape la faute.
C'est la solution la plus économique, et elle ne coûte rien.

## 4. Tout reste synchrone, dans la requête HTTP

C'est l'angle mort le plus coûteux, et il est structurel.

Le runtime de Forge est synchrone (WSGI).
Votre `emit` s'exécute **à l'intérieur** de la requête d'inscription : si l'envoi du courriel prend deux secondes, l'utilisateur attend deux secondes de plus devant son formulaire.
Le découplage que vous avez obtenu est un découplage **du code**, pas un découplage **du temps**.

Beaucoup de gens confondent les deux et attendent d'un système d'événements qu'il rende les traitements asynchrones.
Il ne le fait pas.

Pour sortir du cycle HTTP, c'est l'opt-in `forge-mvc-jobs` qui s'en charge, et l'écouteur devient une simple mise en file :

```python
# mvc/events/listeners/user.py (variante différée)
from typing import Any

from forge_mvc_jobs import enqueue


def send_welcome_mail(data: dict[str, Any]) -> None:
    enqueue("send_welcome_mail", {"email": data["email"]})
```

L'événement reste synchrone, mais il ne fait plus que déposer une tâche, ce qui est rapide.
Le travail lourd est exécuté par le worker, hors requête.
Retenez la répartition des rôles : **les événements découplent le code, les jobs découplent le temps.**

## 5. Ce que nous n'avons volontairement pas écrit

- **Se désabonner.** Aucun `unsubscribe()`. Si un test abonne un écouteur, il pollue les suivants ; prévoyez une remise à zéro du registre dans vos fixtures.
- **Les cycles.** Rien n'empêche un écouteur d'émettre un événement qui le rappelle. La récursion infinie est à votre charge.
- **La priorité.** Pas de poids, pas de tri : voir le point 2.

Chacune de ces absences est une fonctionnalité que l'on pourrait ajouter, et chacune est un engagement que l'on devrait ensuite tenir.

## À retenir

- Un écouteur qui lève est une décision de conception, pas un détail d'implémentation.
- L'ordre d'exécution devient implicite ; documentez-le ou interdisez la dépendance.
- Les événements découplent le code, pas le temps : pour le temps, c'est `forge-mvc-jobs`.
- Chaque fonctionnalité non écrite est un engagement que vous ne prenez pas.

[Continuer avec le Bilan](bilan.md)
