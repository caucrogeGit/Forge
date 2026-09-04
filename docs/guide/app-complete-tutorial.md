# Tutoriel : Application complète avec Forge

Ce tutoriel guide le développement d'une petite application Forge de bout en bout.
Il suppose que Forge est déjà installé et que MariaDB est disponible.

!!! tip "Nouveau sur Forge ?"
    Commencez par [Bonjour Forge](bonjour-forge.md) pour découvrir les bases avant d'aborder ce tutoriel.

---

## Objectif

À la fin de ce tutoriel, vous aurez :

- un projet Forge fonctionnel avec plusieurs entités ;
- deux entités (`Ville` et `Contact`) reliées par une relation `many_to_one` ;
- des CRUD générés pour chaque entité ;
- une compréhension claire des fichiers générés et préservés ;
- un projet validé par les outils de diagnostic Forge.

---

## Ce que tu vas construire

Un **carnet de contacts** minimal :

- une entité `Ville` (nom, code postal) ;
- une entité `Contact` (nom, prénom, email, ville) ;
- une relation : un contact appartient à une ville ;
- les vues liste, fiche, création, modification et suppression pour chaque entité.

Ce n'est pas une application métier complète.
Le but est de montrer Forge : comment les entités s'organisent, comment les relations se déclarent, et comment le code généré se distingue du code que vous écrivez.

---

## Le workflow officiel en un coup d'œil

```text
forge make:entity   → crée l'entité JSON (vous éditez les champs)
forge make:relation → déclare les relations dans relations.json
forge build:model   → régénère TOUT depuis le JSON : SQL, _base.py, relations.sql
forge db:init       → AFFICHE le SQL de provisioning (--run pour l'exécuter)
forge make:crud     → génère contrôleurs, formulaires et vues
forge run           → lance l'application
```

`forge build:model` est la commande centrale : elle régénère, pour **toutes** les entités, le schéma SQL, l'interface `_base.py` et le `relations.sql`, à partir des fichiers JSON.
Les variantes ciblées `forge sync:entity <Nom>` (une seule entité) et `forge sync:relations` (relations seules) servent à **régénérer après édition** d'un élément précis ; pour le parcours initial, `build:model` suffit.

---

## Prérequis

- Forge installé (`forge --version` doit répondre) ;
- Python {{python_min}} ou plus ;
- MariaDB installé et démarré (pour `forge db:init`) ;
- npm installé (facultatif, seulement pour recompiler le CSS Tailwind après avoir modifié les gabarits).

---

## 1. Créer le projet

```bash
forge new carnet_contacts
cd carnet_contacts
source .venv/bin/activate
```

`forge new` crée la structure du projet, installe les dépendances Python, génère les certificats SSL de développement et initialise un dépôt Git propre.

Le CSS Tailwind est livré compilé par le squelette : Node n'est pas requis.
Ajoutez `--with-node` pour installer les dépendances front dès la création.

### Installer les deux opt-ins nécessaires

Le squelette est livré **sans backend de base de données** ([ADR-060](../adr/060-backend-free-skeleton.md)), et le moteur d'entités est un opt-in depuis l'[ADR-070](../adr/070-entities-engine-extraction.md).

```bash
pip install --pre forge-mvc-mariadb forge-mvc-entities
```

Sans le moteur d'entités, `forge make:entity` n'existe pas.
Sans backend, `forge db:init` répond qu'aucun n'est installé.
Un autre backend convient tout aussi bien : `forge-mvc-sqlite`, `forge-mvc-postgres` ou `forge-mvc-mssql`, un seul par projet ([ADR-054](../adr/054-database-backend-optins.md)).

Structure créée :

```text
carnet_contacts/
├── app.py                   # point d'entrée
├── env/dev                  # configuration (.env)
├── mvc/
│   ├── routes.py            # déclaration des routes
│   ├── controllers/         # contrôleurs applicatifs
│   ├── models/              # modèles applicatifs
│   ├── forms/               # formulaires
│   ├── views/               # templates Jinja
│   └── entities/            # entités JSON et relations
│       └── relations.json   # relations globales (vide au départ)
├── static/                  # fichiers statiques
└── forge_profile.txt        # profil du projet
```

---

## 2. Vérifier le projet

```bash
forge doctor
forge project:check
```

Ces deux commandes sont complémentaires :

- `forge doctor` : diagnostic de l'environnement d'exécution ;
- `forge project:check` : cohérence interne du projet Forge (dossiers, configuration, entités, routes, templates, modules).

Un projet neuf doit être sain dès la création.

---

## 3. Créer l'entité Ville

```bash
forge make:entity Ville --no-input
```

Fichiers créés dans `mvc/entities/ville/` (le sous-dossier est en **minuscule**) :

| Fichier | Rôle | Régénérable ? |
|---|---|---|
| `ville.json` | Source de vérité de l'entité | Non (source) |
| `ville.sql` | Schéma SQL généré | Oui (`build:model`) |
| `ville_base.py` | Interface Python générée | Oui (`build:model`) |
| `ville.py` | Modèle manuel (vide au départ) | **Non, préservé** |

### Personnaliser l'entité Ville

Éditez `mvc/entities/ville/ville.json` au **format canonique** (clé racine `name`, types Forge, pas de champ `id` ni de type SQL brut) :

```json
{
  "schema_version": "1.0",
  "name": "Ville",
  "table": "villes",
  "fields": [
    {"name": "nom", "type": "string", "max_length": 100, "required": true},
    {"name": "code_postal", "type": "string", "max_length": 10}
  ]
}
```

!!! note "Le champ `id` est implicite"
    Forge génère la clé primaire `id` automatiquement : ne la déclarez pas dans `fields`.
    Les types sont ceux de Forge (`string`, `integer`, `slug`, `boolean`, `date`, `email`…), jamais du SQL brut comme `VARCHAR(100)`.

---

## 4. Créer l'entité Contact

```bash
forge make:entity Contact --no-input
```

Fichiers créés dans `mvc/entities/contact/`, sur le même modèle que `ville`.

### Personnaliser l'entité Contact

Éditez `mvc/entities/contact/contact.json` :

```json
{
  "schema_version": "1.0",
  "name": "Contact",
  "table": "contacts",
  "fields": [
    {"name": "nom", "type": "string", "max_length": 100, "required": true},
    {"name": "prenom", "type": "string", "max_length": 100, "required": true},
    {"name": "email", "type": "email", "required": true},
    {"name": "ville_id", "type": "integer", "nullable": true}
  ]
}
```

Le champ `ville_id` est un entier ordinaire dans le JSON de Contact.
La contrainte de clé étrangère sera déclarée dans `relations.json`, pas dans l'entité.

---

## 5. Déclarer la relation

La relation entre `Contact` et `Ville` est déclarée dans le fichier global `mvc/entities/relations.json`.

```bash
forge make:relation
```

`forge make:relation` est un assistant interactif.
Il vous pose les questions suivantes :

```text
Type de relation : many_to_one
Entité source (from) : Contact
Entité cible (to) : Ville
Clé étrangère (foreign_key) : ville_id
```

Résultat dans `mvc/entities/relations.json` :

```json
{
  "$schema": "../../schemas/relations.schema.json",
  "schema_version": "1.0",
  "relations": [
    {
      "type": "many_to_one",
      "from": "Contact",
      "to": "Ville",
      "name": "ville",
      "foreign_key": "ville_id",
      "nullable": true,
      "on_delete": "set_null"
    }
  ]
}
```

---

## 6. Régénérer le modèle

Après avoir édité les entités et déclaré la relation, régénérez tout d'une seule commande :

```bash
forge build:model
```

`forge build:model` relit chaque `*.json` et régénère, pour toutes les entités :

- le schéma SQL (`ville.sql`, `contact.sql`) ;
- l'interface Python (`ville_base.py`, `contact_base.py`) ;
- le fichier global `relations.sql` (contraintes `ALTER TABLE` de la clé étrangère).

Les modèles manuels (`ville.py`, `contact.py`) sont **préservés** : Forge ne les réécrit jamais.
Vérifiez la cohérence à tout moment avec `forge check:model`.

---

## 7. Générer les CRUD

```bash
forge make:crud Ville
forge make:crud Contact
```

### Fichiers créés pour Ville

| Fichier | Modifiable ? |
|---|---|
| `mvc/controllers/ville_controller.py` | Oui, **préservé** |
| `mvc/models/ville.py` | Oui, **préservé** |
| `mvc/forms/ville_form.py` | Oui, **préservé** |
| `mvc/views/ville/list.html` | Oui, **préservé** |
| `mvc/views/ville/show.html` | Oui, **préservé** |
| `mvc/views/ville/create.html` | Oui, **préservé** |
| `mvc/views/ville/edit.html` | Oui, **préservé** |
| `mvc/views/ville/delete.html` | Oui, **préservé** |

Les fichiers de `Contact` suivent le même schéma (`contact_controller.py`, `contact_form.py`, `mvc/views/contact/*.html`).

!!! info "make:crud et les relations"
    Quand `Contact` est la source (`from`) d'une relation `many_to_one`, `forge make:crud` génère automatiquement un champ `RelationField` pour `ville_id` dans le formulaire, et un `LEFT JOIN` dans la requête de liste pour afficher le nom de la ville.

!!! info "Fichiers préservés"
    Ces fichiers ne sont **jamais réécrasés** par Forge.
    Si `forge make:crud` est relancé sur une entité existante, il refuse sans l'option `--force`.
    Votre code est en sécurité.

`forge make:crud` écrit `mvc/routes/<entite>_routes.py`, puis **affiche** le branchement à coller dans `mvc/routes/__init__.py` :

```python
from mvc.routes.contact_routes import register_contact_routes
register_contact_routes(router)
```

!!! warning "Ce collage n'est pas facultatif"

    Forge n'écrit jamais dans `mvc/routes/__init__.py` : ce fichier vous appartient (charte, principe 9).
    Sans ce collage, `forge routes:list` ne montrera aucune route de l'entité, et l'application répondra 404 sur `/contact`.

    Cette page annonçait auparavant un branchement « automatique ». Il ne l'a jamais été, et un lecteur qui s'y fiait obtenait un 404 sans comprendre pourquoi (`GUIDE-PRISE-EN-MAIN-EXEC-001`).

---

## 8. Comprendre les fichiers générés

### Architecture des fichiers

```text
mvc/entities/
├── contact/
│   ├── contact.json         ← source de vérité (vous éditez ce fichier)
│   ├── contact.sql          ← généré par build:model (régénérable)
│   ├── contact_base.py      ← généré par build:model (régénérable)
│   └── contact.py           ← modèle manuel (préservé)
├── ville/
│   ├── ville.json           ← source de vérité (vous éditez ce fichier)
│   ├── ville.sql            ← généré par build:model (régénérable)
│   ├── ville_base.py        ← généré par build:model (régénérable)
│   └── ville.py             ← modèle manuel (préservé)
├── relations.json           ← source de vérité des relations (vous éditez ce fichier)
└── relations.sql            ← généré par build:model (régénérable)
```

### La règle centrale

```text
JSON  → build:model → SQL + _base.py + relations.sql   (régénérable à tout moment)
JSON  → make:crud   → controller / model / form / views (préservé - jamais réécrasé)
```

Les fichiers SQL et `_base.py` sont des **projections** du JSON : régénérez-les autant de fois que nécessaire, sans perte.
Les fichiers de `make:crud` et les modèles manuels sont les **vôtres** ; Forge n'y touche plus après la création.
Le [Contrat de stabilité](../release/stability-contract.md) garantit cette règle.

---

## 9. Lancer l'application

### Configurer `env/dev`

```bash
# Renseigner les variables MariaDB dans env/dev
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=<mot_de_passe_root>
DB_APP_LOGIN=carnet_contacts_app
DB_APP_PWD=<mot_de_passe_app>
DB_NAME=carnet_contacts
```

### Provisionner la base

```bash
forge db:init
```

`forge db:init` **affiche** le SQL de provisioning dérivé de `env/` : la base et les deux comptes ([ADR-067](../adr/067-db-init-provisioning-sql.md)).
Forge ne demande jamais le root du serveur : collez ce script dans une session d'administration, ou laissez Forge l'exécuter avec `forge db:init --run` si le compte `DB_ADMIN_*` existe déjà côté serveur.

### Créer les tables

```bash
forge db:apply
```

`forge db:apply` applique les fichiers SQL générés (`ville.sql`, `contact.sql`) puis `relations.sql`.
C'est cette commande qui crée les tables, pas `db:init`.

!!! warning "Ordre des tables"
    `forge db:apply` applique d'abord les fichiers SQL des entités, puis `relations.sql`.
    La table `villes` doit exister avant que la contrainte de clé étrangère sur `contacts` soit ajoutée.
    Cet ordre est géré automatiquement.

### Lancer l'application

```bash
forge run
```

L'application démarre sur `https://localhost:8000` avec HTTPS de développement.

Les routes disponibles :

```text
/ville           → liste des villes
/ville/new       → créer une ville
/contact         → liste des contacts (avec ville affichée)
/contact/new     → créer un contact (sélection de ville disponible)
```

---

## 10. Contrôles finaux

```bash
forge doctor
forge project:check
forge project:audit
```

Un projet avec deux entités, une relation `many_to_one`, et les CRUD générés doit passer les trois contrôles sans `fail`.

```bash
python -m pytest
python -m compileall -q .
```

Les tests valident les générateurs, le runtime et les entités.
La compilation vérifie l'absence d'erreurs de syntaxe.

---

## 11. Limites du tutoriel

Ce tutoriel couvre une application simple.
Il ne couvre pas :

| Limite | Documentation |
|---|---|
| Auth / connexion utilisateur | [Auth/User](../features/auth.md) |
| Rôles et permissions (RBAC) | [Sécurité et RBAC](../philosophy/security.md), RBAC |
| Relations `many_to_many` | [Relations entre entités](../features/relations.md) |
| Déploiement en production | [Déploiement](../deployment/deployment.md) |
| Sécurité en production | [Sécurité en production](../deployment/production-security.md) |

`forge make:relation` est interactif.
Pour les projets sans terminal interactif, éditez directement `mvc/entities/relations.json` selon le format documenté dans [Relations entre entités](../features/relations.md).

`forge db:init` et `forge db:apply` nécessitent un MariaDB local configuré.
Sans MariaDB, les fichiers JSON, SQL, modèles et vues sont générés mais l'application ne peut pas démarrer.

---

## Récapitulatif des commandes

```bash
forge new carnet_contacts          # créer le projet
cd carnet_contacts
source .venv/bin/activate

pip install --pre forge-mvc-mariadb forge-mvc-entities   # backend + moteur d'entités

forge doctor                       # vérifier l'environnement
forge project:check                # cohérence structurelle

forge make:entity Ville --no-input    # créer l'entité Ville, puis éditer ville.json
forge make:entity Contact --no-input  # créer l'entité Contact, puis éditer contact.json

forge make:relation                # déclarer la relation Contact → Ville

forge build:model                  # régénérer SQL + _base.py + relations.sql

forge make:crud Ville              # générer le CRUD Ville
forge make:crud Contact            # générer le CRUD Contact

forge project:check                # vérifier après génération
forge project:audit                # rapport détaillé

forge db:init                      # AFFICHE le SQL de provisioning ; --run l'exécute
forge db:apply                     # crée les tables des entités
forge run                          # lancer l'application
```

---

## Voir aussi

- [Bonjour Forge](bonjour-forge.md), premier contact, sans BDD
- [Guide de démarrage](guide.md), parcours complet avec MariaDB
- [Relations entre entités](../features/relations.md), format `relations.json` complet
- [Architecture des entités](../features/entity_architecture.md), rôle de chaque fichier généré
- [Contrat de stabilité](../release/stability-contract.md), garanties sur les fichiers préservés
- [Référence API et CLI](../reference/api.md), toutes les commandes, dont les filtres de liste CRUD (`list.filter`)
```

