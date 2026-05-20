# 15 minutes avec Forge

Ce tutoriel guide un développeur depuis un projet vide jusqu'à une première entité `Contact` avec CRUD généré et contrôles de projet.

Il suppose que Forge est déjà installé.

!!! tip "Forge n'est pas encore installé ?"
    Commencez par le parcours d'installation :
    [VM Debian vierge](installation-vm-debian.md),
    [pipx](installation-pipx.md),
    [depuis GitHub](installation-github.md).

---

## Objectif

À la fin de ce tutoriel, vous aurez :

- un projet Forge fonctionnel ;
- une entité `Contact` déclarée en JSON ;
- un CRUD généré (contrôleur, modèle, formulaire, vues) ;
- un projet validé par les outils de diagnostic Forge ;
- une compréhension claire des fichiers générés et préservés.

---

## Ce que tu vas construire

Un annuaire de contacts minimal :

- une entité `Contact` avec nom, prénom et email ;
- les vues liste, fiche, création, modification et suppression ;
- un projet prêt à connecter à MariaDB.

---

## Prérequis

Avant de commencer :

- Forge installé (`forge --version` doit répondre) ;
- Python {{python_min}} ou plus ;
- MariaDB installé et démarré (pour `forge db:init` en fin de tutoriel) ;
- npm installé (optionnel — pour recompiler le CSS Tailwind).

---

## 1. Créer le projet

```bash
forge new demo_contacts
cd demo_contacts
source .venv/bin/activate
```

`forge new` crée la structure du projet, installe les dépendances Python,
génère les certificats SSL de développement, compile le CSS Tailwind si npm
est disponible, et initialise un dépôt Git propre.

Structure créée :

```text
demo_contacts/
├── app.py               # point d'entrée
├── env/dev              # configuration (.env)
├── mvc/
│   ├── routes.py        # déclaration des routes
│   ├── controllers/     # contrôleurs applicatifs
│   ├── models/          # modèles applicatifs
│   ├── forms/           # formulaires
│   ├── views/           # templates Jinja
│   └── entities/        # entités JSON
├── static/              # fichiers statiques
└── forge_profile.txt    # profil du projet
```

---

## 2. Vérifier le projet

Avant de toucher quoi que ce soit :

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

---

## 3. Créer une entité

```bash
forge make:entity Contact --no-input
```

`--no-input` génère une entité minimale sans poser de questions.

Fichiers créés dans `mvc/entities/contact/` :

| Fichier | Rôle | Régénérable ? |
|---|---|---|
| `contact.json` | Source de vérité de l'entité | Non (source) |
| `contact.sql` | Schéma SQL généré | Oui (`build:model`) |
| `contact_base.py` | Interface Python générée | Oui (`build:model`) |
| `contact.py` | Modèle manuel (vide au départ) | **Non — préservé** |

Le fichier JSON est la source de vérité. Forge génère le SQL et le `_base.py`
à partir du JSON. Le fichier `contact.py` est le seul que vous modifiez.

### Personnaliser l'entité

Éditez `mvc/entities/contact/contact.json` :

```json
{
  "schema_version": "1.0",
  "name": "Contact",
  "table": "contacts",
  "fields": [
    { "name": "nom",       "type": "string",  "max_length": 100 },
    { "name": "prenom",    "type": "string",  "max_length": 100 },
    { "name": "email",     "type": "string",  "max_length": 200, "unique": true },
    { "name": "telephone", "type": "string",  "max_length": 20,  "nullable": true }
  ]
}
```

La clé primaire `id` est gérée automatiquement par Forge — ne pas la déclarer dans `fields`.

Après chaque modification du JSON, régénérez le SQL et le `_base.py` :

```bash
forge build:model
```

---

## 4. Générer le CRUD

```bash
forge make:crud Contact
```

Fichiers créés :

| Fichier | Rôle | Modifiable ? |
|---|---|---|
| `mvc/controllers/contact_controller.py` | Contrôleur CRUD | Oui — **préservé** |
| `mvc/models/contact.py` | Modèle (étend Contact_base) | Oui — **préservé** |
| `mvc/forms/contact_form.py` | Formulaire | Oui — **préservé** |
| `mvc/views/contact/list.html` | Vue liste | Oui — **préservé** |
| `mvc/views/contact/show.html` | Vue fiche | Oui — **préservé** |
| `mvc/views/contact/create.html` | Vue création | Oui — **préservé** |
| `mvc/views/contact/edit.html` | Vue modification | Oui — **préservé** |
| `mvc/views/contact/delete.html` | Vue suppression | Oui — **préservé** |

!!! info "Fichiers préservés"
    Ces fichiers ne sont **jamais réécrasés** par Forge.
    Si `forge make:crud` est relancé sur une entité existante, il refuse
    sans l'option `--force`. Votre code est en sécurité.

Les routes sont ajoutées automatiquement dans `mvc/routes.py`.

---

## 5. Vérifier le résultat

```bash
forge project:check
```

Vérifie que les entités, routes, templates et modules sont cohérents après
la génération.

```bash
forge project:audit
```

`forge project:audit` produit un rapport détaillé en 4 niveaux :
`ok`, `warn`, `fail`, `info`. Un projet neuf avec une entité CRUD doit
passer sans `fail`.

---

## 6. Comprendre les fichiers générés

### Ce que Forge génère et peut régénérer

| Fichier | Commande de régénération |
|---|---|
| `Contact.sql` | `forge sync:entity Contact` |
| `Contact_base.py` | `forge sync:entity Contact` |

Ces fichiers sont des **projections** du JSON. Ils peuvent être régénérés
à tout moment sans perte — `sync:entity` lit le JSON et écrase le SQL et le
`_base.py`.

### Ce que Forge crée une fois et ne touche plus

| Fichier | Quand créé |
|---|---|
| `Contact.json` | `forge make:entity` |
| `Contact.py` (modèle manuel) | `forge make:entity` |
| `contact_controller.py` | `forge make:crud` |
| `contact.py` (modèle CRUD) | `forge make:crud` |
| `contact_form.py` | `forge make:crud` |
| `mvc/views/contact/*.html` | `forge make:crud` |
| `mvc/routes.py` (entrées ajoutées) | `forge make:crud` |

Ces fichiers sont les vôtres. Forge n'y touche plus après la création.

### Règle centrale

```text
JSON → sync:entity → SQL + _base.py    (régénérable)
JSON → make:crud   → controller/model/form/views  (préservé)
```

---

## 7. Initialiser la base et lancer l'application

### Configurer `env/dev`

```bash
# Renseigner les mots de passe MariaDB dans env/dev
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=<mot_de_passe_root>
DB_APP_LOGIN=demo_contacts_app
DB_APP_PWD=<mot_de_passe_app>
DB_NAME=demo_contacts
```

### Initialiser la base

```bash
forge db:init
```

Crée la base, l'utilisateur applicatif et les tables issues des fichiers SQL
des entités.

### Lancer l'application

```bash
python app.py
```

L'application démarre sur `https://localhost:8000` avec HTTPS de développement.

---

## 8. Limites du tutoriel

Ce tutoriel couvre le chemin minimal. Il ne couvre pas :

| Limite | Ticket / documentation |
|---|---|
| Auth / connexion utilisateur | [Auth/User](auth.md) |
| Rôles et permissions (RBAC) | [Sécurité et RBAC](security.md), [RBAC](rbac.md) |
| Relations entre entités | [Relations](relations.md) |
| Envoi de mails | [Gestion des mails](mail.md) |
| Upload de fichiers / médias | [Module média](media.md) |
| Déploiement en production | [Déploiement](deployment.md) |
| Sécurité en production | [Sécurité en production](production-security.md) |
| Modules Forge | [Vue d'ensemble des starters](starters/index.md) |

`forge make:entity --no-input` génère une entité minimale sans champs réels.
En pratique, vous éditez directement le JSON avant ou après la génération.

`forge db:init` nécessite un MariaDB local configuré. Sans MariaDB, les fichiers
JSON, SQL, modèles et vues sont générés mais l'application ne peut pas démarrer.

---

## 9. Où aller ensuite

| Étape | Ressource |
|---|---|
| Référence complète des commandes | [API et CLI](reference.md) |
| Comprendre les entités et modèles | [Architecture des entités](entity_architecture.md) |
| Ajouter l'authentification | [Auth/User](auth.md) |
| Déployer en production | [Guide de déploiement](deployment.md) |
| Sécurité en production | [Sécurité en production](production-security.md) |
| Utiliser un starter complet | [Vue d'ensemble des starters](starters/index.md) |
| Passer à une version suivante | [Guide de migration](migration-guide.md) |
| Tutoriel application complète | À venir — `DOC-APP-COMPLETE-001` |

---

## Récapitulatif des commandes

```bash
forge new demo_contacts          # créer le projet
cd demo_contacts
source .venv/bin/activate
forge doctor                     # vérifier l'environnement
forge project:check              # cohérence structurelle
forge make:entity Contact --no-input   # créer une entité
forge sync:entity Contact        # régénérer SQL et _base.py
forge make:crud Contact          # générer le CRUD complet
forge project:check              # vérifier après génération
forge project:audit              # rapport détaillé
forge db:init                    # initialiser la base (MariaDB requis)
python app.py                    # lancer l'application
```

---

## Voir aussi

- [Guide de démarrage](guide.md) — parcours complet avec MariaDB
- [Référence API et CLI](reference.md) — toutes les commandes
- [Contrat de stabilité](stability-contract.md) — fichiers garantis préservés
- [Release et compatibilité](release-and-compatibility.md) — versions supportées
