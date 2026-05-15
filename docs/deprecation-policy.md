# Politique de dépréciation Forge

Ce document définit comment Forge annonce, maintient puis retire progressivement
les fonctionnalités obsolètes, remplacées ou incompatibles.

Il complète :

- [Politique de release](release-policy.md) — quand incrémenter MAJOR/MINOR/PATCH
- [Contrat de stabilité](stability-contract.md) — ce qui est stable, interne, expérimental
- [Procédure de release](release.md) — checklist avant chaque tag

---

## Objectif

Garantir que Forge ne casse pas brutalement les projets utilisateurs.

Chaque suppression d'un élément stable passe par un cycle explicite :

```
Annonce → Maintien → Retrait
```

Les projets en Forge 2.x ne doivent jamais se retrouver cassés après une
mise à jour mineure.

---

## Principe général

Une dépréciation doit être :

- **annoncée** dans le CHANGELOG et la documentation avant tout retrait ;
- **documentée** : ce qui est déprécié, pourquoi, quelle alternative utiliser ;
- **testée** : la fonctionnalité dépréciée continue de fonctionner pendant la période de maintien ;
- **accompagnée d'une alternative** : toute dépréciation sans alternative est un retrait abusif ;
- **bornée dans le temps** : la date ou version de retrait doit être indiquée ;
- **retirée dans une version MAJOR**, sauf exception de sécurité.

---

## Ce qui peut être déprécié

| Domaine | Exemples |
|---|---|
| Commandes CLI | `forge old:command` → `forge new:command` |
| Options CLI | `--ancien-flag` → `--nouveau-flag` |
| API Python publique | `core.security.hashing` → `core.auth.password` |
| Décorateurs | `@require_auth` → `@login_required` |
| Clés de configuration `.env` | `DB_APP_USER` → `DB_APP_LOGIN` |
| Conventions de fichiers | ancien format JSON entité |
| Fichiers générés | ancien layout Jinja |
| Comportements runtime | changement de valeur par défaut |
| Modules de compatibilité | shims d'extraction (ex. `core.auth.mfa` → `forge_mvc_mfa`) |

---

## Ce qui ne doit pas être cassé brutalement

Les éléments suivants ne peuvent pas être supprimés sans cycle de dépréciation :

- Commandes CLI documentées dans `docs/reference.md` et `docs/stability-contract.md`.
- Imports publics de `core.http`, `core.auth`, `core.security` documentés.
- Clés `.env` documentées.
- Structure de projet générée par `forge new`.
- Format JSON canonique des entités (v1).
- Comportement de `GET /health`.

Les éléments **internes** ou **expérimentaux** (voir
[Contrat de stabilité](stability-contract.md)) peuvent changer sans
cycle de dépréciation.

---

## Cycle de dépréciation

```
Version N.x   : fonctionnalité stable, fonctionnelle
Version N.m   : dépréciation annoncée (CHANGELOG + doc + avertissement optionnel)
                → alternative documentée obligatoire
                → fonctionnalité toujours fonctionnelle
Série N.x     : maintien garanti
Version (N+1) : retrait possible
```

### Durée minimale de maintien

**Règle :** une fonctionnalité stable dépréciée reste disponible au moins jusqu'à la
prochaine version MAJOR.

| Déprécié en | Maintenu jusqu'au moins | Retiré possible dès |
|---|---|---|
| 2.4.0 | Fin de la série 2.x | 1.0.0 stable |
| 2.x (quelconque) | Fin de la série 2.x | 1.0.0 stable |

**Exception :** une vulnérabilité de sécurité grave peut imposer un retrait
immédiat sans respecter cette durée (voir la section Exceptions de sécurité ci-dessous).

---

## Commandes CLI dépréciées

### Annonce

Ajouter dans `CHANGELOG.md` sous la section `### Modifié` ou `### Déprécié` :

```markdown
- `forge old:command` est dépréciée. Utiliser `forge new:command` à la place.
  Maintien garanti jusqu'à la prochaine version MAJOR.
```

### Avertissement runtime

Afficher un message clair sur `stderr` quand la commande dépréciée est invoquée :

```
AVERTISSEMENT — forge old:command est dépréciée.
Utiliser désormais : forge new:command
Suppression prévue : prochaine version MAJOR.
```

Exemple de pattern :

```python
def _warn_cmd_deprecated() -> None:
    print(
        "AVERTISSEMENT — cette commande est dépréciée. "
        "Utilisez la CLI officielle `forge`.",
        file=sys.stderr,
    )
```

### Retrait

Retirer la commande dans la version MAJOR suivante. Documenter le retrait dans
le CHANGELOG sous `### Supprimé`.

---

## API Python publique dépréciée

### Annonce

Ajouter un `DeprecationWarning` Python dans le module concerné :

```python
import warnings

def ancienne_fonction():
    warnings.warn(
        "ancienne_fonction() est dépréciée depuis Forge 2.4.0. "
        "Utiliser nouvelle_fonction() à la place. "
        "Suppression prévue à la prochaine version MAJOR.",
        DeprecationWarning,
        stacklevel=2,
    )
    return nouvelle_fonction()
```

Ajouter dans `CHANGELOG.md` et dans `docs/auth.md` ou `docs/reference.md`
la mention de la dépréciation.

### Maintien pendant la série 2.x

La fonction dépréciée reste fonctionnelle. Elle délègue à la nouvelle
implémentation ou conserve son comportement original.

### Exemple concret : core.security.hashing

`core.security.hashing` (PBKDF2 legacy) est déprécié en faveur de
`core.auth.password` (Argon2id). Il reste disponible pour la
compatibilité et la migration transparente des anciens hashes. Son retrait
est prévu dans la trajectoire 1.x stable.

### Retrait

Supprimer le module ou la fonction dans la version MAJOR. Documenter
la migration dans le guide de migration (`RELEASE-MIGRATION-GUIDE-001`).

---

## Options CLI dépréciées

### Annonce

Documenter dans `docs/reference.md` que l'option est dépréciée,
quelle option utiliser à la place, et depuis quelle version.

### Avertissement runtime

Si l'option est passée, afficher un avertissement avant d'exécuter la commande :

```
AVERTISSEMENT — L'option --ancien-flag est dépréciée.
Utiliser --nouveau-flag à la place.
Suppression prévue : prochaine version MAJOR.
```

L'option continue de fonctionner (elle est relayée vers la nouvelle option
si applicable).

### Retrait

Retirer l'option dans la version MAJOR suivante.

---

## Conventions projet dépréciées

### Exemples

- Renommage d'une clé JSON dans le format d'entité.
- Renommage d'une clé `.env`.
- Changement de nom d'un fichier généré.

### Règle

Ne pas casser les projets existants en silence. Documenter :

- quelle convention est dépréciée ;
- quelle convention la remplace ;
- depuis quand ;
- si Forge peut migrer automatiquement ou si une action manuelle est nécessaire.

Si une migration automatique est possible (ex. `forge migrate:config`),
la proposer sans l'imposer.

---

## Fichiers générés et compatibilité

Les fichiers générés une fois (contrôleurs, modèles, vues) ne sont pas régénérés
automatiquement. Une modification du gabarit de génération n'affecte pas les
fichiers existants.

Cependant, si le comportement attendu d'un fichier généré change et que les
anciens fichiers deviennent incompatibles :

- Documenter clairement ce qui a changé dans le CHANGELOG.
- Proposer un guide de migration dans `docs/` ou `CHANGELOG.md`.
- Ne pas imposer une régénération destructive sans `--force`.

---

## Messages d'avertissement

### Niveaux

| Contexte | Type d'avertissement |
|---|---|
| Commande CLI dépréciée | Message `AVERTISSEMENT` sur `stderr` |
| API Python publique | `warnings.warn(..., DeprecationWarning, stacklevel=2)` |
| Convention documentaire | Note dans `docs/` + entrée CHANGELOG |
| Clé `.env` dépréciée | Message au démarrage de l'application si détectée |

### Règles de forme

- Indiquer explicitement **ce qui est déprécié**.
- Indiquer **l'alternative recommandée**.
- Indiquer la **version de retrait prévue**.
- Ne pas bloquer l'exécution — la fonctionnalité dépréciée continue de fonctionner.

---

## Changelog

Chaque dépréciation doit figurer dans `CHANGELOG.md`.

Section recommandée : `### Modifié` ou `### Déprécié` (si la section est créée).

Exemple :

```markdown
### Modifié

- `core.security.hashing` est déprécié en faveur de `core.auth.password` (Argon2id).
  Retrait prévu dans la trajectoire 1.x stable. (AUTH-LEGACY-BOUNDARY-001)
```

Chaque retrait doit figurer sous `### Supprimé`.

---

## Retrait en version MAJOR

Un retrait de fonctionnalité stable est réservé à une version MAJOR (1.0.0, 2.0.0…).

Avant le retrait :

1. Vérifier que la dépréciation a bien été annoncée dans la série précédente.
2. Documenter le retrait dans le CHANGELOG sous `### Supprimé`.
3. Documenter la migration dans `docs/` si nécessaire.
4. Mettre à jour `docs/reference.md` et `docs/stability-contract.md`.
5. Supprimer les tests de la fonctionnalité retirée ou les adapter à la nouvelle.

---

## Exceptions de sécurité

Une vulnérabilité de sécurité grave peut imposer un retrait ou une modification
incompatible sans respecter le cycle normal de dépréciation.

Conditions pour une exception de sécurité :

- La fonctionnalité représente un risque d'exploitation active.
- Aucune correction rétrocompatible n'est possible (ex. algorithme de hachage cassé).
- Le risque de maintien dépasse le coût de la rupture.

Dans ce cas :

- Publier une version corrective (`PATCH` ou `MINOR`) en urgence.
- Documenter l'exception dans `CHANGELOG.md` sous `### Sécurité`.
- Mentionner explicitement que la rupture de compatibilité est due à une
  contrainte de sécurité.
- Proposer un chemin de migration aussi court que possible.

---

## Exemples

### Exemple 1 — Suppression de cmd/ (CMD-LEGACY-REMOVE-001, fait en 2.10.0)

- **Déprécié en** : Forge 2.0 (migration vers la CLI officielle `forge`).
- **Supprimé en** : Forge 2.10.0 / 3.0 (note pré-3.0 — suppression directe sans shim).
- **Alternative** : `forge make:entity`, `forge make:crud`, etc.
- **Référence** : ticket `CMD-LEGACY-REMOVE-001`.

### Exemple 2 — Dépréciation de core.security.hashing

- **Déprécié en** : Forge 2.1 (frontier API `core.auth` vs `core.security`).
- **Alternative** : `core.auth.password` (Argon2id).
- **Maintien** : PBKDF2 reste disponible pour vérifier d'anciens hashes et
  effectuer la migration transparente.
- **Retrait prévu** : Forge 1.x stable.
- **Référence** : ticket `AUTH-LEGACY-BOUNDARY-001`.

### Exemple 3 — Dépréciation de @require_auth (legacy decorator)

- **Déprécié en** : Forge 2.x.
- **Alternative** : `core.auth.session.login_required`.
- **Retrait prévu** : Forge 1.x stable.
- **Référence** : `docs/auth.md`, section "Modules core.security dépréciés".

---

## Ce que cette politique ne couvre pas encore

| Domaine | Ticket futur |
|---|---|
| Matrice de compatibilité Python / MariaDB / Node | `RELEASE-COMPAT-001` |
| Guide de migration détaillé entre versions majeures | `RELEASE-MIGRATION-GUIDE-001` |
| Politique LTS (Long Term Support) | `RELEASE-LTS-001` |
| Automatisation de la détection des dépréciations (outil de migration) | post-roadmap |
| Dépréciation de formats de fichiers générés avec migration automatique | post-roadmap |

---

## Voir aussi

- [Vue d'ensemble Release et compatibilité](release-and-compatibility.md)
- [Politique de release](release-policy.md) — règles MAJOR/MINOR/PATCH
- [Guide de migration](migration-guide.md) — gérer les dépréciations lors d'une migration
- [Contrat de stabilité](stability-contract.md) — ce qui peut et ne peut pas changer

---

*Guide défini lors de RELEASE-DEPRECATION-001 (Phase 8 — Release et compatibilité).*
