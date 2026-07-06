# Forge Settings

`forge-mvc-settings` est l'opt-in de paramètres applicatifs de Forge.

Il persiste des réglages d'application dans une table MariaDB `app_settings`, en paire clé/valeur typée, avec une API explicite.
Le but est d'éviter de tout mettre dans `.env` : ce qui change à l'exécution (nom d'établissement, durée d'une session, mode maintenance, options pédagogiques) vit en base, lisible et modifiable par l'application.

## Pourquoi un opt-in séparé

Le cœur de Forge ignore tout des paramètres applicatifs.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse (principe 8).
Le SQL reste visible (constantes du module, migration fournie), aucune écriture cachée (principe 3).

## Mise en route

Installer le paquet, puis créer la table via la migration fournie :

```bash
pip install --pre forge-mvc-settings
forge settings:init        # copie la migration dans mvc/migrations/
forge migration:apply      # crée la table app_settings
```

## Premier usage

```python
from forge_mvc_settings import get_setting, set_setting

set_setting("etablissement.nom", "Collège Victor Hugo")
set_setting("qcm.session_duration", 30)
set_setting("maintenance", False)

nom = get_setting("etablissement.nom")
duree = get_setting("qcm.session_duration", 20)
```

## Périmètre

Types supportés : `str`, `int`, `bool`, `float`, sérialisés en texte et recoercés à la lecture.
Hors périmètre : cache, secrets chiffrés, paramètres par utilisateur.

## Pour aller plus loin

- [Les paramètres](references/store.md) : `get_setting`, `set_setting`, `get_all_settings`, `delete_setting`.
- [L'initialisation](references/cli.md) : `forge settings:init`.
- [Les erreurs](references/errors.md) : `SettingsError`.
