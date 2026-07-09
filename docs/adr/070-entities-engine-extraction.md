# ADR-070 : Extraction du moteur d'entités : `forge-mvc-entities`

## Statut

Proposée (2026-07-09).

## Contexte

Le cœur de Forge est devenu agnostique du SGBD (ADR-054) : il ne connaît qu'un *contrat* de backend (`core/database/backend.py` : `Dialect`, `DbBackend`, résolveur par entry points), et chaque SGBD est fourni par un opt-in (`forge-mvc-mariadb`, `forge-mvc-sqlite`, `forge-mvc-postgres`, `forge-mvc-mssql`).
Le squelette lui-même ne livre plus de backend : `forge new` laisse choisir (trajectoire ADR-060).

Dans le même temps, toute la chaîne de génération et de modélisation d'entités reste dans le cœur (`cli/entities/`) : `make:entity`, `make:relation`, le normaliseur canonique, la validation, `build:model`, la génération de migrations, `make:crud`, `entity:doc`, `entity:validate`.
Or cette chaîne produit du SQL qui a besoin d'un backend installé pour tourner : dans un cœur qui ne livre aucun backend, elle est déjà un demi-outil sans opt-in.
C'est la même incohérence que celle des relations `many_to_many` : on peut les déclarer depuis le cœur, mais elles ne sont pleinement exploitables qu'avec l'opt-in `forge-mvc-pivot` (service d'exécution, `make:pivot-crud`).

La question posée (retour terrain) : à quoi sert de garder la gestion des entités dans un cœur qui ne gère pas la base, alors qu'une entité n'a de sens que contre une base ?

Précédent : dans Symfony, le cœur (HttpKernel) ne contient ni Doctrine (les entités) ni MakerBundle (les générateurs) ; les deux sont des bundles.
`forge-mvc-entities` réunit ces deux rôles.

## Décision

On extrait le **moteur d'entités** du cœur vers un opt-in unique, `forge-mvc-entities`, qui absorbe `forge-mvc-pivot`.

### Ligne de partage

Deux choses sont aujourd'hui confondues sous « la BDD dans le cœur » ; on les sépare nettement.

1. La **couture d'exécution** reste dans le cœur : `core/database/` (contrat `Dialect`/`DbBackend`, résolveur, `db()`, `connection`, `transaction`, `sql_loader`).
   C'est du runtime, c'est agnostique (un contrat, pas un SGBD), et c'est ce dont le cœur a besoin pour parler à n'importe quel backend, notamment pour les sessions.
   C'est le « accès base de données minimal, pas d'ORM » de la charte.

2. La **modélisation et la génération** quittent le cœur pour `forge-mvc-entities` : `make:entity`, `make:relation` (`many_to_one` et `many_to_many`), le normaliseur, la validation, `build:model` / `sync:entity`, la génération de migrations, `make:crud`, `entity:doc`, `entity:validate`, plus le provisioning `db:config` / `db:init` / `db:apply` (workflow « faire vivre les entités dans une base »), et le service d'exécution pivot + `make:pivot-crud` hérités de `forge-mvc-pivot`.

Le nouvel opt-in dépend du **contrat `Dialect`** (exposé par le cœur), jamais d'un backend concret : il reste indépendant du SGBD, exactement comme le reste de l'outillage.
Le code généré (modèles, CRUD) importe la couture runtime du cœur (`core.database`), pas l'opt-in : le sens des dépendances est cœur ← code applicatif, opt-in → cœur, jamais cœur → opt-in.

### Câblage des commandes

Les commandes du moteur d'entités deviennent des **commandes opt-in**, dispatchées par le registre `cli/commands/optin_dispatch.py` (ADR-059) : elles ne sont disponibles que si `forge-mvc-entities` est installé.
Le cœur conserve le dispatcher `forge`, le cycle de vie opt-in et la couture runtime.

### Expérience `forge new`

Pour que l'expérience d'entrée reste inchangée pour la grande majorité (qui modélise des données), `forge new` **installe `forge-mvc-entities` par défaut**, avec une option explicite pour s'en passer (application web sans couche de données).
C'est le même schéma que le choix de backend (ADR-060) : opt-in par conception, activé par défaut par commodité.

## Conséquences

- Le cœur devient un noyau web cohérent : HTTP, routing, configuration, templating, sessions, sécurité, cycle de vie opt-in, et la couture runtime BDD minimale.
  La génération de la couche de données n'y est plus.
- Une seule maison pour le modèle de données : `many_to_one` et `many_to_many` cohabitent dans `forge-mvc-entities`, ce qui règle le partage bancal cœur / pivot (principe 11).
- Le nom devient correct : l'opt-in qui possède les entités s'appelle `forge-mvc-entities`.
- `forge-mvc-pivot` est absorbé et retiré (pré-1.0, sans shim de compatibilité, conformément à la convention du dépôt).
- Amende le périmètre d'ADR-004 (le cœur listait « CLI de génération ») et complète ADR-021 (pivot n'est plus un opt-in séparé) et ADR-052 (classification de l'opt-in).
- La charte §3 (architecture) est mise à jour au prochain jalon pour refléter le nouveau périmètre.
- Rupture d'API publique (les commandes `make:entity`, `build:model`, `make:crud`… quittent le cœur) : par la règle d'évolution C, cette extraction doit être livrée **avant le tag 1.0 stable** ; après, elle exigerait une version majeure 2.0.
- La documentation du moteur d'entités (pages `cli/entities/docs/` et `docs/entities/`) migre dans le paquet et s'agrège au site via mkdocs-monorepo (ADR-038).

## Alternatives écartées

- **Tout sortir, y compris la couture runtime `core/database`** : le cœur deviendrait un micro-noyau strictement web, mais il ne pourrait plus parler à une base seul, ce qui casse les sessions BDD et son rôle actuel.
  On garde la couture runtime au cœur.
- **Statu quo assaini** (garder le moteur d'entités au cœur, se contenter de dé-dupliquer `pivot.schema.json`) : ne traite pas l'incohérence de fond d'un cœur qui génère une couche de données qu'il ne peut pas faire vivre sans opt-in.
- **Séparer par type de relation** (m2o au cœur, m2m dans l'opt-in) : laisse la modélisation à cheval sur deux maisons et n'unifie pas la chaîne de génération.
- **Placer `db:config` / `db:init` / `db:apply` du côté backend** plutôt qu'avec les entités : rejeté car ce sont des étapes du workflow de modélisation (provisionner puis appliquer les entités), pas des primitives de dialecte ; le backend fournit le *comment parler au SGBD*, l'opt-in entités fournit le *workflow de données*.
