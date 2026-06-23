# ADR-044 — Le dépôt Forge ne porte que le framework

## Statut

Proposé — bêta publique 1.0 (`1.0.0-beta.x`).

---

## Date

2026-06-23

---

## Contexte

Le dépôt Forge mélange aujourd'hui deux choses de natures différentes :

1. **Le framework** : `core/`, `cli/`, `packages/` (opt-ins), `schemas/`,
   `docs/`, `forge.py`, `pyproject.toml`, `MANIFEST.in`, la suite de tests.
2. **Une application** : `app.py`, `config.py`, `mvc/` (contrôleurs `auth`,
   `mfa`, `welcome`, entités `media`, vues dont la **landing**), `static/`,
   `storage/`, `env/`, `translations/`.

Cette application racine est l'app de *dogfooding* qui a servi à développer
Forge. Sa présence contredit frontalement le principe 1 de la charte
(séparer framework et application métier) : le dépôt d'un framework ne devrait
pas embarquer une application métier.

### Ce qui a changé depuis ADR-024

ADR-024 a créé un squelette dédié (`cli/skeleton/data/`) comme source unique de
`forge new`, mais a explicitement **écarté** (alternative B) le retrait du
`mvc/` racine, au motif qu'il était « référencé par la quasi totalité de la
suite de tests » et que le déplacer « casserait des centaines de tests ».

Cet argument n'est plus valide :

- **Le squelette est désormais l'application de référence complète et curée**
  (`cli/skeleton/data/` : `app.py`, `config.py`, `mvc/`, `static/`, `storage/`,
  `env/`, `schemas/`). `forge new` ne dépend plus du `mvc/` racine.
- **Le couplage réel des tests au `mvc/` racine est faible.** Sur l'ensemble
  de la suite, seuls **8 fichiers importent réellement le paquet `mvc`** et
  **10 référencent `app`/`config`** racine. Les ~94 autres occurrences de
  `mvc/` sont des assertions sur des **projets temporaires générés**, sans lien
  avec l'app racine.
- **ADR-043** a achevé la documentation embarquée du cœur et du CLI : le dépôt
  est mûr pour une séparation nette framework / application.

### Cas de la landing

La landing marketing de forgemvc.com est aujourd'hui *générée* :
`forge sync:landing` (`cli/assets/sync_landing.py`) copie
`mvc/views/landing/index.html` vers `docs/index.html`, et `static/` vers
`docs/static/`.

Fait décisif : **la sortie `docs/index.html` et `docs/static/` sont déjà
versionnées** et sont les fichiers réellement servis par le site
(nav mkdocs : `Accueil: index.html`). Rendre cette sortie canonique ne coûte
donc aucune perte visuelle : il suffit de cesser de la régénérer.

---

## Décision

1. **Supprimer l'application de dogfooding racine.** Sont retirés du dépôt :
   `app.py`, `config.py`, `mvc/`, `static/`, `storage/`, `translations/` et le
   `env/` applicatif. Le squelette `cli/skeleton/data/` devient la **seule**
   application de référence du dépôt.

2. **Rendre la landing canonique dans `docs/`.** `docs/index.html` et
   `docs/static/` deviennent les sources directes, éditées et buildées sur
   place (Tailwind compilé vers `docs/static/`). Sont supprimés : la source
   `mvc/views/landing/`, le `static/` racine, la commande `sync:landing`
   (`cli/assets/sync_landing.py`), son entrée de dispatch, sa doc embarquée
   (`cli/assets/docs/sync_landing.md`) et ses tests.

3. **`schemas/` racine reste.** Les schémas JSON sont une ressource du
   framework (canonique, gardée en synchronisation avec ses copies par le
   garde-fou existant). Ils ne font pas partie de l'application et sont
   conservés.

4. **Reprendre les tests couplés.** Les 8 tests important le paquet `mvc`
   racine et les 10 référençant `app`/`config` racine sont réécrits pour
   s'appuyer sur un **projet temporaire généré depuis le squelette** (ou une
   fixture dédiée sous `tests/fixtures/`), jamais sur une application racine.

5. **Le dépôt framework ne se « run » pas.** `forge run` cible un projet
   applicatif ; le dépôt Forge n'en est plus un. Le développement et la
   vérification manuelle se font via un projet créé par `forge new`. La
   documentation contributeur le précise.

6. **Lever l'anti-dérive d'ADR-024.** La duplication `app.py`/`config.py`
   (racine de dogfood vs squelette) disparaît avec l'app racine : le squelette
   devient la copie unique. Le garde-fou de cohérence correspondant est retiré
   ou requalifié (il n'a plus de seconde copie à comparer).

---

## Conséquences

### Positives

- Le dépôt devient réellement « framework only » : plus aucune application
  métier embarquée (principe 1), noyau et opt-ins seuls (principe 8).
- La landing survit sans perte visuelle, mais sans pipeline de génération ni
  couplage à une application : un artefact statique committé sous `docs/`.
- Une seule application de référence (le squelette), donc une seule façon
  officielle de représenter « un projet Forge » (principe 11) ; fin de la
  duplication dogfood / squelette d'ADR-024.
- Surface de maintenance réduite : suppression de `sync:landing`, du `static/`
  racine et du build Tailwind applicatif racine.

### Limites

- Rupture interne : la commande `forge sync:landing` disparaît (retrait direct,
  sans alias, convention pré-1.0 de `CLAUDE.md`). La landing s'édite désormais
  directement dans `docs/`.
- Coût de reprise des tests couplés (8 + 10 fichiers) vers des projets
  temporaires ou des fixtures.
- La vérification manuelle « end to end » du framework passe désormais par un
  `forge new`, plus par un `forge run` à la racine du dépôt.

---

## Alternatives écartées

### A — Déplacer l'app racine en fixture de test (`tests/fixtures/app/`)

Conserver l'application comme harnais de test explicite plutôt que la
supprimer.

Rejeté : maintient une application complète dans le dépôt, simplement
renommée. La cause (une app métier vit dans le framework) n'est pas retirée
(règle A). Le squelette joue déjà le rôle d'application de référence ; une
fixture supplémentaire serait une seconde source à maintenir.

### B — Extraire l'app dans un dépôt séparé

Déplacer l'application vers un dépôt distinct (démo/dogfooding).

Rejeté pour l'instant : crée un second dépôt à maintenir et à versionner en
phase avec le framework, pour un bénéfice nul par rapport à la suppression. Le
squelette suffit comme référence, et un projet de démonstration peut toujours
être régénéré par `forge new`.

### C — Conserver la landing générée

Garder `sync:landing` et la source `mvc/views/landing/`.

Rejeté : impose de conserver un fragment d'application (`mvc/views/`) et un
`static/` racine uniquement pour la landing, ce qui contredit la décision. La
sortie étant déjà committée, la rendre canonique est sans perte.

### D — Remplacer la landing par un `docs/index.md` Material

Supprimer le HTML marketing au profit d'une page d'accueil Markdown standard.

Rejeté : jette le design de landing soigné à l'approche de la 1.0 pour une page
générique, alors que conserver `docs/index.html` canonique atteint l'objectif
sans cette perte.

---

## Hors périmètre de cet ADR

- Le détail du nettoyage des dossiers non versionnés présents sur disque
  (`TestForge101/`, `_/`, `sample.json`, `cert.pem`, `key.pem`) : hygiène de
  poste, sans impact sur le dépôt.
- Le détail de la stratégie de fixture vs projet temporaire pour chaque test
  repris (tranché à l'implémentation).
- L'organisation interne future de `docs/` autour de la landing canonique.

---

## Référence

- ADR-001 Périmètre et trajectoire : voir aussi ADR-004.
- ADR-004 Périmètre du core : `docs/adr/004-core-perimeter.md`.
- ADR-023 `forge starter:build` canonique : `docs/adr/023-starter-build-canonical.md`.
- ADR-024 Bootstrap par squelette dédié : `docs/adr/024-skeleton-bootstrap.md`
  (cet ADR rouvre et tranche son alternative B).
- ADR-043 Documentation embarquée cœur/CLI : `docs/adr/043-core-cli-doc-embedding.md`.
- Charte : `CHARTE_DOC.md` (principes 1, 8, 11 ; règle A).
- Code concerné : `cli/assets/sync_landing.py`, `forge.py`, `mkdocs.yml`,
  `cli/skeleton/data/`, `tests/` (fichiers important `mvc`/`app`/`config`).
