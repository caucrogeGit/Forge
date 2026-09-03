# Les routes HTTP

Ce document décrit les routes JSON qui exposent les notifications à une page.

Le fichier de code correspondant est `forge_mvc_notifications/http.py`.

## 1. Ce que le paquet ne faisait pas

Le paquet savait écrire une notification et la relire depuis Python.
Il n'exposait aucune route, là où `forge-mvc-video` livre `register_video_routes` et `forge-mvc-iot` livre `register_iot_routes`.

Chaque application devait donc écrire son contrôleur, sa sérialisation JSON et son compteur de non-lus avant d'afficher quoi que ce soit (`NOTIF-HTTP-ROUTES-001`).

## 2. Poser les routes (`register_notification_routes`)

```python
def register_notification_routes(router, *, recipient_of, db=None)
```

L'appel est explicite, comme tout câblage de routes d'opt-in (ADR-030).

```python
from forge_mvc_notifications import register_notification_routes

from mvc.services.auth import utilisateur_courant


def _destinataire(request):
    utilisateur = utilisateur_courant(request)
    return f"professeur.{utilisateur.id}" if utilisateur else None


register_notification_routes(router, recipient_of=_destinataire)
```

`recipient_of` reçoit la requête et renvoie le destinataire de ses notifications, ou `None` quand personne n'est authentifié.

`db` est l'exécuteur injectable, omis il utilise le backend actif.

## 3. Pourquoi `recipient_of` est obligatoire

Un destinataire est une chaîne libre, `professeur.42`, dont la convention appartient à l'application.
Forge ne sait pas la dériver d'une session.

La seule autre façon de la connaître serait de la lire dans la requête, et `?recipient=professeur.7` donnerait alors à quiconque les notifications de n'importe qui.

Son absence lève `NotificationError` à l'enregistrement, pas à la première requête.
Une application qui monte ces routes sans résolveur a fait une erreur de câblage, et la découvrir au démarrage vaut mieux qu'en production.

Un `recipient_of` qui lève est journalisé, et la requête est traitée comme non authentifiée.
Se rabattre sur « personne » est acceptable, se rabattre sur « tout le monde » ne l'est pas.

## 4. Les quatre routes

| Méthode | Chemin | Nom | Rend |
|---|---|---|---|
| `GET` | `/api/notifications/unread-count` | `notifications-unread-count` | `{"data": {"count": 3}}` |
| `GET` | `/api/notifications` | `notifications-list` | `{"data": {"notifications": [...], "next_before_id": 41}}` |
| `POST` | `/api/notifications/{id}/read` | `notifications-mark-read` | `{"data": {"marked": true}}` |
| `POST` | `/api/notifications/read-all` | `notifications-mark-all-read` | `{"data": {"marked": 3}}` |

Les réponses suivent le contrat unique des API JSON (ADR-088).

Aucune route n'est publique.
Les deux mutations sont en `POST`, donc protégées par CSRF, et un appel HTMX doit porter le jeton.

## 5. Paginer la liste

| Paramètre | Défaut | Rôle |
|---|---|---|
| `limit` | `20` (`DEFAULT_PAGE_SIZE`) | taille de page, bornée par `MAX_LIMIT` |
| `before_id` | aucun | curseur, ne rend que les notifications antérieures |
| `unread` | `0` | `1` ne rend que les non lues |

`next_before_id` porte le curseur de la page suivante.
Il vaut `null` quand la page n'est pas pleine, car il n'y a alors rien après et rendre un curseur ferait demander une page vide.

Une valeur illisible rend `400`, jamais la page par défaut.
La remplacer en silence rendrait une page que l'appelant n'a pas demandée.

## 6. Le marquage est borné au destinataire

`POST /api/notifications/12/read` ne marque la notification 12 que si elle appartient au demandeur.

Sans cette borne, l'identifiant seul suffirait à faire disparaître l'alerte de quelqu'un d'autre, et les identifiants d'une table se devinent.

La réponse ne distingue pas « déjà lue » de « celle d'un autre ».
Les distinguer demanderait une lecture préalable, qui apprendrait à l'appelant qu'un identifiant existe chez quelqu'un d'autre.

## 7. Sérialiser (`serialize_notification`)

```python
def serialize_notification(notification) -> dict
```

Rend `id`, `type`, `message`, `data`, `read`, `created_at` et `target_url`.

`recipient` en est absent.
Le client ne reçoit que les siennes, le lui répéter à chaque ligne n'apprend rien et expose la convention de nommage interne de l'application.

## 8. Rafraîchir l'écran

Ces routes rendent du JSON.
Elles ne poussent rien, n'ouvrent aucune connexion longue et ne fournissent aucun script.

```html
<span id="badge-notifications"
      hx-get="/api/notifications/unread-count"
      hx-trigger="load, every 10s"
      hx-swap="innerHTML"></span>
```

Une interrogation toutes les dix secondes coûte, pour quarante écrans ouverts, quatre requêtes par seconde servies en quelques millisecondes.
Les tenir ouvertes en SSE coûterait quarante travailleurs immobilisés, soit davantage que ce qu'un serveur WSGI de taille courante en compte.

Le choix se renverse à un autre ordre de grandeur, et une application qui l'atteint peut poser sa propre route sans rien changer ici.

## 9. Brancher soi-même (`NotificationHttpController`)

L'application qui veut ses propres chemins ou sa propre enveloppe instancie le contrôleur et pose ses routes.

```python
from forge_mvc_notifications import NotificationHttpController

controleur = NotificationHttpController(_destinataire)
router.add("GET", "/mes-avis/compteur", controleur.unread_count, api=True)
```

Les quatre méthodes sont `unread_count`, `list`, `mark_read` et `mark_all_read`.

## 10. Voir aussi

- [Les notifications](store.md) : `notify`, `get_notifications`, `mark_read`.
- [Les erreurs](errors.md) : `NotificationError`.
