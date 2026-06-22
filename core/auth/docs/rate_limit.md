# Le rate-limit Auth dans Forge

Ce document décrit la protection anti-bruteforce des actions sensibles.

Le fichier de code correspondant est `core/auth/rate_limit.py`.

## 1. À quoi sert ce module ?

Pour freiner le bruteforce (login, reset…), Forge limite le nombre de tentatives par clé (IP, email) sur une fenêtre glissante, en mémoire.

## 2. L'API courante

| Fonction | Rôle |
|---|---|
| `record_login_attempt(ip)` | enregistre une tentative de connexion échouée |
| `is_login_rate_limited(ip)` | `True` si l'IP a atteint la limite |
| `record_attempt(action, key)` | enregistre une tentative pour une action quelconque |
| `is_locked_out(action, key, ...)` | `True` si la clé a dépassé le seuil |
| `clear_attempts(action, key)` | efface les tentatives d'une clé |
| `check_auth_rate_limit(...)` | calcule la décision (autorisé/bloqué) |

## 3. Le contrat et les modèles

`AuthRateLimitAttempt`, `AuthRateLimitRule`, `AuthRateLimitDecision` modélisent tentative, règle et décision ; les fonctions `validate_*` / `normalize_*` / `is_valid_*` valident ces contrats.
Le compteur est **en mémoire processus** (perdu au redémarrage, non partagé entre workers).

## 4. Contextes d'utilisation

- **Login** : `is_login_rate_limited` en garde, `record_login_attempt` sur échec.
- **Actions sensibles** : `record_attempt` / `is_locked_out` par action.

## 5. Voir aussi

- [La session Auth/User](session.md) et [l'audit](audit.md).
