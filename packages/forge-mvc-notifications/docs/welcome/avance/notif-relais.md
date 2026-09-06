# Avancé 3 : Relayer vers un autre canal

Objectif : qu'une notification importante parte aussi par courriel.

## Le paquet annonce, il ne livre pas

Une notification vit dans une table et s'affiche dans l'application.
Quelqu'un qui ne s'y connecte pas de la journée ne la verra pas.

`forge-mvc-notifications` n'importe aucun autre opt-in : il **annonce** chaque création, et l'application décide de ce qu'elle en fait.

```python
from forge_mvc_notifications import on_notification_created


@on_notification_created
def relayer_par_courriel(evenement):
    if evenement.type != "urgent":
        return
    envoyer_le_courriel(a=adresse_de(evenement.recipient), texte=evenement.message)
```

| Champ de `NotificationEvent` | Contenu |
|---|---|
| `notification_id` | la ligne créée |
| `recipient` | à qui elle est destinée |
| `message`, `type`, `data` | ce qu'elle porte |

!!! info "Filtrez sur le type, pas sur tout"
    Relayer chaque notification par courriel transforme un fil d'activité en boîte de réception saturée, et l'utilisateur coupe tout.

    Le type existe pour cela : n'en relayez qu'une part.

!!! warning "Un relais lent ralentit la création"
    Les relais sont appelés dans le fil de `notify`.

    Un envoi SMTP direct ferait donc attendre la requête : enfilez la tâche plutôt que d'envoyer, `forge-mvc-jobs` étant fait pour cela.

!!! danger "Un relais qui échoue ne doit pas perdre la notification"
    La notification est déjà écrite quand les relais sont appelés.

    Un relais qui lève n'annule rien, et c'est voulu : perdre la notification en base parce qu'un courriel n'est pas parti serait pire que le courriel manquant.

## À retenir

- Le paquet annonce chaque création ; aucun canal n'est imposé.
- Filtrez sur le type, sans quoi le relais devient du bruit.
- Enfilez l'envoi plutôt que de le faire dans le fil de la requête.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
