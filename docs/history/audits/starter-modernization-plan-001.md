# Plan STARTER-MODERNIZATION-PLAN-001 — Modernisation des starters historiques

## Objectif

Définir précisément quoi moderniser dans chaque starter historique Forge (1 à 4) avant de modifier leur code, en tenant compte de Forge actuel, des profils de projet et du statut de chaque starter décidé dans `STARTER-LEGACY-DECISION-001`.

Ce document est un **document de planification**. Il ne modifie aucun starter.

---

## Synthèse

| Starter | Statut décidé | Action Phase 9.1 | Ticket |
|---|---|---|---|
| 1 — Contacts | starter officiel simple | rafraîchissement léger | STARTER-CONTACTS-REFRESH-001 |
| 2 — Utilisateurs / Auth | à moderniser | modernisation prioritaire vers `core.auth` | STARTER-AUTH-MODERNIZE-001 |
| 3 — Carnet de contacts | starter officiel relationnel | rafraîchissement léger | STARTER-CARNET-REFRESH-001 |
| 4 — Suivi pédagogique | exemple pédagogique historique | clarification legacy | STARTER-SUIVI-LEGACY-001 |
| 5 — Communes & Séjours | démonstrateur avancé principal | ne pas modifier | — |

---

## Starter 1 — Contacts

**Statut :** starter officiel simple.

**Profil recommandé :** `minimal` ou `standard`.

**Décision :** rafraîchissement léger uniquement.

**À vérifier dans STARTER-CONTACTS-REFRESH-001 :**

- cohérence de la documentation avec les profils `minimal` / `standard` ;
- absence de complexité inutile (pas d'auth, pas de RBAC, pas de médias) ;
- conformité avec les conventions récentes de Forge ;
- non-écrasement des fichiers applicatifs utilisateur ;
- tests existants toujours verts.

**À ne pas faire :**

- ajouter Auth, RBAC, médias ou i18n obligatoire ;
- transformer en application avancée ;
- alourdir le starter de découverte.

---

## Starter 2 — Utilisateurs / Auth

**Statut :** conservé, à moderniser fortement.

**Profil recommandé :** `standard`.

**Décision :** modernisation prioritaire vers `core.auth`.

**Problème identifié (source : STARTER-LEGACY-AUDIT-001) :**

Le starter implémente son propre `auth_model.py` avec une table `utilisateur` (champs `Login`, `PasswordHash`, `Actif`) et utilise `core.security.hashing` / `core.security.session`. Ces deux approches coexistent dans Forge, mais la Phase 4.5 a livré `core.auth` comme brique standardisée :

- table `users` ;
- `current_user(request)` ;
- `is_authenticated(request)` ;
- `@login_required` ;
- hachage argon2 via `core.auth`.

**Ce que STARTER-AUTH-MODERNIZE-001 devra faire :**

- remplacer l'`auth_model.py` custom par les helpers `core.auth` ;
- remplacer la table `utilisateur` par la table `users` ou documenter la coexistence ;
- remplacer `core.security.hashing` / `core.security.session` par les briques Phase 4.5 ;
- documenter le flux Auth moderne minimal dans la page `starter-app-02` ;
- conserver la forme CRUD-light du starter (pas de MFA, pas d'OIDC).

**Résultat attendu :** le starter 2 devient l'exemple Auth moderne minimal, pas une vitrine Auth avancée complète.

**À ne pas faire dans STARTER-AUTH-MODERNIZE-001 :**

- migrer le starter maintenant (pas dans ce ticket de plan) ;
- ajouter MFA/OIDC/RBAC complet ;
- transformer le starter en application complète.

---

## Starter 3 — Carnet de contacts

**Statut :** starter officiel relationnel.

**Profil recommandé :** `standard`.

**Décision :** rafraîchissement léger comme exemple relationnel.

**À vérifier dans STARTER-CARNET-REFRESH-001 :**

- format `relations.json` toujours à jour avec les conventions Forge actuelles ;
- documentation cohérente avec profil `standard` ;
- tests existants toujours verts ;
- non-écrasement des fichiers applicatifs utilisateur ;
- compatibilité avec les conventions récentes.

**À ne pas faire :**

- ajouter Auth, médias ou pages publiques avancées ;
- transformer en Communes & Séjours bis ;
- alourdir le starter relationnel de découverte.

---

## Starter 4 — Suivi pédagogique

**Statut :** exemple pédagogique historique / legacy.

**Profil :** aucun profil officiel direct.

**Décision :** assumer le statut legacy sans modernisation lourde.

**Ce que STARTER-SUIVI-LEGACY-001 devra faire :**

- vérifier que la documentation ne présente plus le starter 4 comme vitrine principale (déjà en grande partie fait dans STARTER-LEGACY-DECISION-001 et STARTER-CS-REPLACE-001) ;
- ajouter ou consolider les mentions "démonstrateur historique" dans la page `starter-app-04` ;
- s'assurer que le starter reste générable et fonctionnel sans modification lourde ;
- ne pas le supprimer.

**À ne pas faire dans STARTER-SUIVI-LEGACY-001 :**

- modernisation Auth complète (même problème que starter 2, mais sans priorité immédiate) ;
- refonte métier ;
- transformation en starter officiel principal.

---

## Starter 5 — Communes & Séjours

**Statut :** démonstrateur avancé principal.

**Décision :** ne pas modifier dans la Phase 9.1.

Le starter 5 est la référence avancée déjà livrée. Il ne fait pas partie des starters à moderniser dans cette phase. Les tickets de modernisation des starters historiques (1 à 4) ne doivent pas le toucher.

---

## Ordre recommandé des tickets

| Ordre | Ticket | Justification |
|---|---|---|
| 1 | STARTER-AUTH-MODERNIZE-001 | Risque le plus fort : écart technique avec `core.auth` |
| 2 | STARTER-CONTACTS-REFRESH-001 | Starter officiel simple — rafraîchissement léger |
| 3 | STARTER-CARNET-REFRESH-001 | Starter officiel relationnel — rafraîchissement léger |
| 4 | STARTER-SUIVI-LEGACY-001 | Clarification documentaire du statut legacy |
| 5 | STARTER-DOC-INDEX-001 | Index des starters, statuts et usages recommandés |
| 6 | CONSOLIDATION-001 | Consolidation Forge — après la Phase 9.1 complète |

**Justification de l'ordre :**

Commencer par le risque le plus fort (starter Auth ancien) avant de traiter les starters officiels simples. Clarifier le starter legacy. Terminer par un index documentaire global. Seulement ensuite lancer la consolidation Forge.

---

## Ce qui ne doit pas être fait dans la Phase 9.1

- Modifier le starter Communes & Séjours.
- Transformer un starter simple en démonstrateur avancé.
- Ajouter MFA, OIDC ou RBAC complet aux starters.
- Supprimer ou renommer un starter.
- Modifier `forge new`, `starter:list`, `starter:build` ou les profils.
- Modifier Forge Design ou `docs/forge-design-roadmap.md`.
- Recréer `docs/roadmap.md`.
- Démarrer la consolidation Forge avant la fin de la Phase 9.1.

---

## Critères de fin de Phase 9.1

La Phase 9.1 pourra être considérée comme terminée quand :

- le starter Auth aura été modernisé ou clairement borné sur `core.auth` ;
- le starter Contacts aura été rafraîchi sans alourdissement ;
- le starter Carnet aura été rafraîchi comme exemple relationnel ;
- le starter Suivi pédagogique sera clairement documenté comme legacy ;
- l'index des starters sera lisible avec les statuts et usages recommandés ;
- les starters auront chacun un rôle net ;
- la roadmap ne présentera plus de contradiction documentaire sur les starters ;
- la consolidation Forge pourra commencer sans dette documentaire évidente sur les starters.

---

*Document produit par STARTER-MODERNIZATION-PLAN-001. Aucun starter n'a été modifié dans ce ticket.*
