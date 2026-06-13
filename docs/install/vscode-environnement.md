# Environnement VS Code de Forge

Ce document rassemble les **extensions** et la **configuration VS Code** utilisées
dans le projet Forge : ce que le dépôt versionne réellement, les extensions
nécessaires au confort de développement, et les extensions recommandées qui
correspondent à l'outillage déjà employé en ligne de commande.

!!! info "Forge ne dépend pas de VS Code"
    Aucune de ces extensions n'est requise pour développer, tester ou livrer
    avec Forge. Tout reste pilotable en ligne de commande (`pytest`, `ruff`,
    `mkdocs`, `forge`). VS Code n'apporte que du confort : autocomplétion,
    auto-import, validation JSON, diagnostics en direct.

---

## 1. Configuration versionnée : `.vscode/settings.json`

Le dépôt ne versionne qu'un seul fichier VS Code, par une exception explicite du
`.gitignore` :

```gitignore
.vscode/*
!.vscode/settings.json
```

Son contenu associe les **schémas JSON de Forge** aux fichiers d'un projet, pour
que VS Code propose les clés autorisées et signale les erreurs pendant la
saisie :

```json
{
  "json.schemas": [
    {
      "fileMatch": ["/mvc/entities/relations.json"],
      "url": "./schemas/relations.schema.json"
    },
    {
      "fileMatch": ["/mvc/entities/*/*.json"],
      "url": "./schemas/entity.schema.json"
    },
    {
      "fileMatch": ["/mvc/security/rbac.json"],
      "url": "./schemas/rbac.schema.json"
    }
  ],
  "files.associations": {
    "**/env/*": "properties"
  }
}
```

| Fichier du projet | Schéma associé | Rôle |
|---|---|---|
| `mvc/entities/relations.json` | `schemas/relations.schema.json` | Relations entre entités |
| `mvc/entities/*/*.json` | `schemas/entity.schema.json` | Définition d'une entité |
| `mvc/security/rbac.json` | `schemas/rbac.schema.json` | Rôles et permissions RBAC |

La clé `json.schemas` est **native** à VS Code : elle ne réclame aucune
extension. Le détail de cette intégration, et la méthode alternative par clé
`$schema` dans chaque fichier, sont décrits dans
[Autocomplétion VS Code avec les schémas JSON](../entities/vscode-json-schema.md).

### Association des fichiers `env/*`

L'entrée `files.associations` indique à VS Code de traiter les fichiers du dossier `env/` (donc `env/dev`, `env/prod`, `env/example`, `env/*.local`) comme du langage `properties`.
Le motif `**/env/*` est volontairement ancré avec `**/`, car VS Code confronte un motif contenant `/` au chemin du fichier ; un motif nu comme `env/*` ne matche pas de façon fiable selon les versions.
VS Code colore alors le format `KEY=VALUE` et les commentaires `#`, sans renommer ces fichiers en `.env` et sans dépendre d'une extension dédiée.
Le squelette produit par `forge new` embarque la même association, pour que chaque nouveau projet en bénéficie sans configuration.

!!! note "L'association s'applique à l'ouverture du fichier"
    Après modification de `files.associations`, rechargez la fenêtre (« Developer: Reload Window ») ou rouvrez le fichier.
    Le mode de langage affiché en bas à droite doit indiquer **Properties**.

!!! warning "Validation partielle"
    VS Code ne remplace pas `forge entity:validate`. Les règles sémantiques de
    Forge (entités inconnues, collisions, cohérence champs/index) ne sont
    vérifiées que par la CLI.

---

## 2. Extensions

### Nécessaires au développement Forge

Ces deux extensions sont celles documentées par le guide d'auto-import des
classes Forge :

| Extension | Identifiant | Pourquoi |
|---|---|---|
| Python | `ms-python.python` | Interpréteur, exécution, débogage, sélection du `.venv`. |
| Pylance | `ms-python.vscode-pylance` | Analyse de types, autocomplétion et auto-import des classes du paquet `core`. |

La configuration fine (interpréteur du `.venv`, indexation profonde de `core`
pour l'auto-import) est détaillée dans
[Configurer VS Code pour l'auto-import des classes Forge](vscode.md).

### Recommandées pour l'outillage du projet

Forge utilise déjà ces outils en ligne de commande (voir
[Mode développement](core-dev.md)). Les extensions correspondantes remontent
leurs diagnostics directement dans l'éditeur. Elles restent optionnelles :

| Extension | Identifiant | Outil CLI correspondant |
|---|---|---|
| Ruff | `charliermarsh.ruff` | `ruff check .` / `ruff format` (lit la config de `pyproject.toml`) |
| YAML | `redhat.vscode-yaml` | Édition de `mkdocs.yml` (validation et autocomplétion YAML) |
| Even Better TOML | `tamasfe.even-better-toml` | Édition de `pyproject.toml` (le fichier de version et de packaging) |

Le JSON (`json.schemas`, fichiers d'entités) est géré par le **support natif**
de VS Code : aucune extension supplémentaire n'est nécessaire.

---

## 3. Déclarer les extensions recommandées (`.vscode/extensions.json`)

Pour que VS Code propose d'installer ces extensions à l'ouverture du dossier,
créer le fichier `.vscode/extensions.json` :

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "redhat.vscode-yaml",
    "tamasfe.even-better-toml"
  ]
}
```

!!! note "Ce fichier n'est pas versionné par défaut"
    Le `.gitignore` ignore tout `.vscode/` sauf `settings.json`. Le fichier
    `extensions.json` reste donc local à votre poste. Pour le partager avec
    l'équipe, ajouter une exception dans `.gitignore` :

    ```gitignore
    !.vscode/extensions.json
    ```

---

## 4. Réglages complémentaires recommandés

Ces réglages s'ajoutent au `.vscode/settings.json` versionné. Ils sont
optionnels et propres au confort de chacun :

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.indexing": true,
  "python.analysis.packageIndexDepths": [
    { "name": "core", "depth": 4, "includeAllSymbols": true }
  ],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

- Les clés `python.*` activent l'auto-import des classes Forge. Leur rôle exact,
  le piège du pluriel `packageIndexDepths` et les étapes d'activation
  (sélection de l'interpréteur, rechargement de la fenêtre) sont expliqués dans
  [Configurer VS Code pour l'auto-import](vscode.md).
- Le bloc `[python]` confie le formatage et l'organisation des imports à Ruff,
  cohérent avec `ruff check` lancé en CLI.

---

## 5. Connexion à la documentation Forge

| Sujet | Page |
|---|---|
| Auto-import des classes `core` (Python + Pylance) | [Configurer VS Code pour l'auto-import](vscode.md) |
| Schémas JSON des entités et relations | [Autocomplétion VS Code avec les schémas JSON](../entities/vscode-json-schema.md) |
| Outils CLI du projet (ruff, mkdocs, pytest) | [Mode développement](core-dev.md) |
