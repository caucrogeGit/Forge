# Guidance agent IA

Forge transmet son expérience de conception aux applications qu'il génère.
À la création d'un projet, et à la demande ensuite, Forge dépose une couche de
guidance destinée aux agents IA (Claude Code, Codex) et aux développeurs.

Cette page explique ce que reçoit une application et comment l'entretenir.
La décision d'architecture correspondante est l'[ADR-047](../adr/047-app-agent-guidance-layer.md).

## Ce que reçoit une application

`forge new` écrit trois fichiers, en write-if-new (un fichier existant n'est
jamais écrasé) :

- `CLAUDE.md` et `AGENTS.md` : le même **briefing** agent, distillé pour le
  développement d'une application Forge.
- `docs/adr/001-adopter-forge.md` : un premier ADR qui acte l'adoption de Forge
  et amorce la pratique des ADR dans le projet.

Le briefing rappelle l'essentiel : les conventions (entités, routes, SQL
visible), les générateurs CLI à utiliser, la règle de préservation du code
(write-if-new, fichiers `*_base.py` régénérables), la discipline ADR, et les
commandes de validation.

Le projet reste nu côté code métier (aucun contrôleur ni entité générés) ; il
gagne seulement ce cadre de travail, au même titre que la configuration VS Code
et les schémas JSON déjà fournis.

## Pourquoi

Le capital de conception de Forge (conventions, ADR, réflexes) sert d'abord à
développer le framework.
Sans cette couche, une application, et l'agent IA qui l'assiste, n'en
bénéficierait pas et pourrait proposer des solutions qui combattent le framework
(ORM caché, écriture dans le code généré, SQL non paramétré).

Le briefing pose un cadre commun aux contributeurs humains et aux agents.

## Mettre à jour une application existante

La commande `forge agents:init` apporte ou rafraîchit cette couche dans un
projet déjà créé.

```bash
forge agents:init            # crée les fichiers manquants (write-if-new)
forge agents:init --check    # diagnostic en lecture seule
forge agents:init --force    # rafraîchit CLAUDE.md et AGENTS.md
forge agents:init --settings # ajoute aussi .claude/settings.json
```

- Par défaut, rien n'est écrasé : seuls les fichiers absents sont créés.
- `--check` signale un fichier absent ou un briefing qui a divergé de la version
  de Forge installée (code de sortie 1) ; pratique en intégration continue.
- `--force` réécrit `CLAUDE.md` et `AGENTS.md` depuis la version installée, sans
  toucher `docs/adr/001-adopter-forge.md`, qui appartient au projet.

Le briefing évolue avec Forge ; `--check` puis `--force` permettent de le garder
aligné après une mise à jour du framework.

## Réglages Claude Code (optionnel)

`forge agents:init --settings` écrit un `.claude/settings.json` qui pré-autorise
les commandes usuelles du développement Forge (`forge`, `pytest`, `ruff`,
`mkdocs`, `git` en lecture) et refuse les commandes destructrices.

C'est un choix opt-in : `forge new` ne le génère pas par défaut, car
pré-autoriser l'exécution de commandes est une décision de sécurité qui revient
au propriétaire du projet.

## Ces fichiers t'appartiennent

`CLAUDE.md`, `AGENTS.md`, l'ADR-001 et `.claude/settings.json` sont à toi.
Tu peux les adapter à ton projet ; Forge ne les réécrit pas sans que tu le
demandes (`--force` pour le seul briefing).

La liste détaillée des options de la commande figure dans la
[référence des commandes CLI](../reference/cli-commands.md#forge-agentsinit).
