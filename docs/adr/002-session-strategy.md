# ADR-002 — Stratégie de session Forge 2.x

!!! warning "ADR historique — Forge 2.x"

    Cet ADR documente la stratégie de session telle qu'elle a été décidée
    pour Forge 2.x. Son contenu est conservé pour trace décisionnelle et n'est
    **pas** mis à jour pour refléter l'état actuel de Forge 3.0.

    Pour l'état actuel, consulter :

    - [`docs/auth.md`](../auth.md) — documentation utilisateur d'authentification
    - [ADR-004 — Périmètre du noyau](004-core-perimeter.md) — séparation core/modules opt-in

## Statut

Acceptée (Forge 2.x — historique)

---

## Contexte

Forge 2.0 stocke les sessions utilisateur dans un dictionnaire Python en mémoire processus
(`_sessions: dict = {}` dans `core/security/session.py`), protégé par un `threading.RLock`.

Ce choix est explicitement assumé dans le code source :

> *« Adapté au développement, à la pédagogie et aux petites applications mono-processus.
> Limites assumées : sessions perdues au redémarrage, pas de partage entre workers,
> pas de scaling horizontal. »*

Les deux piles de session — legacy (`core.security.session`) et moderne
(`core.auth.session`) — partagent ce même backend mémoire. `core/auth/session.py`
délègue la résolution de session à `core.security.session.get_session()` quand l'objet
`request` ne porte pas directement un dict de session.

En résumé : mono-processus est le mode supporté en Forge 2.x ; les autres modes nécessitent un backend de session partagé non encore implémenté.

Caractéristiques techniques actuelles :

| Paramètre | Valeur |
|---|---|
| Backend | Dict Python en mémoire (`_sessions`) |
| Isolation | Processus unique, thread-safe (`threading.RLock`) |
| TTL par défaut | 3 600 secondes (1 heure) |
| Nettoyage | Passif, à chaque création de session |
| Session ID | `secrets.token_hex(32)` (64 caractères hex) |
| Cookie | `session_id=<hex>` (HTTP, HttpOnly recommandé) |
| Flash messages | Stockés dans le même dict de session |

---

## Décision

**1. Forge 2.x utilise des sessions mémoire par défaut.**

Le backend actuel (`_sessions` dict + `RLock`) est le seul backend de session de
Forge 2.x. Il n'est pas remplacé ni enrichi dans ce ticket.

**2. Le mode officiellement supporté est mono-processus.**

Forge 2.x est conçu et documenté pour fonctionner avec un seul processus Python. Ce
choix est cohérent avec les usages cibles : développement local, pédagogie, applications
légères, production mono-processus derrière Nginx.

**3. Le déploiement derrière Nginx est supporté si Forge tourne avec un seul processus.**

La configuration documentée (`systemd` + Nginx reverse proxy + un processus Python)
est le mode de production officiel Forge 2.x. Les sessions sont persistantes tant que
le processus ne redémarre pas.

**4. Le multi-worker n'est pas supporté sans backend de session partagé.**

Lancer Forge avec plusieurs workers (Gunicorn, uWSGI, ou `--workers > 1`) crée des dicts
`_sessions` indépendants par processus. Les sessions ne sont pas partagées entre workers.
Ce mode n'est pas documenté ni recommandé en Forge 2.x.

**5. Le scaling horizontal n'est pas supporté sans backend de session partagé.**

Plusieurs instances Forge derrière un load balancer ne partagent pas leurs sessions.
Ce mode n'est pas supporté en Forge 2.x sans solution tierce (Redis, etc.).

**6. Les sessions ne sont pas garanties après redémarrage avec le backend mémoire.**

Un redémarrage du processus Forge (mise à jour, crash, `systemctl restart`) invalide
toutes les sessions actives. Les utilisateurs connectés sont déconnectés.

**7. Un contrat de backend de session a été introduit dans `SESSION-STORE-CONTRACT-001`.**

Le package `core/sessions/` expose :
- `SessionStore` — Protocol complet (`create`, `get`, `set`, `delete`, `regenerate`, `authenticate`, `touch_expiry`, `set_flash`, `get_flash`)
- `MemorySessionStore` — implémentation par défaut (dict Python + RLock, comportement inchangé)
- `get_session_store()` — retourne le store actif

`core/security/session.py` délègue toutes ses opérations au store via son API publique.
Les alias `_sessions` et `_lock` ont été supprimés dans `SESSIONS-CONTRACT-001` — le code
client ne doit pas accéder aux internals du store.

**10. Les trois backends sont effectivement supportés — `SESSIONS-CONTRACT-001`.**

Le ticket `SESSIONS-CONTRACT-001` a étendu le contrat `SessionStore` et réécrit
`core/security/session.py` pour ne plus toucher à `_store._sessions` ni `_store._lock`.
Toutes les opérations passent par des méthodes publiques du store :

- `authentifier_session` → `_store.authenticate()` (rotation atomique)
- `est_authentifie` → `_store.get()` + `_store.touch_expiry()` (sans accès dict interne)
- `set_flash` → `_store.set_flash()` (atomique)
- `get_flash` → `_store.get_flash()` (lit et supprime atomiquement)

Les trois backends (`MemorySessionStore`, `FileSessionStore`, `MariaDbSessionStore`)
implémentent le contrat complet et sont couverts par un test d'intégration paramétré
(`tests/test_sessions_contract_integration_001.py`).

**Correction apportée dans MFA-SESSION-PERSISTENCE-001 :** `core/auth/mfa.py`
utilisait des mutations en place sur le dict retourné par `get_session()`. Ce patron
fonctionnait avec `MemorySessionStore` (référence live) mais était silencieusement
perdu avec `FileSessionStore` et `MariaDbSessionStore` (copie désérialisée). Les
quatre fonctions de mutation MFA (`start_mfa_challenge`, `clear_mfa_challenge`,
`mark_mfa_revalidated`, `clear_mfa_revalidation`) ont été réécrites pour utiliser
un helper interne `_persist_session_changes` basé sur read-modify-write via
`store.replace()`. La méthode `replace()` a été ajoutée au contrat `SessionStore`
et aux trois backends. Cette limite est levée.

**8. Le backend fichier a été introduit dans `SESSION-FILE-STORE-001`.**

`FileSessionStore` stocke chaque session dans un fichier JSON sous `storage/sessions/`.
Persiste les sessions entre redémarrages du processus Forge, sans dépendance externe.
Ne supporte pas le multi-worker concurrent. Disponible dans `core/sessions/file_store.py`.

**9. Le backend MariaDB a été introduit dans `SESSION-MARIADB-STORE-001`.**

`MariaDbSessionStore` stocke les sessions dans la table `forge_sessions` (voir
`mvc/models/sql/forge_sessions.sql`). Les données sont sérialisées en JSON dans
un champ `LONGTEXT`. Le backend partage les sessions entre processus Forge sur
la même base MariaDB. Il doit être configuré explicitement ; le backend par défaut
reste `MemorySessionStore`. Ne prétend pas résoudre automatiquement le scaling
horizontal complet.

---

## Conséquences

- Tout projet Forge 2.x en production mono-processus fonctionne sans modification.
- Les sessions sont perdues à chaque redémarrage du service ; c'est un comportement
  documenté et attendu, pas un bug.
- Les projets nécessitant la haute disponibilité ou le scaling horizontal doivent attendre
  Forge 2.1 ou 2.2 (ticket `SESSION-STORE-CONTRACT-001`).
- La documentation de déploiement doit mentionner explicitement la limite des sessions
  mémoire (ticket `DEPLOY-SESSION-LIMITS-001`).

---

## Mode supporté en Forge 2.x

| Mode | Statut Forge 2.x | Commentaire |
|---|---|---|
| Développement local mono-processus | **Supporté** | Cas standard, toutes fonctionnalités disponibles |
| Production mono-processus derrière Nginx | **Supporté avec limites** | Sessions perdues au redémarrage du service |
| Threads multiples (un seul processus) | **Supporté** | `threading.RLock` garantit la cohérence |
| Multi-worker local (fork, spawn) | **Non supporté par défaut** | Dicts `_sessions` distincts par processus |
| Gunicorn / uWSGI multi-worker | **Non supporté par défaut** | Backend partagé requis |
| Plusieurs instances derrière load balancer | **Non supporté par défaut** | Backend partagé requis |
| Backend fichier mono-machine | **Disponible** | `FileSessionStore` — persistance locale, pas de multi-worker concurrent |
| Backend MariaDB partagé | **Disponible** | `MariaDbSessionStore` — sessions partagées entre processus Forge |

---

## Backends disponibles et prévus

| Ticket | Backend | Résout | Statut |
|---|---|---|---|
| `SESSION-STORE-CONTRACT-001` | Contrat abstrait (`SessionStore` Protocol) | Interface commune | ✅ terminé |
| `SESSION-FILE-STORE-001` | Fichier JSON (`FileSessionStore`) | Persistance après redémarrage, mono-machine | ✅ terminé |
| `SESSION-MARIADB-STORE-001` | Table MariaDB (`MariaDbSessionStore`) | Persistance, sessions partagées entre processus | ✅ terminé |

Redis n'est pas prévu dans la roadmap Forge 2.x. Les projets qui en ont besoin peuvent
implémenter leur propre backend une fois le contrat défini.

---

## Ce que cette ADR ne fait pas

- Ne modifie pas `core/auth/session.py`.
- N'ajoute pas de backend fichier.
- N'ajoute pas de backend MariaDB.
- N'ajoute pas Redis.
- N'ajoute pas de warning runtime pour le multi-worker.
- Ne bloque pas le démarrage multi-process (Forge démarre normalement, les sessions
  seront simplement non partagées).
- Ne modifie pas les cookies de session.
- Ne modifie pas les tests fonctionnels de session.
- Ne refond pas la documentation de déploiement complète.

---

## Tickets dépendants

| Ticket | Sujet | Relation |
|---|---|---|
| `DEPLOY-SESSION-LIMITS-001` | Documenter les limites des sessions mémoire dans le guide de déploiement | dépend directement de cette ADR |
| `SESSION-STORE-CONTRACT-001` | Définir le contrat d'interface d'un backend de session pluggable | prérequis pour FILE et MARIADB |
| `SESSION-FILE-STORE-001` | Implémenter un backend fichier | dépend de `SESSION-STORE-CONTRACT-001` |
| `SESSION-MARIADB-STORE-001` | Implémenter un backend MariaDB | dépend de `SESSION-STORE-CONTRACT-001` |
| `CONCURRENCY-SESSION-TESTS-001` | Tests de non-partage inter-processus | vérification du comportement documenté |
| `HTTP-E2E-TESTS-001` | Tests E2E du cycle login / session / logout | validation end-to-end du backend mémoire |
