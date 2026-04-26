# Starter 1 — Contacts

Premier parcours Forge : une seule entité `Contact`, un CRUD généré, puis un câblage manuel des routes.

## Présentation rapide

### Objectif

Construire une petite application de gestion de contacts avec :

- une liste simple, enrichissable ensuite ;
- une page de création ;
- une page de détail ;
- une page de modification ;
- une suppression en `POST` ;
- des messages flash après création, modification ou suppression.

Le starter sert à comprendre le flux Forge minimal : JSON canonique, SQL visible, modèle Python généré, CRUD MVC explicite et routes copiées manuellement.

### Niveau

Niveau 1 — débutant Forge.

Le parcours ne contient ni relation, ni authentification métier spécifique, ni logique complexe. Il est conçu pour vérifier que le projet, la base de données, les formulaires, les vues Jinja2 et les routes fonctionnent ensemble.

### Temps estimé

1h à 2h.

### Résultat attendu

Application CRUD complète pour gérer des contacts — liste, création, modification, suppression — avec formulaires validés, messages flash et HTTPS local.

### Schéma général du starter

Ce premier starter suit volontairement un parcours simple : une requête arrive par une route, le contrôleur appelle le modèle, le modèle dialogue avec MariaDB, puis le contrôleur renvoie une vue Jinja2 au navigateur.

```text
Navigateur
   │
   │ GET /contacts, POST /contacts, etc.
   ▼
mvc/routes.py
   │
   ▼
ContactController
   │
   ├── utilise ContactForm pour lire et valider les formulaires
   │
   ├── appelle contact_model.py pour lire ou écrire en base
   │        │
   │        ▼
   │      MariaDB
   │
   └── rend une vue Jinja2
            │
            ▼
        HTML affiché
```

L'objectif n'est pas seulement d'obtenir un CRUD fonctionnel. L'objectif est surtout de voir les pièces réelles utilisées par Forge : routes, contrôleur, formulaire, modèle SQL, templates et base de données.

---

## Installation du projet Forge

### Méthode A — installation automatique (recommandée)

```bash
pipx install git+https://github.com/caucrogeGit/Forge.git
forge new Contacts
cd Contacts
source .venv/bin/activate
forge doctor
```

### Méthode B — installation manuelle

```bash
git clone https://github.com/caucrogeGit/Forge.git Contacts
cd Contacts
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
npm install
forge doctor
```

> Si une commande globale `forge ...` échoue, utiliser la commande locale équivalente `python forge.py ...`.

### Schéma d'installation

Les deux méthodes arrivent au même résultat : un projet Forge local avec un environnement Python actif et une commande `forge` utilisable.

```text
Méthode A — automatique
pipx install ...
   │
   ▼
forge new Contacts
   │
   ▼
projet Forge prêt

Méthode B — manuelle
git clone ... Contacts
   │
   ▼
python -m venv .venv
   │
   ▼
pip install -r requirements.txt
pip install -e .
   │
   ▼
projet Forge prêt
```

Dans les deux cas, la commande de contrôle est la même :

```bash
forge doctor
```

---

## Préparation de la base

### Configurer l'administrateur MariaDB du projet

Avant d'exécuter `forge db:init`, renseigner dans `env/dev` un compte MariaDB disposant des droits nécessaires pour :

- créer la base de données du projet ;
- créer l'utilisateur applicatif ;
- appliquer les privilèges nécessaires.

En développement local, on peut utiliser temporairement un compte administrateur MariaDB existant.

Exemple pour une application nommée `Contacts` :

```env
DB_HOST=localhost
DB_PORT=3306

DB_NAME=contact_simple

DB_ADMIN_USER=forge_admin
DB_ADMIN_PWD=MotDePasseAdminFort

DB_APP_USER=contacts_app
DB_APP_PWD=ContactsApp_2026!
```

Dans cet exemple :

- `DB_ADMIN_USER=forge_admin` correspond à un utilisateur MariaDB déjà existant ;
- `DB_ADMIN_PWD` est le mot de passe de cet utilisateur administrateur ;
- `DB_NAME=contact_simple` est la base que Forge va créer ;
- `DB_APP_USER=contacts_app` est l'utilisateur applicatif que Forge va créer ;
- `DB_APP_PWD` est le mot de passe de l'utilisateur applicatif.

`DB_ADMIN_USER` sert uniquement à l'initialisation de la base avec `forge db:init`.
Ensuite, l'application utilise `DB_APP_USER`, plus limité, pour se connecter à la base.

### Schéma : rôle des comptes MariaDB

Il y a deux comptes à ne pas confondre.

```text
Étape d'initialisation

forge db:init
   │
   ▼
DB_ADMIN_USER
   │
   ├── crée la base DB_NAME
   ├── crée DB_APP_USER
   └── donne les droits nécessaires à DB_APP_USER

Étape d'exécution de l'application

python app.py
   │
   ▼
DB_APP_USER
   │
   └── lit et écrit uniquement dans la base du projet
```

Le compte administrateur sert à préparer la base. Le compte applicatif sert ensuite au fonctionnement normal de l'application.

### Initialiser la base

```bash
forge db:init
```

Cette commande crée la base de données du projet, l'utilisateur applicatif et applique les droits.

Prérequis :

- MariaDB installé et en cours d'exécution ;
- les identifiants de connexion renseignés dans `env/dev` (`DB_ADMIN_USER`, `DB_ADMIN_PWD`, `DB_APP_USER`, `DB_APP_PWD`, etc.).

---

## Développement de l'application

### Ce que l'on apprend

- Créer une entité avec `forge make:entity`.
- Compléter le JSON canonique après `--no-input`.
- Vérifier le modèle avec `forge check:model`.
- Prévisualiser la génération avec `forge build:model --dry-run`.
- Générer `contact.sql` et `contact_base.py`.
- Appliquer le SQL avec `forge db:apply`.
- Prévisualiser un CRUD avec `forge make:crud Contact --dry-run`.
- Générer un CRUD avec `forge make:crud Contact`.
- Copier les routes dans `mvc/routes.py`.
- Lire et adapter les fichiers générés sans attendre d'admin magique.

### Schéma du parcours de développement

Le développement du starter suit un enchaînement volontairement déterministe.

```text
make:entity
   │
   ▼
édition de contact.json
   │
   ▼
check:model
   │
   ▼
build:model --dry-run
   │
   ▼
build:model
   │
   ├── génère contact.sql
   └── génère contact_base.py
   │
   ▼
db:apply
   │
   ▼
make:crud --dry-run
   │
   ▼
make:crud
   │
   ├── génère le contrôleur
   ├── génère le modèle SQL applicatif
   ├── génère le formulaire
   └── génère les templates
   │
   ▼
copie des routes dans mvc/routes.py
```

Ce schéma est important : Forge ne saute pas directement à une application terminée. Il produit des fichiers lisibles, puis le développeur les câble explicitement.

### Navigation de l'application

```text
/contacts           liste des contacts
/contacts/new       formulaire de création
/contacts/{id}      détail d'un contact
/contacts/{id}/edit formulaire de modification
```

`/contacts/new` doit rester déclaré avant `/contacts/{id}` dans les routes afin d'éviter que `new` soit interprété comme un identifiant.

### Schéma de navigation

```text
/contacts
   │
   ├── bouton "Nouveau contact"
   │        ▼
   │    /contacts/new
   │
   ├── lien "Voir"
   │        ▼
   │    /contacts/{id}
   │
   └── lien "Modifier"
            ▼
        /contacts/{id}/edit

/contacts/{id}
   └── bouton "Supprimer" en POST vers /contacts/{id}/delete
```

La liste est le point d'entrée principal. Les autres pages partent de cette liste.

### Charte graphique

Le starter utilise une charte volontairement simple. Les couleurs ci-dessous correspondent aux classes Tailwind utilisées dans les vues générées.

| Usage | Couleur | Code hexadécimal | Aperçu |
|---|---:|---:|---|
| Fond des pages de formulaire et de liste | Slate très clair | `#F8FAFC` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #CBD5E1;background:#F8FAFC;border-radius:0.25rem;"></span> |
| Barre supérieure dans `mvc/views/layouts/app.html` | Slate très foncé | `#0F172A` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #0F172A;background:#0F172A;border-radius:0.25rem;"></span> |
| Actions principales | Orange Forge | `#EA580C` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #C2410C;background:#EA580C;border-radius:0.25rem;"></span> |
| Survol des actions principales | Orange Forge foncé | `#C2410C` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #9A3412;background:#C2410C;border-radius:0.25rem;"></span> |
| Actions secondaires : retour, annulation | Gris clair | `#E2E8F0` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #CBD5E1;background:#E2E8F0;border-radius:0.25rem;"></span> |
| Texte principal | Slate foncé | `#0F172A` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #0F172A;background:#0F172A;border-radius:0.25rem;"></span> |
| Texte secondaire | Slate moyen | `#64748B` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #475569;background:#64748B;border-radius:0.25rem;"></span> |
| Cartes de formulaire et de détail | Blanc | `#FFFFFF` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #CBD5E1;background:#FFFFFF;border-radius:0.25rem;"></span> |
| Bordures des cartes | Slate clair | `#E2E8F0` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #CBD5E1;background:#E2E8F0;border-radius:0.25rem;"></span> |
| Message flash de succès | Vert clair | `#DCFCE7` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #86EFAC;background:#DCFCE7;border-radius:0.25rem;"></span> |
| Message flash d'erreur | Rouge clair | `#FEE2E2` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #FCA5A5;background:#FEE2E2;border-radius:0.25rem;"></span> |

Le but n'est pas de créer un thème complet, mais d'obtenir une interface lisible et facile à modifier.

### Modèle de données

Fichier canonique : `mvc/entities/contact/contact.json`.

```json
{
  "format_version": 1,
  "entity": "Contact",
  "table": "contact",
  "description": "Contacts — starter niveau 1",
  "fields": [
    {
      "name": "id",
      "sql_type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "nom",
      "sql_type": "VARCHAR(80)",
      "constraints": {
        "not_empty": true,
        "max_length": 80
      }
    },
    {
      "name": "prenom",
      "sql_type": "VARCHAR(80)",
      "constraints": {
        "not_empty": true,
        "max_length": 80
      }
    },
    {
      "name": "email",
      "sql_type": "VARCHAR(120)",
      "unique": true,
      "constraints": {
        "not_empty": true,
        "max_length": 120
      }
    },
    {
      "name": "telephone",
      "sql_type": "VARCHAR(20)",
      "nullable": true,
      "constraints": {
        "max_length": 20
      }
    }
  ]
}
```

Forge génère ensuite `mvc/entities/contact/contact.sql` et `mvc/entities/contact/contact_base.py`. Le fichier manuel `mvc/entities/contact/contact.py` reste préservé.

La contrainte `unique: true` empêche deux contacts d'utiliser le même email. Dans ce starter, cette contrainte est principalement portée par la base MariaDB. Si un doublon est saisi, la base peut refuser l'insertion ou la mise à jour.

### Schéma : du JSON canonique aux fichiers générés

```text
contact.json
   │
   │ source canonique modifiée par le développeur
   ▼
forge build:model
   │
   ├── contact.sql
   │      └── structure SQL visible de la table contact
   │
   └── contact_base.py
          └── classe Python régénérable avec validations simples

contact.py
   └── fichier manuel préservé pour la logique métier
```

La règle à retenir est simple : on modifie le JSON et le fichier métier manuel, pas les fichiers régénérables.

### Commandes Forge

Cette partie montre les commandes, mais aussi ce que Forge écrit réellement dans le projet. L'objectif est de comprendre l'envers du décor : Forge ne cache pas le modèle, le SQL, le contrôleur ni les vues.

#### 1. Créer l'entité minimale

```bash
forge make:entity Contact --no-input
```

Cette commande crée la structure de départ de l'entité :

```text
mvc/entities/contact/
├── __init__.py
├── contact.json
├── contact.sql
├── contact_base.py
└── contact.py
```

À ce stade, `contact.json` est volontairement minimal. Le développeur le complète ensuite avec les champs métier présentés plus haut : `nom`, `prenom`, `email`, `telephone`.

Le fichier manuel `contact.py` sert de point d'extension métier. Il n'est pas écrasé lors des régénérations.

```python
from .contact_base import ContactBase


class Contact(ContactBase):
    """Point d'extension métier pour Contact."""

    pass
```

#### 2. Vérifier le modèle canonique

```bash
forge check:model
```

Cette commande lit les fichiers JSON présents dans `mvc/entities/` et vérifie leur cohérence. Elle ne modifie aucun fichier.

Elle sert à repérer les erreurs avant génération : champ incomplet, type SQL invalide, clé primaire absente, doublon de table ou incohérence de modèle.

#### 3. Prévisualiser la génération du modèle

```bash
forge build:model --dry-run
```

Le mode `--dry-run` indique ce que Forge générerait, sans écrire les fichiers. C'est une étape de contrôle.

Forge prépare principalement deux fichiers régénérables :

```text
mvc/entities/contact/contact.sql
mvc/entities/contact/contact_base.py
```

#### 4. Générer le SQL et la classe de base

```bash
forge build:model
```

Cette commande régénère les fichiers techniques à partir de `contact.json`.

Exemple de SQL généré dans `mvc/entities/contact/contact.sql` :

```sql
CREATE TABLE IF NOT EXISTS contact (
    Id INT NOT NULL AUTO_INCREMENT,
    Nom VARCHAR(80) NOT NULL,
    Prenom VARCHAR(80) NOT NULL,
    Email VARCHAR(120) NOT NULL,
    UNIQUE KEY uk_contact_email (Email),
    Telephone VARCHAR(20) NULL,
    PRIMARY KEY (Id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

Extrait simplifié de `mvc/entities/contact/contact_base.py` :

```python
from core.validation import ValidationError, max_length, not_empty, nullable, typed


class ContactBase:
    """Classe de base régénérable de Contact."""

    def __init__(self, nom, prenom, email, id=None, telephone=None):
        self.nom = nom
        self.prenom = prenom
        self.email = email
        self.id = id
        self.telephone = telephone

    @property
    def nom(self):
        return self._nom

    @nom.setter
    @typed(str)
    @not_empty
    @max_length(80)
    def nom(self, value):
        if value is None:
            raise ValidationError("nom", 'La propriété "nom" ne peut pas être nulle.')
        self._nom = value

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "email": self.email,
            "telephone": self.telephone,
        }
```

Le fichier `contact_base.py` est régénérable. Il ne faut pas y écrire de logique métier manuelle. La logique métier se place dans `contact.py`.

#### 5. Appliquer le SQL sur la base de développement

```bash
forge db:apply
```

Cette commande applique le SQL généré sur la base MariaDB configurée dans `env/dev`.

Dans ce starter, `forge db:apply` est utilisé sur une base de développement neuve. Le starter ne présente pas encore un système complet de migrations avancées. Si le modèle change fortement après création de la table, il faut traiter la modification de schéma avec prudence.

#### 6. Prévisualiser le CRUD

```bash
forge make:crud Contact --dry-run
```

Cette commande montre les fichiers que Forge créerait pour le CRUD, sans les écrire.

Elle permet de vérifier que Forge va travailler sur la bonne entité et qu'aucun fichier existant ne sera créé par erreur.

#### 7. Générer le CRUD

```bash
forge make:crud Contact
```

Cette commande crée les fichiers MVC applicatifs s'ils sont absents :

```text
mvc/controllers/contact_controller.py
mvc/models/contact_model.py
mvc/forms/contact_form.py
mvc/views/layouts/app.html
mvc/views/contact/index.html
mvc/views/contact/show.html
mvc/views/contact/form.html
```

Schéma de génération du CRUD :

```text
forge make:crud Contact
   │
   ├── contact_controller.py
   │      └── reçoit les requêtes et choisit la réponse
   │
   ├── contact_model.py
   │      └── contient les requêtes SQL explicites
   │
   ├── contact_form.py
   │      └── lit et valide les données de formulaire
   │
   └── views/contact/*.html
          └── affichent la liste, le formulaire et le détail
```

Extrait du modèle généré dans `mvc/models/contact_model.py` :

```python
from core.database.connection import get_connection, close_connection

SELECT_ALL   = "SELECT * FROM contact ORDER BY Id"
SELECT_BY_ID = "SELECT * FROM contact WHERE Id = ?"
INSERT       = "INSERT INTO contact (Nom, Prenom, Email, Telephone) VALUES (?, ?, ?, ?)"
UPDATE       = "UPDATE contact SET Nom = ?, Prenom = ?, Email = ?, Telephone = ? WHERE Id = ?"
DELETE       = "DELETE FROM contact WHERE Id = ?"
```

Extrait du formulaire généré dans `mvc/forms/contact_form.py` :

```python
from core.forms import Form, StringField


class ContactForm(Form):
    nom = StringField(label="Nom", required=True, max_length=80)
    prenom = StringField(label="Prenom", required=True, max_length=80)
    email = StringField(label="Email", required=True, max_length=120)
    telephone = StringField(label="Telephone", required=False, max_length=20)
```

Extrait du contrôleur généré dans `mvc/controllers/contact_controller.py` :

```python
class ContactController(BaseController):

    @staticmethod
    def index(request):
        contacts = get_contacts()
        return BaseController.render(
            "contact/index.html",
            context={"contacts": contacts, "flash_html": render_flash_html(request)},
            request=request,
        )

    @staticmethod
    def create(request):
        form = ContactForm.from_request(request)
        if not form.is_valid():
            return BaseController.validation_error(
                "contact/form.html",
                context={"form": form, "action": "/contacts", "titre": "Nouveau contact"},
                request=request,
            )

        add_contact(form.cleaned_data)
        return BaseController.redirect_with_flash(request, "/contacts", "Contact créé.")
```

Forge génère donc une base de travail lisible, mais le développeur garde la main : les routes restent à déclarer explicitement dans `mvc/routes.py`.

### Routes à ajouter

Après la génération du CRUD, copier ou vérifier les routes dans `mvc/routes.py`.

```python
from mvc.controllers.contact_controller import ContactController

# Routes protégées par défaut.
# Pour un test local sans authentification :
# with router.group("/contacts", public=True, csrf=False) as g:
with router.group("/contacts") as g:
    g.add("GET",  "",              ContactController.index,   name="contact_index")
    g.add("GET",  "/new",          ContactController.new,     name="contact_new")
    g.add("POST", "",              ContactController.create,  name="contact_create")
    g.add("GET",  "/{id}",         ContactController.show,    name="contact_show")
    g.add("GET",  "/{id}/edit",    ContactController.edit,    name="contact_edit")
    g.add("POST", "/{id}",         ContactController.update,  name="contact_update")
    g.add("POST", "/{id}/delete",  ContactController.destroy, name="contact_destroy")
```

Dans ce groupe, la route `/new` doit rester déclarée avant `/{id}` afin d'éviter que `new` soit interprété comme un identifiant.

### Fichiers créés ou modifiés

Fichiers canoniques et générés :

```text
mvc/entities/contact/contact.json       source canonique à modifier
mvc/entities/contact/contact.sql        généré
mvc/entities/contact/contact_base.py    généré
mvc/entities/contact/contact.py         manuel, préservé
mvc/entities/contact/__init__.py        manuel, préservé
```

Fichiers CRUD créés s'ils sont absents :

```text
mvc/controllers/contact_controller.py
mvc/models/contact_model.py
mvc/forms/contact_form.py
mvc/views/layouts/app.html
mvc/views/contact/index.html
mvc/views/contact/show.html
mvc/views/contact/form.html
```

Fichier à modifier manuellement :

```text
mvc/routes.py
```

### Vue d'ensemble de l'arborescence

```text
mvc/
├── entities/
│   └── contact/
│       ├── contact.json        # source canonique
│       ├── contact.sql         # SQL généré
│       ├── contact_base.py     # classe générée
│       ├── contact.py          # classe métier manuelle
│       └── __init__.py
│
├── controllers/
│   └── contact_controller.py   # logique HTTP du CRUD
│
├── models/
│   └── contact_model.py        # requêtes SQL explicites
│
├── forms/
│   └── contact_form.py         # validation du formulaire
│
├── views/
│   ├── layouts/
│   │   └── app.html            # layout commun
│   └── contact/
│       ├── index.html          # liste
│       ├── form.html           # création / modification
│       └── show.html           # détail
│
└── routes.py                   # routes à compléter manuellement
```

Cette arborescence montre le principe de Forge : le code généré reste visible, classé et modifiable quand il appartient à la partie applicative.

### Classes Python utilisées

- `ContactBase` : classe générée depuis le JSON.
- `Contact` : classe métier manuelle qui hérite de `ContactBase`.
- `ContactForm` : formulaire généré, basé sur `core.forms.Form`.
- `ContactController` : contrôleur MVC généré, avec les actions `index`, `new`, `create`, `show`, `edit`, `update` et `destroy`.
- `BaseController` : rendu HTML, redirections, flash et erreurs de validation.

Le contrôleur généré lit les formulaires via l'API réelle Forge.

Exemple simplifié pour la création d'un contact :

```python
form = ContactForm.from_request(request)

if not form.is_valid():
    return BaseController.validation_error(
        "contact/form.html",
        context={"form": form, "action": "/contacts", "titre": "Nouveau contact"},
        request=request,
    )

add_contact(form.cleaned_data)
return BaseController.redirect_with_flash(request, "/contacts", "Contact créé.")
```

Le modèle généré expose des fonctions SQL explicites :

```python
get_contacts()
get_contact_by_id(id)
add_contact(data)
update_contact(id, data)
delete_contact(id)
```

### Schéma : cycle d'une création de contact

Exemple avec l'envoi du formulaire de création.

```text
Navigateur
   │
   │ POST /contacts
   ▼
mvc/routes.py
   │
   ▼
ContactController.create(request)
   │
   ├── ContactForm.from_request(request)
   │
   ├── form.is_valid()
   │       │
   │       ├── non
   │       │    └── retour vers contact/form.html avec les erreurs
   │       │
   │       └── oui
   │            └── add_contact(form.cleaned_data)
   │                    │
   │                    ▼
   │                  MariaDB
   │
   └── redirect_with_flash(request, "/contacts", "Contact créé.")
```

Le formulaire ne va pas directement en base. Il passe par le contrôleur, puis par le modèle SQL.

### Création des templates Jinja

Le CRUD génère trois vues pour `Contact`, plus un layout commun.

```text
mvc/views/layouts/app.html
mvc/views/contact/index.html
mvc/views/contact/form.html
mvc/views/contact/show.html
```

#### Schéma : héritage des templates

```text
layouts/app.html
   │
   ├── barre supérieure
   ├── messages flash
   └── block content
          ▲
          │
          ├── contact/index.html  # liste des contacts
          ├── contact/form.html   # création et modification
          └── contact/show.html   # détail d'un contact
```

Le layout contient la structure commune de la page. Les vues `index.html`, `form.html` et `show.html` remplissent uniquement la zone principale avec `{% block content %}`.

#### Template de liste : `contact/index.html`

La liste reçoit une variable `contacts`, fournie par le contrôleur.

```jinja2
{% extends "layouts/app.html" %}

{% block content %}
<h1>Contacts</h1>

<a href="/contacts/new">Nouveau contact</a>

{% for contact in contacts %}
    <article>
        <h2>{{ contact.Nom }} {{ contact.Prenom }}</h2>
        <p>{{ contact.Email }}</p>
        <a href="/contacts/{{ contact.Id }}">Voir</a>
        <a href="/contacts/{{ contact.Id }}/edit">Modifier</a>
    </article>
{% endfor %}
{% endblock %}
```

Dans cette vue, `contact.Nom`, `contact.Prenom`, `contact.Email` et `contact.Id` correspondent aux colonnes SQL retournées par `cursor(dictionary=True)`.

#### Template de formulaire : `contact/form.html`

Le même template sert à la création et à la modification. La différence vient de la variable `action` fournie par le contrôleur.

```jinja2
{% extends "layouts/app.html" %}

{% block content %}
<h1>{{ titre }}</h1>

<form method="post" action="{{ action }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    <label>Nom</label>
    <input type="text" name="nom" value="{{ form.value('nom') }}">

    <label>Prénom</label>
    <input type="text" name="prenom" value="{{ form.value('prenom') }}">

    <label>Email</label>
    <input type="email" name="email" value="{{ form.value('email') }}">

    <label>Téléphone</label>
    <input type="text" name="telephone" value="{{ form.value('telephone') }}">

    <button type="submit">Enregistrer</button>
</form>
{% endblock %}
```

Dans le formulaire, les noms utilisés sont les noms Python du JSON canonique : `nom`, `prenom`, `email`, `telephone`.

#### Template de détail : `contact/show.html`

La page de détail reçoit un seul dictionnaire `contact`.

```jinja2
{% extends "layouts/app.html" %}

{% block content %}
<h1>{{ contact.Nom }} {{ contact.Prenom }}</h1>

<p>Email : {{ contact.Email }}</p>
<p>Téléphone : {{ contact.Telephone }}</p>

<a href="/contacts/{{ contact.Id }}/edit">Modifier</a>

<form method="post" action="/contacts/{{ contact.Id }}/delete">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button type="submit">Supprimer</button>
</form>
{% endblock %}
```

La suppression utilise une requête `POST`. Cela évite de supprimer une donnée avec une simple navigation en `GET`.

#### À retenir sur les noms utilisés

```text
Dans contact.json et ContactForm
   └── noms Python : nom, prenom, email, telephone

Dans les vues alimentées par MariaDB
   └── colonnes SQL : Nom, Prenom, Email, Telephone, Id
```

Les champs de formulaire utilisent donc `form.value("nom")`, tandis que les vues de liste et de détail affichent `contact.Nom` ou `contact.Email`.

#### Classes CSS/Tailwind importantes

Le CRUD généré s'appuie sur des classes utilitaires simples.

```text
Mise en page
├── max-w-5xl
├── mx-auto
├── px-6
└── py-8

Cartes
├── bg-white
├── border
├── rounded
└── shadow-sm

Texte
├── text-slate-900
└── text-slate-500

Actions principales
├── bg-orange-600
├── hover:bg-orange-700
└── text-white

Composition
├── grid
├── gap-4
├── flex
├── items-center
└── justify-between
```

Ces classes peuvent être remplacées par votre propre design sans modifier la doctrine Forge.

### Test navigateur

1. Lancer `python app.py`.
2. Ouvrir `/contacts`.
3. Cliquer sur "Nouveau contact".
4. Soumettre le formulaire vide et vérifier l'affichage des erreurs.
5. Créer un contact valide.
6. Vérifier le retour à la liste et le message flash.
7. Ouvrir le détail du contact.
8. Modifier le contact.
9. Supprimer le contact avec le bouton prévu.
10. Vérifier que la liste est cohérente après suppression.

### Limites du starter

- Pas d'authentification dédiée.
- Pas de recherche avancée.
- Pas de pagination générée automatiquement.
- Pas de validation métier au-delà des contraintes simples.
- Pas de relation : ce starter est volontairement mono-entité.
- Pas d'ORM : les requêtes SQL restent visibles dans `mvc/models/contact_model.py`.

---

## Vérification finale du starter

La vérification finale sert à contrôler trois choses : l'environnement Forge, les routes et le comportement réel dans le navigateur.

### Schéma de vérification

```text
forge doctor
   │
   └── vérifie l'environnement du projet

forge routes:list
   │
   └── vérifie que les routes /contacts existent

python app.py
   │
   └── lance le serveur HTTPS local

Navigateur
   │
   └── vérifie le CRUD complet
```

### Vérifier l'environnement Forge

```bash
forge doctor
```

Cette commande permet de vérifier que le projet est correctement installé et que Forge trouve les éléments nécessaires à son fonctionnement.

### Vérifier les routes

```bash
forge routes:list
```

Les routes suivantes doivent apparaître ou être équivalentes selon l'affichage de Forge :

```text
GET   /contacts
GET   /contacts/new
POST  /contacts
GET   /contacts/{id}
GET   /contacts/{id}/edit
POST  /contacts/{id}
POST  /contacts/{id}/delete
```

Si `/contacts/new` n'apparaît pas avant `/contacts/{id}`, il faut vérifier l'ordre des routes dans `mvc/routes.py`.

### Lancer le serveur local

```bash
python app.py
```

Ouvrir ensuite dans le navigateur :

```text
https://localhost:8000/contacts
```

### Scénario de test navigateur

```text
1. Ouvrir /contacts
2. Cliquer sur "Nouveau contact"
3. Soumettre le formulaire vide
4. Vérifier l'affichage des erreurs
5. Créer un contact valide
6. Vérifier le retour à la liste
7. Vérifier le message flash
8. Ouvrir le détail du contact
9. Modifier le contact
10. Supprimer le contact
11. Vérifier que le contact supprimé n'apparaît plus dans la liste
```

### Erreurs fréquentes

| Symptôme | Cause probable | Fichier ou commande à vérifier |
|---|---|---|
| `/contacts` affiche une erreur 404 | routes non copiées | `mvc/routes.py` |
| `/contacts/new` est interprété comme un identifiant | ordre des routes incorrect | placer `/new` avant `/{id}` |
| erreur de connexion MariaDB | variables incorrectes | `env/dev` |
| table `contact` absente | SQL non appliqué | `forge db:apply` |
| erreur sur `contact.Nom` dans la vue | colonnes SQL différentes | `contact.sql`, `contact_model.py`, template Jinja |
| formulaire sans protection CSRF | champ caché absent | `contact/form.html` |
| doublon email refusé | contrainte `unique: true` | vérifier la donnée saisie |

## Reconstruction

Le fichier complet de reconstruction est disponible dans [starters/01-contact-simple/rebuild.md](starters/01-contact-simple/rebuild.md).
