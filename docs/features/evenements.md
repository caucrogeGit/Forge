# Événements

**Forge ne fournit aucun système d'événements.**
Pas de bus, pas de dispatcher, pas de `@events.on`, pas de signaux.

Ce n'est pas un manque à combler : c'est une décision, portée par l'[ADR-052](../adr/052-optin-strategy.md).
Cette page explique ce qui existe à la place, ce qu'il faut écrire quand on croit avoir besoin d'événements, et à quelles conditions un registre explicite devient légitime.

## Ce que Forge appelle « événement »

Le mot apparaît dans plusieurs briques, et il y désigne toujours une **donnée enregistrée**, jamais un déclenchement.

| Brique | Objet | Ce qui se passe |
|---|---|---|
| Cœur, `core.auth` | `AuthAuditEvent`, `log_auth_event()` | Une vingtaine de types normalisés, émis via le logging Python. La persistance reste applicative ([ADR-008](../adr/008-auth-audit-architecture.md)). |
| `forge-mvc-stats` | `StatsEvent`, `track_event()` | Insère une ligne dans `stats_events`, agrégats calculés à la demande. |
| `forge-mvc-audit` | journal d'audit applicatif | Écrit une ligne dans la table d'audit. |
| `forge-mvc-iot` | table `iot_events` | Stocke les mesures reçues par MQTT. |

Dans les quatre cas, **c'est vous qui appelez la fonction**, à l'endroit voulu.
Aucun abonné n'est notifié, aucune réaction n'est déclenchée.
Ces briques répondent à « garder une trace de ce qui s'est passé », pas à « faire réagir le système ».

## Le seul point d'extension du cycle de requête

Si vous cherchez un endroit pour brancher un comportement transverse sur toutes les requêtes, ce sont les **middlewares**, pas des événements.

```python
# app.py (extrait)
from core.app.application import Application
from core.security.middleware import AuthMiddleware

_app = Application(_routes.router, middlewares=[AuthMiddleware("/login")])
```

Chaque middleware expose `check(request) -> Response | None`.
Ils sont évalués **dans l'ordre de la liste**, et le premier qui renvoie une `Response` court-circuite la requête.
L'ordre est visible, la liste est complète, le fichier est unique : c'est un pipeline, pas un système d'abonnement.

Voir [Auth/User](auth.md) pour les middlewares fournis.

## Ce qu'il faut écrire à la place

Le réflexe idiomatique de Forge est l'**appel explicite**.
Quand plusieurs traitements suivent un fait métier, on écrit une fonction qui les nomme :

```python
# mvc/services/registration.py
def after_registration(user_id: int, email: str) -> None:
    """Tout ce qui suit une inscription, dans l'ordre, en un seul endroit."""
    send_welcome_mail(email)
    record_registration(user_id)
    notify_admins(user_id)
```

Cette fonction est presque toujours la bonne réponse.
Elle est explicite, ordonnée, typée, testable, et elle se lit d'un coup.
Un contrôleur qui l'appelle reste lisible de bout en bout.

Ne cherchez pas plus loin tant que ces trois conditions ne sont pas **toutes** réunies :

1. plusieurs réactions **indépendantes** suivent un même fait métier ;
2. ces réactions **changent souvent** ;
3. elles appartiennent à des **domaines différents** (courriel, statistiques, notification).

Trois réactions figées depuis deux ans ne justifient rien.
Trois réactions qui bougent tous les mois, et dont la liste s'allonge, commencent à peser.

## Quand un registre devient légitime

Si les trois conditions sont réunies, l'ADR-052 admet une forme, et une seule :

> Si un besoin réel apparaît, seule une forme **explicite et minimale** (registre câblé dans un fichier visible, `emit` manuel) serait recevable ; le couplage par décorateur est refusé.

Ce registre est du **code applicatif**, à écrire dans `mvc/events/`.
Forge ne le fournit pas et ne le génère pas.

Le parcours [welcome-events](../starters/welcome-events/installation.md) le construit pas à pas, en six paliers, et le soumet ensuite à la critique : ce que le patron fait gagner, ce qu'il fait perdre, et les quatre décisions qu'il impose de prendre (écouteur qui lève, ordre d'exécution, désabonnement, cycles).

L'invariant à retenir : **un fichier de câblage unique, lu de haut en bas, doit répondre entièrement à la question « que se passe-t-il quand tel événement est émis ? »**.
Le jour où la réponse exige de chercher ailleurs, vous avez perdu la propriété qui justifiait Forge.

## La forme refusée

```python
# Contre-exemple : ce que Forge refuse. Ne l'écrivez pas.
@events.on("user.registered")
def send_welcome_mail(data):
    ...
```

Le décorateur déclare l'abonnement **là où la fonction est définie**, donc éparpillé dans tout le projet.
Deux conséquences, toutes deux graves pour un code que l'on veut auditer :

- savoir ce qui se passe à l'inscription impose de fouiller l'ensemble du code, au lieu d'ouvrir un fichier ;
- un écouteur ne se déclenche pas si son module n'a jamais été importé, **sans la moindre erreur** pour le signaler.

C'est le motif de refus de l'ADR-052 : violation du principe 3 (refuser la magie cachée) et du principe 11 (une seule façon officielle).

## Événements et jobs : ne pas confondre

C'est le contresens le plus fréquent.

**Les événements découplent le code. Les jobs découplent le temps.**

Le runtime de Forge est synchrone (WSGI).
Un `emit()` s'exécute **à l'intérieur** de la requête HTTP : si l'envoi du courriel prend deux secondes, l'utilisateur attend deux secondes de plus.
Un registre d'événements ne rend rien asynchrone, jamais.

Pour sortir du cycle de requête, c'est [forge-mvc-jobs](../jobs/reference.md), avec une mise en file explicite et un worker :

```python
from forge_mvc_jobs import enqueue

enqueue("send_welcome_mail", {"email": email})
```

Les deux mécanismes se combinent bien : l'écouteur ne fait que déposer une tâche, ce qui est rapide, et le travail lourd part au worker.

## Voir aussi

- [welcome-events](../starters/welcome-events/installation.md) : parcours qui construit un registre explicite et le critique.
- [ADR-052](../adr/052-optin-strategy.md) : critères d'admission des opt-ins et classement de `events`.
- [forge-mvc-jobs](../jobs/reference.md) : file de tâches de fond, pour le découplage temporel.
- [Auth/User](auth.md) : middlewares fournis et audit d'authentification.
