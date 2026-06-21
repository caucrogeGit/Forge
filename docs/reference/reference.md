# Forge — Référence API et CLI

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette section décrit l'API publique actuelle de Forge `{{forge_version}}`.
Elle est organisée par thème pour faciliter la navigation.

Pour les flux guidés, voir aussi le [guide de démarrage](../guide/guide.md),
le [CRUD explicite](../features/crud.md) et l'[architecture des entités](../features/entity_architecture.md).
Pour les décisions d'architecture, voir [ADR-001](../adr/001-auth-strategy.md),
[ADR-002](../adr/002-session-strategy.md) et l'[index des ADR](../adr/index.md).
Pour ce qui est garanti stable, voir le [contrat de stabilité](../release/stability-contract.md).

## Schéma complet

<details>
<summary>Voir le schéma complet</summary>

```mermaid
flowchart LR
    CLI["CLI forge"] --> Project["Projet Forge"]
    CLI --> EntityGen["Génération entités"]
    CLI --> CrudGen["Génération CRUD"]
    CLI --> DbTools["db:init / db:apply"]

    Project --> CoreConfig["core.forge"]
    Project --> Router["core.http.router"]
    Project --> App["core.app.application"]
    Project --> Templates["core.templating + integrations.jinja2"]
    Project --> Controllers["core.mvc.controller"]
    Project --> Forms["core.forms"]
    Project --> Security["core.security"]
    Project --> Database["core.database"]
    Project --> Uploads["forge-mvc-files (opt-in)"]
    Project --> Entities["mvc/entities"]

    App --> Router
    App --> Security
    Router --> Request["core.http.request"]
    Router --> Response["core.http.response"]
    Controllers --> Response
    Controllers --> Templates
    Controllers --> Forms
    Controllers --> Security
    Controllers --> Database
    Forms --> Validation["core.validation"]
    EntityGen --> Entities
    Entities --> GeneratedSql["*.sql / relations.sql"]
    Entities --> GeneratedBase["*_base.py"]
    Entities --> ManualClass["classe métier manuelle"]
    Database --> MariaDB["MariaDB"]
    DbTools --> MariaDB
    Uploads --> Storage["storage/uploads"]
```

</details>

---

## Index thématique

### API et CLI

- [API Forge complète](api.md) — fonctions, classes, contrats, helpers
- [CRUD enrichi et relations](crud.md) — relations avancées entre entités
- [Pages publiques](pages-publiques.md) — génération de pages génériques

### Opt-ins officiels

- [Workflow](../workflow/reference.md) — statuts et transitions (`forge-mvc-workflow`)
- [Statistiques](../stats/reference.md) — tracking d'événements (`forge-mvc-stats`)
- [Modules Forge](modules.md) — système de modules, cycle de vie, routes
- [Auth — Challenge MFA](auth-mfa.md) — flux MFA à la connexion (`forge-mvc-mfa`)

### Sécurité et sessions

- [Audit Auth](audit-auth.md) — journalisation, cookies, headers, uploads
- [Sessions](sessions.md) — concurrence et garanties

### Outils et infrastructure

- [Profils de projet](profils.md) — environnements et endpoint de santé
- [Tests E2E](tests-e2e.md) — HTTP, MariaDB, CSRF

---

## Opt-ins officiels

Les opt-ins suivants sont distribués séparément du core :

| Opt-in | Paquet PyPI | README |
|---|---|---|
| MFA | `forge-mvc-mfa` | `packages/forge-mvc-mfa/README.md` |
| RBAC | `forge-mvc-rbac` | `packages/forge-mvc-rbac/README.md` |
| Workflow | `forge-mvc-workflow` | `packages/forge-mvc-workflow/README.md` |
| Statistiques | `forge-mvc-stats` | `packages/forge-mvc-stats/README.md` |

Les pages de référence ci-dessus documentent l'API publique de ces opt-ins
pour mémoire. Pour l'installation, l'usage applicatif et les exemples,
voir le README de chaque opt-in.

---

**Note** : cette page est un index. Le contenu détaillé vit dans `docs/reference/`.
Si un lien est cassé ou un sujet manque, voir le
CHANGELOG et la [roadmap](../roadmap/forge-roadmap.md).
