# Profils de projet Forge

## Principe

Un profil Forge décrit le type de projet à créer. Il ne remplace pas les starters : un profil définit une base technique, un starter fournit un exemple ou un démonstrateur.

Chaque profil cible un cas d'usage précis et permet de créer des projets adaptés sans avoir à retirer ou ajouter manuellement des composants.

**Le profil ne change pas le fonctionnement de Forge. Il enregistre l'intention de départ du projet.**

---

## Commande

L'option `--profile` est disponible avec `forge new` :

```bash
forge new MonProjet
forge new MonProjet --profile minimal
forge new MonProjet --profile standard
forge new MonProjet --profile dynamic
forge new MonProjet --profile multilingual
```

Sans `--profile`, Forge utilise le profil `standard`.

---

## Profil par défaut

Le profil par défaut est `standard`.

```bash
forge new MonProjet          # équivalent à --profile standard
forge new MonProjet --profile standard
```

---

## Profils officiels

| Profil | Usage | Base |
|---|---|---|
| `minimal` | Projet le plus simple, pédagogique | — |
| `standard` | Application classique recommandée | `minimal` + composants standard |
| `dynamic` | Application avec interactions front légères | `standard` + intention HTMX / Alpine.js |
| `multilingual` | Application prête pour l'internationalisation | `standard` + intention i18n |
| `auth-mfa` | Application avec MFA (TOTP) activé | `standard` + intention `forge-mvc-mfa` |

---

## Profil `minimal`

**Objectif** : projet Forge le plus simple possible.

**Intention** :

- structure MVC de base ;
- Jinja ;
- aucun HTMX ;
- aucun Alpine.js ;
- i18n non forcée ;
- aucun composant avancé ;
- aucun exemple métier.

**Usage** : pour démarrer un projet très simple ou à des fins pédagogiques.

---

## Profil `standard`

**Objectif** : projet Forge recommandé pour une application classique.

**Intention** :

- structure MVC complète ;
- Jinja ;
- Tailwind ;
- layout public / admin ;
- formulaires avec validation ;
- flash messages ;
- pagination ;
- composants de base.

**Usage** : pour la majorité des projets Forge. C'est le profil utilisé si aucune option `--profile` n'est fournie.

---

## Profil `dynamic`

**Objectif** : projet Forge avec interactions front légères.

**Intention** :

- tout le contenu du profil `standard` ;
- HTMX activé ou préparé ;
- Alpine.js optionnel ou préparé ;
- blocs scripts prêts ;
- conventions de fragments HTMX.

**Usage** : pour les projets qui veulent du dynamisme sans SPA.

---

## Profil `multilingual`

**Objectif** : projet Forge prêt pour l'internationalisation.

**Intention** :

- tout le contenu du profil `standard` ;
- `forge i18n:init` appliqué au démarrage ;
- `translations/fr.json` présent ;
- helper `trans(...)` disponible dans les templates ;
- conventions de clés documentées.

**Décision** : `multilingual` hérite de `standard`, pas de `dynamic`. L'i18n et le dynamisme front sont deux dimensions indépendantes.

**Usage** : pour les projets qui gèrent plusieurs langues ou préparent une internationalisation.

---

---

## Profil `auth-mfa`

**Objectif** : projet Forge avec authentification MFA (TOTP) activée via `forge-mvc-mfa`.

**Intention** :

- tout le contenu du profil `standard` ;
- `forge-mvc-mfa` installé (`pip install --pre forge-mvc-mfa` — publié sur PyPI depuis `1.0.0-beta.9`, statut Alpha) ;
- contrôleurs auth sans stubs ni lazy imports MFA ;
- routes `/login/mfa` toujours actives.

**Usage** :

```bash
forge new MonProjet --profile auth-mfa
# forge-mvc-mfa : pip install --pre forge-mvc-mfa (publié sur PyPI depuis 1.0.0-beta.9)
forge starter:build auth-mfa
```

`forge starter:build auth-mfa` remplace les contrôleurs stub du squelette par les versions complètes (sans try/except ni `_MFA_AVAILABLE`).

**Prérequis** : `forge-mvc-mfa` installé dans le venv. Sans ce module, les routes `/login/mfa` redirigent vers `/login` (comportement du squelette stub par défaut).

---

## Hiérarchie des profils

```text
minimal
  └── standard
        ├── dynamic      (standard + intention HTMX/Alpine)
        ├── multilingual (standard + intention i18n)
        └── auth-mfa     (standard + intention forge-mvc-mfa)
```

`minimal` est la base la plus sobre. `standard` est le profil par défaut. `dynamic` ajoute l'intention front dynamique. `multilingual` ajoute l'intention i18n. `auth-mfa` ajoute l'intention MFA.

---

## Fichier `forge_profile.txt`

`forge new` écrit le profil choisi dans `forge_profile.txt` à la racine du projet généré :

```text
standard
```

Ce fichier :

- contient uniquement le nom du profil ;
- est lisible en UTF-8 ;
- pourra servir plus tard à `forge doctor`, `project:check`, des diagnostics ou à Forge Design ;
- ne contient pas de configuration complexe.

---

## Ce qui est déjà livré

La Phase 9 a livré l'intégralité du contrat des profils :

| Ticket | Livraison |
|---|---|
| `PROFILE-001` | Contrat : `SUPPORTED_PROJECT_PROFILES`, `DEFAULT_PROJECT_PROFILE`, descriptions |
| `PROFILE-002` | Option `--profile` dans `forge new`, écriture de `forge_profile.txt` |
| `PROFILE-003` | Tests de génération par profil — les 4 profils validés automatiquement |
| `PROFILE-DOC-001` | Documentation finale consolidée |

---

## Profils et starters

Un profil cible une **base technique** ; un starter fournit un **exemple d'application**. Les deux sont complémentaires : on choisit un profil pour définir la structure du projet, puis on peut s'inspirer d'un starter pour construire dessus.

| Besoin | Profil recommandé | Starter recommandé |
|---|---|---|
| Projet très simple, pédagogique | `minimal` | Contacts |
| Projet classique | `standard` | Contacts ou Carnet de contacts |
| Projet avec relation many_to_one | `standard` | Carnet de contacts |
| Projet avec authentification (moderne) | `standard` | Utilisateurs/Auth |
| Démonstrateur avancé, pages publiques | `standard` | Communes & Séjours |
| Démonstrateur historique / legacy | — | Suivi pédagogique (non recommandé pour un nouveau projet) |

Les statuts des starters ont été formalisés dans `STARTER-LEGACY-AUDIT-001` et `STARTER-LEGACY-DECISION-001`. Le ticket `STARTER-CS-REPLACE-001` confirme Communes & Séjours comme démonstrateur avancé principal.

---

## Limites actuelles

- Les profils sont reconnus, validés et enregistrés dans `forge_profile.txt`.
- La différenciation complète des squelettes reste volontairement limitée : tous les profils produisent actuellement la même structure de base.
- Les profils ne remplacent pas les starters.
- Les profils personnalisés ne sont pas encore supportés.
- Forge Design n'est pas concerné directement par ce ticket.

À ce stade, les profils sont une base contractuelle et CLI. Ils ne déclenchent pas encore une refonte complète du squelette généré.

---

## Prochaines évolutions

La différenciation progressive des squelettes par profil sera introduite dans des tickets ultérieurs.
