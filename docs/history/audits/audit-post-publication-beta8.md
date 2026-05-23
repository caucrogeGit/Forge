# Audit post-publication — Forge 1.0.0-beta.8

**Ticket** : `BETA9-AUDIT-PLAN-001`
**Date** : 2026-05-22
**Version auditée** : `1.0.0-beta.8` (tag `v1.0.0-beta.8`)
**Branche** : `main`
**Commit** : `73d5df1`

---

## Périmètre

Audit complet conduit après la publication PyPI complète de `1.0.0-beta.8`
(core + 5 opt-ins : stats, rbac, workflow, media, mfa).

Double source :

- audit automatisé par agent Claude (Sonnet 4.6) — architecture, sécurité, tests, packaging
- session de publication Claude Code — constats terrain lors des publications opt-in

---

## Constats par domaine

### 1. Sécurité

| Réf | Constat | Sévérité |
|---|---|---|
| S-1 | `cryptography>=42,<46` dans `forge-mvc-mfa` : vulnérabilités connues dans les versions < 46.0.7 | **Haute** |
| S-2 | `core/security/api_auth.py` : comparaison de token par `==` au lieu de `hmac.compare_digest` — timing attack | **Haute** |
| S-3 | Absence de helper `set_session_cookie()` : les starters posent le cookie `session_id` sans le préfixe `__Host-` | **Moyenne** |
| S-4 | Starters générés : cookie de session sans `Secure`, `HttpOnly`, `SameSite=Strict` systématiques | **Moyenne** |

### 2. HTTP / Réseau

| Réf | Constat | Sévérité |
|---|---|---|
| N-1 | `core/http/request.py` : `REMOTE_ADDR` utilisé directement — IP réelle perdue derrière un reverse proxy (`X-Real-IP` non lu) | **Moyenne** |
| N-2 | ThreadingHTTPServer (stdlib) : pas de WSGI/ASGI — incompatible Gunicorn/uWSGI sans entrypoint dédié | **Haute** |

### 3. Sessions / Authentification

| Réf | Constat | Sévérité |
|---|---|---|
| A-1 | Rate limiting en mémoire de processus : inutile en multi-workers — aucun avertissement au démarrage | **Moyenne** |
| A-2 | `MemorySessionStore` : sessions non nettoyées automatiquement — leak mémoire en longue durée | **Basse** |
| A-3 | `core/security/session.py` : noms ou conventions métier francophones encore présents dans le core, à dédomainiser conformément à l'ADR-003 | **Basse** |

### 4. Packaging / CI

| Réf | Constat | Sévérité |
|---|---|---|
| P-1 | `forge-mvc-media` absent de la matrice CI — régression silencieuse possible | **Moyenne** |
| P-2 | `package-lock.json` : version `3.0.0` vs `package.json` `1.0.0-beta.8` — désynchronisation | **Basse** |

### 5. Documentation

| Réf | Constat | Sévérité |
|---|---|---|
| D-1 | Roadmap active : anciennes références beta.4 / 3.0.x encore présentes dans des sections historiques ou actives à clarifier | **Basse** |
| D-2 | Docs actives contenant des références à `3.0.x` ou `beta.4` encore non mises à jour | **Basse** |
| D-3 | Limites de production (ThreadingHTTPServer, rate limiting mono-process) non documentées explicitement | **Moyenne** |

---

## Plan de correction — Phase B9 (beta.9)

14 tickets planifiés, classés par priorité décroissante :

| Ticket | Domaine | Priorité |
|---|---|---|
| SECURITY-CRYPTOGRAPHY-MFA-001 | Dépendance vulnérable | Haute |
| SECURITY-API-AUTH-COMPARE-DIGEST-001 | Timing attack | Haute |
| WSGI-ENTRYPOINT-001 | Déployabilité | Haute |
| SECURITY-SESSION-COOKIE-HELPER-001 | Sécurité cookie | Moyenne |
| SECURITY-SESSION-COOKIE-STARTERS-001 | Sécurité starters | Moyenne |
| HTTP-TRUSTED-PROXY-IP-001 | IP réelle | Moyenne |
| AUTH-RATE-LIMIT-PROD-WARNING-001 | Avertissement prod | Moyenne |
| DOCS-PRODUCTION-LIMITS-001 | Clarté prod | Moyenne |
| CI-OPTIN-MEDIA-BUILD-001 | CI media | Moyenne |
| SESSION-CLEANUP-AUTO-001 | Leak session | Basse |
| CORE-SESSION-DEDOMAIN-001 | Conformité ADR-003 | Basse |
| RELEASE-PACKAGE-LOCK-SYNC-001 | Cohérence packaging | Basse |
| DOCS-VERSION-SWEEP-BETA9-001 | Cohérence docs | Basse |
| RELEASE-BETA9-001 | Publication | — |

---

## État de référence à la date de l'audit

```
pytest       : 9 693 passed (core)
compileall   : OK
mkdocs build : OK
git diff --check : OK
PyPI core    : forge-mvc==1.0.0b8 — publié
PyPI opt-ins : forge-mvc-stats, rbac, workflow, media, mfa == 1.0.0b8 — publiés
```

---

## Limites de cet audit

- L'audit ne couvre pas le comportement sous Gunicorn / uWSGI (tests réels requis).
- Les starters n'ont pas été testés en déploiement production.
- La rotation de clé MFA (TOTP) reste hors périmètre.
