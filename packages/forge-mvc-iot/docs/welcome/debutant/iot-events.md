# Lire les événements IoT

Objectif : lire les mesures déjà **stockées** par le module IoT et les renvoyer
en JSON.

**Ce que vous allez apprendre :** le `IotEventRepository` et sa méthode
`list_recent`, qui renvoie les derniers événements de la table `iot_events`
(ordre du plus récent). Et un réflexe Forge : rester **pédagogique** quand la
table n'existe pas encore, au lieu de planter.

Palier 2 du **niveau débutant** de la progression IoT, après
[Welcome IoT](iot-welcome.md).

## Ce que ce starter montre

- la lecture des derniers événements via `IotEventRepository.list_recent` ;
- une réponse JSON `{ "events": [...] }` ;
- une **réponse `503` explicite** quand la table `iot_events` n'est pas encore
  disponible (aucun `iot:init` lancé), au lieu d'une erreur brute.

Aucun broker, aucune écriture.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_iot.storage.IotEventRepository` | Lire les événements stockés. | [Forge IoT : stockage](../../storage-events.md) |
| `IotEventRepository.list_recent` | Derniers événements (ordre `received_at` décroissant). | [Forge IoT : stockage](../../storage-events.md) |
| `Response.json` | Renvoyer les événements (ou l'erreur) en JSON. | Response |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/iot-events`. Sans table créée, la route répond
`503` avec un message qui invite à lancer `forge iot:init`. Une fois la table
présente (et des mesures injectées au niveau intermédiaire), elle renvoie la
liste des événements.

## Le contrôleur

Créez le fichier ci-dessous, complet et copiable tel quel.

```python
# mvc/controllers/iot_events_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.storage import IotEventRepository


_STORAGE_NOT_READY = {
    "error": "iot_storage_not_ready",
    "message": (
        "La table iot_events n'est pas encore disponible. "
        "Applique la migration Forge IoT (forge iot:init) avant de lire "
        "les événements."
    ),
}


class IotEventsController(BaseController):
    """Starter pédagogique : lire les derniers événements IoT stockés."""

    @staticmethod
    def index(request: Request) -> Response:
        repo = IotEventRepository()
        try:
            events = repo.list_recent(limit=20)
        except Exception:
            # Table absente, base inaccessible… on reste pédagogique.
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({"events": events})
```

### Comprendre ce code

- `IotEventRepository()` utilise par défaut l'accès base de Forge
  (`core.database.db`), aucun branchement manuel.
- `list_recent(limit=20)` renvoie les 20 derniers événements sous forme de
  dictionnaires, directement sérialisables en JSON.
- Le `try/except` **ne masque pas un bug** : il traduit l'absence de table en
  réponse `503` pédagogique. Un starter de découverte ne doit jamais planter
  parce que l'infrastructure n'est pas encore montée.

## La route

Déclarez la route dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.iot_events_controller import IotEventsController

with router.group("", public=True) as public:
    public.add("GET", "/iot-events", IotEventsController.index, name="iot_events_index")
```

## À retenir

- `IotEventRepository.list_recent` lit les derniers événements stockés.
- Le repository s'appuie sur l'accès base standard de Forge.
- Un starter de découverte **reste pédagogique** quand la table manque (`503`),
  il ne plante pas.

## Après ce starter

Vous savez lire le flux global des événements. La suite : cibler un capteur
précis.

[Les événements d'un capteur](iot-device.md)
