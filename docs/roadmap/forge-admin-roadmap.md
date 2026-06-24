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
| ADMIN-OPTIN-DOCS-001 | documenter le positionnement de Forge Admin | à venir |
| ADMIN-INIT-COMMAND-001 | ajouter `forge admin:init` | à venir |
| ADMIN-RESOURCE-CONTRACT-001 | définir le contrat d'une ressource admin | à venir |
| ADMIN-DASHBOARD-MINIMAL-001 | afficher un dashboard admin minimal | à venir |
| ADMIN-LIST-VIEW-001 | afficher une liste paginée pour une entité | à venir |
| ADMIN-DETAIL-VIEW-001 | afficher le détail d'une entité | à venir |
| ADMIN-FORM-NEW-001 | créer une entité depuis l'admin | à venir |
| ADMIN-FORM-EDIT-001 | modifier une entité depuis l'admin | à venir |
| ADMIN-DELETE-ACTION-001 | supprimer une entité avec garde-fous | à venir |
| ADMIN-CSRF-SECURITY-001 | verrouiller les actions sensibles avec CSRF | à venir |
| ADMIN-RBAC-INTEGRATION-001 | intégrer RBAC si l'opt-in est installé | à venir |
| ADMIN-TEMPLATE-OVERRIDE-001 | permettre la surcharge explicite des templates | à venir |
| ADMIN-DOCTOR-001 | ajouter `forge admin:doctor` | à venir |
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

Forge Admin recevra plus tard des pages dédiées.

Pages prévues :

- `docs/admin/index.md` : présentation et positionnement ;
- `docs/admin/install.md` : installation de l'opt-in ;
- `docs/admin/resources.md` : déclaration des ressources administrables ;
- `docs/admin/security.md` : sécurité et contrôle d'accès ;
- `docs/admin/templates.md` : surcharge explicite des templates ;
- `docs/admin/rbac.md` : intégration RBAC ;
- `docs/admin/limits.md` : limites assumées.

Ces pages ne sont pas créées par cette roadmap.
Elles seront produites par les tickets `ADMIN-*` au fil de l'implémentation.

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
