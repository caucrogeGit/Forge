# ADR-028 — welcome-forge : tutoriel continu manuel sur les trois niveaux, un mini-projet par niveau

## Statut

Accepté — Forge 1.0.0-beta.15 (ticket `WELCOME-FORGE-LEVELS-ADR-028`).

Généralise [ADR-025](025-welcome-forge-continuous-tutorial.md) (qui ne couvrait
que le niveau débutant) et amende sa décision D3.

Amendé le 2026-06-15 (`DOCS-WELCOME-FORGE-INDEX-001`) : le point d'entrée du
parcours devient `index.md`, voir la section « Amendement » plus bas.

---

## Date

2026-06-08

---

## Contexte

[ADR-025](025-welcome-forge-continuous-tutorial.md) a converti le **niveau
débutant** de welcome-forge en tutoriel continu manuel : un seul projet que le
learner construit à la main, palier après palier, sans `forge starter:build`.
Elle a explicitement laissé **hors périmètre** les niveaux intermédiaire et
avancé (D3 : « le reste reste buildable »).

### État avant la décision

Le parcours welcome-forge est aujourd'hui **incohérent entre ses niveaux** :

| Niveau | Formalisme actuel |
|---|---|
| Débutant (12 paliers) | Tutoriel continu **manuel** (ADR-025) : un projet écrit à la main, sans `starter:build`. |
| Intermédiaire (9 paliers) | **Starters buildables** (`cli/starters/data/list-records`, `filter-list`, `pagination`…) : « Ce que ce starter montre », migrations autonomes. |
| Avancé (5 paliers) | **Starters buildables** (`relations`, `db-transaction`, `file-upload`, `json-api`) : même formalisme « starter ». |

Un learner qui passe de débutant à intermédiaire change donc complètement de
mode d'apprentissage (« j'écris le code » puis « je build une boîte et je la
lis »). Cette double réalité contredit le principe 11 de la charte (« une seule
façon officielle de faire chaque chose ») et l'esprit d'ADR-025.

### Faits techniques établis

- ADR-025 D5 a **assoupli la numérotation** des starters : seule l'absence de
  doublon est requise, plus aucune plage dense `1..N`. Retirer des starters ne
  force donc **aucune renumérotation** des survivants.
- ADR-024 fait de `forge new` un **projet nu** : un mini-projet par niveau se
  bootstrappe naturellement par un `forge new` propre.
- Les starters intermédiaires/avancés embarquent déjà leur propre
  `CREATE TABLE IF NOT EXISTS` : chacun peut redevenir un mini-projet autonome
  sans dépendre des autres niveaux.

---

## Décision

1. **D1 — Formalisme unique sur les trois niveaux.** Les niveaux intermédiaire
   et avancé adoptent le **même formalisme** que le débutant : un tutoriel
   continu manuel, où le learner écrit le code à la main, palier après palier.
   Plus aucun `forge starter:build` dans welcome-forge.
2. **D2 — Un mini-projet distinct par niveau.** Chaque niveau est un **mini-projet
   autonome** : il repart d'un `forge new` propre et grandit palier après palier.
   Un niveau ne continue plus narrativement le projet du niveau précédent ; on
   peut entrer directement en intermédiaire ou en avancé. Chaque niveau établit
   son propre modèle de données dès son premier palier (intermédiaire : une table
   travaillée par lister/filtrer/paginer/modifier/supprimer ; avancé : son propre
   fil conducteur relationnel).
3. **D3 — Suppression des starters buildables intermédiaire et avancé.** Les
   dossiers `cli/starters/data/<palier>/` des paliers intermédiaires (9) et
   avancés (5) de welcome-forge sont retirés. Le contrat public gelé des starters
   décroît d'autant ; les survivants ne sont **pas** renumérotés (ADR-025 D5).
4. **D4 — Bootstrap par niveau.** Chaque niveau a son préambule de démarrage
   (création du projet neuf, prérequis, modèle de données initial). La page
   `installation.md` du parcours reste le point d'entrée et oriente vers le
   bootstrap du niveau choisi.
5. **D5 — Opt-ins inchangés pour l'instant.** Les dix parcours opt-in (iot, video,
   images, files, audio, mfa, rbac, workflow, stats, mail) et les starters CRUD
   **restent** des starters buildables `forge starter:build`. L'unification de
   leur formalisme est une **question explicitement rouverte plus tard**, hors
   périmètre de cet ADR.

Cette décision **amende ADR-025 D3** (« intermédiaire et avancé restent
buildables ») et **lève** son point « hors périmètre » sur ces deux niveaux.

---

## Conséquences

### Positives

- Cohérence totale du parcours welcome-forge : un seul formalisme sur les trois
  niveaux (principe 11), aligné sur le projet nu d'ADR-024 et sur « refuser la
  magie cachée » (principe 3) et « préserver le code utilisateur » (principe 4).
- Chaque niveau est auto-contenu : un learner peut attaquer l'intermédiaire ou
  l'avancé sans rejouer tout le débutant.
- Le squelette (ADR-024) reste strictement neutre : le tutoriel vit dans la
  documentation, jamais dans `cli/skeleton/data/`.

### Limites / Risques

- Perte de la génération automatique (`forge starter:build`) pour les 14 paliers
  intermédiaires et avancés (assumée : tout se tape à la main).
- Rupture des contrats de test par palier (contenu figé des contrôleurs/snippets)
  et des assertions « livré — starter `x` » : tests supprimés ou réécrits en
  garde-fous de continuité, comme au pivot débutant.
- Réécriture documentaire des 14 paliers (du formalisme « starter » vers le
  formalisme « tutoriel continu manuel »), plus le bootstrap de chaque niveau.
- Le contrat public gelé des starters décroît : compteurs et garde-fous
  transverses à mettre à jour (sans renumérotation, ADR-025 D5).

---

## Alternatives écartées

### A — Garder intermédiaire/avancé buildables, narrer la continuité par-dessus

Conserver les 14 starters et raconter une progression manuelle au-dessus. Rejeté
pour la même raison qu'ADR-025 alternative A : deux réalités parallèles (starter
buildable vs tutoriel manuel), divergence doc/starter, contraire au principe 11.
C'est précisément l'état incohérent que cet ADR corrige.

### B — Un seul projet continu sur les trois niveaux

Un unique projet qui grandit du débutant à l'avancé. Rejeté : impose d'avoir fait
tout le débutant pour suivre l'intermédiaire, alourdit l'entrée dans les niveaux
supérieurs, et rend chaque niveau dépendant des précédents. Le mini-projet par
niveau (D2) offre des scopes auto-contenus, plus adaptés à des publics d'entrée
différents.

### C — Convertir aussi les parcours opt-in dans le même chantier

Unifier d'un coup welcome-forge et les dix parcours opt-in. Rejeté : périmètre
trop large pour un seul chantier ; welcome-forge (le cœur) sert de pilote, la
question des opt-ins est rouverte ensuite (D5).

---

## Hors périmètre de cet ADR

- Les dix parcours opt-in et les starters CRUD, qui restent buildables (D5).
- Le mécanisme `forge starter:build` lui-même, préservé pour D5.
- La refonte du contenu pédagogique des paliers (notions enseignées) : cet ADR
  fixe le formalisme et la structure, pas une réécriture du fond.

---

## Amendement (2026-06-15, `DOCS-WELCOME-FORGE-INDEX-001`)

Cet amendement révise le point d'entrée fixé par **D4**.

**Constat.** welcome-forge n'est pas un parcours opt-in : il n'installe aucune
brique, il s'appuie sur le cœur de Forge déjà présent dès qu'un projet existe.
Son ancien préambule `installation.md` réinstallait pourtant Forge et créait le
projet, en doublon avec les guides d'installation (`poste-linux.md`,
`windows-wsl.md`, `github.md`).
Cette duplication contredit le principe 11 (une seule façon officielle de faire
chaque chose) : Forge s'installe à un seul endroit, le guide d'installation.

**Décision.**

1. Le point d'entrée du parcours devient `index.md` (et non plus
   `installation.md`).
   `index.md` présente le parcours, pose comme **prérequis** un projet Forge
   déjà créé via un guide d'installation, et propose une **vérification**
   (`forge --version`, `forge doctor`) plutôt qu'une réinstallation.
2. La page `installation.md` de welcome-forge est **supprimée** : la création du
   projet n'appartient pas au parcours.
3. **Convention de point d'entrée des starters** : un starter **opt-in** garde
   une page `installation.md` (il installe réellement une brique) ; un starter
   **hors opt-in** a une page `index.md` (présentation et vérification, le projet
   étant un prérequis).
   welcome-forge est aujourd'hui le seul starter hors opt-in.

Le reste de l'ADR (tutoriel continu manuel, un mini-projet par niveau, D1 à D5)
est inchangé.

---

## Référence

- ADR généralisé : [ADR-025](025-welcome-forge-continuous-tutorial.md)
  (welcome-forge débutant en tutoriel continu, amendé D3).
- ADR-024 Bootstrap squelette dédié : [ADR-024](024-skeleton-bootstrap.md)
  (préservé : `forge new` = projet nu, base du mini-projet par niveau).
- Tickets d'implémentation (séquence prévue) : `WELCOME-FORGE-LEVELS-ADR-028`
  (cet ADR), puis conversion du niveau intermédiaire, conversion du niveau
  avancé, et clôture (recapitulatif, index, contrat gelé, garde-fous transverses).
- Code et docs concernés : `docs/starters/welcome-forge/intermediaire/`,
  `docs/starters/welcome-forge/avance/`, `docs/starters/welcome-forge/index.md`
  (point d'entrée depuis l'amendement du 2026-06-15),
  `docs/starters/welcome-forge/recapitulatif.md`, `docs/starters/index.md`,
  `cli/starters/data/` (paliers intermédiaires et avancés).
- Charte : `CHARTE_DOC.md` (principes 1, 2, 3, 4, 11 ; règle A).
