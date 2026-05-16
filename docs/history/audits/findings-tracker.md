# Tracker des constats d'audit Forge

**Ticket** : `AUDIT-FINDINGS-TRACKER-001`  
**Date de création** : 2026-05-15  
**Baseline** : `baseline/audit-2026-05-15`  
**Version de départ** : `1.0.0-beta.1`  
**Commit de départ** : `baba2f4`

---

## Audits de référence

| Audit | Fichier | Version auditée | Date |
|---|---|---|---|
| Audit complet Claude | [`audit-claude.md`](audit-claude.md) | Forge 2.0.0 (commit `435ffa9`) | 2026-05-09 |
| Audit renforcé 3.0.2 | [`audit-renforce-3.0.2-001.md`](audit-renforce-3.0.2-001.md) | Forge 3.0.2 (tag `v3.0.2`) | 2026-05-13 |

---

## Règle de mise à jour

Un constat ne passe à **FERMÉ** que si le ticket de correction correspondant est
livré, validé, documenté et **accepté administrativement**.

Un constat **REPORTÉ** signifie que la correction est repoussée à une phase
ultérieure avec une raison documentée.

Un constat **HORS PÉRIMÈTRE** signifie que Forge ne prend pas en charge cette
correction dans son périmètre déclaré.

Tant qu'aucun ticket de correction post-audit n'a été accepté,
**aucun constat ne peut passer à FERMÉ**.

---

## Constats — Documentation publique

| ID | Domaine | Constat | Gravité | Statut | Ticket cible | Notes |
|---|---|---|---|---|---|---|
| FND-DOC-001 | Documentation | Imports MFA/RBAC documentés depuis `core.auth` échouent en runtime (8 cas) : `from core.auth import is_mfa_enabled`, `require_user_permission`, etc. | IMPORTANT | OUVERT | DOCS-OPTIN-INSTALL-CONTRACT-001 | §2 audit renforcé, groupes A+B. Partiellement traité (DOCS-OPTIN-INSTALL-CONTRACT-001) : commandes d'installation corrigées + contrat opt-in documenté. Reste : corriger les exemples d'imports `from core.auth import ...` qui devraient pointer vers `forge_mvc_mfa.auth` et `forge_mvc_rbac` |
| FND-DOC-002 | Documentation | API FR obsolète dans docs actives : `authentifier_session`, `creer_session` dans `docs/security.md` et `docs/rbac.md` | IMPORTANT | OUVERT | À définir | §2 audit renforcé, groupe C |
| FND-DOC-003 | Documentation | Python 3.11 mentionné dans 10 fichiers de guides alors que ADR-006 impose Python 3.12+ | MINEUR | OUVERT | À définir | §3 audit renforcé. Fichiers : `docs/15-minutes.md`, `docs/deployment.md`, 8 autres |
| FND-DOC-004 | Documentation | Références `v3.0.1` dans guides d'installation principaux (3 occurrences : `git clone --branch v3.0.1`) | IMPORTANT | FERMÉ | VERSION-COHERENCE-1.0-001 + ROADMAP-PUBLIC-VERSION-CLEANUP-001 | §3 audit renforcé. Les occurrences `v3.0.1` remplacées par `{{forge_tag}}`. Mentions `3.1+`, `3.1.0`, `Forge 3.x` dans docs actives corrigées vers `1.0.x`. Roadmap active nettoyée (Phase 14 marquée terminée, trajectoire 1.0.0-beta.x ajoutée, "au-delà de 3.0" corrigé). Constat fermé — 2026-05-15. |

---

## Constats — Tests

| ID | Domaine | Constat | Gravité | Statut | Ticket cible | Notes |
|---|---|---|---|---|---|---|
| FND-TESTS-001 | Tests | `pytest` en environnement core-only produit 30 erreurs de collecte (exit 2) — tests opt-in importent sans `pytest.importorskip` | IMPORTANT | OUVERT | À définir | §1 audit renforcé. PYTEST-CORE-ONLY-CONTRACT-CLARIFY-001 a documenté la distinction sans corriger les fichiers tests |
| FND-TESTS-002 | Tests | Angle mort : `test_docs_no_phantom_modules_001.py` ne détecte pas les symboles obsolètes dans les modules réels | MINEUR | OUVERT | À définir | §4 audit renforcé. Test à créer : `tests/meta/test_docs_imports_executable_001.py` |
| FND-TESTS-003 | Tests | Absence de tests d'intégration HTTP end-to-end (démarrage serveur + requêtes HTTP réelles via `requests`) | MINEUR | OUVERT | À définir | §7.2 audit Claude. Les tests E2E-CLI-001 existants sont CLI-level, non HTTP-level |

---

## Constats — Packaging / PyPI

| ID | Domaine | Constat | Gravité | Statut | Ticket cible | Notes |
|---|---|---|---|---|---|---|
| FND-PKG-001 | Packaging | Paquets opt-in (`forge-mvc-mfa`, `-rbac`, `-workflow`, `-stats`) non publiés sur PyPI — source-only via GitHub | INFO | FERMÉ | `OPTIN-PACKAGES-PUBLICATION-POLICY-001` | Politique de publication documentée dans `docs/release-policy.md`. rbac/workflow/stats publiables à beta.5 (publication coordonnée). forge-mvc-mfa non publié en série 1.0 (Pre-Alpha, SEC-MFA-SECRET-ENCRYPTION-001 requis). |

---

## Constats — Sécurité

| ID | Domaine | Constat | Gravité | Statut | Ticket cible | Notes |
|---|---|---|---|---|---|---|
| FND-SEC-001 | Sécurité | PBKDF2 : `hacher_mot_de_passe` avec 260K itérations (< OWASP 600K min) — utilisé dans auth controller par défaut et générateur suivi-comportement | CRITIQUE | OUVERT | À définir | §5.2 audit Claude |
| FND-SEC-002 | Sécurité | Incohérence Argon2 (CLI `forge auth:user:create`) vs PBKDF2 (auth controller par défaut) — connexion impossible sans erreur explicite | CRITIQUE | OUVERT | À définir | §5.3 audit Claude |
| FND-SEC-003 | Sécurité | Hashes PBKDF2 existants en base de données non encore migrés vers Argon2 | IMPORTANT | REPORTÉ | À définir | REPORTÉ : migration des hashes existants ne peut pas se faire sans accès à chaque connexion utilisateur — correction différée à une phase ultérieure, après fermeture de FND-SEC-001 et FND-SEC-002 |
| FND-SEC-004 | Sécurité | Configuration TLS dans `app.py` sans `minimum_version` ni `set_ciphers` explicites | MINEUR | OUVERT | À définir | §5.6 audit Claude. Le README documente que la prod utilise Nginx pour TLS |
| FND-SEC-005 | Sécurité | CSP sans mécanisme de nonce — cassera avec HTMX hyperscript ou Alpine inline | MINEUR | OUVERT | À définir | §5.7 audit Claude |

---

## Constats — Auth

| ID | Domaine | Constat | Gravité | Statut | Ticket cible | Notes |
|---|---|---|---|---|---|---|
| FND-AUTH-001 | Auth | Double pile auth `core/security/` (legacy FR) vs `core/auth/` (moderne EN) — API dupliquée, fallback explicite entre les deux | IMPORTANT | FERMÉ | AUTH-SESSION-COMPATIBILITY-BRIDGE-001 | §4.2.1 audit Claude. Décision canonique actée (ADR-010). Pont bidirectionnel livré par AUTH-SESSION-COMPATIBILITY-BRIDGE-001 : get_authenticated_user_id reconnaît les sessions legacy ; is_authenticated legacy reconnaît les sessions canoniques. Aucune pollution de session. Constat fermé — 2026-05-16. |
| FND-AUTH-002 | Auth | Doublons API : `login_required` vs `require_auth`, deux implémentations RBAC | MINEUR | FERMÉ | AUTH-SESSION-LEGACY-DEPRECATION-001 | §6.4 audit Claude. (1) Incompatibilité legacy/canonique : **résolu** — le pont 4.2b garantit que require_auth reconnaît les sessions canoniques et login_required reconnaît les sessions legacy. (2) API legacy encore présente : **dépréciée** — authenticate_session, is_authenticated, get_user, create_session émettent un DeprecationWarning depuis AUTH-SESSION-LEGACY-DEPRECATION-001. Migration des usages applicatifs : ticket 4.4 (STARTER-AUTH-MODERNIZE-001). Constat fermé — 2026-05-16. |

---

## Constats — CRUD

| ID | Domaine | Constat | Gravité | Statut | Ticket cible | Notes |
|---|---|---|---|---|---|---|
| FND-CRUD-001 | CRUD | Générateur CRUD : colonnes de filtres concaténées sans whitelist — risque injection SQL si `filters` provient de `request.params` sans validation | IMPORTANT | OUVERT | À définir | §5.4 audit Claude. Valeurs paramétrisées (correct), noms de colonnes non validés (manquant). `_ALLOWED_SORT` existe mais pas `_ALLOWED_FILTERS` |

---

## Constats — Sessions

| ID | Domaine | Constat | Gravité | Statut | Ticket cible | Notes |
|---|---|---|---|---|---|---|
| FND-SESSION-001 | Sessions | Sessions in-memory bloquantes en production multi-process — sessions non partagées entre workers | IMPORTANT | FERMÉ | SESSIONS-CONFIGURABLE-STORE-001 | Store configurable livré par SESSIONS-CONFIGURABLE-STORE-001 ; contrat des stores documenté par SESSIONS-STORE-CONTRACT-DOC-001 ; limites thread-safety de MemorySessionStore documentées par SESSIONS-MEMORY-THREADSAFE-DOC-001. Constat fermé — 2026-05-16. |

---

## Constats — Modules

| ID | Domaine | Constat | Gravité | Statut | Ticket cible | Notes |
|---|---|---|---|---|---|---|
| FND-MODULE-001 | Modules | Modules monolithiques : `core/auth/oidc.py` 1011 LOC, `core/auth/mfa.py` 799 LOC | MINEUR | OUVERT | À définir | §4.2.3 audit Claude |
| FND-MODULE-002 | Modules | Injection de routes modules via écriture dans `mvc/routes.py` — violation du principe §9 | IMPORTANT | FERMÉ | MODULE-ROUTES-INJECTION-REMOVE-001 + MODULE-ROUTES-EXPLICIT-DOC-001 | §7.3 audit Claude. `prepare_module_route_injection()` supprimée. `_build_injection_block`, `_module_marker` supprimés. `generate_module_routes()` est le seul mécanisme (explicite). Contrat explicite documenté dans `docs/module-author-guide.md` et `docs/reference/modules.md`. Constat fermé — 2026-05-16. |

---

## Constats — CLI

| ID | Domaine | Constat | Gravité | Statut | Ticket cible | Notes |
|---|---|---|---|---|---|---|
| FND-CLI-001 | CLI | 5 commandes absentes de `forge --help` : `sync:landing`, `docs:pdf`, `i18n:init`, `i18n:check`, `mail:render` | INFO | OUVERT | À définir | §5 audit renforcé. Situation stable — certaines expérimentales, d'autres internes. À trancher : documenter ou retirer |

---

## Récapitulatif

| Statut | Nombre |
|---|---|
| **OUVERT** | 15 |
| **REPORTÉ** | 1 |
| **HORS PÉRIMÈTRE** | 0 |
| **FERMÉ** | 3 |
| **Total** | 19 |

---

## Limites de ce document

- Ce document **ne corrige aucun constat** — il les recense et les suit.
- Aucun constat n'est FERMÉ : aucun ticket de correction post-audit n'a encore été livré et accepté.
- Les tickets cibles "À définir" seront précisés lors des phases de correction post-audit.
- Le seul constat REPORTÉ (FND-SEC-003) est justifié dans la colonne Notes.
- Ce tracker est le document vivant de la Phase 0 de consolidation post-audits.
