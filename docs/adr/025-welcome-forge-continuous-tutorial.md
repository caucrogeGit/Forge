# ADR-025 — welcome-forge : tutoriel continu manuel au lieu de starters par palier

## Statut

Accepté — Forge 1.0.0-beta.15 (ticket `STARTER-WELCOME-FORGE-TUTORIAL-ADR-025`).

---

## Date

2026-06-07

---

## Contexte

Le parcours pédagogique « welcome-forge » (premiers pas) est aujourd'hui une
série de **starters indépendants** : un par palier, chacun avec son propre
contrôleur, son `routes.py.snippet` et son `starter.json`, applicable par
`forge starter:build <id>` (ADR-023).

### État avant la décision

1. **Chaque palier repart de zéro.** Le palier 2 (`query-params`) crée un
   `QueryParamsController` distinct du `WelcomeController` du palier 1, et la
   page ré-explique les bases (imports, `BaseController`, groupe de routes)
   comme si le palier précédent n'existait pas. Le code d'un palier n'est jamais
   la suite du précédent.
2. **L'indépendance est une fin en soi.** ADR-016 pose le starter comme « démo
   pédagogique autonome » ; ADR-023 en fait une unité buildable isolément.
   Pour une *progression* « premiers pas », cette indépendance va à l'encontre
   de l'apprentissage : un débutant veut construire **un seul projet qui
   grandit**, pas réinstaller un starter neuf à chaque notion.
3. **La doc est déjà un tutoriel manuel.** Les pages disent déjà « créez
   manuellement les fichiers », et ADR-024 fait de `forge new` un projet nu.
   Le `forge starter:build <palier>` fait donc doublon avec un parcours qui se
   suit à la main.

### Faits techniques établis

- Les 11 paliers débutants couvrent des notions HTTP pures (1→9 : texte,
  paramètres, vue HTML, route dynamique, debug, JSON, CSRF, formulaire POST,
  validation) puis SQL (10→11 : lecture puis écriture sur `first_sql_messages`).
- Les starters intermédiaires/avancés qui touchent `first_sql_messages`
  embarquent **déjà** leur propre `CREATE TABLE IF NOT EXISTS` : supprimer le
  starter `first-sql` ne casse aucun starter survivant (dépendance purement
  narrative).
- Le garde-fou de neutralité du squelette (`tests/test_skeleton_guard_001.py`,
  ADR-024) interdit tout contenu welcome dans `forge_cli/skeleton/data/` : le
  tutoriel vit dans la **documentation**, pas dans le squelette.

---

## Décision

1. **D1 — Tutoriel continu manuel.** Le parcours welcome-forge niveau débutant
   devient un **tutoriel continu** : le learner construit, à la main, un seul
   projet qui grandit palier après palier. Le code suit le palier précédent au
   lieu de recommencer. Césure 9/2 : un `WelcomeController` accumule les méthodes
   des paliers 1→9 (HTTP pur), puis un `MessageController` porte les paliers
   SQL 10→11 (enseigne « nouveau domaine = nouveau contrôleur », charte §2). Un
   unique `mvc/routes.py` accumule toutes les routes.
2. **D2 — Suppression des 11 starters débutant.** Les dossiers
   `forge_cli/starters/data/<palier>/` des 11 paliers débutants sont retirés :
   il n'y a plus de `forge starter:build` par palier débutant.
3. **D3 — Le reste reste buildable.** Les niveaux intermédiaire et avancé de
   welcome-forge, ainsi que tous les parcours opt-in (iot, video, images, files,
   audio, mfa, rbac, workflow, stats, mail) et les starters CRUD, **restent** des
   starters indépendants `forge starter:build`.
4. **D4 — Francisation.** Les pages du parcours débutant sont mises en
   conformité avec le style francophone (CLAUDE.md §2.1 : retrait des tirets
   cadratins U+2014, anglicismes).
5. **D5 — Numérotation assouplie.** Le garde-fou de numérotation des starters
   n'exige plus une plage dense `1..N` : seule l'absence de doublon est requise.
   Les starters survivants ne sont pas renumérotés.

---

## Conséquences

### Positives

- Parcours débutant réellement progressif : un projet unique qui grandit, sans
  redite des bases. Meilleure pédagogie « premiers pas ».
- Une seule façon officielle de suivre le parcours débutant (charte §11), alignée
  sur le projet nu d'ADR-024 et sur les pages « créez manuellement ».
- Le squelette (ADR-024) reste strictement neutre : aucun contenu welcome n'y est
  ajouté.

### Limites / Risques

- Perte de la génération automatique (`forge starter:build`) pour les 11 paliers
  débutants (assumée : le parcours se tape à la main).
- Rupture des contrats de test par palier (contenu figé des contrôleurs/snippets)
  et des assertions « livré — starter `x` » : tests supprimés ou réécrits.
- État transitoire : débutant en tutoriel continu, intermédiaire/avancé encore en
  starters indépendants jusqu'à leurs propres chantiers.

---

## Alternatives écartées

### A — Continuité au niveau de la doc seulement, starters conservés

Garder les 11 starters indépendants et narrer la continuité par-dessus. Rejeté :
deux réalités parallèles (starter buildable vs tutoriel manuel), divergence
doc/starter, contraire au principe 11.

### B — Un seul contrôleur pour les 11 paliers

Tout empiler dans `WelcomeController`. Rejeté : aux paliers SQL le contrôleur
devient un fourre-tout, en tension avec « un palier = une responsabilité »
(charte §2). La césure 9/2 enseigne en plus « nouveau domaine = nouveau
contrôleur ».

### C — Renumérotation dense des starters survivants

Décrémenter le `number` des ~96 starters restants pour conserver `1..N`. Rejeté :
~96 éditions et risque sur des tests de contrat figeant un `number` précis, pour
un invariant cosmétique. D5 assouplit le test à la place.

---

## Hors périmètre de cet ADR

- Les niveaux intermédiaire et avancé de welcome-forge (chantiers ultérieurs).
- Tous les parcours opt-in et les starters CRUD.
- Le mécanisme `forge starter:build` lui-même, qui reste en place pour D3.

---

## Référence

- Tickets d'implémentation (séquence) : `STARTER-WELCOME-FORGE-TUTORIAL-ADR-025`,
  `STARTER-WELCOME-FORGE-DOC-CONTINUITY-001`, `STARTER-WELCOME-FORGE-TESTS-PIVOT-001`,
  `STARTER-WELCOME-FORGE-DROP-DATA-001`, `STARTER-WELCOME-FORGE-CLOSE-001`.
- Code et docs concernés : `docs/starters/welcome-forge/debutant/`,
  `docs/starters/index.md`, `forge_cli/starters/data/` (paliers débutants),
  `tests/meta/test_starter_progression_001.py`,
  `tests/meta/test_consolidation_starter_001.py`.
- ADR-016 Unification opt-in : `docs/adr/016-opt-in-unification.md` (amendé).
- ADR-023 `forge starter:build` canonique : `docs/adr/023-starter-build-canonical.md` (amendé).
- ADR-024 Bootstrap squelette dédié : `docs/adr/024-skeleton-bootstrap.md` (préservé).
- Charte : `CHARTE_DOC.md` (principes 1, 2, 8, 11 ; règle A).
