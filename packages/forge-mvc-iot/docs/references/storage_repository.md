# Le repository d'événements IoT dans Forge

Ce document décrit l'insertion des mesures dans la table `iot_events`.

Le fichier de code correspondant est `forge_mvc_iot/storage/repository.py`.

## 1. À quoi sert ce module ?

Le **repository** insère les `Measurement` reçues dans la table `iot_events`.
Il s'appuie sur un adaptateur de base (`DbAdapter`) injectable, ce qui le rend testable sans base réelle.

## 2. L'API

| Élément | Rôle |
|---|---|
| `DbAdapter` | l'interface attendue (exécution SQL) par le repository |
| `IotEventRepository(db_adapter=None)` | insère les `Measurement` dans `iot_events` |

```python
from forge_mvc_iot.storage.repository import IotEventRepository

repository = IotEventRepository()
repository.insert(measurement)
```

Sans `db_adapter`, la connexion du noyau est utilisée ; on peut en injecter un pour les tests.

## 3. Le rôle dans la chaîne

Le repository est le maillon final : le subscriber valide, [le contrat SQL](storage_events.md) sérialise, le repository **persiste**.
C'est aussi lui que l'API HTTP de lecture interroge.

## 4. Contextes d'utilisation

- **Écoute** : `on_measurement = repository.insert` dans le subscriber.
- **API HTTP** : le repository alimente les routes de lecture.

## 5. Voir aussi

- [Le contrat SQL des événements](storage_events.md) : la requête exécutée.
- [L'API HTTP](http.md) : lit les événements stockés.
- [Stockage des événements (guide)](../storage-events.md).
