# Historique roadmap Forge — phases 7 à 10

> Note : ce document conserve le journal d'avancement des phases 7 à 10 (Forge 1.5.0 → 2.0.0). Il décrit l'état du projet au moment de sa rédaction. Les compteurs de tests, versions et chemins peuvent avoir évolué depuis.

---

## Phase 7 — Workflow, statistiques et modules

Phase pleinement close. Audits de durcissement `MODULE-ROUTES-RUNTIME-AUDIT-001` et `MODULE-FILES-SECURITY-001` terminés. Tickets `DOC-VERSION-CONSISTENCY-001`, `DOC-DEPENDENCIES-001` et `DOC-LICENSE-CONSISTENCY-001` terminés. Consolidation documentaire close.

---

## Phase 8 — Starter Communes & Séjours

Phase terminée. Tous les tickets `STARTER-CS-*` livrés.

---

## Phase 9 — Profils de projet

Phase terminée. Forge dispose maintenant de profils officiels, d'une option `--profile` dans `forge new`, d'un fichier `forge_profile.txt` dans les projets générés, de tests de génération par profil et d'une documentation consolidée.

---

## Phase 9.1 — Modernisation des starters historiques

Phase terminée :

- `STARTER-LEGACY-AUDIT-001` — statuts des starters 1 à 4 décidés (1 et 3 officiels, 2 à moderniser, 4 démonstrateur historique).
- `STARTER-LEGACY-DECISION-001` — décisions prises.
- `STARTER-PROFILES-001` — relation profils / starters documentée dans `docs/profiles.md`.
- `STARTER-CS-REPLACE-001` — Communes & Séjours devient le démonstrateur avancé principal.
- `ROADMAP-STARTER-MODERNIZATION-001` — Phase 9.1 insérée.
- `STARTER-MODERNIZATION-PLAN-001` — plan dans `docs/audits/starter-modernization-plan-001.md`.
- `DOC-STARTERS-STRUCTURE-001` / `DOC-STARTERS-STRUCTURE-002` — documentation réorganisée dans `docs/starters/`.
- `STARTER-AUTH-MODERNIZE-001` — starter Utilisateurs/Auth modernisé vers `core.auth`.
- `STARTER-CONTACTS-REFRESH-001` — starter Contacts rafraîchi.
- `STARTER-CARNET-REFRESH-001` — starter Carnet rafraîchi.
- `STARTER-SUIVI-LEGACY-001` — starter Suivi marqué historique/legacy.
- `STARTER-DOC-INDEX-001` — index des starters avec statuts et usages.

---

## Phase 9.5 — Consolidation Forge avant publication

Phase terminée. 9 audits de consolidation réalisés, 0 incohérence bloquante :

- `CONSOLIDATION-001` — audit global architecture.
- `CONSOLIDATION-CLI-001` — audit CLI.
- `CONSOLIDATION-DOC-001` — audit documentation.
- `CONSOLIDATION-TESTS-001` — audit tests.
- `CONSOLIDATION-NON-OVERWRITE-001` — préservation code utilisateur validée.
- `CONSOLIDATION-MODULES-001` — cycle modules validé.
- `CONSOLIDATION-PROFILES-001` — profils cohérents.
- `CONSOLIDATION-FRONT-001` — Tailwind / HTMX / Alpine / templates validés.
- `CONSOLIDATION-STARTER-001` — Communes & Séjours démontre Forge sans polluer le core.
- `CONSOLIDATION-ROADMAP-001` — Phase 9.5 close.

---

## Phase 10 — Publication Forge 2.0

Phase terminée :

- `PUBLICATION-2.0-PREP-001` — dépôt prêt.
- `PUBLICATION-2.0-VERSION-001` — version 2.0.0 verrouillée.
- `PUBLICATION-2.0-BUILD-001` — wheel `forge_mvc-2.0.0-py3-none-any.whl` construit.
- `PUBLICATION-2.0-TAG-001` — tag `v2.0.0` créé et poussé.
- `PUBLICATION-2.0-RELEASE-001` — release GitHub publiée.
- `PUBLICATION-2.0-POST-RELEASE-001` — documentation post-release alignée.

Release GitHub : https://github.com/caucrogeGit/Forge/releases/tag/v2.0.0

---

## Post-release — Phase 1 consolidation (Forge 2.0.1)

Phase terminée — livrée dans Forge v2.0.1 (2026-05-09) :

- `AUTH-DEFAULT-ALIGN-001` — authentification par défaut alignée sur Argon2id.
- `AUTH-CLI-LOGIN-E2E-TEST-001` — test CLI Auth → login.
- `STARTERS-AUTH-AUDIT-001` — audit Auth des starters.
- `CRUD-FILTER-WHITELIST-001` — whitelist filtres CRUD.
- `SECURITY-PBKDF2-HARDENING-001` — PBKDF2 legacy durci.
- `AUTH-HASH-MIGRATION-001` — migration PBKDF2 → Argon2id.
- `DEPLOY-SESSION-LIMITS-001` — limites sessions documentées.
- `ADR-001` / `ADR-002` — décisions Auth et Session formalisées.

Release GitHub : https://github.com/caucrogeGit/Forge/releases/tag/v2.0.1
