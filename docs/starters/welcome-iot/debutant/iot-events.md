# Lire les événements IoT

Objectif : lire les mesures déjà **stockées** par le module IoT et les renvoyer
en JSON.

**Ce que vous allez apprendre :** le `IotEventRepository` et sa méthode
`list_recent`, qui renvoie les derniers événements de la table `iot_events`
(ordre du plus récent). Et un réflexe Forge : rester **pédagogique** quand la
table n'existe pas encore, au lieu de planter.

Palier 2 du **niveau débutant** de la progression IoT, après
[Bonjour Forge IoT](iot-welcome.md).

## Ce que ce starter montre

- la lecture des derniers événements via `IotEventRepository.list_recent` ;
- une réponse JSON `{ "events": [...] }` ;
- une **réponse `503` explicite** quand la table `iot_events` n'est pas encore
  disponible (aucun `iot:init` lancé), au lieu d'une erreur brute.

Aucun broker, aucune écriture.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_iot.storage.IotEventRepository` | Lire les événements stockés. | [Forge IoT — stockage](../../../iot/storage-events.md) |
| `IotEventRepository.list_recent` | Derniers événements (ordre `received_at` décroissant). | [Forge IoT — stockage](../../../iot/storage-events.md) |
| `Response.json` | Renvoyer les événements (ou l'erreur) en JSON. | [Response](../../../reference/api.md#corehttp) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/iot-events`. Sans table créée, la route répond
`503` avec un message qui invite à lancer `forge iot:init`. Une fois la table
présente (et des mesures injectées au niveau intermédiaire), elle renvoie la
liste des événements.

## Le contrôleur

```python
# mvc/controllers/iot_events_controller.py
from forge_mvc_iot.storage import IotEventRepository


_STORAGE_NOT_READY = {
    "error": "iot_storage_not_ready",
    "message": "La table iot_events n'est pas encore disponible. "
               "Applique la migration Forge IoT (forge iot:init)…",
}


class IotEventsController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        repo = IotEventRepository()
        try:
            events = repo.list_recent(limit=20)
        except Exception:
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({"events": events})
```

### Comprendre ce code

- `IotEventRepository()` utilise par défaut l'accès base de Forge
  (`core.database.db`) — aucun branchement manuel.
- `list_recent(limit=20)` renvoie les 20 derniers événements sous forme de
  dictionnaires, directement sérialisables en JSON.
- Le `try/except` **ne masque pas un bug** : il traduit l'absence de table en
  réponse `503` pédagogique. Un starter de découverte ne doit jamais planter
  parce que l'infrastructure n'est pas encore montée.

## À retenir

- `IotEventRepository.list_recent` lit les derniers événements stockés.
- Le repository s'appuie sur l'accès base standard de Forge.
- Un starter de découverte **reste pédagogique** quand la table manque (`503`),
  il ne plante pas.

## Après ce starter

Vous savez lire le flux global des événements. Faites le point dans le bilan du
niveau.

[Bilan du niveau débutant](bilan.md)
