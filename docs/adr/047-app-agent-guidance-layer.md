# ADR-047 — Couche de guidance agent IA dans les applications Forge

## Statut

Accepté — bêta publique 1.0 (`1.0.0-beta.x`).
Décision prise ; mise en œuvre par les tickets `AGENTS-*` listés plus bas.

---

## Date

2026-06-24

---

## Contexte

Le développement de Forge a produit un capital de conception important : la
charte (`CHARTE_DOC.md`), les ADR, les conventions (`docs/contributing/`), et le
briefing des agents IA (`CLAUDE.md`, config `.claude/`).
Ce capital vise le développement **du framework**.

Quand `forge new` génère une **application**, le squelette est volontairement nu
(ADR-024) : il n'embarque aucune guidance pour les agents IA (`CLAUDE.md`,
`AGENTS.md`) ni convention de développement applicatif.
Conséquence : un développeur, et son agent IA, qui travaille sur une application
Forge ne bénéficie pas de l'expérience accumulée ; l'agent peut proposer des
solutions qui combattent le framework (ORM maison, écriture dans le code généré,
SQL caché), faute de cadre.

Le squelette ship déjà du tooling pour l'application (`.vscode/`, `schemas/`
JSON) : transmettre une guidance agent en est l'extension naturelle.

---

## Décision

Forge distille son expérience en une **couche de guidance agent**, générée dans
l'application et taillée pour le développement applicatif (pas pour le
développement du framework).

1. **Contenu** : un briefing concis et actionnable.
   Conventions (entités JSON, routes `/contrôleur/méthode`, SQL visible),
   générateurs CLI à utiliser (`forge make:*`, `forge doctor`), ce qu'il faut
   éviter (ORM maison, écrire dans le code généré, casser les contrats), où
   vivent les choses (`mvc/...`), comment valider (`pytest`, `forge doctor`).
   Pas la gouvernance interne du framework (charte complète, ADR, processus).

2. **Cibles** : `CLAUDE.md` (Claude Code) et `AGENTS.md` (Codex et standard
   d'agents), avec le même contenu, écrits **par défaut** par `forge new`.
   Optionnellement, un `.claude/settings.json` qui pré-autorise `forge`,
   `pytest`, `ruff`.

3. **Source canonique et fraîcheur** : le gabarit du briefing vit dans le
   framework, versionné avec lui (donnée de paquet).
   `forge new` l'écrit (write-if-new, principe 9 : le développeur en devient
   propriétaire).
   Une commande `forge agents:init` (re)génère ou met à jour le briefing depuis
   la version installée, pour les applications existantes aussi ; un mode
   `--check` signale un briefing périmé.

---

## Conséquences

Positives :

- l'expérience de conception de Forge profite à chaque application et à son
  agent IA, dès `forge new` ;
- le briefing reste cohérent avec la version de Forge installée, via la commande
  de rafraîchissement ;
- couverture des deux principaux agents (`CLAUDE.md`, `AGENTS.md`) sans
  duplication de contenu (même texte) ;
- le développeur possède les fichiers (write-if-new) et peut les adapter.

Coûts et limites :

- déviation assumée d'ADR-024 : le projet généré n'est plus strictement « nu »,
  il gagne une couche de guidance (voir ci-dessous) ;
- un gabarit de plus à maintenir dans le framework, à garder distillé (ne pas y
  recopier la charte ni les ADR) ;
- le briefing est un instantané au moment de l'écriture ; sa fraîcheur dépend de
  la commande de rafraîchissement, pas d'une magie automatique.

---

## Relation avec ADR-024 (projet nu)

ADR-024 garde tout son sens pour le **code applicatif** : `forge new` ne génère
pas de contrôleurs, d'entités ni de pages métier.
Cet ADR précise que le projet généré peut porter du **tooling et de la
guidance** (DX), au même titre que `.vscode/` et `schemas/` déjà présents.
La frontière reste : pas de code métier généré, mais un cadre de travail fourni.

---

## Alternatives écartées

**Snapshot figé à `forge new`, sans rafraîchissement.**
Simple, mais l'application diverge de l'expérience Forge au fil des versions, et
le développeur doit recopier à la main.

**Briefing minimal renvoyant uniquement vers forgemvc.com.**
Toujours à jour, mais dépend d'un accès en ligne et oblige l'agent à aller
chercher ; moins actionnable hors connexion.

**Guidance en opt-in seulement (hors `forge new`).**
Préserve le projet nu, mais l'expérience n'est transmise que si le développeur y
pense ; la décision retenue est de la fournir par défaut.

---

## Mise en œuvre (tickets `AGENTS-*`)

- `AGENTS-BRIEFING-TEMPLATE-001` : rédiger le gabarit canonique du briefing
  applicatif (donnée de paquet), distillé et versionné.
- `AGENTS-SEED-ADR-001` : fournir un ADR-001 d'amorçage (« Adopter Forge et ses
  conventions ») écrit dans `docs/adr/001-adopter-forge.md` du projet, qui acte
  une décision réelle et sert d'exemple de format.
- `AGENTS-SKELETON-EMIT-001` : `forge new` écrit `CLAUDE.md`, `AGENTS.md` et
  l'ADR-001 (write-if-new) depuis les gabarits.
- `AGENTS-INIT-COMMAND-001` : commande `forge agents:init` (génération /
  rafraîchissement) avec mode `--check`.
- `AGENTS-SETTINGS-001` : `.claude/settings.json` applicatif optionnel
  (commandes pré-autorisées).
- `AGENTS-DOCS-001` : documenter la couche guidance et la commande.
- `AGENTS-CLOSING-001` : audit de clôture et suite complète.

---

## Liens

- Projet nu : [ADR-024](024-skeleton-bootstrap.md).
- Convention de route : [ADR-029](029-route-naming-convention.md).
- Briefing du framework (référence interne, à ne pas confondre) : `CLAUDE.md`.
