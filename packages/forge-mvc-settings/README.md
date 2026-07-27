# forge-mvc-settings

Paramètres applicatifs opt-in pour Forge : des réglages d'application persistés
dans MariaDB, en paire clé/valeur typée, avec une API explicite.

Ce paquet évite de tout mettre dans `.env` : ce qui change à l'exécution (nom
d'établissement, durée d'une session, mode maintenance, options pédagogiques)
vit dans une table `app_settings`, lisible et modifiable par l'application.

## Installation

```bash
pip install --pre forge-mvc-settings
```

En développement depuis le dépôt Forge : `pip install -e ./packages/forge-mvc-settings`.

## Mise en place de la table

La table n'est pas créée automatiquement (principe : SQL visible, pas d'écriture
cachée). Le paquet fournit une migration :

```bash
forge settings:init        # copie la migration dans mvc/migrations/
forge migration:apply      # crée la table app_settings
```

## Utilisation

```python
from forge_mvc_settings import get_setting, set_setting

set_setting("etablissement.nom", "Collège Victor Hugo")
set_setting("qcm.session_duration", 30)        # int
set_setting("maintenance", False)              # bool

nom = get_setting("etablissement.nom")          # "Collège Victor Hugo"
duree = get_setting("qcm.session_duration", 20) # 30 (int)
en_maintenance = get_setting("maintenance")     # False (bool)
```

L'API expose `get_setting`, `set_setting`, `get_all_settings`, `delete_setting`,
plus `SettingsError`, `TABLE_NAME` et `SUPPORTED_TYPES`.

## Périmètre

- Types supportés : `str`, `int`, `bool`, `float` (sérialisés en texte,
  recoercés à la lecture).
- Le cœur de Forge ignore tout des paramètres ; la dépendance va de l'opt-in
  vers le cœur, jamais l'inverse.
- Hors périmètre : cache, secrets chiffrés, paramètres par utilisateur.

Documentation complète : <https://forgemvc.com/docs/forge/>.
