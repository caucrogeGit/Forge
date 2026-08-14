# Premier paramètre

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-settings` avant de commencer : voir sa [référence](../../reference.md).

    ```bash
    pip install --pre forge-mvc-settings    # installe le paquet
    forge opt-in:enable settings          # le branche au projet
    ```

    Sans le paquet, l'application refuse de démarrer sur un `ModuleNotFoundError` au chargement des routes.

    `forge opt-in:install settings` **affiche** la commande d'installation adaptée à votre environnement, pipx compris ; il n'installe rien lui-même (ADR-016).

Objectif : premier contact avec le module **opt-in** `forge-mvc-settings`.

**Ce que vous allez apprendre :** un paramètre applicatif est une paire clé/valeur stockée en base.
On écrit un paramètre avec `set_setting`, puis on le relit avec `get_setting`.
La table de stockage doit d'abord exister, ce qui se fait en deux commandes.

Premier palier du **niveau débutant** de la progression Settings.

!!! note "Module opt-in"
    Si `forge-mvc-settings` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- créer la table des paramètres avec `forge settings:init` puis `forge migration:apply` ;
- écrire un premier paramètre avec `set_setting` ;
- le relire avec `get_setting`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `set_setting(key, value)` | Crée ou met à jour un paramètre. | Opt-ins |
| `get_setting(key, default)` | Lit la valeur d'un paramètre. | Opt-ins |

## 1. Créer la table

La table n'est pas créée automatiquement.
On la prépare une seule fois, depuis la racine du projet :

```bash
forge settings:init
forge migration:apply
```

### Comprendre ce code

- `forge settings:init` copie la migration SQL dans `mvc/migrations/`.
- `forge migration:apply` exécute la migration et crée la table `app_settings`.
- Une écriture en base reste explicite : rien n'est créé en silence.

## 2. Écrire et relire un paramètre

```python
from forge_mvc_settings import set_setting, get_setting

set_setting("etablissement.nom", "Collège Victor Hugo")

nom = get_setting("etablissement.nom")
print(nom)   # Collège Victor Hugo
```

### Comprendre ce code

- `set_setting("etablissement.nom", "Collège Victor Hugo")` enregistre la valeur.
- Le type est déduit de la valeur : ici une chaîne (`str`).
- `get_setting("etablissement.nom")` relit la valeur telle qu'elle a été stockée.

## À retenir

- Un paramètre se crée avec `set_setting(clé, valeur)`.
- `get_setting(clé)` renvoie la valeur enregistrée.
- La table `app_settings` doit exister : `forge settings:init` puis `forge migration:apply`.

## Après ce starter

Vous avez écrit et relu un premier paramètre.
Approfondissons l'écriture et la lecture, avec les valeurs par défaut.

[Écrire et lire](settings-set-get.md)
