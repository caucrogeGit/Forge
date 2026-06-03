# Diagnostiquer le module IoT

Objectif : vérifier que le module IoT est **sain** et savoir où chercher quand il
ne l'est pas.

**Ce que vous allez apprendre :** le diagnostic Forge IoT. La commande
`forge iot:doctor` vérifie l'ensemble (paquet, configuration, API, base, broker).
Ce starter expose en JSON son **sous-ensemble non invasif** — les contrôles qui
ne touchent ni la base ni le broker — directement dans l'application.

Dernier palier du **niveau avancé** de la progression IoT, après
[Le subscriber MQTT](iot-subscriber.md).

## Ce que ce starter montre

- l'appel des vérifications non invasives du diagnostic :
    - `check_package_importable` — le paquet est installé,
    - `check_config_loadable` — la configuration se charge,
    - `check_http_api_registrable` — l'API HTTP peut être branchée ;
- un statut global `healthy` + le détail de chaque contrôle, en JSON.

Le diagnostic **complet** (table en base, connexion broker) reste la commande
`forge iot:doctor`.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `check_package_importable` / `check_config_loadable` / `check_http_api_registrable` | Vérifications de diagnostic **non invasives**. | [Forge IoT — doctor](../../../iot/doctor.md) |
| `forge iot:doctor` (CLI) | Diagnostic complet (avec `--db`, `--mqtt`). | [Forge IoT — doctor](../../../iot/doctor.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/iot-doctor` : la réponse JSON donne `healthy` et la
liste des contrôles avec leur statut. Pour le diagnostic complet, en ligne de
commande :

```bash
forge iot:doctor          # config + paquet + API
forge iot:doctor --db     # + vérifie la table iot_events
forge iot:doctor --mqtt   # + teste la connexion au broker
```

## Le contrôleur

```python
# mvc/controllers/iot_doctor_controller.py
from forge_mvc_iot.cli.doctor import (
    check_config_loadable,
    check_http_api_registrable,
    check_package_importable,
)


_SAFE_CHECKS = (check_package_importable, check_config_loadable, check_http_api_registrable)


class IotDoctorController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        checks = []
        for check in _SAFE_CHECKS:
            result = check()
            checks.append({"status": result.status, "label": result.label, "detail": result.detail})
        healthy = all(c["status"] == "ok" for c in checks)
        return Response.json({"healthy": healthy, "checks": checks})
```

### Comprendre ce code

- On n'appelle que les contrôles **sûrs** : aucun ne touche la base ni le broker,
  donc la route reste rapide et sans effet de bord.
- Chaque contrôle renvoie un `status`, un `label` et un `detail` — on les expose
  tels quels.
- Pour les contrôles **invasifs** (table, broker), on délègue à la CLI
  `forge iot:doctor`, qui les active explicitement via `--db` / `--mqtt`.

## À retenir

- `forge iot:doctor` diagnostique le module ; ses contrôles non invasifs sont
  réutilisables en application.
- Un diagnostic sépare le **sûr** (config, paquet) de l'**invasif** (base,
  broker) — on n'effleure l'infrastructure que sur demande.
- Savoir diagnostiquer fait partie de l'exploitation d'un module en production.

## Après ce starter

Vous avez terminé le **niveau avancé** et toute la progression IoT : contrat,
subscriber temps réel, diagnostic. Faites le point dans le bilan du niveau.

[Bilan du niveau avancé](bilan.md)
