# L'audit Auth/User dans Forge

Ce document décrit la journalisation des événements d'authentification.

Le fichier de code correspondant est `core/auth/audit.py`.

## 1. À quoi sert ce module ?

Forge **fournit le vocabulaire et l'émission** des événements d'audit auth (login, échec, changement de mot de passe…) ; la **persistance** est à la charge de l'application (ADR-008).
Les valeurs sensibles sont masquées avant journalisation.

## 2. L'API

| Élément | Rôle |
|---|---|
| `AuthAuditEvent` | événement d'audit lisible et stockable |
| `create_auth_audit_event(...)` | construit un événement sans effet de bord |
| `log_auth_event(...)` | journalise via le logger `forge.auth.audit` |
| `safe_log_auth_event(...)` | journalise sans jamais propager d'exception |
| `sanitize_auth_audit_metadata(metadata)` | retire les clés sensibles connues |
| `validate_auth_audit_event_contract` / `normalize_auth_audit_event` / `is_valid_auth_audit_event` | contrat |
| `get_audit_failure_count` / `reset_audit_failure_count` | compteur d'échecs (tests) |

## 3. Le périmètre

Forge fournit le **logging** ; persister les audits (table, rétention) appartient à l'application. Le vocabulaire d'audit (y compris les événements MFA) est assumé dans le cœur (ADR-011).

## 4. Contextes d'utilisation

- **Login** : `safe_log_auth_event("login.success"/"login.failed", ...)`.
- **Admin** : `user.disabled`, `user.password_changed`…

## 5. Voir aussi

- [La session Auth/User](session.md) et [le rate-limit](rate_limit.md).
