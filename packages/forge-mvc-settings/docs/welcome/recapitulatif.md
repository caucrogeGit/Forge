# Aide-mémoire Settings

Synthèse de l'API de `forge-mvc-settings`, à garder sous la main.

## Mise en place de la table

| Commande | Effet |
|----------|-------|
| `forge settings:init` | Copie la migration SQL dans `mvc/migrations/`. |
| `forge migration:apply` | Applique la migration et crée la table `app_settings`. |

La table n'est jamais créée automatiquement.

## Écrire et lire

| Appel | Résultat |
|-------|----------|
| `set_setting(key, value)` | Upsert : crée ou met à jour ; renvoie `None`. |
| `get_setting(key)` | Valeur recoercée selon son type, ou `None` si absente. |
| `get_setting(key, default)` | Valeur, ou `default` si la clé n'existe pas. |
| `get_all_settings()` | `dict` de tous les paramètres, triés par clé. |
| `delete_setting(key)` | `True` si le paramètre existait, `False` sinon. |

Toutes ces fonctions acceptent un paramètre `db=` injectable (défaut
`core.database.db`), utile en test.

## Clés et types

| Élément | Règle |
|---------|-------|
| Clé | Une lettre, puis lettres, chiffres, `_` ou `.`, sur 191 caractères au plus. |
| Clé hiérarchique | Le point structure les noms : `qcm.session_duration`, `etablissement.nom`. |
| Types | `SUPPORTED_TYPES == ("str", "int", "bool", "float")`. |
| Type déduit | `set_setting` choisit le type d'après la valeur ; `get_setting` le recoerce. |

## Constantes et erreurs

| Nom | Valeur ou rôle |
|-----|----------------|
| `TABLE_NAME` | `app_settings` |
| `SUPPORTED_TYPES` | `("str", "int", "bool", "float")` |
| `CREATE_TABLE_SQL` | Définition SQL de la table, exposée pour inspection. |
| `SettingsError` | Levée sur clé invalide ou type non supporté. |

## Rappel

Forge Core ne dépend pas du paquet.
L'application décide quels réglages elle persiste et où la table est créée.
