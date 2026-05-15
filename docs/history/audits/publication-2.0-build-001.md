# Audit PUBLICATION-2.0-BUILD-001 — Build package Forge 2.0

**Date :** 2026-05-09  
**Ticket :** PUBLICATION-2.0-BUILD-001  
**Statut :** VALIDÉ

---

## Objectif

Construire le package Python Forge 2.0 et vérifier qu'il est installable localement
depuis le wheel généré. Valider que Forge 2.0 est correctement empaqueté avant
création du tag `v2.0.0`.

Ce ticket ne crée pas de tag, ne publie pas, ne crée pas de release GitHub.

---

## Synthèse

Le package Forge 2.0.0 est construisible, installable et utilisable localement.
Les 5 starters sont inclus dans le wheel. La CLI installée répond correctement.
Aucun tag `v2.0.0` n'a été créé.

---

## Version construite

`2.0.0`

---

## Commandes exécutées

```bash
# Nettoyage
rm -rf dist build *.egg-info

# Build
python -m build

# Installation locale
pipx install dist/forge_mvc-2.0.0-py3-none-any.whl --force

# Vérification CLI
forge --version
forge help
forge starter:list
forge doctor
```

---

## Artefacts générés

| Fichier | Taille |
|---|---|
| `dist/forge_mvc-2.0.0-py3-none-any.whl` | 295 Ko |
| `dist/forge_mvc-2.0.0.tar.gz` | 482 Ko |

---

## Contenu du wheel

- **Total :** 217 entrées
- **forge_cli/** : 116 fichiers (starters, builder, registry, scaffold…)
- **forge.py** : inclus ✅
- **core/** : inclus ✅
- **forge_cli/starters/** : inclus ✅

### Starters inclus (5/5)

| Starter | starter.json présent |
|---|---|
| 1 — Contacts (`contact-simple`) | ✅ |
| 2 — Utilisateurs/Auth (`utilisateurs-auth`) | ✅ |
| 3 — Carnet de contacts (`carnet-contacts`) | ✅ |
| 4 — Suivi pédagogique (`suivi-comportement-eleves`) | ✅ |
| 5 — Communes & Séjours (`communes-sejours`) | ✅ |

---

## Installation locale

```
  installed package forge-mvc 2.0.0, installed using Python 3.12.3
  These apps are now globally available
    - forge
```

Installation réussie via `pipx`. ✅

---

## Vérification CLI

### `forge --version`
```
Forge 2.0.0
```
✅ Version correcte.

### `forge help`
```
forge.py — CLI officielle de Forge

Usage :
    forge --version
    forge new NomProjet [--ref <branche>] [--profile <profil>]
    forge make:entity NomEntite
    forge make:crud NomEntite [--dry-run]
    ...
```
✅ Aide affichée.

### `forge starter:list`
```
  1  Contacts                                disponible
  2  Utilisateurs / authentification         disponible
  3  Carnet de contacts                      disponible
  4  Suivi pédagogique                       disponible
  5  Communes & Séjours                      disponible
```
✅ 5 starters disponibles.

### `forge doctor`
```
Forge doctor — 2.0.0

  [OK]    Python — 3.12.3 — requis >= 3.11
  [OK]    Environnement — env/dev chargé — clés essentielles présentes
  [OK]    Structure MVC — mvc/ valide
  [OK]    Entités — 1 entité(s) valide(s)
  [OK]    Certificats SSL — cert.pem et key.pem présents
  [OK]    Node.js / npm — npm disponible
  [WARN]  Base de données — connexion applicative impossible — normal avant forge db:init

1 avertissement(s), 0 erreur(s).
```
✅ Doctor fonctionne. L'avertissement DB est attendu (pas de connexion active sans `db:init`).

---

## Vérification starters

Les 5 starters sont accessibles depuis le wheel installé via `forge starter:list`. ✅

---

## Points validés

- [x] Build `python -m build` réussi sans erreur
- [x] Wheel généré : `forge_mvc-2.0.0-py3-none-any.whl`
- [x] Sdist généré : `forge_mvc-2.0.0.tar.gz`
- [x] `forge.py` inclus dans le wheel
- [x] `core/` inclus dans le wheel
- [x] `forge_cli/` inclus dans le wheel (116 fichiers)
- [x] Les 5 starters inclus avec leurs données
- [x] Installation `pipx` réussie
- [x] `forge --version` → `Forge 2.0.0`
- [x] `forge help` → aide affichée
- [x] `forge starter:list` → 5 starters disponibles
- [x] `forge doctor` → 1 warn DB (attendu), 0 erreur
- [x] Tag `v2.0.0` non créé
- [x] Aucune publication PyPI
- [x] Aucune release GitHub
- [x] `docs/forge-design-roadmap.md` non modifié
- [x] `docs/roadmap.md` inexistant (non recréé)
- [x] Dépôt propre après build (`git status` vide)

---

## Problèmes détectés

Aucun.

---

## Risques restants

| Risque | Niveau | Note |
|---|---|---|
| Tag `v2.0.0` non encore créé sur GitHub | Attendu | Ticket suivant : PUBLICATION-2.0-TAG-001 |
| Wheel non testé dans un environnement vierge (sans `.venv` local) | Faible | Test `pipx` valide l'isolation |
| `forge new` non testé (requiert réseau/git) | Faible | Hors périmètre build local |

---

## Ticket suivant proposé

**PUBLICATION-2.0-TAG-001** — Créer le tag `v2.0.0` sur GitHub et la release.

---

## Verdict final

**VALIDÉ.**

Le package Forge 2.0.0 est construisible, installable et pleinement utilisable localement.
`forge --version` retourne `Forge 2.0.0`. Les 5 starters sont embarqués dans le wheel.
Le dépôt reste propre. Aucun tag ni release créés.
