# Les avertissements de production dans Forge

Ce document décrit l'avertissement émis en production quand la session est en mémoire.

Le fichier de code correspondant est `core/app/prod_warnings.py`.

## 1. À quoi sert ce module ?

Le store de session **mémoire** (par défaut) ne convient pas à la production (sessions perdues au redémarrage, non partagées entre workers).
Ce module détecte ce cas en `prod` et émet un avertissement clair.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `is_memory_session_store(store)` | `True` si le store est mémoire (ou non configuré) |
| `should_warn_memory_store_in_prod(env, store)` | `True` si `prod` + store mémoire |
| `format_memory_store_warning()` | le message d'avertissement (multi-lignes) |
| `emit_memory_store_warning_if_needed(...)` | émet le warning via le logger si la condition est vraie |

## 3. Contextes d'utilisation

- **Démarrage en prod** : alerter d'un store mémoire et orienter vers un backend persistant.

## 4. Voir aussi

- [Les backends de session (core/sessions)](../core-sessions/manager.md).
- [Le serveur de dev](dev_server.md) : les autres gardes de démarrage.
