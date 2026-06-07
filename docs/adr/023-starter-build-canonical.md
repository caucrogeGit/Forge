# ADR-023 — `forge starter:build` comme seule façon de construire un starter

## Statut

Accepté — Forge 1.0.0-beta.13 (ticket `CLI-NEW-DROP-STARTER-001`).

---

## Date

2026-06-07

---

## Contexte

Forge distingue deux actes :

- **créer un projet** : `forge new <NomProjet>` clone le squelette nu, configure
  l'environnement, génère les certificats et initialise Git ;
- **construire un starter** : `forge starter:build <n|nom>` copie les fichiers
  d'un starter dans le projet courant et injecte ses routes.

Jusqu'à ce ticket, `forge new` acceptait aussi un flag `--starter <id>` qui
appliquait un starter juste après l'initialisation, via une fonction interne
`_apply_starter_to_new_project`. Il existait donc **deux chemins** pour obtenir
un projet contenant un starter :

```bash
forge new mon-projet --starter welcome        # chemin A (retiré)
forge new mon-projet && forge starter:build welcome   # chemin B (conservé)
```

### État avant la décision

- `forge new --starter <id>` dupliquait, en version dégradée, la logique de
  `forge starter:build` : la fonction `_apply_starter_to_new_project` ne savait
  pas gérer les starters nécessitant une base (`requires_db`) et se contentait
  d'un avertissement, alors que `starter:build` gère le cas proprement.
- Un seul parcours pédagogique utilisait `forge new --starter` : le parcours
  **welcome**. Tous les autres parcours (iot, video, images, files, audio, mfa,
  rbac, workflow, stats, mail) utilisaient déjà `forge starter:build <id>`.
  Le parcours d'entrée était donc l'exception.
- Conceptuellement, `forge new` est censé produire un **projet nu**. Mélanger la
  construction d'un starter dans la commande de création brouille ce modèle.

---

## Décision

1. `forge new` produit **toujours** un projet nu. Le flag `--starter` est retiré
   de la commande, de son parsing et de son aide.
2. La fonction interne `_apply_starter_to_new_project` est supprimée.
3. `forge starter:build <n|nom>` devient la **seule façon officielle** de
   construire un starter, toujours dans le projet courant.

Flux résultant pour le parcours d'entrée :

```bash
forge new mon-projet
cd mon-projet
forge starter:build welcome
forge run
```

---

## Conséquences

### Positives

- Une seule façon officielle de construire un starter (charte, principe 11).
- `forge new` respecte strictement le modèle « projet nu » (principe 8).
- Suppression d'une duplication de logique (la cause, pas le symptôme —
  règle A) : plus de second chemin dégradé à maintenir.
- Tous les parcours pédagogiques deviennent cohérents : `forge starter:build`
  partout.

### Limites

- Le parcours d'entrée passe d'une commande à deux. C'est assumé : la création
  d'un projet et la construction d'un starter sont deux actes distincts, et les
  rendre explicites est pédagogiquement plus clair.
- Rupture d'une surface CLI publique. En phase bêta pré-1.0, la suppression se
  fait directement, sans alias de dépréciation (convention pré-1.0 de
  `CLAUDE.md`). Aucun code applicatif externe n'est protégé.

---

## Alternatives écartées

### A — Conserver `forge new --starter` et `forge starter:build`

Garder les deux chemins.

Rejeté : viole le principe 11 (une seule façon officielle) et maintient une
duplication de logique en version dégradée.

### B — Garder `--starter` mais le retirer seulement de la documentation

Laisser le flag dans la CLI, ne plus le documenter.

Rejeté : un flag public non documenté reste une surface publique et une source
de confusion. Règle A : retirer la cause, pas le symptôme.

### C — Supprimer `forge starter:build`, garder `forge new --starter`

Faire l'inverse.

Rejeté : `forge starter:build` s'applique au projet courant et gère les
starters `requires_db` ; il est utilisé par tous les autres parcours. C'est la
commande la plus complète et la mieux placée.

---

## Hors périmètre de cet ADR

- La pédagogie « installation construit le starter / le palier le refait à la
  main » du parcours welcome (tension préexistante, non traitée ici).
- Toute évolution de `forge starter:build` elle-même (options, format).

---

## Référence

- Ticket d'implémentation CLI : `CLI-NEW-DROP-STARTER-001` (retrait du flag,
  `forge.py`, `forge_cli/help_dispatch.py`).
- Ticket d'alignement documentaire : `DOC-STARTER-BUILD-ALIGN-001`.
- Code concerné : `forge.py` (`cmd_new`, dispatch `new`),
  `forge_cli/starters/` (`forge starter:build`).
- ADR-004 Périmètre du core : `docs/adr/004-core-perimeter.md`.
- Charte : `CHARTE_DOC.md` (principes 8 et 11, règle A).
