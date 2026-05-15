# Décision STARTER-LEGACY-DECISION-001 — Statut des starters historiques

## Objectif

Figer le statut officiel de chaque starter Forge après l'audit `STARTER-LEGACY-AUDIT-001`. Ces décisions orientent la documentation et les tickets futurs sans modifier le code des starters.

---

## Synthèse des décisions

| Starter | Statut décidé | Profil associé | Action future |
|---|---|---|---|
| 1 — Contacts | **officiel simple** | `minimal` / `standard` | conserver — aucune modification urgente |
| 2 — Utilisateurs / Auth | **à moderniser** | `standard` | aligner sur Auth/User Phase 4.5 dans `STARTER-AUTH-MODERNIZE-001` |
| 3 — Carnet de contacts | **officiel relationnel** | `standard` | conserver — aucune modification urgente |
| 4 — Suivi pédagogique | **démonstrateur historique / legacy** | aucun profil officiel direct | documenter clairement, ne plus présenter comme starter principal |
| 5 — Communes & Séjours | **démonstrateur avancé principal** | `standard` / vitrine avancée | conserver comme vitrine commerciale et pédagogique |

---

## Starter 1 — Contacts

**Statut décidé : officiel simple.**

**Justification :**

- stable et fonctionnel ;
- pédagogique — idéal pour découvrir Forge ;
- entité unique, CRUD simple, aucune dépendance fragile ;
- ne concurrence pas Communes & Séjours ;
- aligné naturellement sur le profil `minimal` ou `standard`.

**Action future :** conserver tel quel. Peut être associé au profil `minimal` dans `STARTER-PROFILES-001`.

---

## Starter 2 — Utilisateurs / Auth

**Statut décidé : starter à moderniser.**

**Justification :**

- utile pour démontrer l'authentification dans une application Forge ;
- mais son implémentation repose sur `core.security.hashing` / `core.security.session` et un `auth_model.py` custom avec une table `utilisateur` — approche antérieure à la Phase 4.5 ;
- la Phase 4.5 a livré `core.auth` avec une table `users` standardisée, `current_user()`, `is_authenticated()`, `@login_required` ;
- laisser ce starter se présenter comme référence auth sans avertissement est trompeur.

**Ce qui change dans ce ticket :**

- ajout d'un avertissement explicite dans la page `starter-app-02-utilisateurs-auth.md` ;
- le starter reste disponible et fonctionnel.

**Ce qui ne change pas :**

- le code du starter n'est pas modifié ;
- le starter n'est pas supprimé.

**Action future :** ticket `STARTER-AUTH-MODERNIZE-001` — réécrire le starter 2 en utilisant `core.auth`.

---

## Starter 3 — Carnet de contacts

**Statut décidé : officiel relationnel.**

**Justification :**

- stable et fonctionnel ;
- bon exemple de relation `many_to_one` entre deux entités (`Ville` → `Contact`) ;
- représente un niveau de complexité intermédiaire bien positionné entre le starter 1 (entité seule) et Communes & Séjours (démonstrateur avancé) ;
- pas trop métier — applicable à beaucoup de projets.

**Action future :** conserver tel quel. Peut être associé au profil `standard` dans `STARTER-PROFILES-001`.

---

## Starter 4 — Suivi pédagogique

**Statut décidé : démonstrateur historique / legacy.**

**Justification :**

- reste fonctionnel et générable ;
- mais trop spécifique à un métier (suivi d'élèves) pour être un starter générique ;
- auth custom (`core.security`) décalée de Phase 4.5, comme le starter 2 ;
- présenté actuellement comme "vitrine technique Forge" — cette formulation entre en concurrence directe avec Communes & Séjours, le démonstrateur avancé officiel depuis Phase 8 ;
- un utilisateur qui cherche un démonstrateur avancé doit être dirigé vers le starter 5.

**Ce qui change dans ce ticket :**

- ajout d'un avertissement dans la page `starter-app-04-suivi-comportement-eleves.md` ;
- le starter reste disponible et générable.

**Ce qui ne change pas :**

- le code du starter n'est pas modifié ;
- le starter n'est pas supprimé ni renommé ;
- le starter reste listable par `forge starter:list`.

**Action future :** lors de `STARTER-PROFILES-001`, clarifier son positionnement. Envisager de retirer la mention "vitrine technique" au profit de "démonstrateur historique" ou "exemple pédagogique avancé pré-Phase 8".

---

## Starter 5 — Communes & Séjours

**Statut décidé : démonstrateur avancé principal.**

**Justification :**

- couvre les briques modernes de Forge : pages publiques, formulaire, mails, i18n, médias, seed JSON ;
- positionné depuis Phase 8 comme vitrine commerciale et pédagogique ;
- la page `starter-app-05-communes-sejours.md` dit déjà explicitement : "Communes & Séjours est le démonstrateur avancé de Forge" — formulation juste, à préserver.

**Action future :** conserver. Peut évoluer avec les nouvelles briques Forge dans des tickets futurs.

---

## Conséquences pour la documentation

| Page | Modification décidée |
|---|---|
| `starter-app-01-contacts.md` | aucune modification nécessaire |
| `starter-app-02-utilisateurs-auth.md` | ajouter un avertissement sur l'approche auth pré-Phase 4.5 |
| `starter-app-03-carnet-contacts.md` | aucune modification nécessaire |
| `starter-app-04-suivi-comportement-eleves.md` | ajouter un avertissement sur le statut de démonstrateur historique |
| `starter-app-05-communes-sejours.md` | aucune modification nécessaire — déjà bien positionné |

---

## Tickets futurs recommandés

| Ticket | Objectif | Priorité |
|---|---|---|
| `STARTER-PROFILES-001` | Aligner la présentation des starters avec les profils Forge | prochaine |
| `STARTER-AUTH-MODERNIZE-001` | Réécrire le starter 2 en utilisant `core.auth` (Phase 4.5) | après STARTER-PROFILES-001 |
| `STARTER-CS-REPLACE-001` | Confirmer Communes & Séjours comme démonstrateur avancé principal | intégré dans STARTER-PROFILES-001 |

---

*Document produit par STARTER-LEGACY-DECISION-001. Les modifications de code des starters sont hors périmètre de ce ticket.*
