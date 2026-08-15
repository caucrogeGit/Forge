# Tableau de bord IoT

Objectif : afficher les derniers événements dans une **page HTML** lisible par un humain.

**Ce que vous allez apprendre :** combiner `IotEventRepository.list_recent` et `BaseController.render` pour présenter les événements dans un tableau.
Après l'API JSON (côté machine), voici la lecture **côté humain**.

Dernier palier du **niveau intermédiaire** de la progression IoT, après [Exposer l'API IoT](iot-api.md).

## Ce que ce starter montre

- la lecture des derniers événements (`list_recent`) ;
- leur affichage dans un **tableau HTML** via un template Jinja ;
- un **état vide** clair quand aucun événement n'est encore stocké.

La table `iot_events` est garantie par la migration livrée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `IotEventRepository.list_recent` | Lire les derniers événements à afficher. | [Forge IoT : stockage](../../storage-events.md) |
| `BaseController.render` | Rendre le tableau de bord HTML. | BaseController |

## Tester

```bash
forge db:config    # amorce DB_NAME dans env/ (une seule fois)
forge db:init
forge iot:init    # copie la migration de l'opt-in
forge migration:apply    # l'applique en base
forge run
```

Ouvrez `https://localhost:8000/iot-dashboard` : les événements injectés au palier *Simuler une mesure IoT* s'affichent dans un tableau.
Sans données, la page affiche un message d'invitation.

## Le contrôleur

Créez le fichier ci-dessous, complet et copiable tel quel.

```python
# mvc/controllers/iot_dashboard_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.storage import IotEventRepository


class IotDashboardController(BaseController):
    """Starter pédagogique : afficher les événements IoT dans une page HTML."""

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

- `list_recent(limit=50)` renvoie les 50 derniers événements ; on les passe au template via le `context`.
- Le `try/except` garde la page **robuste** : pas de table → tableau vide, pas de page d'erreur.
- C'est le **même** repository qu'aux paliers de lecture : on change seulement la sortie (HTML au lieu de JSON).

## La vue

Créez le gabarit ci-dessous, complet et copiable tel quel.

```html
<!-- mvc/views/iot_dashboard/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Tableau de bord IoT - Forge</title>
</head>
<body>
  <h1>Tableau de bord IoT</h1>

  {% if events %}
  <table>
    <thead>
      <tr><th>Site</th><th>Capteur</th><th>Type</th><th>Valeur</th><th>Unité</th><th>Horodatage</th></tr>
    </thead>
    <tbody>
      {% for e in events %}
      <tr>
        <td>{{ e.site }}</td>
        <td>{{ e.device_id }}</td>
        <td>{{ e.kind }}</td>
        <td>{{ e.value }}</td>
        <td>{{ e.unit }}</td>
        <td>{{ e.timestamp }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>Aucun événement à afficher. Injectez des mesures (palier <em>Simuler une mesure IoT</em>).</p>
  {% endif %}
</body>
</html>
```

## La route

Déclarez la route dans `mvc/routes/__init__.py`, à l'intérieur du groupe public.

```python
# mvc/routes/__init__.py
from mvc.controllers.iot_dashboard_controller import IotDashboardController

with router.group("", public=True) as public:
    public.add("GET", "/iot-dashboard", IotDashboardController.index, name="iot_dashboard_index")
```

## La migration

Le tableau de bord lit la table `iot_events`.
Créez le fichier de migration ci-dessous (le nom commence par un horodatage), puis appliquez-le avec `forge db:init`.

```sql
-- mvc/migrations/20260601190000_create_iot_events.sql
CREATE TABLE IF NOT EXISTS iot_events (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site          VARCHAR(64)     NOT NULL,
    device_id     VARCHAR(64)     NOT NULL,
    kind          VARCHAR(64)     NOT NULL,
    value         DOUBLE          NOT NULL,
    unit          VARCHAR(32)     NOT NULL,
    timestamp     VARCHAR(40)     NOT NULL,
    metadata_json TEXT            NULL,
    received_at   DATETIME(6)     NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_iot_events_site_device (site, device_id),
    INDEX idx_iot_events_received_at (received_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

`CREATE TABLE IF NOT EXISTS` rend la migration idempotente : elle est sûre même si un autre palier a déjà créé la table.

## À retenir

- Un tableau de bord = `list_recent` + `render`, rien de plus.
- Le même repository alimente l'API JSON **et** la page HTML.
- Une page de lecture reste robuste quand les données manquent.

## Après ce starter

Vous avez terminé le **niveau intermédiaire** : simulation, API, tableau de bord.
Faites le point dans le bilan du niveau.

[Bilan du niveau intermédiaire](bilan.md)
