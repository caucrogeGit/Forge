# Roadmap : Réorganisation & normalisation des starters

> **Document de planification** (ticket `STARTER-REORG-ROADMAP-001`).
> Cadre la réorganisation des starters Forge : archivage des applications,
> noms anglais, conventions de nommage explicites, renumérotation.
> Aucune phase n'est démarrée tant que le feu vert n'est pas donné.

## Objectif

Un système de starters **propre, anglais et conventionné** :

- **noms anglais** pour tous les starters ;
- la **dépendance** d'un starter (opt-in vs cœur) est **lisible dans son nom** ;
- les « applications » métier ne sont **plus** des starters (archivées, débranchées
  de Forge, conservées pour mémoire).

## Conventions de nommage actées

| Famille | Schéma | Exemples |
|---------|--------|----------|
| Progression de découverte | `welcome` + nom de concept | `welcome`, `query-params`, `first-html-view`, `first-sql`… |
| Capstone CRUD | `first-crud[-variante]` | `first-crud` (à la main), `first-crud-generated` (généré) |
| Starter d'**opt-in** | `welcome-optin-<module>` | `welcome-optin-iot`, `welcome-optin-mfa` |
| Starter d'**API cœur** | `<sujet>-core-<api>` | `users-core-auth` |

Le token central (`optin` / `core`) signale d'où vient la capacité démontrée.

### Starters multi-niveaux & structure des dossiers

Un sujet peut être augmenté de **niveaux** (découverte → intermédiaire → expert). Le
niveau est porté par le **préfixe** ; `welcome-` = niveau découverte :

```
<niveau>-optin-<module>   →  welcome-optin-iot, intermediate-optin-iot, expert-optin-iot
```

On **anticipe ce patron dès maintenant** : les docs sont **groupées par sujet** dans un
dossier (jamais à plat), une page par niveau + un `index.md` de sujet. La couche `data`,
elle, **reste à plat** (un dossier par starter buildable).

```
docs/starters/
    welcome/                      ← progression de découverte (paliers)
        welcome.md … first-sql-write.md, bilan.md, recapitulatif.md
    crud/                         ← sujet « CRUD » (capstones)
        index.md
        first-crud.md             (CRUD à la main, SQL visible)
        first-crud-generated.md   (CRUD généré, entité neutre)
    optin-iot/                    ← sujet opt-in IoT
        index.md
        welcome-optin-iot.md
    optin-mfa/                    ← sujet opt-in MFA
        index.md
        welcome-optin-mfa.md
    core-auth/                    ← sujet API cœur « auth »
        index.md
        users-core-auth.md
    old/                          ← applications archivées
        carnet-contacts/  communes-sejours/  suivi-comportement-eleves/

cli/starters/data/          ← À PLAT (inchangé), un dossier = un starter buildable
    welcome-optin-iot/  welcome-optin-mfa/  users-core-auth/
    first-crud/  first-crud-generated/  welcome/  query-params/  …
```

Règles :
- **docs groupées par sujet** : dossier `<sujet>/`, fichier = id du starter, plus un
  `index.md` de sujet (vue d'ensemble + parcours des niveaux) ;
- **data à plat** : `cli/starters/data/<id>/` ; le `doc_url` pointe vers le chemin
  sujet (ex. `/starters/optin-iot/welcome-optin-iot/`) ;
- **nav** : un groupe par sujet ; chaînage entre niveaux comme les paliers `welcome`.

## Décisions verrouillées

**Archivage** (applications, pas des starters) → `docs/starters/old/<id>/` + retrait du
registry Forge :

- `carnet-contacts`, `communes-sejours`, `suivi-comportement-eleves`

**Renommages :**

| Avant | Après | Raison |
|-------|-------|--------|
| `welcome-iot` | `welcome-optin-iot` | convention opt-in explicite |
| `auth-mfa` | `welcome-optin-mfa` | convention opt-in explicite |
| `utilisateurs-auth` | `users-core-auth` | anglais + convention API cœur |
| `premier-crud` | `first-crud` | anglais + famille `first-*` |
| `contact-simple` | `first-crud-generated` **(+ entité neutralisée)** | paire CRUD généré / à la main, sans notion métier |

**Renumérotation** : après archivage, compresser les `number` des starters restants
en `1..N` contigus (ordre relatif conservé).

---

## Phases

### Phase 0 : Convention de nommage (gouvernance)
**`STARTER-NAMING-CONVENTION-001`**, *à faire en premier : la règle écrite cadre
tous les renommages.*

- Formaliser les 4 familles de nommage dans
  [`docs/contributing/starter-welcome-model.md`](../contributing/starter-welcome-model.md)
  (section « nommage »).
- Option : ADR `016-starter-naming-convention.md` + entrée dans l'index ADR.
- Validation : `mkdocs build --strict`.

### Phase 1 : Archivage des applications (débranchement Forge)
**`STARTER-ARCHIVE-LEGACY-APPS-001`**, gros ticket.

- `git mv docs/starters/{carnet-contacts,communes-sejours,suivi-comportement-eleves}`
  → `docs/starters/old/<id>/` **+ relink** (les pages descendent d'un niveau :
  `../index.md` → `../../index.md`, etc.).
- Supprimer `cli/starters/data/<id>/` (sortie du registry / CLI / build).
- [`docs/starters/index.md`](../starters/index.md) : retirer des tableaux et sections,
  recâbler la chaîne « prochain starter ».
- `mkdocs.yml` : section nav « Anciennes applications (archive) » → `old/`.
- Landing (`mvc/views/landing/index.html` **+** `docs/index.html`) : retirer les cartes.
- Tests : adapter/retirer ceux qui traitent ces 3 comme starters actifs (canonical,
  e2e, relations, scaffold, navigation séquentielle, reposition).
- Validation : `mkdocs build --strict`, tests starters ciblés.

### Phase 2 : Renumérotation contiguë
**`STARTER-RENUMBER-CONTIGUOUS-001`**

- Compresser les `number` restants en `1..N`.
- Mettre à jour les tests qui figent un numéro (`test_starter_*_001`,
  `test_starter_cli`).
- *Peut être fusionnée avec la Phase 1 (même cause), mais isolée = diff plus lisible.*

### Phase 3 : Renommages (anglais + conventions + dossiers-sujets)
Un ticket par renommage. **Cible docs = dossier-sujet** (cf. structure ci-dessus,
avec `index.md` de sujet) ; **data reste à plat**. Chaque ticket : rename
`data/<ancien>/` → `data/<nouveau>/` + page `docs/starters/<sujet>/<id>.md`
(+ `index.md` de sujet) + `doc_url` + `aliases` + nav + catalogue + chaîne + landing
+ tests.

- **`STARTER-RENAME-WELCOME-OPTIN-IOT-001`** : `welcome-iot` → `welcome-optin-iot`
  (docs → `starters/optin-iot/`)
- **`STARTER-RENAME-WELCOME-OPTIN-MFA-001`** : `auth-mfa` → `welcome-optin-mfa`
  (docs → `starters/optin-mfa/`)
- **`STARTER-RENAME-USERS-CORE-AUTH-001`** : `utilisateurs-auth` → `users-core-auth`
  (docs → `starters/core-auth/`)
- **`STARTER-RENAME-FIRST-CRUD-001`** : `premier-crud` → `first-crud`
  (docs → `starters/crud/`)
- **`STARTER-RENAME-FIRST-CRUD-GENERATED-001`** : `contact-simple` → `first-crud-generated`
  (docs → `starters/crud/`) **+ neutralisation de l'entité** (`Contact` → entité neutre
  alignée sur `first-crud`, pour en faire un starter de *mécanisme*, CRUD généré, et
  non une app métier).

### Phase 4 : Cohérence finale & garde-fous
**`STARTER-REORG-CONSISTENCY-001`**

- Balayer [`index.md`](../starters/index.md),
  [`starter-welcome-model.md`](../contributing/starter-welcome-model.md), `README`,
  `forge-roadmap`, `CHANGELOG`.
- Recâbler la chaîne finale « prochain starter ».
- Garde-fou méta : « tous les noms de starters sont anglais et conformes aux
  conventions (`welcome-optin-*`, `*-core-*`, …) ».
- **Grand test final** : `pytest` + `ruff check .` + `python -m compileall -q .`
  + `mkdocs build --strict` + `git diff --check`.

---

## Points techniques / risques

- **Relink** (Phase 1) : les pages sous `old/` restent buildées par MkDocs, leurs
  liens relatifs doivent être recalculés sinon `mkdocs --strict` échoue.
- **Cascade tests numéros** (Phase 2) : plusieurs `test_starter_*_001` figent un
  numéro (`form-post`, `server-validation`, `first-sql`…).
- **Cascade renommages** (Phase 3) : chaque rename touche ~30-40 fichiers
  (cf. précédent `progression → welcome`).
- **Neutralisation d'entité** (`first-crud-generated`) : réécriture du manifeste
  d'entité + artefacts générés + tests associés.
- **Archives immuables** : les snapshots sous `docs/history/**` ne sont pas réécrits ;
  seules les références « état courant » sont mises à jour.
- **Landing** : source `mvc/views/landing/index.html` et généré `docs/index.html`
  à garder synchronisés.

## Ordre recommandé

`0 → 1 → 2 → 3 (5 renames) → 4`. Chaque phase = commit(s) atomique(s), validation
`mkdocs --strict` à chaque phase, grand test final en Phase 4.

## Statut

| Phase | Ticket | Statut |
|-------|--------|--------|
| 0 | STARTER-NAMING-CONVENTION-001 | à venir |
| 1 | STARTER-ARCHIVE-LEGACY-APPS-001 | à venir |
| 2 | STARTER-RENUMBER-CONTIGUOUS-001 | à venir |
| 3 | STARTER-RENAME-* (×5) | à venir |
| 4 | STARTER-REORG-CONSISTENCY-001 | à venir |
