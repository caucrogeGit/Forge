# Aide-mémoire Notifications

Synthèse de l'API de `forge-mvc-notifications`, à garder sous la main.

## Création

| Appel | Résultat |
|-------|----------|
| `notify(recipient, message)` | Crée une notification et renvoie son identifiant (`int`). |
| `notify(recipient, message, type="alerte")` | Qualifie la notification par un type libre. |
| `notify(recipient, message, data={...})` | Attache un dict sérialisé en JSON (`NotificationError` si non-JSON). |

## Lecture

| Appel | Résultat |
|-------|----------|
| `get_notifications(recipient)` | `list[Notification]`, plus récentes d'abord (défaut `limit=50`). |
| `get_notifications(recipient, unread_only=True)` | Uniquement les non lues. |
| `get_notifications(recipient, limit=100)` | Borne le nombre (max `MAX_LIMIT` = 1000 ; `limit < 1` lève `NotificationError`). |
| `unread_count(recipient)` | Nombre de notifications non lues (`int`). |

## État lu

| Appel | Résultat |
|-------|----------|
| `mark_read(notification_id)` | Marque lue ; `True` si elle était non lue. |
| `mark_all_read(recipient)` | Marque tout lu ; renvoie le nombre marqué (`int`). |

## Objet et constantes

| Nom | Valeur ou rôle |
|-----|----------------|
| `Notification` | Objet immuable : `id`, `recipient`, `type`, `message`, `data`, `read`, `created_at`. |
| `TABLE_NAME` | `notifications` |
| `MAX_LIMIT` | `1000` |
| `NotificationError` | Levée sur argument manquant, `data` non-JSON ou `limit < 1`. |

## Mise en place de la table

```bash
forge notifications:init
forge migration:apply
```

## Rappel

Forge Core ne dépend pas du paquet.
Le périmètre V1 est strictement in-app ; la livraison hors application (email, push) reste applicative, par exemple via `forge-mvc-jobs` et `forge-mvc-mail`.
Chaque fonction accepte `db=` pour injecter une connexion.
