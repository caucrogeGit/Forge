# Le rendu Markdown des erreurs dans Forge

Ce document décrit la transformation du journal d'erreurs JSONL en Markdown lisible.

Le fichier de code correspondant est `core/errors/runtime_error_markdown.py`.

## 1. À quoi sert ce module ?

Le journal d'erreurs est en JSONL (une ligne par erreur), pratique pour la machine mais pas pour l'humain.
Ce module le rend en **Markdown** lisible, pour relire et trier les erreurs.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `load_error_events_from_jsonl(path)` | charge les événements depuis un fichier JSONL |
| `render_error_event_markdown(event)` | rend un événement en Markdown |
| `render_errors_markdown(events)` | rend une liste d'événements en un document Markdown |
| `write_errors_markdown(jsonl_path, markdown_path)` | lit le JSONL et écrit le fichier Markdown |

## 3. Contextes d'utilisation

- **Revue d'erreurs** : convertir `storage/logs/errors.jsonl` en page lisible.

## 4. Voir aussi

- [Le collecteur d'erreurs](runtime_error_logger.md) : produit le JSONL.
- [Le schéma des erreurs](runtime_errors.md).
