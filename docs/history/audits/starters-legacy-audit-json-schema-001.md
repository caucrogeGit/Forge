# Audit — Starters en format legacy JSON Schema

**Ticket** : STARTERS-LEGACY-001  
**Date** : 2026-05-18  
**Auteur** : Forge (audit automatique post-roadmap ENTITY-CONTRACT)  
**Périmètre** : `forge_cli/starters/data/` — tous les starters distribués avec la CLI

**Mise à jour** : 2026-05-18 — `contact-simple` migré par STARTERS-MIGRATE-001.
**Mise à jour** : 2026-05-18 — `utilisateurs-auth` migré par STARTERS-MIGRATE-002.
**Mise à jour** : 2026-05-18 — `carnet-contacts` migré par STARTERS-MIGRATE-003.
**Mise à jour** : 2026-05-18 — `suivi-comportement-eleves` migré par STARTERS-MIGRATE-004.
**Mise à jour** : 2026-05-18 — `communes-sejours` migré par STARTERS-MIGRATE-005. Tous les starters avec entités/relations sont désormais en format canonique.

---

## 1. Résumé exécutif

L'audit porte sur 6 starters présents dans `forge_cli/starters/data/`.
**100 % des fichiers entité/relation audités utilisent le format legacy** (format_version: 1).
Aucun starter n'a encore migré vers le format canonique (schema_version: "1.0").

| Métrique | Valeur |
|---|---|
| Starters audités | 6 |
| Starters avec fichiers entité/relation | 5 |
| Starters sans entité (controllers-only) | 1 (`auth-mfa`) |
| Fichiers entité `.json` (legacy) | 0 (12 à l'audit initial) |
| Fichiers relation `.json` (legacy) | 0 (3 à l'audit initial) |
| Fichiers en format canonique | 12 entités + 3 relations |
| Taux de migration | 100 % entités (12/12), 100 % relations (3/3) |

---

## 2. Matrice d'audit par starter

### 2.1 `auth-mfa`

| Attribut | Valeur |
|---|---|
| Type | Controllers-only (pas d'entité ni de relation) |
| Fichiers entité | 0 |
| Fichiers relation | 0 |
| Format | N/A |
| Impact migration | Néant |

Ce starter ne génère aucun fichier entité — il est hors périmètre de migration.

---

### 2.2 `contact-simple`

| Attribut | Valeur |
|---|---|
| Fichier entité | `contact.json` |
| Fichiers relation | 0 |
| Format | legacy (`format_version: 1`) |
| Entité | `Contact` → table `contact` |

**Champs (5 dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (primary_key, auto_increment) | PK implicite — à retirer des fields[] |
| `nom` | VARCHAR(80) | string |
| `prenom` | VARCHAR(80) | string |
| `email` | VARCHAR(120) | string ou email |
| `telephone` | VARCHAR(20) | string |

**Anomalies :** aucune anomalie particulière. PK nommée `id` (standard).

---

### 2.3 `carnet-contacts`

| Attribut | Valeur |
|---|---|
| Fichiers entité | `entities/contact.json`, `entities/ville.json` |
| Fichier relation | `relations.json` (1 relation : Contact → Ville) |
| Format | legacy (`format_version: 1`) |

**Entité Contact (6 champs dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (pk, ai, column=ContactId) | PK implicite — à retirer |
| `nom` | VARCHAR(80) | string |
| `prenom` | VARCHAR(80) | string |
| `email` | VARCHAR(120) | string ou email |
| `telephone` | VARCHAR(20) | string |
| `ville_id` | INT | integer (FK) |

**Entité Ville (3 champs dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (pk, ai, column=VilleId) | PK implicite — à retirer |
| `nom` | VARCHAR(100) | string |
| `code_postal` | VARCHAR(10) | string |

**Relation :**

| Clé legacy | Valeur |
|---|---|
| `from_entity` | Contact |
| `to_entity` | Ville |
| `foreign_key_name` | fk_contact_ville |

**Anomalies :**
- Clé `column` présente sur le champ PK (`"column": "ContactId"`, `"column": "VilleId"`) — alias non standard, sans équivalent canonique direct.

---

### 2.4 `utilisateurs-auth`

| Attribut | Valeur |
|---|---|
| Fichier entité | `entities/utilisateur.json` |
| Fichiers relation | 0 |
| Format | legacy (`format_version: 1`) |
| Entité | `Utilisateur` → table `utilisateur` |

**Champs (7 dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `utilisateur_id` | INT (pk, ai) | PK implicite — à retirer |
| `login` | VARCHAR(80) | string |
| `prenom` | VARCHAR(80) | string |
| `nom` | VARCHAR(80) | string |
| `password_hash` | VARCHAR(255) | password ou string |
| `email` | VARCHAR(120) | string ou email |
| `actif` | BOOLEAN | boolean |

**Anomalies :**
- PK nommée `utilisateur_id` (et non `id`) — déviation par rapport à la convention standard Forge (PK implicite dans le format canonique).

---

### 2.5 `suivi-comportement-eleves`

| Attribut | Valeur |
|---|---|
| Fichiers entité | `entities/cours.json`, `entities/eleve.json`, `entities/observation_cours.json`, `entities/utilisateur.json` |
| Fichier relation | `relations.json` (2 relations) |
| Format | legacy (`format_version: 1`) |

**Entité Cours (4 champs dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (pk, ai) | PK implicite |
| `date_cours` | DATE | date |
| `titre` | VARCHAR(120) | string |
| `classe` | VARCHAR(40) | string |

**Entité Eleve (5 champs dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (pk, ai) | PK implicite |
| `nom` | VARCHAR(80) | string |
| `prenom` | VARCHAR(80) | string |
| `classe` | VARCHAR(40) | string |
| `actif` | BOOLEAN | boolean |

**Entité ObservationCours (10 champs dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (pk, ai) | PK implicite |
| `eleve_id` | INT | integer (FK) |
| `cours_id` | INT | integer (FK) |
| `ne_travaille_pas` | BOOLEAN | boolean |
| `bavarde` | BOOLEAN | boolean |
| `dort` | BOOLEAN | boolean |
| `telephone` | BOOLEAN | boolean |
| `perturbe` | BOOLEAN | boolean |
| `refuse_consigne` | BOOLEAN | boolean |
| `remarque` | TEXT | text |

**Entité Utilisateur (7 champs dont 1 PK) :**  
Même structure que `utilisateurs-auth/entities/utilisateur.json` — PK nommée `utilisateur_id`.

**Relations (2) :**

| Relation | from_entity | to_entity | foreign_key_name |
|---|---|---|---|
| observation_cours_eleve | ObservationCours | Eleve | fk_observation_cours_eleve |
| observation_cours_cours | ObservationCours | Cours | fk_observation_cours_cours |

**Anomalies :**
- PK `utilisateur_id` (même cas que `utilisateurs-auth`).
- Entité `ObservationCours` a un champ `telephone` de type BOOLEAN — homonyme trompeur avec un champ métier de type string.

---

### 2.6 `communes-sejours`

| Attribut | Valeur |
|---|---|
| Fichiers entité | `files/mvc/entities/commune/commune.json`, `demande_sejour/demande_sejour.json`, `hebergement/hebergement.json`, `proprietaire/proprietaire.json` |
| Fichier relation | `files/mvc/entities/relations.json` (3 relations) |
| Format | legacy (`format_version: 1`) |

**Entité Commune (6 champs dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (pk, ai) | PK implicite |
| `nom` | VARCHAR(100) | string |
| `code_postal` | VARCHAR(10) | string |
| `description` | TEXT | text |
| `created_at` | DATETIME | datetime |
| `updated_at` | DATETIME | datetime |

**Entité Proprietaire (6 champs dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (pk, ai) | PK implicite |
| `nom` | VARCHAR(100) | string |
| `email` | VARCHAR(120) | string ou email |
| `telephone` | VARCHAR(20) | string |
| `created_at` | DATETIME | datetime |
| `updated_at` | DATETIME | datetime |

**Entité Hebergement (11 champs dont 1 PK + section `media`) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (pk, ai) | PK implicite |
| `titre` | VARCHAR(200) | string |
| `slug` | VARCHAR(200) | string |
| `description` | TEXT | text |
| `adresse` | VARCHAR(255) | string |
| `capacite` | INT | integer |
| `commune_id` | INT | integer (FK) |
| `proprietaire_id` | INT | integer (FK) |
| `is_published` | BOOLEAN | boolean |
| `created_at` | DATETIME | datetime |
| `updated_at` | DATETIME | datetime |

Section `media` présente (clé `"media": [...]`) — pas de correspondance dans le format canonique actuel.

**Entité DemandeSejour (11 champs dont 1 PK) :**

| Champ | sql_type legacy | type Forge canonique |
|---|---|---|
| `id` | INT (pk, ai) | PK implicite |
| `hebergement_id` | INT | integer (FK) |
| `nom` | VARCHAR(100) | string |
| `email` | VARCHAR(120) | string ou email |
| `telephone` | VARCHAR(20) | string |
| `message` | TEXT | text |
| `date_arrivee` | DATE | date |
| `date_depart` | DATE | date |
| `nombre_personnes` | INT | integer |
| `statut` | VARCHAR(30) | string |
| `created_at` | DATETIME | datetime |

**Relations (3) :**

| Relation | from_entity | to_entity | foreign_key_name |
|---|---|---|---|
| hebergement_commune | Hebergement | Commune | fk_hebergement_commune |
| hebergement_proprietaire | Hebergement | Proprietaire | fk_hebergement_proprietaire |
| demande_hebergement | DemandeSejour | Hebergement | fk_demande_hebergement |

**Anomalies :**
- Section `"media"` sur `Hebergement` — clé non supportée par le schéma canonique (forge-mvc-media, non intégré au format entity).
- Starter le plus complexe : 4 entités, 3 relations, 11 champs max.

---

## 3. Table de correspondance des types SQL → Forge

| sql_type legacy | type Forge canonique |
|---|---|
| `INT` | `integer` |
| `VARCHAR(N)` | `string` |
| `TEXT` | `text` |
| `BOOLEAN` | `boolean` |
| `DATE` | `date` |
| `DATETIME` | `datetime` |

Types Forge disponibles (field.schema.json) : `string`, `text`, `integer`, `big_integer`, `float`, `decimal`, `boolean`, `date`, `datetime`, `email`, `password`, `json`.

---

## 4. Risques identifiés

| Risque | Sévérité | Détail |
|---|---|---|
| `entity:validate` produit 28 erreurs sur tout projet issu de `forge new` | Haute | Les starters injectent des entités legacy — la commande de validation est inutilisable pour les utilisateurs |
| `starter:build` suivi de `entity:validate` → 55 erreurs | Haute | Cumul : entités du starter + entité media.json (legacy, clonée depuis GitHub) |
| Clé `column` (alias SQL) sans équivalent canonique | Moyenne | `carnet-contacts` : perte de l'alias lors de la migration si non prévu dans le schéma cible |
| PK non standard (`utilisateur_id`) | Moyenne | Doit être traité en amont (convention PK implicite dans le format canonique) |
| Section `media` (Hebergement) | Moyenne | Aucun équivalent dans entity.schema.json — à traiter séparément ou à exclure du format entité |
| Duplication Utilisateur (2 starters identiques) | Faible | `utilisateurs-auth` et `suivi-comportement-eleves` partagent la même entité Utilisateur — cohérence à maintenir lors de la migration |

---

## 5. Tickets de migration proposés

La migration est hors périmètre du présent ticket (audit seul). Les tickets suivants sont proposés à titre indicatif :

| Ticket proposé | Périmètre |
|---|---|
| STARTERS-MIGRATE-001 | `contact-simple` — 1 entité, 0 relation (cas le plus simple) |
| STARTERS-MIGRATE-002 | `utilisateurs-auth` — 1 entité (PK non standard), 0 relation |
| STARTERS-MIGRATE-003 | `carnet-contacts` — 2 entités (alias column), 1 relation |
| STARTERS-MIGRATE-004 | `suivi-comportement-eleves` — 4 entités, 2 relations |
| STARTERS-MIGRATE-005 | `communes-sejours` — 4 entités, 3 relations, section media |

Ordre de migration recommandé : du plus simple (MIGRATE-001) au plus complexe (MIGRATE-005).

---

## 6. Commandes de validation exécutées

```
forge entity:validate mvc/entities/
# → 28 erreurs sur projet vierge issu de forge new

forge starter:build carnet-contacts
forge entity:validate mvc/entities/
# → 55 erreurs après injection du starter
```

Ces traces confirment que les starters legacy sont incompatibles avec `entity:validate` en l'état.

---

## 7. Périmètre exclu

- `auth-mfa` : pas de fichier entité/relation — hors périmètre de migration.
- `forge new` clone `media.json` depuis GitHub — hors scope du présent audit (fichier externe au dépôt Forge).
- La migration effective des fichiers est réservée aux tickets STARTERS-MIGRATE-001 à STARTERS-MIGRATE-005.
- La section `media` de `hebergement.json` est documentée mais sa migration est hors scope immédiat.

---

## 8. Clôture de la migration des starters

**Ticket de clôture** : STARTERS-MIGRATE-CLOSE-001
**Date de clôture** : 2026-05-18
**Statut** : terminée

### 8.1 État final

Tous les starters contenant des entités ou relations sont migrés vers le format JSON canonique (`schema_version: "1.0"`).

| Starter | Entités | Relations | Format final | entity:validate | build:model | Statut |
|---|---:|---:|---|---|---|---|
| `contact-simple` | 1 | 0 | canonique | OK | OK | migré |
| `utilisateurs-auth` | 1 | 0 | canonique | OK | OK | migré |
| `carnet-contacts` | 2 | 1 | canonique | OK | OK | migré |
| `suivi-comportement-eleves` | 4 | 2 | canonique | OK | OK | migré |
| `communes-sejours` | 4 | 3 | canonique | OK | non applicable (skeleton) | migré |
| `auth-mfa` | 0 | 0 | sans entité | N/A | N/A | hors périmètre |

### 8.2 Traces legacy

Aucune trace de clé legacy (`format_version`, `sql_type`, `primary_key`, `auto_increment`, `from_entity`, `to_entity`, `foreign_key_name`) ne subsiste dans les fichiers d'entité ou de relation des starters distribués.

### 8.3 Décisions prises lors de la migration

- **PK non standard `utilisateur_id`** : normalisée en `id` canonique (PK implicite) dans `utilisateurs-auth` et `suivi-comportement-eleves`.
- **Alias `column` (`ContactId`, `VilleId`)** : supprimé de `carnet-contacts` ; les colonnes canoniques (`Id`, `EleveId`, etc.) sont dérivées automatiquement par `_column_from_name`.
- **Section `media` de `hebergement.json`** : supprimée (Option B — hors schéma canonique, non fonctionnelle dans le starter skeleton). Support media canonique à traiter séparément si besoin.

### 8.4 Limites restantes

- Le support legacy du core (`format_version: 1`) n'est **pas supprimé** — il reste fonctionnel pour les projets existants. Sa dépréciation nécessite une décision séparée (`LEGACY-POLICY-001`).
- La section `media` de `communes-sejours/hebergement.json` a été supprimée. Un ticket `MEDIA-CONTRACT-001` est proposé si un support media canonique dans le format entité est requis.
- `auth-mfa` ne contient pas d'entités à migrer — hors périmètre de la campagne.
- La publication PyPI reste hors périmètre de cette campagne de migration.
