# Préambule : construire un registre d'événements

Ce parcours vous apprend à construire, **à la main**, un petit registre d'événements dans `mvc/events/` : un `emit()`, un `subscribe()`, et un fichier de câblage visible.
Puis, au dernier palier, à le **critiquer** : ce que vous avez gagné, ce que vous avez perdu.

!!! warning "Forge ne fournit aucun système d'événements"
    Ce n'est pas un oubli, c'est une décision écrite ([ADR-052](../../adr/052-optin-strategy.md)).
    Un bus d'événements à découverte automatique (`@events.on`) viole le principe 3 (refuser la magie cachée) et le principe 11 (une seule façon officielle).
    Le code que vous écrivez ici est **le vôtre**, dans votre application.
    Forge ne le génère pas, ne l'impose pas et ne le réécrira jamais.

## Prérequis

- Un projet Forge déjà créé (voir [Parcours Welcome Forge](../welcome-forge/index.md)).
- Avoir suivi le niveau débutant, notamment les paliers formulaire et écriture SQL.

## Le problème que nous traitons

Prenez un contrôleur d'inscription.
Après avoir créé l'utilisateur, il doit envoyer un courriel de bienvenue, enregistrer une statistique, et créer une notification.

```python
# mvc/controllers/register_controller.py (extrait, avant)
def store(self, request):
    user_id = create_user(request.form["email"])
    send_welcome_mail(request.form["email"])
    record_registration(user_id)
    notify_admins(user_id)
    return self.redirect("/login")
```

Trois appels alignés.
Demain il y en aura cinq, puis huit, et le contrôleur ne parlera plus d'inscription : il parlera de tout ce qui suit une inscription.

C'est le symptôme que l'on cherche à traiter.
Gardez bien en tête que ce code **fonctionne**, qu'il est parfaitement lisible, et qu'un lecteur pressé sait en trois secondes tout ce qui se passe.
Nous allons échanger cette qualité contre une autre.

## Ce que vous allez obtenir

    mvc/events/ ├── __init__.py # ré-exporte emit et subscribe ├── _registry.py # le registre : subscribe, emit ├── wiring.py # LA liste des abonnements, à la main └── listeners/ └── user.py # les réactions à l'inscription

Cinq paliers : le registre, le câblage, le cas réel, les angles morts, le bilan.

[Continuer avec Le registre](registre.md)
