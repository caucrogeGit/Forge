# Politique LTS Forge

Ce document évalue l'intérêt d'une version LTS (Long Term Support) pour Forge
et définit les conditions à remplir avant qu'une telle version puisse être déclarée.

Il complète :

- [Politique de release](release-policy.md) — règles MAJOR/MINOR/PATCH
- [Politique de dépréciation](deprecation-policy.md) — cycle annonce → retrait
- [Matrice de compatibilité](compatibility.md) — Python, MariaDB, Node.js
- [Guide de migration](migration-guide.md) — passer d'une version à l'autre

---

## Objectif

Répondre clairement à la question :

> Forge doit-il proposer une version LTS maintenant, plus tard, ou pas encore ?

Ce document est une évaluation, pas une promesse. Il ne déclare pas de version LTS.

---

## Ce qu'est une LTS

Une version LTS (Long Term Support) est une version d'un logiciel qui bénéficie
d'un **support prolongé et documenté** au-delà du cycle normal de releases.

Elle implique un engagement explicite sur :

- la durée de support (souvent 2 à 5 ans) ;
- les types de corrections incluses (sécurité, bugs critiques) ;
- les types de changements exclus (nouvelles fonctionnalités, refactoring) ;
- la compatibilité maintenue pendant toute la durée du support ;
- la procédure de fin de support (EOL — End of Life) ;
- la communication proactive des corrections.

### Exemples de LTS connues

| Projet | Cycle LTS |
|---|---|
| Python | 5 ans de support actif |
| Ubuntu | 5 ans LTS (10 ans avec ESM) |
| Node.js | 30 mois LTS |
| Django | Versions LTS avec 3 ans de corrections sécurité |

---

## Ce qu'une LTS implique

Déclarer une LTS engage Forge sur plusieurs points :

1. **Maintenance active** : corrections de sécurité et bugs critiques pendant toute la durée.
2. **Stabilité de l'interface** : aucune rupture d'API stable pendant la période LTS.
3. **Compatibilité maintenue** : la matrice de compatibilité reste valide.
4. **Communication explicite** : les corrections sont documentées et les releases identifiées.
5. **Politique de fin de support** : une date ou version d'arrêt est annoncée à l'avance.
6. **Gestion humaine** : une capacité réelle à maintenir la branche LTS dans la durée.

Une LTS qui n'est pas tenue est pire que pas de LTS du tout.

---

## État actuel de Forge

### Ce qui est en place

| Domaine | État |
|---|---|
| Versionnement SemVer | Documenté (`RELEASE-POLICY-001`) |
| Politique de dépréciation | Documentée (`RELEASE-DEPRECATION-001`) |
| Matrice de compatibilité | Documentée (`RELEASE-COMPAT-001`) |
| Guide de migration | Créé (`RELEASE-MIGRATION-GUIDE-001`) |
| Audits de sécurité | 7 audits terminés |
| Tests | 6 722 tests (5 237 unitaires + E2E) |
| Documentation de production | Guide complet (`DEPLOY-PROD-SECURITY-DOC-001`) |
| Contrat de stabilité | Défini (`APP-STABILITY-CONTRACT-001`) |
| DX avancée | `forge doctor`, `project:check`, `project:audit` |
| Backends de session | Mémoire, fichier, MariaDB |

### Ce qui manque encore

| Domaine | Manque |
|---|---|
| API JSON légère | Pas encore créée |
| Documentation avancée | Pas encore restructurée en parcours |
| SQL versionné | Pas de système type Alembic |
| Tests E2E MariaDB | Opt-in uniquement, pas en CI automatique |
| Dettes sécurité | `SECURITY-CACHE-001`, `CRUD-RBAC-UI-001`, `E2E-UPLOAD-HTTP-001`, `SECURITY-UPLOAD-RATE-LIMIT-001` |
| Guide migration MAJOR | À créer avant Forge 1.0.0 stable |
| Forge Design | Projet compagnon pas encore disponible |

---

## Arguments pour une LTS

### 1. Forge 2.2.0 est une base sérieuse

Forge 2.2.0 est livré, documenté et fortement testé :

- 6 722 tests verts ;
- 7 audits de sécurité terminés ;
- CLI cohérente et documentée ;
- structure de projet stable ;
- contrat de stabilité explicite.

### 2. La politique de release est formalisée

La politique SemVer adaptée est documentée. Les règles de rupture compatible et
incompatible sont claires. Une LTS pourrait s'appuyer sur ce cadre sans ambiguïté.

### 3. La politique de dépréciation est en place

Le cycle `annonce → maintien → retrait` garantit qu'aucune rupture ne survient
sans préavis. Une branche LTS pourrait interdire tout retrait pendant sa durée.

### 4. La compatibilité est documentée

La matrice de compatibilité couvre Python {{python_min}}–3.14, MariaDB 10.11+ et Node.js.
Une LTS pourrait geler cette matrice pour toute sa durée.

### 5. Des projets réels peuvent s'appuyer sur Forge 2.x

Le starter Communes & Séjours est un démonstrateur viable. Des projets applicatifs
construits sur Forge 2.2.0 méritent une stabilité garantie dans le temps.

---

## Arguments contre une LTS immédiate

### 1. L'API JSON légère n'est pas encore créée

Une LTS couvrant Forge 2.x sans API JSON serait incomplète pour les usages
web modernes. L'ajout d'une API JSON après la déclaration LTS est risqué :
elle devrait être stable dès sa création.

### 2. La documentation avancée n'est pas restructurée

Les parcours pédagogiques (tutoriel 15 min, application complète, guide contributeur)
ne sont pas encore créés. Une LTS sur une documentation partielle crée une fausse
promesse de maturité.

### 3. Des dettes de sécurité restent ouvertes

Quatre tickets de sécurité identifiés lors des audits restent ouverts :

- `SECURITY-CACHE-001` — `Cache-Control: no-store` absent sur les pages auth
- `CRUD-RBAC-UI-001` — boutons Modifier/Supprimer sans guard `{% if can() %}`
- `E2E-UPLOAD-HTTP-001` — tests upload HTTP réels pas encore créés
- `SECURITY-UPLOAD-RATE-LIMIT-001` — rate limit sur les uploads absent

Ces dettes, même mineures, ne devraient pas faire partie d'une promesse LTS
sans être d'abord corrigées.

### 4. Les tests E2E MariaDB ne sont pas automatisés en CI

Les tests MariaDB réels sont opt-in (`FORGE_E2E_MARIADB=1`). Une LTS sérieuse
implique une CI complète, y compris avec une base de données réelle.

### 5. Le SQL versionné est absent

L'absence de migrations SQL versionnées (type Alembic) est une limite structurelle
pour les projets qui évoluent. Les projets LTS ont souvent des cycles de vie longs
avec des schémas SQL qui changent.

### 6. La capacité de maintenance LTS n'est pas encore évaluée

Une LTS implique un engagement humain dans la durée. Forge est un projet qui
évolue encore rapidement. S'engager sur 2 ou 3 ans de maintenance d'une branche
figée serait prématuré à ce stade.

---

## Scénarios possibles

### Scénario A — Pas de LTS maintenant (recommandé)

Forge continue en série 2.x sans promesse LTS.

**Avantages :**

- pas de promesse prématurée ;
- plus de liberté d'évolution vers l'API JSON, la documentation avancée ;
- les dettes de sécurité peuvent être corrigées sans contrainte LTS ;
- le projet reste agile.

**Inconvénients :**

- les projets applicatifs existants n'ont pas de garantie formelle de stabilité
  longue durée.

**Mitigation :** le [Contrat de stabilité](stability-contract.md) offre déjà
des garanties claires sur les API publiques en 2.x, sans aller jusqu'à une LTS.

---

### Scénario B — LTS candidate après Forge 2.5.0 ou 2.6.0

Une version future pourrait devenir candidate LTS après :

- Phase documentaire avancée terminée (DOC-STRUCTURE-001, DOC-15MIN-001, DOC-APP-COMPLETE-001) ;
- API JSON légère stable (API-JSON-001 à API-DOC-001) ;
- dettes de sécurité corrigées (SECURITY-CACHE-001, CRUD-RBAC-UI-001, E2E-UPLOAD-HTTP-001) ;
- tests E2E MariaDB intégrés en CI automatique ;
- guide de migration MAJOR 2.x → 1.0 disponible si applicable.

**Avantages :**

- LTS déclarée sur une base plus solide ;
- dettes résorbées avant l'engagement.

**Inconvénients :**

- délai avant LTS de 6 à 12 mois minimum selon la cadence de release.

---

### Scénario C — LTS après stabilisation de Forge 1.0.0

Forge attend la stabilisation de `1.0.0` pour déclarer sa première LTS.

**Avantages :**

- meilleure base contractuelle : les ruptures MAJOR sont passées ;
- la base LTS est plus propre car la dette héritée a été traitée dans MAJOR ;
- moins de risque de devoir corriger en LTS des comportements legacy.

**Inconvénients :**

- La première version stable `1.0.0` n'a pas encore de date définie ;
- les projets actuels sur Forge 2.x n'ont pas de garantie formelle longue durée ;
- délai potentiellement long.

---

## Critères avant de déclarer une LTS

Une LTS Forge ne peut être déclarée que si toutes les conditions suivantes
sont remplies :

| Critère | Statut actuel |
|---|---|
| Politique de release documentée | ✅ |
| Politique de dépréciation documentée | ✅ |
| Matrice de compatibilité documentée | ✅ |
| Guide de migration disponible | ✅ |
| Contrat de stabilité explicite | ✅ |
| Documentation avancée restructurée | ❌ |
| API JSON légère stable | ❌ |
| Dettes sécurité CRUD-RBAC-UI-001 / SECURITY-CACHE-001 corrigées | ❌ |
| Tests E2E MariaDB en CI automatique | ❌ |
| Engagement humain de maintenance évalué | ❌ |
| Politique EOL (fin de support) définie | ❌ |

---

## Durée de support envisageable

Si une LTS était déclarée, une durée réaliste pour un projet de cette taille serait :

| Horizon | Détail |
|---|---|
| 18 mois | Corrections critiques garanties |
| 24 mois | Corrections de sécurité garanties |
| Au-delà | Hors capacité actuelle |

Ces durées sont indicatives. Elles dépendent de la capacité de maintenance réelle.

---

## Ce qui serait supporté en LTS

Si une LTS était déclarée, le support couvrirait :

- corrections de vulnérabilités de sécurité identifiées ;
- corrections de bugs critiques bloquants (perte de données, crash reproductible) ;
- mises à jour de compatibilité (nouvelle version Python LTS, MariaDB LTS) ;
- mise à jour des dépendances avec vulnérabilités identifiées.

---

## Ce qui serait exclu du support LTS

| Exclu | Raison |
|---|---|
| Nouvelles fonctionnalités | Risque de rupture, hors périmètre LTS |
| Refactoring | Hors périmètre LTS |
| Nouvelles commandes CLI | Hors périmètre LTS |
| Amélioration de performance | Hors périmètre LTS sauf régression |
| Support de nouvelles versions MariaDB | Si introduction incompatibilité |
| Corrections de comportements non documentés | Hors périmètre LTS |

---

## Recommandation

Sur la base de cette évaluation :

**Forge ne doit pas déclarer de version LTS maintenant.**

Les raisons principales :

1. Les dettes de sécurité identifiées doivent être corrigées avant tout engagement LTS.
2. L'API JSON légère n'est pas encore créée — promettre une LTS sans API JSON
   gèlerait une version incomplète.
3. La documentation avancée n'est pas structurée — les utilisateurs d'une LTS
   ont besoin d'une documentation pédagogique complète.
4. Les tests E2E MariaDB ne sont pas automatisés — une LTS sans CI MariaDB
   réelle est une promesse fragile.
5. La capacité humaine de maintenance LTS n'a pas été évaluée formellement.

---

## Décision actuelle

```text
Décision : Forge ne déclare pas encore de version LTS.

Forge peut préparer une future version LTS candidate après :
- stabilisation de la documentation avancée ;
- création de l'API JSON légère ;
- correction des dettes de sécurité restantes ;
- intégration des tests E2E MariaDB en CI automatique ;
- évaluation formelle de la capacité de maintenance.

La LTS candidate la plus réaliste serait une version `1.0.0` stable ou une version ultérieure de la série 1.x.
```

---

## Tickets à terminer avant une LTS

| Ticket | Domaine |
|---|---|
| `DOC-STRUCTURE-001` | Documentation par parcours |
| `DOC-15MIN-001` | Tutoriel "15 minutes avec Forge" |
| `DOC-APP-COMPLETE-001` | Tutoriel application complète |
| `DOC-CONTRIBUTE-001` | Guide contribuer |
| `API-JSON-001` à `API-DOC-001` | API JSON légère |
| `SECURITY-CACHE-001` | Cache-Control sur pages auth |
| `CRUD-RBAC-UI-001` | Guards RBAC UI dans templates CRUD |
| `E2E-UPLOAD-HTTP-001` | Tests upload HTTP réels |
| `SECURITY-UPLOAD-RATE-LIMIT-001` | Rate limit uploads |
| `E2E-MARIADB-CI` | Tests MariaDB en CI automatique |
| Évaluation capacité maintenance LTS | Décision humaine |
| Politique EOL explicite | À définir avant déclaration LTS |

---

## Voir aussi

- [Vue d'ensemble Release et compatibilité](release-and-compatibility.md)
- [Politique de release](release-policy.md) — règles MAJOR/MINOR/PATCH
- [Politique de dépréciation](deprecation-policy.md) — cycle annonce → retrait
- [Contrat de stabilité](stability-contract.md) — garanties Forge 2.x
- [Matrice de compatibilité](compatibility.md) — Python, MariaDB, Node.js

---

*Guide défini lors de RELEASE-LTS-001 (Phase 8 — Release et compatibilité).*
