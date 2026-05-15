# Audit CONSOLIDATION-PROFILES-001 — Cohérence des profils Forge

**Date :** 2026-05-09
**Périmètre :** système de profils `forge_cli/project_profiles.py` + option `--profile` de `forge new`
**Ticket :** CONSOLIDATION-PROFILES-001

---

## Objectif

Vérifier que les profils officiels Forge (`minimal`, `standard`, `dynamic`, `multilingual`) sont clairement définis, générés, documentés et alignés avec la philosophie Forge avant publication de Forge 2.0.

Ce ticket n'ajoute aucun profil nouveau.

---

## Synthèse

| Profil | État | Commentaire |
|---|---|---|
| `minimal` | OK | Déclaré, validé, documenté, forge_profile.txt correct |
| `standard` | OK | Profil par défaut, déclaré, validé, documenté |
| `dynamic` | OK | Déclaré, HTMX mentionné, forge_profile.txt correct |
| `multilingual` | OK | Déclaré, i18n mentionné, forge_profile.txt correct |
| Profil par défaut | OK | `standard`, documenté, cohérent avec comportement historique |
| Profil invalide | OK | `SystemExit` avant toute création, message explicite |
| `forge_profile.txt` | OK | Créé, contenu correct (nom seul), UTF-8 |
| Documentation | OK | `docs/profiles.md` complet, limites assumées |
| Starters associés | OK | Correspondance établie dans `docs/profiles.md` et `docs/starters/index.md` |
| Forge Design séparé | OK | Aucune dépendance, pas de promesse d'éditeur graphique |

---

## Méthode d'audit

- Lecture de `forge_cli/project_profiles.py`
- Lecture des sections profils de `forge.py` (lignes 110-113, 320-356, 474-493)
- Lecture de `docs/profiles.md` (203 lignes)
- Lecture de `docs/starters/index.md` (164 lignes)
- Vérification de `README.md`
- Revue de `tests/test_project_profiles.py` (400 lignes, 39 tests)
- Exécution de tous les tests existants (verts)
- Ajout de tests ciblés dans `tests/test_consolidation_profiles_001.py`

---

## Fichiers audités

| Fichier | Lignes | Responsabilité |
|---|---|---|
| `forge_cli/project_profiles.py` | 37 | Constantes : profils, défaut, descriptions |
| `forge.py` (sections profils) | ~40 | Validation, écriture `forge_profile.txt`, dispatch |
| `docs/profiles.md` | 203 | Documentation publique des profils |
| `docs/starters/index.md` | 164 | Relation profils / starters |
| `README.md` | ~300 | Mention des profils |
| `tests/test_project_profiles.py` | 400 | 39 tests (PROFILE-001 à PROFILE-DOC-001) |

---

## Profils audités

### Profil `minimal`

**Définition :** structure MVC de base, sans composants avancés, sans exemple métier.

**Contrat déclaré :**
- Aucun HTMX
- Aucun Alpine.js
- i18n non forcée
- Pas de layout public/admin complexe

**État :** validé — déclaré dans `SUPPORTED_PROJECT_PROFILES`, décrit dans `PROJECT_PROFILE_DESCRIPTIONS`, documenté dans `docs/profiles.md`.

**Limitation :** comme tous les profils, `minimal` génère actuellement la même structure de base que `standard`. La différenciation complète du squelette est documentée comme évolution future.

---

### Profil `standard`

**Définition :** profil recommandé pour une application classique. Layout public/admin, formulaires, flash, pagination.

**Contrat déclaré :**
- Structure MVC complète
- Jinja
- Tailwind
- Layout public/admin
- Formulaires avec validation
- Flash messages, pagination

**État :** validé — profil par défaut confirmé (`DEFAULT_PROJECT_PROFILE = "standard"`), documenté, testé.

---

### Profil `dynamic`

**Définition :** profil standard enrichi de l'intention HTMX et Alpine.js optionnel.

**Contrat déclaré :**
- Tout le contenu du profil `standard`
- HTMX activé ou préparé
- Alpine.js optionnel ou préparé
- Conventions de fragments HTMX

**État :** validé — HTMX mentionné dans la description et la documentation. `forge_profile.txt` contient `dynamic` correctement.

---

### Profil `multilingual`

**Définition :** profil standard avec i18n initialisée.

**Contrat déclaré :**
- Tout le contenu du profil `standard`
- `forge i18n:init` appliqué au démarrage
- `translations/fr.json` présent
- Helper `trans(...)` disponible dans les templates

**État :** validé — i18n mentionné dans la description et la documentation. `forge_profile.txt` contient `multilingual` correctement.

**Note architecturale :** `multilingual` hérite de `standard`, pas de `dynamic`. L'i18n et le dynamisme front sont deux dimensions indépendantes — c'est une décision de conception explicite et correcte.

---

## Profil par défaut

- **Valeur :** `"standard"` (ligne 17 de `forge_cli/project_profiles.py`)
- **Comportement :** si aucun `--profile` n'est fourni, `cmd_new` utilise `DEFAULT_PROJECT_PROFILE`
- **`forge_profile.txt` :** contient `"standard\n"` dans ce cas
- **Documentation :** `docs/profiles.md` l'indique clairement : *"C'est le profil utilisé si aucune option `--profile` n'est fournie."*
- **Test de non-régression :** `test_comportement_historique_preserve_sans_profile` — garantit la compatibilité historique

---

## `forge_profile.txt`

| Propriété | Valeur |
|---|---|
| Créé par | `forge.py:356` |
| Contenu | Nom du profil + newline (ex. `"standard\n"`) |
| Encodage | UTF-8 |
| Emplacement | Racine du projet généré |
| Format | Texte simple, une seule ligne non vide |

**Usage actuel :** enregistrement du profil choisi, visible dans le projet.

**Usage futur documenté :** `forge doctor`, diagnostics, potentiellement Forge Design. Aucune lecture de ce fichier n'a été détectée dans le code actuel (hors tests).

---

## Gestion des profils invalides

```python
# forge.py:331-336
if profile not in SUPPORTED_PROJECT_PROFILES:
    profiles_list = ", ".join(SUPPORTED_PROJECT_PROFILES)
    sys.exit(
        f"Profil inconnu : {profile}. "
        f"Profils disponibles : {profiles_list}."
    )
```

**Comportement :**
1. Validation **avant** `_require_command` → pas de vérification système inutile
2. Validation **avant** le clonage → aucun dossier partiel créé
3. Message explicite listant les profils disponibles
4. `SystemExit` propre

---

## Cohérence documentation

### `docs/profiles.md`

Document dédié de 203 lignes couvrant :

- Principe des profils (vs starters)
- Syntaxe `--profile`
- Profil par défaut `standard`
- Description de chaque profil
- Hiérarchie `minimal → standard → dynamic / multilingual`
- `forge_profile.txt`
- Tickets livrés (PROFILE-001 à PROFILE-DOC-001)
- Correspondance profils/starters
- **Limites assumées** (même squelette pour tous les profils actuellement)

### `docs/starters/index.md`

- Colonne "Profil associé" dans le tableau des starters
- Section dédiée "Différence entre profil et starter"
- Starter 1 → `minimal` / `standard`
- Starter 2 → `standard`
- Starter 3 → `standard`
- Starter 4 → aucun profil principal (legacy)
- Starter 5 → `standard`

### `README.md`

Mention explicite (ligne ~160) :
> Un profil peut être précisé avec `--profile` (`minimal`, `standard`, `dynamic`, `multilingual`) — `standard` est le profil par défaut.

---

## Cohérence starters / profils

La correspondance est clairement établie :

| Besoin | Profil recommandé | Starter |
|---|---|---|
| Projet simple, pédagogique | `minimal` | Contacts |
| Projet classique | `standard` | Contacts ou Carnet |
| Avec authentification | `standard` | Utilisateurs/Auth |
| Démonstrateur avancé | `standard` | Communes & Séjours |
| Legacy | — | Suivi pédagogique |

La distinction profil/starter est claire : **un profil définit la base technique, un starter fournit un exemple d'application**.

---

## Séparation Forge Design

- `forge_cli/project_profiles.py` ne contient aucune référence à Forge Design
- `docs/profiles.md` ne promet pas d'éditeur graphique lié aux profils
- La mention de Forge Design dans `forge_profile.txt` (section "usage futur") est une possibilité explorée, pas une promesse
- `docs/forge-design-roadmap.md` n'a pas été modifié par ce ticket
- Les profils restent exclusivement des outils de génération CLI

---

## Points cohérents

1. **Contrat minimal complet** : 4 profils, descriptions, défaut, validation — tout est implémenté.
2. **Validation avant action** : un profil invalide ne déclenche ni clonage, ni vérification système.
3. **`forge_profile.txt` simple** : format minimaliste, lisible par n'importe quel outil.
4. **Hiérarchie explicite** : `minimal → standard → dynamic / multilingual` documentée et cohérente.
5. **Limites assumées** : la limitation "même squelette" est documentée dans `docs/profiles.md`, pas cachée.
6. **Tests exhaustifs** : 39 tests dédiés dans `test_project_profiles.py` couvrant tous les cas.
7. **Séparation Forge Design** : aucun couplage.

---

## Incohérences détectées

### 1. Différenciation réelle des squelettes non implémentée — **assumée**

Tous les profils produisent actuellement la même structure de base. La description de `minimal` promet "aucun HTMX", "aucun Alpine.js", "i18n non forcée" — mais si le squelette est identique pour tous les profils, ces promesses ne sont effectivement tenues que dans l'intention.

**Niveau :** incohérence documentée et assumée dans `docs/profiles.md:191-192`.
**Impact :** ne bloque pas Forge 2.0 — les profils sont contractuels et la différenciation est annoncée comme évolution future.
**Action recommandée :** ticket `PROFILE-DIFFERENTIATION-001` (post-Forge 2.0).

### 2. `forge_profile.txt` non relu par le code actuel — **acceptable**

Le fichier est créé mais jamais relu par `forge doctor`, `build:model`, ou les générateurs. Son utilité actuelle est uniquement informative.

**Impact :** aucun, c'est documenté comme "usage futur".
**Action recommandée :** aucune pour Forge 2.0.

---

## Risques restants

| Risque | Niveau | Commentaire |
|---|---|---|
| Squelettes non différenciés | Moyen | Attendu par l'utilisateur, pas encore implémenté |
| `forge_profile.txt` non exploité | Faible | Usage futur documenté |
| Profils `dynamic`/`multilingual` = `standard` en pratique | Moyen | Limitation assumée, documentée |

---

## Recommandations

1. **Documenter clairement dans le message de `forge new`** que les profils sont actuellement contractuels mais ne différencient pas encore les squelettes.
2. **Ticket `PROFILE-DIFFERENTIATION-001`** : implémenter la différenciation réelle des squelettes (post-Forge 2.0).
3. **Aucune modification fonctionnelle** requise avant Forge 2.0.

---

## Tickets futurs proposés

| Ticket | Sujet |
|---|---|
| `PROFILE-DIFFERENTIATION-001` | Différencier les squelettes selon le profil (minimal sans HTMX, dynamic avec HTMX, multilingual avec i18n) |
| `PROFILE-DOCTOR-001` | Utiliser `forge_profile.txt` dans `forge doctor` pour des conseils adaptés au profil |

---

## Verdict final

**Les profils Forge sont cohérents et suffisamment stables pour Forge 2.0.**

Le contrat est complet : 4 profils officiels, défaut `standard`, validation propre des profils invalides, `forge_profile.txt` correct, documentation alignée, starters associés documentés, séparation Forge Design garantie.

La seule incohérence notable — la non-différenciation réelle des squelettes — est **explicitement assumée et documentée** dans `docs/profiles.md`. Elle ne bloque pas Forge 2.0 car les profils jouent leur rôle de contrat CLI et d'intention documentée.

**Résultat :** CONSOLIDATION-PROFILES-001 — **VALIDÉ**
