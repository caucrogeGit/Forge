# Forge — Roadmap POST-2.0 Consolidation

## Objectif

Consolider Forge 2.0.0 après publication GitHub afin de corriger les incohérences critiques, clarifier les limites production, réduire la dette legacy et préparer une base plus durable avant tout nouvel élargissement fonctionnel.

## Phase 1 — Corrections critiques — ✅ Forge 2.0.1 (2026-05-09)

- [x] AUTH-DEFAULT-ALIGN-001 — Aligner l’authentification par défaut sur `core.auth` / Argon2id.
- [x] AUTH-CLI-LOGIN-E2E-TEST-001 — Test de non-régression CLI Auth → login.
- [x] STARTERS-AUTH-AUDIT-001 — Audit et alignement Auth des starters.
- [x] CRUD-FILTER-WHITELIST-001 — Whitelister les clés de filtres dans le CRUD généré.
- [x] SECURITY-PBKDF2-HARDENING-001 — Durcir PBKDF2 legacy (600 000 itérations, format versionné).
- [x] AUTH-HASH-MIGRATION-001 — Migration PBKDF2 → Argon2id après login réussi.
- [x] DEPLOY-SESSION-LIMITS-001 — Documenter explicitement les limites des sessions mémoire en production.
- [x] ADR-001 / ADR-002 — Formaliser les décisions Auth et Session.

## Phase 2 — Cohérence documentaire Forge 2.0

- [x] POST-2.0-DOC-CLEANUP-001 — Corriger les incohérences de version, README, Auth, roadmap et legacy.
- [x] POST-2.0-ROADMAP-RESTRUCTURE-001 — Restructurer la roadmap active post-2.0 et archiver l’historique.

## Phase 3 — Nettoyage legacy

- [x] CMD-LEGACY-REMOVE-001 — Suppression définitive du dossier `cmd/` (fait en Forge 2.10.0).
- [ ] AUTH-LEGACY-BOUNDARY-001 — Documenter la frontière entre `core.security` et `core.auth`.

## Phase 4 — Maintenabilité

- [ ] CRUD-GENERATOR-SPLIT-001 — Découper `make_crud.py` sans changement fonctionnel.
- [ ] OIDC-MODULE-SPLIT-001 — Découper `core/auth/oidc.py` sans changement d’API.
- [ ] MFA-MODULE-SPLIT-001 — Découper `core/auth/mfa.py` sans changement d’API.

## Phase 5 — Hygiène qualité

- [ ] I18N-CACHE-001 — Ajouter un cache au chargement des catalogues de traduction.
- [ ] QUALITY-RUFF-001 — Ajouter Ruff en mode non destructif.
- [ ] QUALITY-TYPING-BASELINE-001 — Préparer un typage statique progressif.

## Phase 6 — Production légère

- [ ] SESSION-STORE-CONTRACT-001 — Créer un contrat de backend de session.
- [ ] SESSION-FILE-STORE-001 — Ajouter un backend de session fichier.
- [ ] SESSION-MARIADB-STORE-001 — Ajouter un backend de session MariaDB.
- [ ] SECURITY-CSP-NONCE-001 — Ajouter un mécanisme optionnel de nonce CSP.
- [ ] SECURITY-TLS-DEFAULTS-001 — Rendre la configuration TLS dev plus explicite.

## Phase 7 — Modules et profils

- [ ] MODULE-LIFECYCLE-001 — Documenter les limites du cycle de vie des modules.
- [ ] MODULE-REMOVE-001 — Ajouter une désinstallation contrôlée de module.
- [ ] MODULE-UPDATE-001 — Ajouter une mise à jour contrôlée de module.
- [ ] PROFILE-DIFFERENTIATION-001 — Rendre les profils projet réellement différenciés.

## Phase 8 — Sécurité projet public

- [x] SECURITY-MD-001 — Ajouter une politique de sécurité.
- [x] DEPENDENCY-SCAN-001 — Ajouter un contrôle de dépendances.
- [x] RELEASE-CHECKLIST-001 — Documenter la procédure de release.

## Phase 9 — Tests d’intégration

- [ ] HTTP-E2E-TESTS-001 — Ajouter des tests HTTP réels.
- [ ] CONCURRENCY-SESSION-TESTS-001 — Ajouter des tests de concurrence simples sur les sessions.

## Phase 10 — Observabilité légère

- [ ] HEALTH-ENDPOINT-001 — Ajouter un endpoint `/health`.
- [ ] LOGGING-STRUCTURE-001 — Clarifier la structure des logs.
- [ ] METRICS-BASIC-001 — Préparer des métriques simples.