# ADR-082 : Le squelette livre un ADR de style de documentation

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-13

## Contexte

Depuis ADR-047, `forge new` (et `forge agents:init`) posent une couche de guidance dans l'application générée : `CLAUDE.md`, `AGENTS.md`, et un premier ADR d'amorçage `docs/adr/001-adopter-forge.md` qui acte l'adoption de Forge et de ses conventions.

Forge applique à sa propre documentation une directive de style précise (français, une phrase par ligne, pas de tiret cadratin, ponctuation française, liens vérifiés au build strict). Cette directive vit dans la charte et le briefing agent, mais rien ne la donnait au projet généré sous une forme que le projet possède et peut faire respecter chez lui. Un nouveau projet redécouvrait ou ignorait ces règles.

## Décision

`forge new` et `forge agents:init` posent un **second ADR d'amorçage** dans le projet : `docs/adr/002-style-documentation.md`.

- Il acte, au format ADR (Statut, Date, Contexte, Décision, Conséquences, Alternatives), les règles de rédaction de la documentation du projet : français, une phrase par ligne, pas de tiret cadratin, ponctuation française, liens internes vérifiés au build strict, anglicismes évités.
- Il est écrit en **write-if-new**, comme l'ADR-001 : jamais écrasé, propriété du projet, daté à l'écriture.
- `forge agents:init --check` vérifie sa présence ; `--force` ne le touche pas.
- Le journal du squelette (`docs/adr/index.md`) le référence, et la numérotation des ADR suivants du projet démarre à `003`.

C'est une extension du périmètre d'ADR-047 (couche guidance des applications), au même titre que l'ADR-001 d'amorçage.

## Conséquences

- Chaque nouveau projet démarre avec une convention de rédaction explicite, qu'il possède et peut appliquer, plutôt que de la redécouvrir.
- La règle est un ADR du projet, pas une contrainte imposée par le framework : le projet peut l'amender comme n'importe quel ADR (write-if-new, jamais réécrit).
- Surface : un fichier supplémentaire posé par `forge new` / `agents:init` (additif). `render_seed_adr_doc_style` dans `cli/agents/seed_adr.py`, émis par `emit_app_agent_files`.
- Garde-fous : le format et le contenu de l'ADR-002 sont figés par test, y compris le fait que l'ADR qui interdit le tiret cadratin n'en contient pas.

## Alternatives écartées

- **Laisser la directive uniquement dans le briefing agent (`CLAUDE.md`/`AGENTS.md`).**
  Écartée : le briefing s'adresse aux agents IA et se rafraîchit avec la version de Forge ; il n'est pas un artefact que le projet possède et versionne comme une décision. Un ADR du projet est plus durable et relu par les humains comme par les agents.
- **Un ADR unique fusionnant adoption de Forge et style de doc.**
  Écartée : une décision, une responsabilité (charte, principe 2). Le style de rédaction est une décision distincte de l'adoption du framework.
- **Ne rien poser et documenter la règle ailleurs (site, guide).**
  Écartée : un guide externe n'engage pas le projet ; l'ADR posé dans le dépôt du projet, si.

## Référence

- Charte : `CHARTE_DOC.md` (principe 2, une responsabilité ; directive de style francophone § 2.1).
- [ADR-047](047-app-agent-guidance-layer.md) : couche de guidance agent IA dans les applications Forge.
- `cli/agents/seed_adr.py`, `cli/agents/emit.py` : émission des ADR d'amorçage.
