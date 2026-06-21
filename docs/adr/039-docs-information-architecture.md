# ADR-039 : Refonte de l'architecture d'information de `docs/` (cœur)

## Statut

Proposé, Forge 1.0.0-beta.x (ticket `ADR-DOCS-IA-001`).

Fait suite à l'ADR-038 (doc des opt-ins embarquée par paquet) : une fois les
douze opt-ins sortis de `docs/`, la structure cœur héritée laisse apparaître des
doublons, des frontières floues et un regroupement de nav incomplet.
Aucun fichier n'est déplacé avant validation de la cible et exécution séquencée
(modèle anti-casse de l'ADR-038).

---

## Date

2026-06-21

---

## Contexte

Audit de `docs/` après l'ADR-038. Problèmes constatés :

1. **Tas plat des opt-ins dans la nav.** Les douze `!include` figurent comme
   douze entrées sœurs de premier niveau, au lieu d'un tronc unique
   « Opt-ins officiels » (dette explicite laissée par l'ADR-038).
2. **Doublons de sujet.**
   - `features/crud.md` et `reference/crud.md` ;
   - `features/migrations.md`, `features/migration-guide.md` et
     `entities/migration-legacy-vers-canonique.md`.
3. **Modèle de données éclaté** entre `features/` (`entity_architecture.md`,
   `relations.md`) et `entities/` (`entity-schema.md`, `relations-schema.md`,
   `pivots-many-to-many.md`, `slugs.md`, `types-forge-mariadb.md`,
   `json-canonique.md`, `limites-contrats-json.md`, `entity-validate.md`,
   `vscode-json-schema.md`).
4. **`reference/` mélange** la vraie référence (`api.md`, `api-json.md`,
   `cli-commands.md`, `http.md`, `sessions.md`, `audit-auth.md`,
   `pages-publiques.md`, `profils.md`, `public-contract-1.0.md`,
   `runtime-errors-schema.md`, `vocabulaire-opt-in.md`) et des pages qui n'en
   relèvent pas (`markdown.md`, aide-mémoire Markdown ; `crud.md`, doublon).
5. **`features/` est un fourre-tout** : guides d'usage du cœur mêlés à des pages
   de référence et à des sujets périphériques (`imagemagick-logos.md`,
   `pdf.md`).
6. **Section nav trompeuse** : « Modules et starters » ne contient plus que des
   parcours cœur (`welcome-forge`, `welcome-helpers`, `welcome-markdown`) et le
   hub `starters/index.md`.
7. **Dossier mort** : `docs/concepts/` est vide.

Hors périmètre (ne pas « ranger ») :

- `history/` : archive brute volontaire (conventions D) ;
- `javascripts/ static/ stylesheets/ logos/` : assets MkDocs ;
- `starters-pedagogique/welcome-reseau` : support temporaire 2TNE, suppression
  déjà programmée (2026-06-28).

---

## Décision (cible proposée)

Règle directrice : **un sujet a un seul emplacement canonique**, et le nom du
dossier dit sa nature (apprendre / utiliser / référencer / opérer).

Buckets de premier niveau visés pour la nav (cœur) :

1. **Accueil** — `index`.
2. **Découvrir** — positionnement, « Bonjour Forge », prise en main, concepts,
   FAQ (regroupe `guide/`).
3. **Installer** — `install/` (inchangé, déjà cohérent).
4. **Apprendre (parcours)** — parcours cœur uniquement : `welcome-forge`,
   `welcome-helpers`, `welcome-markdown`, plus le tutoriel applicatif complet.
   Le hub `starters/index.md` est recentré sur le cœur (les opt-ins ont leur
   propre progression dans leur paquet).
5. **Guides du cœur** — guides d'usage : auth, CRUD, front, médias, PDF,
   profils, migrations (issus de `features/`, dédoublonnés).
6. **Modèle de données** — unifie `entities/` et les pages data de `features/`
   (`entity_architecture`, `relations`) en un seul bucket « Entités & relations ».
7. **Référence** — référence stricte uniquement (`reference/` nettoyé :
   `markdown.md` part vers « Contribuer / écrire la doc », le doublon `crud.md`
   est supprimé au profit du guide canonique).
8. **Déploiement** — `deployment/` (inchangé).
9. **Opt-ins officiels** — tronc unique regroupant les douze `!include`
   (referme la dette de l'ADR-038).
10. **Philosophie & contribution** — `philosophy/`, `contributing/`,
    `architecture/`.
11. **Projet** — `release/`, `roadmap/`, `testing/`, `project/`, `history/`.

Dédoublonnages actés :

- `crud` : un seul emplacement (guide du cœur) ; l'entrée `reference/crud.md`
  est supprimée ou réduite à un renvoi.
- `migrations` : fusionner `features/migrations.md` et
  `features/migration-guide.md` ; `entities/migration-legacy-vers-canonique.md`
  rejoint « Modèle de données ».
- `docs/concepts/` (vide) : supprimé.
- `reference/markdown.md` : déplacé hors de la référence.

---

## Plan d'exécution séquencé (anti-casse)

Mêmes garde-fous que l'ADR-038 : déplacements par `git mv`, recâblage des liens
entrants, mise à jour des tests `tests/meta/*`, `mkdocs build --strict` vert à
chaque étape, et lecture du **compteur** pytest (pas du tail).

1. **Quick win nav** : grouper les douze `!include` sous « Opt-ins officiels »
   (nav seulement, zéro déplacement). Referme la dette ADR-038.
2. **Parcours** : renommer/recentrer « Modules et starters » → « Apprendre »,
   nettoyer le hub `starters/index.md`.
3. **Modèle de données** : fusionner les pages data de `features/` dans un
   bucket « Entités & relations » avec `entities/`.
4. **Référence** : sortir `markdown.md`, dédoublonner `crud`, resserrer
   `reference/` sur la référence stricte.
5. **Guides du cœur** : recentrer `features/` sur les guides d'usage.
6. **Découvrir / Projet** : regrouper `guide/` et les sections projet ;
   supprimer le dossier mort `concepts/`.

Chaque étape est un ticket séparé (`DOCS-IA-<n>`), commit distinct, validé avant
le suivant. La nav (`mkdocs.yml`) est la source de l'IA ; les chemins disque
suivent la nav.

---

## Conséquences

**Positives :**

- Une seule porte d'entrée par sujet (principe 11 appliqué à la doc).
- Frontières de dossiers lisibles (apprendre / utiliser / référencer / opérer).
- Tronc opt-ins propre (dette ADR-038 close).

**Négatives / coûts :**

- Beaucoup de `git mv` + recâblage de liens + mise à jour de tests `meta`.
- Les URLs publiques de plusieurs pages cœur changent (acceptable en bêta,
  pas d'utilisateurs externes à protéger — note pré-1.0 de la charte).
- Risque de liens cassés : maîtrisé par `mkdocs build --strict` à chaque étape.

---

## Charte appliquée

- Principe 11 — une seule façon officielle (un sujet, un emplacement).
- Principe 2 — petits tickets (exécution par étapes `DOCS-IA-<n>`).
- Principe 6 — tester avant d'élargir (`--strict` + suite meta à chaque étape).
- Règle B — révéler avant de corriger (audit explicite ci-dessus).

---

## ADR liés

- **Fait suite à l'ADR-038** (doc opt-ins embarquée) : referme la dette du tronc
  de nav et range le cœur resté en place.
