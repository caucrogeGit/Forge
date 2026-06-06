# Les événements d'un capteur

Objectif : lire les événements d'**un capteur précis** et leur nombre, via une
route paramétrée.

**Ce que vous allez apprendre :** cibler un capteur par `site` et `device_id`
avec `IotEventRepository.find_by_device`, et compter ses événements avec
`count_by_device`. C'est la lecture filtrée, après le flux global du palier
précédent.

Dernier palier du **niveau débutant** de la progression IoT, après
[Lire les événements IoT](iot-events.md).

## Ce que ce starter montre

- une route **paramétrée** `/iot-device/{site}/{device_id}` ;
- les événements d'un capteur via `find_by_device` ;
- le nombre d'événements via `count_by_device` ;
- la même **réponse `503` pédagogique** si la table n'existe pas encore.

Lecture seule, aucun broker.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `request.route_param` | Lire `site` et `device_id` dans l'URL. | [Request](../../../reference/api.md#corehttprequest) |
| `IotEventRepository.find_by_device` | Événements d'un capteur (ordre du plus récent). | [Forge IoT — stockage](../../../iot/storage-events.md) |
| `IotEventRepository.count_by_device` | Nombre d'événements d'un capteur. | [Forge IoT — stockage](../../../iot/storage-events.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/iot-device/atelier/capteur-1`. La réponse JSON
donne le `site`, le `device_id`, le `count` et la liste `events` de ce capteur
(ou `503` tant que la table n'est pas créée).

## Le contrôleur

```python
# mvc/controllers/iot_device_controller.py
from forge_mvc_iot.storage import IotEventRepository


class IotDeviceController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        site = request.route_param("site")
        device_id = request.route_param("device_id")
        repo = IotEventRepository()
        try:
            events = repo.find_by_device(site, device_id, limit=20)
            count = repo.count_by_device(site, device_id)
        except Exception:
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({
            "site": site,
            "device_id": device_id,
            "count": count,
            "events": events,
        })
```

### Comprendre ce code

- `site` et `device_id` viennent de l'**URL** (`route_param`) : on cible le
  capteur sans query string.
- `find_by_device(...)` filtre les événements de ce capteur ; `count_by_device`
  donne le total — deux lectures complémentaires du même repository.
- Comme au palier précédent, l'absence de table devient un `503` pédagogique.

## À retenir

- `find_by_device(site, device_id)` filtre les événements d'un capteur.
- `count_by_device(site, device_id)` en donne le nombre.
- Une route **paramétrée** cible une ressource précise via `route_param`.

## Après ce starter

Vous avez terminé le **niveau débutant** : configuration, flux global, lecture
par capteur. Faites le point dans le bilan du niveau.

[Bilan du niveau débutant](bilan.md)
