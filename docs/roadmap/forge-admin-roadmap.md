# Roadmap Forge Admin - Opt-in de back-office applicatif

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette roadmap cadre un futur opt-in de back-office applicatif pour les projets Forge.

Elle ne décrit pas du code livré.
Elle fixe le positionnement, les limites, le découpage en tickets et les critères de clôture.

Le paquet cible s'appellera provisoirement `forge-mvc-admin`.
Son nom fonctionnel est Forge Admin.

> **Statut** : roadmap de cadrage.
> Aucun code Forge Admin n'existe à ce jour.
> Le travail réel commencera par les tickets `ADMIN-*` listés en section 9.

---

## 1. Positionnement

Forge Admin est un opt-in.

C'est une brique installable séparément, comme les autres modules `forge-mvc-*`.
Elle fournit un back-office applicatif standard pour administrer les entités d'un projet Forge.

Forge Admin sert l'application.
Forge Design sert le développeur.
Forge Core reste autonome et ne dépend de ni l'un ni l'autre.

Forge Admin produit ou configure un espace d'administration à partir des contrats d'entités Forge.
Le code généré reste explicite, lisible et modifiable par le développeur.

---

## 2. Pourquoi cette roadmap existe

Le besoin d'un back-office applicatif est réel.
Beaucoup de projets veulent une interface pour lister, créer, éditer et supprimer leurs entités sans réécrire le même CRUD à la main.

Ce besoin est couvert ailleurs par Symfony EasyAdmin, Django Admin ou Laravel Nova.
Forge peut s'en inspirer, mais ne doit pas les copier aveuglément.

La fonctionnalité complète est trop large pour un seul ticket.
Le bon premier pas est donc une roadmap dédiée, qui borne le périmètre avant toute ligne de code.

Cette roadmap existe pour éviter trois dérives :

- transformer un opt-in en cœur de Forge ;
- exposer un CRUD brut sans contrôle de sécurité ;
- ajouter de la magie cachée qui réécrit le code utilisateur.

---

## 3. Ce que Forge Admin doit être

Forge Admin doit être :

- un opt-in installable séparément ;
- un back-office applicatif destiné aux entités d'un projet ;
- une interface d'administration construite depuis les contrats Forge ;
- un outil explicite, dont le code reste lisible et modifiable ;
- minimal au départ, puis enrichi par petits tickets ;
- sécurisé par défaut ;
- séparé de Forge Core et de Forge Design ;
- sans dépendance front-end lourde imposée.

L'espace d'administration vise un schéma d'URL standard :

```text
/admin
/admin/<ressource>
/admin/<ressource>/new
/admin/<ressource>/<id>
/admin/<ressource>/<id>/edit
/admin/<ressource>/<id>/delete
```

Ces routes sont une cible indicative.
Elles devront être validées par les tickets d'implémentation.

---

## 4. Ce que Forge Admin ne doit pas être

Forge Admin ne doit pas être :

- le cœur de Forge ;
- une dépendance obligatoire ;
- un clone de Symfony EasyAdmin ;
- un cockpit développeur ;
- un éditeur graphique d'entités ;
- un ORM ;
- une couche d'introspection automatique de la base de données ;
- une interface magique qui devine tout sans configuration explicite ;
- un CRUD brut exposé en page publique.

Forge Admin n'introspecte pas la base.
Il part des contrats d'entités déclarés par le projet.

Forge Admin n'expose aucune entité tant que le projet ne l'a pas déclarée administrable.
Le choix reste explicite.

---

## 5. Séparation entre Forge Core, Forge Admin et Forge Design

Les trois briques répondent à des besoins distincts.

| Brique | Sert | Rôle | Dépendance |
|---|---|---|---|
| Forge Core | le runtime | framework MVC minimal, autonome | aucune vers Admin ou Design |
| Forge Admin | l'application | back-office d'administration des entités | opt-in, dépend de Core |
| Forge Design | le développeur | outil graphique de production de templates | projet compagnon séparé |

Forge Core reste minimal et ne connaît pas Forge Admin.
Aucun ticket Forge Admin ne doit ajouter de dépendance du cœur vers l'opt-in.

Forge Admin et Forge Design ne se recouvrent pas.
Forge Design aide à dessiner des vues publiques ; Forge Admin fournit une interface d'administration applicative.

La roadmap Forge Design est traitée à part : voir [Roadmap Forge Design](forge-design-roadmap.md).

---

## 6. Dépendances techniques préalables

Forge Admin s'appuie sur des briques Forge qui doivent rester stables.

Dépendances attendues :

- contrats JSON d'entités (voir [Schéma d'entité](../entities/entity-schema.md) et [JSON canonique](../entities/json-canonique.md)) ;
- validation des entités (voir [Validation d'entité](../entities/entity-validate.md)) ;
- CRUD généré fiable ;
- formulaires serveur ;
- protection CSRF ;
- sessions ;
- authentification ;
- RBAC optionnel (`forge-mvc-rbac`), pris en compte seulement s'il est installé ;
- templates Jinja ;
- conventions de fichiers générés et de fichiers manuels.

Une dépendance technique a été identifiée au cadrage de l'intégration HTTP : pour
servir des templates embarqués dans le paquet, le cœur doit exposer un registre
de loaders Jinja ([ADR-046](../adr/046-optin-jinja-template-loaders.md)).
C'est un prérequis du dashboard et des vues (ticket `CORE-JINJA-OPTIN-LOADERS-001`).

Certains tickets Forge Admin peuvent attendre la stabilisation des contrats JSON.
La trajectoire des contrats est suivie dans la [roadmap des contrats JSON](roadmap-forge-contrats-json-schema.md).

Si le contrat de ressource admin dépend d'un point encore mouvant du contrat d'entité, le ticket concerné est mis en attente plutôt que figé sur une base instable.

---

## 7. Architecture cible de l'opt-in

Forge Admin suit une architecture **hybride et explicite**.

Trois directions étaient possibles :

| Option | Conséquence |
|---|---|
| Runtime-registry (style EasyAdmin) | peu de fichiers côté projet, mais admin opaque et customisation difficile ; en tension avec les principes 3 et 9 |
| Génération pure (style `make:crud`) | tout explicite et possédé par le développeur, mais beaucoup de fichiers et de la duplication entre ressources |
| Hybride (retenue) | un châssis mince réutilisable dans le paquet, des contrôleurs de ressource générés et éditables côté projet |

L'option hybride est retenue parce qu'elle respecte la charte sans imposer de duplication.
Le paquet porte ce qui est stable et partagé.
Le projet porte ce qui est spécifique et doit rester modifiable.

### Couche 1 — châssis runtime (dans le paquet)

Le châssis est un runtime mince, installé avec l'opt-in et non modifié par le projet.
Il fournit la mécanique commune : layout, navigation, helpers de rendu liste et formulaire, mapping des types Forge vers des widgets, garde-fous de sécurité.

```text
packages/forge-mvc-admin/
├── pyproject.toml
├── forge_mvc_admin/
│   ├── __init__.py
│   ├── registry.py      # registre des ressources déclarées
│   ├── dashboard.py     # rendu du tableau de bord
│   ├── resources.py     # base d'une ressource admin
│   ├── fields.py        # mapping type Forge -> widget
│   ├── actions.py       # actions standard (list/new/edit/delete)
│   ├── security.py      # auth requise, CSRF, hook RBAC
│   ├── templates/       # gabarits par défaut, surchargeables
│   └── static/
└── tests/
```

Le châssis reste minimal.
Il ne contient aucune connaissance des entités d'un projet donné.

### Couche 2 — contrôleurs de ressource générés (dans le projet)

À l'inverse, ce qui est propre à une entité est **généré** dans le projet, à partir de son contrat JSON, puis possédé par le développeur.

```text
mvc/admin/
├── dashboard.py         # branchement du dashboard du projet
├── resources.py         # déclaration des ressources administrables
└── templates/
    └── admin/           # surcharges de gabarits propres au projet
```

`forge admin:resource Article` génère la déclaration de ressource et, au besoin, son contrôleur.
Le code produit est lisible et reste éditable : il s'appuie sur le châssis mais n'est jamais regénéré par-dessus les modifications du développeur.

### Répartition des responsabilités

| Aspect | Châssis (paquet) | Ressource (projet) |
|---|---|---|
| Layout, navigation, rendu commun | oui | non |
| Sécurité par défaut (auth, CSRF, hook RBAC) | oui | configurable |
| Mapping type Forge -> widget | oui | surchargeable |
| Choix des entités administrables | non | oui (explicite) |
| Colonnes, filtres, libellés | défauts | oui |
| Surcharge de gabarit | base | oui |

Cette structure est une cible.
Les noms de fichiers et les frontières exactes seront validés par les tickets d'implémentation.

Forge Admin génère des fichiers nouveaux ou affiche du code à copier, mais ne réécrit jamais silencieusement un fichier applicatif existant.

### Intégration HTTP (cadrage)

L'essentiel du stack HTTP de Forge est déjà disponible et réutilisé tel quel.

- **Routes** : le paquet expose `register_admin_routes(router, *, registry=None)`.
  L'application le monte explicitement (`optins/admin/routes.py` -> `optins/registry.py` -> `mvc/routes.py`), conformément à l'ADR-030 et au principe 9.
  Aucune injection silencieuse de routes.
- **Surface visée** : `GET /admin` (dashboard), puis `/admin/<slug>`, `/admin/<slug>/<id>`, `/admin/<slug>/new`, `/admin/<slug>/<id>/edit`, `POST /admin/<slug>/<id>/delete`, ajoutées au fil des tickets de vues.
- **Contrôleur** : un `AdminController` dans le paquet, rendu via `BaseController.render(...)` du cœur (qui injecte déjà `csrf_token` et les fournisseurs de contexte).
- **Sécurité acquise par défaut** : les routes admin n'activent pas `public=True`, donc l'authentification s'applique automatiquement (`/admin` jamais public) ; la protection CSRF est automatique sur les méthodes non sûres ; l'intégration RBAC reste un hook optionnel (`forge-mvc-rbac` non requis).
- **Templates embarqués** : le rendu de templates portés par le paquet nécessite un registre de loaders Jinja dans le cœur ([ADR-046](../adr/046-optin-jinja-template-loaders.md)).
  L'ordre du `ChoiceLoader` (projet d'abord, paquet ensuite) fournit nativement la surcharge de gabarit (`ADMIN-TEMPLATE-OVERRIDE-001`).

### Accès aux données (cadrage)

Le back-office lit la base par **mapping déclaré**, sans ORM ni introspection automatique (charte principes 3 et 5).

- **Mapping physique dans `AdminResource`** : la ressource déclare la **table** (et la colonne de tri par défaut) en plus de l'entité et des `list_fields`.
  Le nom de table n'est pas dérivable du nom d'entité ; il est donc explicite.
- **SELECT contraint dans le châssis** : le paquet construit la requête de liste à partir du mapping déclaré.
  Les identifiants (table, colonnes, colonne de tri) sont validés en **liste blanche** et ne sont jamais paramétrables ; seules les valeurs passent par des paramètres `?`.
  C'est le précédent anti-injection de `forge-mvc-stats` (liste blanche du `group_by`).
- **Pagination** : `LIMIT ? OFFSET ?` bornés, via `core/mvc/view/pagination.py` (`Pagination`).
- **Connexion** : `core.database.db.fetch_all`, avec un adaptateur injectable pour les tests (précédent iot/stats).
- **Source unique** : il n'existe pas de lecture de contrat d'entité au runtime, et on n'en ajoute pas.
  Le futur `admin:resource <Entity>` remplira `table` et les colonnes en lisant le contrat d'entité **au temps CLI** (où la lecture de contrat existe déjà), évitant toute duplication à maintenir à la main et toute lecture de fichier à la requête.

Conséquence : `AdminResource` gagnera un champ `table` (et une colonne de tri par défaut) avec le ticket `ADMIN-LIST-VIEW-001`.
Le rapprochement entre la ressource déclarée et le contrat d'entité réel (table et colonnes existantes) relève de `admin:doctor`.

### Écriture et formulaires (cadrage)

L'écriture (création, édition, suppression) réutilise la pile existante du cœur, sans nouveau mécanisme.

- **Colonnes en liste blanche** : seules les `form_fields` déclarées sont écrites (pas de mass-assignment d'une colonne arbitraire) ; les identifiants sont validés, les valeurs passent par des paramètres `?`.
- **CSRF** : automatique. Les routes d'écriture utilisent une méthode non sûre (POST) avec `csrf=True` (défaut) ; le middleware vérifie le jeton **avant** le handler. Le formulaire embarque `csrf_token` (injecté par `BaseController.render`).
- **Champs vides → NULL** : une valeur vide est insérée comme `NULL` (précédent `public_form`), pour ne pas casser les colonnes nullables.
- **Écriture** : `core.database.db.insert` (retourne `lastrowid`), adaptateur injectable pour les tests.
- **Flux POST-Redirect-GET** : en cas de succès, redirection vers la fiche de la ligne créée (`/admin/<slug>/<id>`) avec un message flash (`redirect_with_flash`).
- **Validation** : faute de contrat au runtime, il n'y a pas de validation par champ dans cette première version.
  Les contraintes (obligatoire, type) restent celles de la base ; une violation aboutit à la page d'erreur (cause affichée en `dev`).
  La validation par champ et les messages d'erreur amicaux sont **différés** (ils supposent des métadonnées de type, hors de ce socle).

Conséquence : `ADMIN-FORM-NEW-001` ajoute `GET`/`POST /admin/<slug>/new` (formulaire + création), un template `admin/form.html` embarqué et `pk` est déjà disponible pour la redirection.

### Intégration RBAC (cadrage)

Le back-office est déjà protégé par l'authentification (routes non publiques, `@require_auth`).
RBAC ajoute, par-dessus, un contrôle de **permission**, et reste un opt-in : `forge-mvc-admin` ne dépend pas de `forge-mvc-rbac`.

- **Opt-in explicite par l'application** : l'admin n'exige une permission que si l'application le demande, via `register_admin_routes(router, permission="admin.access")`.
  Sans ce paramètre (défaut), l'admin reste en auth seule, comportement actuel.
  Conséquence voulue : installer `forge-mvc-rbac` pour une autre raison ne verrouille pas l'admin.
- **Gate global** : une permission unique protège toutes les routes admin.
  La granularité par ressource et action pourra venir plus tard, sans rupture.
- **Vérification optionnelle** : si une permission est demandée, le contrôle se fait via `forge_mvc_rbac.require_contract_permission_for_request` importé en `try/except ImportError`.
  Si `forge-mvc-rbac` est installé : refus en 403 quand la permission manque.
  Si `forge-mvc-rbac` est absent : fail-open (auth seule) et `forge doctor` avertit (précédent symétrique à MFA, `check_rbac_dependency`).
- **Place du contrôle** : la permission garde chaque route admin, en plus de `@require_auth` ; côté templates, le helper `can()` du cœur reste disponible pour masquer des actions.

Conséquence : `ADMIN-RBAC-INTEGRATION-001` ajoute le paramètre `permission` à `register_admin_routes` et une garde de permission optionnelle, sans dépendance dure ni changement pour les projets qui ne l'activent pas.

### Vérification (admin:doctor) (cadrage)

`forge admin:doctor` ferme la boucle de l'accès aux données : il rapproche les ressources déclarées du contrat d'entité réel, au temps CLI.

- **Obtenir les ressources déclarées** : la commande importe le module du projet `mvc/admin/resources.py`, qui peuple le registre, puis lit `registry.all()`.
  C'est la seule voie, les ressources étant des déclarations Python ; le précédent existe (le doctor auth importe des modules, le doctor du cœur charge `config.py` en isolation).
  L'import se fait avec `sys.path` ajusté puis nettoyé.
  Si `mvc/admin/resources.py` est absent : `skip` (conseiller `forge admin:init`).
  Si l'import échoue ou qu'une `AdminResourceError` est levée : `fail` (la déclaration est cassée).
- **Lire le contrat d'entité** : au temps CLI via `cli/entities` (les contrats `mvc/entities/<snake>/<snake>.json`, normalisés), ce qui donne le nom d'entité, la table et les **colonnes physiques** (`column`) plus la clé primaire.
- **Rapprochements** : pour chaque ressource, retrouver l'entité par son nom, puis vérifier que la table déclarée correspond, et que `list_fields`, `form_fields`, `order_by` et `pk` désignent des colonnes physiques présentes au contrat.
  Rappel : ces champs sont des **noms de colonnes physiques** (ils entrent tels quels dans le `SELECT`), à rapprocher des `column` du contrat.
- **Sévérité** : `fail` uniquement quand la déclaration ne charge pas (import cassé).
  Tout écart avec le contrat est un `warn` : le contrat peut être en retard sur la base, et l'admin interroge la table directement, donc une divergence n'est pas forcément une panne.
  Le code de sortie est 1 seulement s'il y a un `fail`.
- **Sortie** : lignes `[OK]`/`[WARN]`/`[FAIL]`/`[SKIP]` puis un résumé, à l'image du doctor du cœur et de `audio:doctor`.
- **Câblage CLI** : `admin:doctor` se branche comme `admin:init` (dispatch dans `forge.py`, entrées d'aide, liste figée des commandes) ; le namespace `admin:` est déjà exclu de la référence CLI du cœur (ADR-042).

Conséquence : `ADMIN-DOCTOR-001` ajoute `forge admin:doctor` (lecture seule, aucune connexion base) et son aide ; il ne lit pas la base, seulement les contrats et les déclarations.

---

## 8. Commandes futures envisagées

Ces commandes sont des pistes.
Elles ne sont pas implémentées par cette roadmap.

| Commande envisagée | Rôle attendu |
|---|---|
| `forge admin:init` | préparer la structure admin du projet (write-if-new) |
| `forge admin:resource Article` | déclarer une entité administrable |
| `forge admin:doctor` | vérifier la cohérence admin : contrats, templates, sécurité |

Le nommage et le périmètre exacts seront tranchés par les tickets correspondants.

---

## 9. Découpage proposé en tickets

Le futur travail est découpé en petits tickets, une responsabilité chacun.
Chaque ticket reste décrit en quelques lignes ; aucun n'est détaillé ici comme une spec complète.

| Ticket | Objectif | État |
|---|---|---|
| ADMIN-OPTIN-PACKAGE-001 | créer le paquet `forge-mvc-admin` vide et installable | **livré** (scaffold : paquet installable, `__version__`, `py.typed`, smoke test) |
| ADMIN-OPTIN-DOCS-001 | documenter le positionnement de Forge Admin | **livré** (page embarquée `packages/forge-mvc-admin/docs/index.md`, montée sous `/admin/`) |
| ADMIN-INIT-COMMAND-001 | ajouter `forge admin:init` | **livré** (commande write-if-new ; prépare `mvc/admin/__init__.py` + `resources.py`) |
| ADMIN-RESOURCE-CONTRACT-001 | définir le contrat d'une ressource admin | **livré** (`AdminResource` + `AdminRegistry` dans le paquet, déclaration Python validée, registre explicite) |
| CORE-JINJA-OPTIN-LOADERS-001 | registre de loaders Jinja du cœur (ADR-046) : prérequis du rendu admin | **livré** (registre + loader dynamique projet-puis-paquet) |
| ADMIN-DASHBOARD-MINIMAL-001 | afficher un dashboard admin minimal (dépend de CORE-JINJA-OPTIN-LOADERS-001) | **livré** (`register_admin_routes`, `GET /admin` non publique, template embarqué) |
| ADMIN-LIST-VIEW-001 | afficher une liste paginée pour une entité (étend `AdminResource` avec `table` + tri par défaut ; SELECT contraint en liste blanche) | **livré** (`GET /admin/<slug>`, pagination, template embarqué) |
| ADMIN-DETAIL-VIEW-001 | afficher le détail d'une entité (`GET /admin/<slug>/<id>`, `WHERE <pk> = ?`) | **livré** |
| ADMIN-FORM-NEW-001 | créer une entité depuis l'admin (`GET`/`POST /admin/<slug>/new`, INSERT liste blanche, CSRF, PRG) | **livré** |
| ADMIN-FORM-EDIT-001 | modifier une entité depuis l'admin (`GET`/`POST /admin/<slug>/<id>/edit`, UPDATE liste blanche `WHERE <pk> = ?`) | **livré** |
| ADMIN-DELETE-ACTION-001 | supprimer une entité avec garde-fous (confirmation GET + `POST /admin/<slug>/<id>/delete`, `DELETE … WHERE <pk> = ?`) | **livré** |
| ADMIN-CSRF-SECURITY-001 | verrouiller les actions sensibles avec CSRF (garde-fou : routes non publiques, mutations POST+CSRF, auth exigée) | **livré** |
| ADMIN-RBAC-INTEGRATION-001 | intégrer RBAC si l'opt-in est installé (opt-in explicite `register_admin_routes(permission=...)`, gate global, fail-open) | **livré** |
| ADMIN-TEMPLATE-OVERRIDE-001 | permettre la surcharge explicite des templates (acquis via l'ordre du loader ADR-046 ; documenté + test) | **livré** |
| ADMIN-DOCTOR-001 | ajouter `forge admin:doctor` (rapproche ressources ↔ contrats d'entité, lecture seule ; fail si déclaration cassée, warn sur écart) | **livré** |
| ADMIN-WELCOME-001 | parcours pédagogique embarqué `welcome-admin` (3 niveaux, réalisé à la main, ADR-028/035/038) | à venir (cadré, voir §11) |
| ADMIN-CLOSING-AUDIT-001 | clôturer la roadmap Forge Admin | à venir |

L'ordre est indicatif.
Les tickets de contrat et de sécurité conditionnent les tickets de vues et d'actions.

---

## 10. Sécurité attendue

La sécurité est posée dès le cadrage, pas ajoutée après coup.

Exigences :

- `/admin` n'est jamais public par défaut ;
- les actions `new`, `edit` et `delete` sont protégées ;
- CSRF obligatoire sur tous les formulaires sensibles ;
- intégration RBAC quand `forge-mvc-rbac` est installé ;
- aucune entité n'est exposée automatiquement sans déclaration explicite ;
- la suppression est contrôlée, jamais en un clic non confirmé ;
- pas d'upload ni de média administrable sans ticket dédié ;
- pas de SQL brut injecté depuis la configuration admin ;
- pas de surcharge de template permettant de sortir du répertoire autorisé.

Ces exigences sont des contraintes de conception.
Un ticket qui ne peut pas les respecter est revu, pas contourné.

---

## 11. Documentation attendue

La documentation de Forge Admin est **embarquée dans le paquet** sous
`packages/forge-mvc-admin/docs/`, conformément à l'ADR-038.
Elle est agrégée dans le site unique au build (plugin mkdocs-monorepo) et montée
sous le préfixe `/admin/`.

Page livrée :

- `packages/forge-mvc-admin/docs/index.md` : présentation et positionnement
  (ticket `ADMIN-OPTIN-DOCS-001`).

Pages prévues, ajoutées avec leur ticket de fonctionnalité :

- installation de l'opt-in ;
- déclaration des ressources administrables ;
- sécurité et contrôle d'accès ;
- surcharge explicite des templates ;
- intégration RBAC ;
- limites assumées.

Conformément à l'ADR-042, ces pages restent dans l'espace « Opt-ins officiels »
et ne tissent pas de liens transversaux avec la documentation du cœur.

### Parcours `welcome-admin` (cadrage)

Comme chaque opt-in (ADR-028, ADR-035, ADR-038), Forge Admin reçoit un parcours
pédagogique embarqué, réalisé **à la main** (aucune commande `forge new` ni
`forge starter:build` dans les pages), sous `packages/forge-mvc-admin/docs/welcome/`.

**Prérequis du parcours** : un projet Forge existant avec une entité et son CRUD
(par exemple l'`Article` de `welcome-forge`).
Le back-office s'administre au-dessus d'une entité ; le parcours ne crée pas
l'entité, il l'administre.

**Fil conducteur** : trois niveaux, trois étapes chacun, chaînées par un lien
« suivant », un `bilan.md` par niveau qui pointe vers le niveau suivant, puis un
`recapitulatif.md`. Chaque étape ajoute une fonctionnalité déjà livrée.

| Niveau | Pages (chaînées) | Ce qui est appris |
|---|---|---|
| Installation | `installation.md` | installer `forge-mvc-admin`, `forge admin:init`, brancher `register_admin_routes` dans `optins/admin/routes.py` ; pointe vers la première étape débutant |
| Débutant | `debutant/admin-welcome.md` → `admin-resource.md` → `admin-list.md` → `bilan.md` | voir `/admin` ; déclarer une `AdminResource` ; la liste paginée |
| Intermédiaire | `intermediaire/admin-detail.md` → `admin-new.md` → `admin-edit.md` → `bilan.md` | la fiche ; créer (formulaire + CSRF) ; éditer |
| Avancé | `avance/admin-delete.md` → `admin-override.md` → `admin-rbac.md` → `bilan.md` | suppression contrôlée ; surcharger un template ; exiger une permission RBAC + `admin:doctor` |
| Récapitulatif | `recapitulatif.md` | synthèse et points clés |

**Câblage** : les pages sont ajoutées à la nav du paquet
(`packages/forge-mvc-admin/mkdocs.yml`) sous une rubrique « Progression », à
l'image de `forge-mvc-i18n`.

**Test de nav** : un garde-fou `test_starter_welcome_admin_nav_001` verrouille le
chaînage (chaque étape lie la suivante, chaque bilan lie le niveau suivant ou le
récapitulatif, `installation.md` lie la première étape) et l'absence des commandes
interdites, sur le modèle des 11 parcours existants.

**Style** : français, une phrase par ligne, pas de tiret cadratin, ton direct ;
aucun lien transversal vers la documentation du cœur (ADR-042).

Conséquence : `ADMIN-WELCOME-001` ajoute ces pages, la nav du paquet et le test
de chaînage, sans toucher au code de production.

---

## 12. Tests attendus

Forge Admin est aujourd'hui un sujet documentaire.

Aucun test fonctionnel n'est ajouté tant que le paquet n'existe pas.

Quand l'opt-in sera créé, il suivra le modèle des autres paquets : au minimum un smoke test par paquet, puis des tests unitaires au fil de l'eau.
La cohérence documentaire de cette roadmap est couverte par les tests méta existants (présence des fichiers, navigation MkDocs, absence de pages orphelines).

---

## 13. Limites assumées

Au démarrage, Forge Admin ne fournit pas :

- de tableau de bord analytique avancé ;
- d'éditeur graphique d'entités ;
- d'introspection automatique de la base ;
- de gestion de médias ou d'upload intégrée ;
- de moteur de recherche full-text ;
- d'export ou d'import de données ;
- de système de plugins admin ;
- d'interface multi-tenant ;
- de personnalisation par glisser-déposer ;
- de dépendance front-end imposée (Bootstrap, Tailwind, Alpine, HTMX ou autre).

Ces limites sont volontaires.
Chacune peut faire l'objet d'un ticket futur, séparé et explicite, jamais d'un ajout implicite.

---

## 14. Critères de clôture de la roadmap

Cette roadmap de cadrage est considérée comme aboutie quand :

- le positionnement de Forge Admin est clair et stable ;
- la séparation Forge Core / Forge Admin / Forge Design est explicite ;
- le découpage en tickets `ADMIN-*` est partagé et suivi ;
- les dépendances avec les contrats JSON et le CRUD sont explicites ;
- la sécurité admin est posée comme contrainte de conception.

Le travail réel est ensuite porté par les tickets `ADMIN-*`.
La clôture finale de l'effort Forge Admin relève du ticket `ADMIN-CLOSING-AUDIT-001`.

---

## Règle de mise à jour

Les tickets Forge Admin mettent à jour `docs/roadmap/forge-admin-roadmap.md`.

Les tickets Forge classiques ne modifient pas cette roadmap, sauf s'ils changent explicitement la relation entre Forge et Forge Admin.

La roadmap principale ([Roadmap Forge](forge-roadmap.md)) pointe vers cette roadmap, sans en recopier le contenu.
