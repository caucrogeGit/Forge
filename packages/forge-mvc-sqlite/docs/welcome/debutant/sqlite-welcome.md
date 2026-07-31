# Première base SQLite

!!! note "Prérequis : deux paquets"
    ```bash
    pip install --pre forge-mvc-sqlite forge-mvc-entities
    ```

    Le backend seul ne suffit pas.
    Les commandes de base de données (`db:init`, `db:apply`, `migration:*`) sont fournies par le moteur d'entités, extrait du cœur par l'[ADR-070](/docs/forge/adr/070-entities-engine-extraction/).
    Sans lui, `forge db:init` répond que le module n'est pas installé.

    Voir la [référence](../../reference.md) pour la mise en service complète.

Objectif : premier contact avec le backend **opt-in** `forge-mvc-sqlite`.

**Ce que vous allez apprendre :** SQLite range la base dans un fichier.
Le cœur de Forge le découvre dès qu'il est installé, et `forge db:init` crée ce fichier.

Premier palier du **niveau débutant** de la progression SQLite.

!!! note "Backend sans serveur"
    SQLite n'a pas de serveur : il n'y a ni base distante, ni compte à créer.

    `db:init` prépare simplement le fichier et la table technique `forge_migrations`.

## Ce que ce palier montre

- vérifier que le backend est actif ;
- dire à Forge où ranger le fichier ;
- créer la base avec `forge db:init`.

## 1. Vérifier le backend actif

```bash
forge doctor
```

`doctor` indique le backend BDD résolu.
Avec seulement `forge-mvc-sqlite` installé, c'est `sqlite`.

À ce stade `doctor` signale que `DB_NAME` n'est pas défini, ce que le palier suivant corrige.

## 2. Dire où ranger le fichier

```bash
forge db:config
```

Cette commande pose `DB_NAME` dans `env/example`, `env/dev` et `env/prod`, sans jamais écraser une valeur déjà renseignée (ADR-064).
Sans elle, le backend ne sait pas quel fichier ouvrir et `db:init` refuse de deviner.

## 3. Créer la base

```bash
forge db:init
```

Forge crée le fichier SQLite (chemin `DB_NAME`) et la table `forge_migrations`.

Aucun serveur n'est contacté : tout se passe dans un fichier local.

## Après cette étape

[Palier suivant : Appliquer une entité](sqlite-apply.md)
