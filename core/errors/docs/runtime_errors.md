# Le schéma des erreurs runtime dans Forge

Ce document décrit le schéma canonique d'un événement d'erreur runtime.

Le fichier de code correspondant est `core/errors/runtime_errors.py`.

## 1. À quoi sert ce module ?

Quand une erreur survient à l'exécution, Forge la décrit sous une forme **structurée et stable** (JSONL), pour la journaliser puis la relire.
Ce module construit et valide cet événement.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `build_error_event(exception_type, message, *, environment="dev", ...)` | construit un événement à partir de champs |
| `build_error_event_from_exc(exc, *, environment="dev", ...)` | construit un événement depuis une exception active |
| `safe_request_info(method, path, query=None, ...)` | objet requête **sécurisé** pour l'événement (valeurs sensibles écartées) |
| `validate_event(event)` | vérifie la présence des champs obligatoires |
| `serialize_event(event)` | sérialise l'événement en une ligne JSONL |

## 3. La sécurité

`safe_request_info` ne retient que des informations sûres de la requête : pas de secret, pas de corps sensible.

## 4. Contextes d'utilisation

- **Journalisation** : alimenté par [le collecteur](runtime_error_logger.md).
- **Relecture** : les événements sont rendus en Markdown par [le rendu](runtime_error_markdown.md).

## 5. Voir aussi

- [Le collecteur d'erreurs](runtime_error_logger.md) et [le rendu Markdown](runtime_error_markdown.md).
