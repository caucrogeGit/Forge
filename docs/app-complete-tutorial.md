# Tutoriel — Application complète avec Forge

!!! warning "Tutoriel en cours de mise à jour"
    Les exemples JSON de ce tutoriel utilisent le **format legacy** (avant Forge 1.0 canonique).
    Les clés `"entity"`, `sql_type`, `primary_key`, `auto_increment` et `constraints`
    ne sont **plus valides** dans le format actuel.

    Pour créer une entité Forge correctement :

    - La clé racine est `"name"` (et non `"entity"`).
    - Le fichier se place dans `mvc/entities/<nom>/<nom>.json` (sous-dossier en minuscule).
    - Le champ `id` est auto-généré — ne pas le déclarer dans `fields`.
    - Les types de champs utilisent la syntaxe canonique : `"type": "string"`, pas `sql_type`.
    - Référence : [Le JSON canonique dans Forge](entities/json-canonique.md).

Ce tutoriel guide le développement d'une petite application Forge de bout en bout.
Il suppose que Forge est déjà installé et que MariaDB est disponible.

!!! tip "Nouveau sur Forge ?"
    Commencez par [15 minutes avec Forge](15-minutes.md) pour découvrir les
    bases avant d'aborder ce tutoriel.

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

Ce n'est pas une application métier complète. Le but est de montrer Forge :
comment les entités s'organisent, comment les relations se déclarent, et comment
le code généré se distingue du code que vous écrivez.

---

## Prérequis

- Forge installé (`forge --version` doit répondre) ;
- Python {{python_min}} ou plus ;
- MariaDB installé et démarré (pour `forge db:init` en fin de tutoriel) ;
- npm installé (optionnel — pour recompiler le CSS Tailwind).

---

## 1. Créer le projet

```bash
forge new carnet_contacts
cd carnet_contacts
source .venv/bin/activate
```

`forge new` crée la structure du projet, installe les dépendances Python,
génère les certificats SSL de développement, compile le CSS Tailwind si npm
est disponible, et initialise un dépôt Git propre.

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
```

`forge doctor` vérifie l'environnement, les migrations, les templates et
les modules. Un projet neuf doit être sain dès la création.

```bash
forge project:check
```

`forge project:check` vérifie la cohérence structurelle du projet :
structure de dossiers, configuration, entités, routes, templates et modules.

Ces deux commandes sont complémentaires :

- `forge doctor` : diagnostic de l'environnement d'exécution ;
- `forge project:check` : cohérence interne du projet Forge.

---

## 3. Créer l'entité Ville

```bash
forge make:entity Ville --no-input
```

Fichiers créés dans `mvc/entities/Ville/` :

| Fichier | Rôle | Régénérable ? |
|---|---|---|
| `Ville.json` | Source de vérité de l'entité | Non (source) |
| `Ville.sql` | Schéma SQL généré | Oui (`sync:entity`) |
| `Ville_base.py` | Interface Python générée | Oui (`sync:entity`) |
| `Ville.py` | Modèle manuel (vide au départ) | **Non — préservé** |

### Personnaliser l'entité Ville

Éditez `mvc/entities/Ville/Ville.json` :

```json
{
  "entity": "Ville",
  "table": "villes",
  "primary_key": "id",
  "fields": [
    {"name": "id",           "type": "INT",        "nullable": false, "auto_increment": true},
    {"name": "nom",          "type": "VARCHAR(100)","nullable": false},
    {"name": "code_postal",  "type": "VARCHAR(10)", "nullable": true}
  ],
  "constraints": []
}
```

Régénérez le SQL et le `_base.py` :

```bash
forge sync:entity Ville
```

---

## 4. Créer l'entité Contact

```bash
forge make:entity Contact --no-input
```

Fichiers créés dans `mvc/entities/Contact/` :

| Fichier | Rôle | Régénérable ? |
|---|---|---|
| `Contact.json` | Source de vérité de l'entité | Non (source) |
| `Contact.sql` | Schéma SQL généré | Oui (`sync:entity`) |
| `Contact_base.py` | Interface Python générée | Oui (`sync:entity`) |
| `Contact.py` | Modèle manuel (vide au départ) | **Non — préservé** |

### Personnaliser l'entité Contact

Éditez `mvc/entities/Contact/Contact.json` :

```json
{
  "entity": "Contact",
  "table": "contacts",
  "primary_key": "id",
  "fields": [
    {"name": "id",       "type": "INT",         "nullable": false, "auto_increment": true},
    {"name": "nom",      "type": "VARCHAR(100)", "nullable": false},
    {"name": "prenom",   "type": "VARCHAR(100)", "nullable": false},
    {"name": "email",    "type": "VARCHAR(200)", "nullable": false},
    {"name": "ville_id", "type": "INT",          "nullable": true}
  ],
  "constraints": []
}
```

Le champ `ville_id` est un entier ordinaire dans le JSON de Contact.
La contrainte de clé étrangère sera déclarée dans `relations.json`, pas dans
l'entité.

Régénérez le SQL et le `_base.py` :

```bash
forge sync:entity Contact
```

---

## 5. Déclarer la relation

La relation entre `Contact` et `Ville` est déclarée dans le fichier global
`mvc/entities/relations.json`.

```bash
forge make:relation
```

`forge make:relation` est un assistant interactif. Il vous pose les questions
suivantes :

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

### Régénérer le SQL de relations

```bash
forge sync:relations
```

`forge sync:relations` génère `mvc/entities/relations.sql` à partir de
`relations.json`. Ce fichier contient les contraintes `ALTER TABLE` qui
ajoutent la clé étrangère entre `contacts` et `villes`.

| Fichier | Rôle | Régénérable ? |
|---|---|---|
| `relations.json` | Source de vérité des relations | Non (source) |
| `relations.sql` | Contraintes SQL générées | Oui (`sync:relations`) |

---

## 6. Générer les CRUD

```bash
forge make:crud Ville
forge make:crud Contact
```

### Fichiers créés pour Ville

| Fichier | Modifiable ? |
|---|---|
| `mvc/controllers/ville_controller.py` | Oui — **préservé** |
| `mvc/models/ville.py` | Oui — **préservé** |
| `mvc/forms/ville_form.py` | Oui — **préservé** |
| `mvc/views/ville/list.html` | Oui — **préservé** |
| `mvc/views/ville/show.html` | Oui — **préservé** |
| `mvc/views/ville/create.html` | Oui — **préservé** |
| `mvc/views/ville/edit.html` | Oui — **préservé** |
| `mvc/views/ville/delete.html` | Oui — **préservé** |

### Fichiers créés pour Contact

| Fichier | Modifiable ? |
|---|---|
| `mvc/controllers/contact_controller.py` | Oui — **préservé** |
| `mvc/models/contact.py` | Oui — **préservé** |
| `mvc/forms/contact_form.py` | Oui — **préservé** |
| `mvc/views/contact/list.html` | Oui — **préservé** |
| `mvc/views/contact/show.html` | Oui — **préservé** |
| `mvc/views/contact/create.html` | Oui — **préservé** |
| `mvc/views/contact/edit.html` | Oui — **préservé** |
| `mvc/views/contact/delete.html` | Oui — **préservé** |

!!! info "make:crud et les relations"
    Quand `Contact` est la source (`from`) d'une relation `many_to_one`, `forge make:crud`
    génère automatiquement un champ `RelationField` pour `ville_id` dans le formulaire,
    et un `LEFT JOIN` dans la requête de liste pour afficher le nom de la ville.

!!! info "Fichiers préservés"
    Ces fichiers ne sont **jamais réécrasés** par Forge.
    Si `forge make:crud` est relancé sur une entité existante, il refuse
    sans l'option `--force`. Votre code est en sécurité.

Les routes sont ajoutées automatiquement dans `mvc/routes.py`.

---

## 7. Vérifier la structure

```bash
forge project:check
```

Vérifie que les entités, relations, routes, templates et modules sont cohérents
après la génération.

```bash
forge project:audit
```

`forge project:audit` produit un rapport détaillé en 4 niveaux :
`ok`, `warn`, `fail`, `info`. Un projet avec deux entités CRUD et une relation
doit passer sans `fail`.

Ces deux commandes sont complémentaires :

| Commande | Ce qu'elle vérifie |
|---|---|
| `forge project:check` | Cohérence structurelle : entités, routes, templates |
| `forge project:audit` | Qualité et diagnostic : avertissements, manques, info |

---

## 8. Comprendre les fichiers générés

### Architecture des fichiers

```text
mvc/entities/
├── Contact/
│   ├── Contact.json         ← source de vérité (vous éditez ce fichier)
│   ├── Contact.sql          ← généré par sync:entity (régénérable)
│   ├── Contact_base.py      ← généré par sync:entity (régénérable)
│   └── Contact.py           ← modèle manuel (préservé)
├── Ville/
│   ├── Ville.json           ← source de vérité (vous éditez ce fichier)
│   ├── Ville.sql            ← généré par sync:entity (régénérable)
│   ├── Ville_base.py        ← généré par sync:entity (régénérable)
│   └── Ville.py             ← modèle manuel (préservé)
├── relations.json           ← source de vérité des relations (vous éditez ce fichier)
└── relations.sql            ← généré par sync:relations (régénérable)
```

### Rôle de chaque fichier

| Fichier | Rôle |
|---|---|
| `<Entite>.json` | Déclare les champs, le type SQL, la clé primaire. Source unique. |
| `<Entite>.sql` | Schéma `CREATE TABLE` généré. Passé à `forge db:init`. |
| `<Entite>_base.py` | Interface Python minimale générée : accès aux champs, SELECT/INSERT/UPDATE/DELETE. |
| `<Entite>.py` | Modèle que vous complétez : validations métier, propriétés calculées. |
| `relations.json` | Déclare les relations globales entre entités. Source unique. |
| `relations.sql` | Contraintes `ALTER TABLE` générées. Passé à `forge db:init`. |
| `<entite>_controller.py` | Contrôleur CRUD généré. Vous pouvez le modifier librement. |
| `<entite>.py` (modèle CRUD) | Modèle CRUD généré. Vous pouvez le modifier librement. |
| `<entite>_form.py` | Formulaire généré. Vous pouvez le modifier librement. |
| `mvc/views/<entite>/*.html` | Templates Jinja générés. Vous pouvez les modifier librement. |
| `mvc/routes.py` | Routes ajoutées automatiquement par `make:crud`. |

---

## 9. Comprendre les fichiers préservés

### La règle centrale

```text
JSON      → sync:entity   → SQL + _base.py          (régénérable à tout moment)
JSON      → sync:relations → relations.sql            (régénérable à tout moment)
JSON      → make:crud     → controller/model/form/views  (préservé — jamais réécrasé)
```

### Ce que Forge régénère librement

| Commande | Fichiers régénérés |
|---|---|
| `forge sync:entity Ville` | `Ville.sql`, `Ville_base.py` |
| `forge sync:entity Contact` | `Contact.sql`, `Contact_base.py` |
| `forge sync:relations` | `relations.sql` |

Ces fichiers sont des **projections** du JSON. Vous pouvez les régénérer autant
de fois que nécessaire sans perte.

### Ce que Forge ne touche plus après la création

| Fichier | Commande de création |
|---|---|
| `Contact.json`, `Ville.json` | `forge make:entity` |
| `Contact.py`, `Ville.py` | `forge make:entity` |
| `relations.json` | `forge make:relation` |
| `contact_controller.py`, `ville_controller.py` | `forge make:crud` |
| `contact.py`, `ville.py` (modèles CRUD) | `forge make:crud` |
| `contact_form.py`, `ville_form.py` | `forge make:crud` |
| `mvc/views/contact/*.html`, `mvc/views/ville/*.html` | `forge make:crud` |
| `mvc/routes.py` (entrées ajoutées) | `forge make:crud` |

Ces fichiers sont les vôtres. Forge n'y touche plus après la création.
Le [Contrat de stabilité](stability-contract.md) garantit formellement cette règle.

---

## 10. Lancer l'application

### Configurer `env/dev`

```bash
# Renseigner les variables MariaDB dans env/dev
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=<mot_de_passe_root>
DB_APP_LOGIN=carnet_contacts_app
DB_APP_PWD=<mot_de_passe_app>
DB_NAME=carnet_contacts
```

### Initialiser la base

```bash
forge db:init
```

Crée la base, l'utilisateur applicatif et les tables issues des fichiers SQL
des entités (`Ville.sql`, `Contact.sql`) et des relations (`relations.sql`).

!!! warning "Ordre des tables"
    `forge db:init` applique d'abord les fichiers SQL des entités, puis
    `relations.sql`. La table `villes` doit exister avant que la contrainte
    de clé étrangère sur `contacts` soit ajoutée. Cet ordre est géré automatiquement.

### Lancer l'application

```bash
python app.py
```

L'application démarre sur `https://localhost:8000` avec HTTPS de développement.

Les routes disponibles :

```text
/ville/          → liste des villes
/ville/new       → créer une ville
/contact/        → liste des contacts (avec ville affichée)
/contact/new     → créer un contact (sélection de ville disponible)
```

---

## 11. Contrôles finaux

```bash
forge doctor
forge project:check
forge project:audit
```

Un projet avec deux entités, une relation `many_to_one`, et les CRUD générés
doit passer les trois contrôles sans `fail`.

```bash
python -m pytest
python -m compileall -q .
```

Les tests Forge valident les générateurs, le runtime et les entités. La
compilation vérifie l'absence d'erreurs de syntaxe.

---

## 12. Structure finale du projet

```text
carnet_contacts/
├── app.py
├── env/dev
├── mvc/
│   ├── routes.py                        # routes Ville et Contact ajoutées
│   ├── controllers/
│   │   ├── ville_controller.py          # CRUD Ville (préservé)
│   │   └── contact_controller.py        # CRUD Contact (préservé)
│   ├── models/
│   │   ├── ville.py                     # modèle CRUD Ville (préservé)
│   │   └── contact.py                   # modèle CRUD Contact (préservé)
│   ├── forms/
│   │   ├── ville_form.py                # formulaire Ville (préservé)
│   │   └── contact_form.py              # formulaire Contact (préservé)
│   ├── views/
│   │   ├── ville/                       # 5 templates Ville (préservés)
│   │   └── contact/                     # 5 templates Contact (préservés)
│   └── entities/
│       ├── Ville/
│       │   ├── Ville.json               # source (modifié)
│       │   ├── Ville.sql                # régénérable
│       │   ├── Ville_base.py            # régénérable
│       │   └── Ville.py                 # préservé
│       ├── Contact/
│       │   ├── Contact.json             # source (modifié)
│       │   ├── Contact.sql              # régénérable
│       │   ├── Contact_base.py          # régénérable
│       │   └── Contact.py              # préservé
│       ├── relations.json               # source (modifié)
│       └── relations.sql                # régénérable
└── forge_profile.txt
```

---

## 13. Limites du tutoriel

Ce tutoriel couvre une application simple. Il ne couvre pas :

| Limite | Documentation |
|---|---|
| Auth / connexion utilisateur | [Auth/User](auth.md) |
| Rôles et permissions (RBAC) | [Sécurité et RBAC](security.md), [RBAC](rbac.md) |
| Relations `many_to_many` | [Relations entre entités](relations.md) |
| Envoi de mails | [Gestion des mails](mail.md) |
| Upload de fichiers / médias | [Module média](media.md) |
| Déploiement en production | [Déploiement](deployment.md) |
| Sécurité en production | [Sécurité en production](production-security.md) |
| API JSON légère | À venir — API-JSON-001 |
| Pages publiques | [Outils — Génération PDF, Module média](media.md) |
| Forge Design | Projet compagnon séparé |

`forge make:relation` est interactif. Pour les projets sans terminal interactif,
éditez directement `mvc/entities/relations.json` selon le format documenté
dans [Relations entre entités](relations.md).

`forge db:init` nécessite un MariaDB local configuré. Sans MariaDB, les
fichiers JSON, SQL, modèles et vues sont générés mais l'application ne peut
pas démarrer.

---

## 14. Aller plus loin

| Étape | Ressource |
|---|---|
| Référence complète des commandes | [API et CLI](reference.md) |
| Filtres de liste CRUD (`list.filter`) | [API et CLI — Filtres CRUD](reference.md) |
| Comprendre les entités et modèles | [Architecture des entités](entity_architecture.md) |
| Déclarer des relations avancées | [Relations entre entités](relations.md) |
| Ajouter l'authentification | [Auth/User](auth.md) |
| Déployer en production | [Guide de déploiement](deployment.md) |
| Sécurité en production | [Sécurité en production](production-security.md) |
| Utiliser un starter complet | [Vue d'ensemble des starters](starters/index.md) |
| Passer à une version suivante | [Guide de migration](migration-guide.md) |
| Garanties sur les fichiers préservés | [Contrat de stabilité](stability-contract.md) |

---

## Récapitulatif des commandes

```bash
forge new carnet_contacts          # créer le projet
cd carnet_contacts
source .venv/bin/activate

forge doctor                       # vérifier l'environnement
forge project:check                # cohérence structurelle

forge make:entity Ville --no-input # créer l'entité Ville
forge make:entity Contact --no-input  # créer l'entité Contact

forge sync:entity Ville            # régénérer SQL et _base.py pour Ville
forge sync:entity Contact          # régénérer SQL et _base.py pour Contact

forge make:relation                # déclarer la relation Contact → Ville
forge sync:relations               # générer relations.sql

forge make:crud Ville              # générer le CRUD Ville
forge make:crud Contact            # générer le CRUD Contact

forge project:check                # vérifier après génération
forge project:audit                # rapport détaillé

forge db:init                      # initialiser la base (MariaDB requis)
python app.py                      # lancer l'application
```

---

## Voir aussi

- [15 minutes avec Forge](15-minutes.md) — tutoriel de démarrage rapide
- [Guide de démarrage](guide.md) — parcours complet avec MariaDB
- [Relations entre entités](relations.md) — format `relations.json` complet
- [Architecture des entités](entity_architecture.md) — rôle de chaque fichier généré
- [Contrat de stabilité](stability-contract.md) — garanties sur les fichiers préservés
- [Référence API et CLI](reference.md) — toutes les commandes
