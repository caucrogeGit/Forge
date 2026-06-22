# ADR-043 : Documentation embarquée du cœur et du CLI, renommage `forge_cli` → `cli`

## Statut

Accepté.

## Contexte

L'ADR-038 a embarqué la documentation des 12 opt-ins dans chaque paquet
(`packages/<pkg>/docs/`), agrégée au build par `mkdocs-monorepo`.
Le cœur (`core/`) et le CLI de génération (`forge_cli/`) gardaient, eux, toute
leur documentation dans un dossier `docs/` central et hétérogène (~330 pages
mêlant référence, guides, tutoriels, ADR, mémoire).

Cette asymétrie va à rebours du principe 11 (une seule façon de faire) : la
référence d'un module devrait vivre à côté de son code, comme pour les opt-ins.

## Décision

1. **Renommer le paquet `forge_cli` en `cli`.**
   Refactor de code isolé (imports, `pyproject.toml`, package-data, tests,
   hooks), validé par la suite complète **avant** tout travail de
   documentation. Le point d'entrée `forge = "forge:cli_entrypoint"` est
   inchangé.

2. **Embarquer la RÉFÉRENCE par module à côté du code.**
   Pour chaque sous-paquet de `core/` et de `cli/`, créer un dossier
   `docs/references/` contenant **un fichier `.md` par fichier `.py`** à API
   publique (miroir exact de la convention opt-in `references/<module>.md`).
   Exemple : `core/app/docs/references/<module>.md`.
   Ces docs sont agrégées au site unique par `mkdocs-monorepo` (`!include`),
   comme les opt-ins.

3. **Seule la référence migre dans le code.**
   Les pages **conceptuelles et transverses** (guides, concepts, tutoriels
   `starters/`, ADR, `history/`, gouvernance, philosophie) ne correspondent à
   aucun fichier `.py` : elles **restent centralisées** dans `docs/`.
   Seul le contenu de `docs/reference/*` qui documente un module précis est
   déplacé vers `core/`/`cli/`.

4. **Formalisme unique.**
   Toute documentation, nouvelle comme migrée, suit le gabarit
   `docs/reference/http/request.md` (titre `# … dans Forge`, mention du
   fichier `.py` source, sections numérotées pédagogiques, tables d'API,
   exemples, « Contextes d'utilisation », « Voir aussi »).
   La directive de style francophone (CHARTE §2.1 : une phrase par ligne, pas
   de tiret cadratin) s'applique aux deux.

## Conséquences

- Symétrie totale : cœur, CLI et opt-ins documentent leur référence de la même
  façon, à côté de leur code.
- Le `docs/` central se recentre sur le conceptuel, le pédagogique et la
  mémoire (ADR, history).
- Volume : ~125 pages de référence à écrire (65 modules cœur + 60 CLI),
  phasées sous-paquet par sous-paquet.
- `CLAUDE.md` mentionne encore `forge_cli` (fichier protégé, hors périmètre des
  agents) : à resynchroniser au prochain tag majeur.

## Alternatives écartées

- **Garder toute la doc dans `docs/`** : conserve l'asymétrie avec les opt-ins.
- **Migrer aussi les guides conceptuels dans le code** : la plupart ne se
  rattachent à aucun `.py` ; forcer ce rattachement dégraderait la cohérence.
