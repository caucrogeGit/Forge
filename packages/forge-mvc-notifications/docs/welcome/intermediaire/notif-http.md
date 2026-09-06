# Intermédiaire 3 : Les routes HTTP

Objectif : une pastille de notifications qui se met à jour, sans écrire quatre contrôleurs.

## Quatre routes, une ligne de câblage

```python
from forge_mvc_notifications import register_notification_routes

register_notification_routes(router, recipient_of=lambda request: utilisateur_courant(request))
```

| Route | Ce qu'elle rend |
|---|---|
| `GET /notifications` | les notifications du destinataire, paginées |
| `GET /notifications/unread-count` | le seul nombre, pour la pastille |
| `POST /notifications/{id}/read` | marque une notification lue |
| `POST /notifications/read-all` | marque tout comme lu |

!!! danger "`recipient_of` est obligatoire, et c'est tout le contrôle d'accès"
    Sans elle, l'appel lève au câblage plutôt que de démarrer.

    Accepter un `?recipient=professeur.7` dans l'URL donnerait à quiconque les notifications de n'importe qui : c'est la requête, et elle seule, qui dit à qui appartient la session.

!!! warning "Le destinataire ne sort jamais dans la réponse"
    Les notifications rendues ne portent pas leur champ `recipient`.

    Il n'apprend rien au titulaire, qui sait qui il est, et le rendre confirmerait à un attaquant que sa tentative a visé juste.

!!! info "La pastille se rafraîchit par sondage, pas par magie"
    `unread-count` est fait pour être appelé toutes les trente secondes par un fragment HTMX ou un `fetch`.

    Forge ne pousse rien vers le navigateur : cela demanderait un canal permanent, hors du périmètre d'un runtime WSGI.

## Un lien cible pour chaque notification

```python
notify("prof.7", "Trois copies à corriger", type="devoir",
       target_url="/copies?statut=a_corriger")
```

Le lien accompagne la notification, et l'écran en fait un lien cliquable.

!!! danger "Les liens dangereux sont refusés à l'écriture"
    `javascript:...` et les liens protocole-relatifs comme `//site-tiers.fr` lèvent.

    Une notification est affichée dans une page authentifiée : y placer un lien de ce genre est le vecteur exact d'une redirection ouverte, ou pire.

## À retenir

- Quatre routes, câblées en une ligne, avec un résolveur de destinataire obligatoire.
- La réponse ne dit jamais à qui appartient la notification.
- Les liens cibles sont validés à l'écriture, pas à l'affichage.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
