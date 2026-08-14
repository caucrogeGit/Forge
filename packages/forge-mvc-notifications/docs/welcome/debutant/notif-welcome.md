# Première notification

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-notifications` avant de commencer : voir sa [référence](../../reference.md).

    ```bash
    pip install --pre forge-mvc-notifications    # installe le paquet
    forge opt-in:enable notifications          # le branche au projet
    ```

    Sans le paquet, l'application refuse de démarrer sur un `ModuleNotFoundError` au chargement des routes.

    `forge opt-in:install notifications` **affiche** la commande d'installation adaptée à votre environnement, pipx compris ; il n'installe rien lui-même (ADR-016).

Objectif : premier contact avec le module **opt-in** `forge-mvc-notifications`.

**Ce que vous allez apprendre :** une notification in-app se crée avec la fonction `notify`.
On lui donne un destinataire et un message, et elle est enregistrée en base.
Le module ne sait rien de la signification métier du message : l'application décide quoi notifier.

Premier palier du **niveau débutant** de la progression Notifications.

!!! note "Module opt-in"
    Si `forge-mvc-notifications` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- créer une notification in-app avec `notify` ;
- récupérer l'identifiant renvoyé par la fonction.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `notify(recipient, message)` | Crée une notification et renvoie son identifiant. | Opt-ins |

## 1. Créer une notification

```python
from forge_mvc_notifications import notify

notification_id = notify("eleve.42", "Votre note est publiée")
print("notification créée :", notification_id)
```

### Comprendre ce code

- `notify("eleve.42", "Votre note est publiée")` insère une ligne dans la table `notifications`.
- Le premier argument est le destinataire, le second est le message ; les deux sont obligatoires.
- La fonction renvoie l'identifiant entier de la notification, utile pour la marquer lue plus tard.
- Si le destinataire ou le message est vide, une `NotificationError` est levée.

## À retenir

- Une notification se crée avec `notify(destinataire, message)`.
- `notify` renvoie l'identifiant entier de la ligne insérée.
- Le destinataire et le message sont obligatoires.

## Après ce starter

Vous avez créé une notification.
Voyons maintenant comment la relire et compter les non lues.

[Lire les notifications](notif-read.md)
