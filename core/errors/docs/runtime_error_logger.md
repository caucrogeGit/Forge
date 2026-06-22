# Le collecteur d'erreurs runtime dans Forge

Ce document décrit la journalisation d'une erreur survenue à l'exécution.

Le fichier de code correspondant est `core/errors/runtime_error_logger.py`.

## 1. À quoi sert ce module ?

Quand une exception non gérée traverse l'application, Forge l'enregistre dans un journal JSONL (`storage/logs/errors`) et prépare un contexte pour la page d'erreur de développement.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `log_runtime_error(exc, request=None)` | enregistre l'erreur dans le journal JSONL |
| `build_dev_error_context(exc)` | contexte d'erreur pour la page `errors/500.html` (dev), ou `None` |
| `set_jsonl_dir(path)` | surcharge le répertoire de logs (tests) ; `None` rétablit le défaut |

## 3. Le contrat dev / prod

En `dev`, `build_dev_error_context` fournit un contexte riche pour diagnostiquer ; en `prod`, la page d'erreur reste sobre et ne divulgue rien.

## 4. Contextes d'utilisation

- **Application** : journaliser les erreurs non gérées + afficher la page 500.
- **Tests** : `set_jsonl_dir` pour isoler le journal.

## 5. Voir aussi

- [Le schéma des erreurs](runtime_errors.md) : la forme de l'événement journalisé.
- [Le rendu Markdown](runtime_error_markdown.md) : relire le journal.
