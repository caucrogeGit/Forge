# L'API HTTP IoT dans Forge

Ce document décrit les routes de lecture JSON des événements IoT et leur branchement.

Le fichier de code correspondant est `forge_mvc_iot/http.py`.

## 1. À quoi sert ce module ?

Une fois les mesures stockées, on veut les **lire** : par une API JSON, pour un tableau de bord ou un autre service.
Ce module branche les routes de lecture des événements IoT sur un `Router` Forge.

Le module reste **opt-in** : l'application appelle `register_iot_routes` explicitement.

## 2. Brancher les routes

```python
from forge_mvc_iot.http import register_iot_routes

def register_routes(router):
    register_iot_routes(router)
    return router
```

`register_iot_routes(router, *, repository=None, config=None)` enregistre les routes de lecture.
Sans `repository` ni `config`, ils sont construits depuis l'environnement.

## 3. La sécurité

Si `config.api_token` est défini (`FORGE_IOT_API_TOKEN`), les routes exigent `Authorization: Bearer <token>` ; sinon elles sont ouvertes (mode local / pédagogique).

## 4. Le contrôleur (`IotHttpController`)

`register_iot_routes` instancie `IotHttpController(repository, *, api_token=None)`, dont les handlers lisent les événements via le [repository](storage_repository.md) et répondent en JSON.

## 5. Contextes d'utilisation

- **Tableau de bord** : consommer l'API JSON pour afficher les mesures.
- **Déploiement protégé** : `FORGE_IOT_API_TOKEN` pour exiger un Bearer.

## 6. Voir aussi

- [Le repository d'événements](storage_repository.md) : la source des données lues.
- [La configuration IoT](config.md) : `api_token`.
- [API HTTP (guide)](../http-api.md) : le détail des routes et réponses.
