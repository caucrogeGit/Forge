# Audit CONSOLIDATION-STARTER-001 — Starters Forge et Communes & Séjours

**Date :** 2026-05-09
**Périmètre :** starters 1 à 5, documentation, doc_url, rebuild.md, séparation core / métier
**Ticket :** CONSOLIDATION-STARTER-001

---

## Objectif

Vérifier que les starters Forge sont cohérents avec leur statut documentaire, que les `doc_url` sont corrects, que `docs/starters/communes-sejours/rebuild.md` existe, et que Communes & Séjours démontre Forge sans polluer le cœur du framework.

Ce ticket ne modifie pas le core, les modules, les profils ou les fonctionnalités métier des starters.

---

## Synthèse

| Zone | État | Commentaire |
|---|---|---|
| Contacts | OK | Starter officiel simple, doc_url correct, rebuild.md présent |
| Utilisateurs/Auth | OK | Modernisé vers core.auth, doc_url corrigé dans ce ticket |
| Carnet de contacts | OK | Starter officiel relationnel, doc_url correct, rebuild.md présent |
| Suivi pédagogique | OK | Clairement documenté legacy/historique, rebuild.md présent |
| Communes & Séjours | OK | Démonstrateur avancé, rebuild.md créé dans ce ticket |
| starter:list | OK | 5 starters affichés, statuts corrects |
| starter:build | OK | Dry-run fonctionnel pour tous les starters |
| doc_url | OK | Corrigés pour starters 2 et 5 dans ce ticket |
| rebuild.md | OK | Présent pour les 5 starters après ce ticket |
| profils recommandés | OK | Cohérents dans docs/starters/index.md |
| séparation core / métier | OK | Aucune logique Communes & Séjours dans core/ |

---

## Méthode d'audit

- Lecture de `forge_cli/starters/__init__.py` (CLI : `starter:list`, `starter:build`)
- Lecture de `forge_cli/starters/registry.py` (résolution par numéro ou alias)
- Lecture des 5 fichiers `starter.json`
- Vérification des `doc_url` contre la structure MkDocs (`mkdocs.yml` + `site/starters/`)
- Lecture de `docs/starters/index.md` (tableau de synthèse, statuts, profils)
- Lecture des index et rebuild.md des starters 1 à 4
- Vérification de l'absence de `docs/starters/communes-sejours/rebuild.md`
- Grep de `communes_sejours`, `demande_sejour` dans `core/` et `forge_cli/` hors `starters/data/`
- Lecture du contrôleur packagé `communes_sejours_controller.py`
- Vérification des clés i18n `fr.json` du starter 5
- Vérification des fichiers packagés dans `forge_cli/starters/data/communes-sejours/files/`
- Lecture de `docs/starters/communes-sejours/index.md`
- Revue des tests existants (`test_starter_cli.py` : 118 tests, `test_starter_communes_sejours.py` : 192 tests)

---

## Fichiers audités

| Fichier | Rôle |
|---|---|
| `forge_cli/starters/__init__.py` | CLI starter:list / starter:build |
| `forge_cli/starters/registry.py` | Résolution des starters |
| `forge_cli/starters/data/*/starter.json` | Métadonnées des 5 starters |
| `forge_cli/starters/data/communes-sejours/files/` | Fichiers packagés du starter 5 |
| `docs/starters/index.md` | Index et tableau de synthèse |
| `docs/starters/communes-sejours/index.md` | Présentation du démonstrateur |
| `docs/starters/communes-sejours/rebuild.md` | Créé dans ce ticket |

---

## Starters audités

### Starter 1 — Contacts

**Statut attendu :** officiel simple
**Statut documenté :** starter officiel simple

- CRUD unique, entité `Contact`
- `doc_url` : `https://caucrogegit.github.io/Forge/starters/01-contact-simple/` — **correct**
- `rebuild.md` : présent
- Profil recommandé : `minimal` / `standard` — cohérent
- Aucune logique métier dans `core/`

**État : OK**

---

### Starter 2 — Utilisateurs / Auth

**Statut attendu :** Auth minimale moderne
**Statut documenté :** Auth minimale moderne (`core.auth`)

- Contrôleur auth importe depuis `core.auth` (`verify_password`, `login_user`, `logout_user`, `@login_required`, `hash_password`)
- `doc_url` (avant ce ticket) : `https://caucrogegit.github.io/Forge/starter-app-02-utilisateurs-auth/` — **incorrect**
- `doc_url` (après correction) : `https://caucrogegit.github.io/Forge/starters/02-utilisateurs-auth/` — **correct**
- `rebuild.md` : présent
- Profil recommandé : `standard` — cohérent

**Incohérence corrigée :** `doc_url` utilisait l'ancienne structure `starter-app-02-` au lieu de `starters/02-`.

**État : OK (après correction)**

---

### Starter 3 — Carnet de contacts

**Statut attendu :** officiel relationnel
**Statut documenté :** officiel relationnel

- Deux entités (`Ville`, `Contact`), `many_to_one`, `LEFT JOIN` SQL
- `doc_url` : `https://caucrogegit.github.io/Forge/starters/03-carnet-contacts/` — **correct**
- `rebuild.md` : présent
- Profil recommandé : `standard` — cohérent

**État : OK**

---

### Starter 4 — Suivi pédagogique

**Statut attendu :** démonstrateur historique / legacy
**Statut documenté :** exemple pédagogique historique / legacy

- Clairement documenté dans `docs/starters/04-suivi-comportement-eleves/index.md`
- `doc_url` : `https://caucrogegit.github.io/Forge/starters/04-suivi-comportement-eleves/` — **correct**
- `rebuild.md` : présent
- Aucun profil principal — cohérent avec le statut legacy

**État : OK**

---

### Starter 5 — Communes & Séjours

**Statut attendu :** démonstrateur avancé principal
**Statut documenté :** démonstrateur avancé principal

- `kind` : `skeleton` (pas un CRUD généré automatiquement)
- `requires_db` : `false` (fonctionne sans base de données pour les pages publiques)
- `doc_url` (avant ce ticket) : `https://caucrogegit.github.io/Forge/starter-app-05-communes-sejours/` — **incorrect**
- `doc_url` (après correction) : `https://caucrogegit.github.io/Forge/starters/communes-sejours/` — **correct**
- `rebuild.md` : **absent avant ce ticket**, **créé dans ce ticket**
- Profil recommandé : `standard` — cohérent

**État : OK (après corrections)**

---

## Génération des starters

### forge starter:list

Affiche les 5 starters avec numéro, nom, description et `doc_url`. Formatage cohérent. Statuts tous `disponible`.

### forge starter:build

- Dry-run fonctionnel pour les 5 starters
- Starter inconnu → `SystemExit` avec message mentionnant `forge starter:list`
- `--force` disponible pour forcer la réinstallation
- `--public` refusé pour les starters avec routes mixtes publiques/protégées

---

## Documentation des starters

### Structure

Chaque starter a un sous-dossier dans `docs/starters/` avec au minimum `index.md`. Les starters 1 à 4 avaient déjà un `rebuild.md`. Communes & Séjours disposait uniquement de `index.md`.

### rebuild.md

| Starter | rebuild.md |
|---|---|
| 1 — Contacts | présent |
| 2 — Utilisateurs/Auth | présent |
| 3 — Carnet de contacts | présent |
| 4 — Suivi pédagogique | présent |
| 5 — Communes & Séjours | **créé dans ce ticket** |

### index des starters

`docs/starters/index.md` contient :
- tableau de synthèse avec statuts, profils associés et usages recommandés ;
- section explicite sur la différence entre profil et starter ;
- liens vers `rebuild.md` pour les 5 starters (après ce ticket).

---

## doc_url

| Starter | doc_url avant | doc_url après |
|---|---|---|
| 1 — Contacts | `starters/01-contact-simple/` | inchangé |
| 2 — Utilisateurs/Auth | `starter-app-02-utilisateurs-auth/` | `starters/02-utilisateurs-auth/` |
| 3 — Carnet de contacts | `starters/03-carnet-contacts/` | inchangé |
| 4 — Suivi pédagogique | `starters/04-suivi-comportement-eleves/` | inchangé |
| 5 — Communes & Séjours | `starter-app-05-communes-sejours/` | `starters/communes-sejours/` |

Les anciennes URL `starter-app-XX` correspondaient à la structure documentaire précédente, avant la réorganisation dans `docs/starters/`. La structure MkDocs publie maintenant les starters sous `starters/XX-*` et `starters/communes-sejours/`.

---

## Cohérence profils / starters

| Starter | Profil recommandé | Cohérence |
|---|---|---|
| 1 — Contacts | `minimal` / `standard` | OK |
| 2 — Utilisateurs/Auth | `standard` | OK |
| 3 — Carnet de contacts | `standard` | OK |
| 4 — Suivi pédagogique | Aucun profil principal | OK (legacy) |
| 5 — Communes & Séjours | `standard` | OK |

---

## Séparation framework / application métier

Vérifications sur `core/` et `forge_cli/` (hors `starters/data/`) :

- **`core/`** : aucune référence à `communes_sejours`, `demande_sejour`, `hebergement` ou termes métier du starter 5
- **`forge_cli/` hors `starters/`** : aucune référence métier du starter 5
- Exception documentée : `forge_cli/i18n.py` contient `"sejour"` dans `_FORBIDDEN_KEY_TERMS` — c'est une *protection* qui empêche les clés i18n génériques d'utiliser des termes métier de starters

Le contrôleur `communes_sejours_controller.py` packagé dans `forge_cli/starters/data/` :
- importe exclusivement depuis `core.*` et `mvc.*` ;
- n'importe pas depuis `forge_cli.*` ;
- utilise `trans()` depuis `core.i18n`.

---

## Limites métier assumées

`docs/starters/communes-sejours/index.md` documente explicitement ce qui **n'est pas livré** :

- réservation confirmée ;
- paiement en ligne ;
- calendrier de disponibilités ;
- tarification ;
- comptes propriétaires et espace privé ;
- authentification spécifique au starter ;
- back-office métier ;
- workflow métier avancé ;
- dashboard statistiques ;
- insertion SQL automatique du seed.

La formule "démonstrateur" est explicitement répétée dans le document.

---

## Points cohérents

1. **5 starters disponibles** — tous avec `status: available`, numérotés 1 à 5.
2. **Statuts documentaires cohérents** — Contacts/Carnet officiels, Auth modernisé, Suivi legacy, Communes & Séjours démonstrateur avancé.
3. **Séparation core/métier garantie** — aucune logique Communes & Séjours dans `core/`.
4. **i18n protégée** — `_FORBIDDEN_KEY_TERMS` dans `forge_cli/i18n.py` empêche les termes métier dans les clés génériques.
5. **Starter 5 sans DB** — fonctionne immédiatement après `forge starter:build 5` sans `db:init`.
6. **Suite de tests robuste** — 310 tests existants sur les starters (118 + 192), 67 tests ajoutés dans ce ticket.
7. **doc_url corrigés** — les 5 starters pointent vers la structure MkDocs actuelle.
8. **rebuild.md complet** — tous les starters ont maintenant un fichier de reconstruction.

---

## Incohérences détectées

### 1. doc_url starters 2 et 5 — corrigée

Les `doc_url` des starters 2 et 5 utilisaient l'ancienne structure `starter-app-XX-` au lieu de la structure actuelle `starters/XX-`.

**Correction appliquée :** les deux `starter.json` ont été mis à jour.

### 2. rebuild.md absent pour Communes & Séjours — corrigée

`docs/starters/communes-sejours/rebuild.md` était absent, alors que les starters 1 à 4 en disposaient tous.

**Correction appliquée :** `rebuild.md` créé avec les commandes exactes, la structure générée et les limites documentées.

### 3. Lien rebuild.md absent dans docs/starters/index.md — corrigée

La table des fichiers de reconstruction dans `index.md` affichait « — » pour Communes & Séjours.

**Correction appliquée :** lien `rebuild.md` ajouté dans le tableau et dans la section démonstrateur.

---

## Risques restants

| Risque | Niveau | Commentaire |
|---|---|---|
| Suivi pédagogique auth pré-core.auth | Faible | Clairement documenté legacy, non recommandé |
| Seed non insérable automatiquement | Faible | Documenté, fonctionnalité hors périmètre |
| Routes non traduites dans starter 5 | Faible | Limite documentée dans index.md |

---

## Recommandations

1. **Aucune modification fonctionnelle** requise avant Forge 2.0.
2. **Ticket `CONSOLIDATION-DOC-FRONT-001`** (déjà proposé) : ajouter `js:init` dans `docs/reference.md`.
3. **Ticket `STARTER-SEED-001`** (futur) : si une commande `forge db:seed` est créée, le seed Communes & Séjours pourrait être insérable.

---

## Tickets futurs proposés

| Ticket | Sujet |
|---|---|
| `CONSOLIDATION-DOC-FRONT-001` | Ajouter `js:init` dans `docs/reference.md` |
| `STARTER-SEED-001` | Commande `forge db:seed` pour insérer les seeds |
| `FRONT-PROFILE-001` | Différencier les squelettes front selon les profils |

---

## Verdict final

**Les starters Forge sont cohérents pour Forge 2.0.**

Les 5 starters sont disponibles, documentés avec leur statut, dotés d'un `rebuild.md` et alignés sur la structure MkDocs. Les `doc_url` des starters 2 et 5 ont été corrigés. Communes & Séjours démontre correctement Forge sans polluer le cœur : aucune logique métier dans `core/`, contrôleur packagé importé depuis `core.*` uniquement, i18n protégée par `_FORBIDDEN_KEY_TERMS`.

**Résultat :** CONSOLIDATION-STARTER-001 — **VALIDÉ**
