# Tableau de bord IoT

Objectif : afficher les derniers événements dans une **page HTML** lisible par un
humain.

**Ce que vous allez apprendre :** combiner `IotEventRepository.list_recent` et
`BaseController.render` pour présenter les événements dans un tableau. Après
l'API JSON (côté machine), voici la lecture **côté humain**.

Dernier palier du **niveau intermédiaire** de la progression IoT, après
[Exposer l'API IoT](iot-api.md).

## Ce que ce starter montre

- la lecture des derniers événements (`list_recent`) ;
- leur affichage dans un **tableau HTML** via un template Jinja ;
- un **état vide** clair quand aucun événement n'est encore stocké.

La table `iot_events` est garantie par la migration livrée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `IotEventRepository.list_recent` | Lire les derniers événements à afficher. | [Forge IoT — stockage](../../../iot/storage-events.md) |
| `BaseController.render` | Rendre le tableau de bord HTML. | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge db:init
forge run
```

Ouvrez `https://localhost:8000/iot-dashboard` : les événements injectés au palier
*Simuler une mesure IoT* s'affichent dans un tableau. Sans données, la page
affiche un message d'invitation.

## Le contrôleur

```python
# mvc/controllers/iot_dashboard_controller.py
from forge_mvc_iot.storage import IotEventRepository


class IotDashboardController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        try:
            events = IotEventRepository().list_recent(limit=50)
        except Exception:
            events = []
        return BaseController.render(
            "iot_dashboard/index.html",
            context={"events": events},
            request=request,
        )
```

### Comprendre ce code

- `list_recent(limit=50)` renvoie les 50 derniers événements ; on les passe au
  template via le `context`.
- Le `try/except` garde la page **robuste** : pas de table → tableau vide, pas de
  page d'erreur.
- C'est le **même** repository qu'aux paliers de lecture : on change seulement la
  sortie (HTML au lieu de JSON).

## La vue

```html
<!-- mvc/views/iot_dashboard/index.html -->
{% if events %}
<table>
  <thead><tr><th>Site</th><th>Capteur</th><th>Type</th><th>Valeur</th><th>Unité</th><th>Horodatage</th></tr></thead>
  <tbody>
    {% for e in events %}
    <tr><td>{{ e.site }}</td><td>{{ e.device_id }}</td><td>{{ e.kind }}</td><td>{{ e.value }}</td><td>{{ e.unit }}</td><td>{{ e.timestamp }}</td></tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
<p>Aucun événement à afficher.</p>
{% endif %}
```

## À retenir

- Un tableau de bord = `list_recent` + `render`, rien de plus.
- Le même repository alimente l'API JSON **et** la page HTML.
- Une page de lecture reste robuste quand les données manquent.

## Après ce starter

Vous avez terminé le **niveau intermédiaire** : simulation, API, tableau de bord.
Faites le point dans le bilan du niveau.

[Bilan du niveau intermédiaire](bilan.md)
