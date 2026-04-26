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

### Navigation de l'application

```text
/contacts           liste des contacts
/contacts/new       formulaire de création
/contacts/{id}      détail d'un contact
/contacts/{id}/edit formulaire de modification
```

`/contacts/new` doit rester déclaré avant `/contacts/{id}` dans les routes afin d'éviter que `new` soit interprété comme un identifiant.

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

### Création des templates Jinja

La commande `forge make:crud Contact` ne crée pas une interface cachée. Elle écrit de vrais fichiers HTML dans `mvc/views/`. Ces fichiers sont des templates Jinja2 classiques : le développeur peut les ouvrir, les lire, les modifier ou les remplacer.

#### Fichiers de templates créés

```text
mvc/views/layouts/app.html      layout commun de l'application
mvc/views/contact/index.html    liste des contacts
mvc/views/contact/show.html     détail d'un contact
mvc/views/contact/form.html     formulaire de création et de modification
```

Le fichier `app.html` sert de squelette général. Les vues `index.html`, `show.html` et `form.html` remplissent seulement la zone centrale de la page.

#### 1. Le layout commun

Le layout définit la structure HTML globale : chargement de Tailwind, barre supérieure, zone principale et affichage des messages flash.

Extrait simplifié de `mvc/views/layouts/app.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ titre | default("Application") }}</title>
    <link rel="stylesheet" href="/static/tailwind.css">
</head>
<body class="bg-slate-50 min-h-screen text-slate-900">

    <nav class="bg-slate-900 text-white px-6 py-4 shadow">
        <a href="/" class="text-xl font-bold">Contacts</a>
    </nav>

    <main class="max-w-5xl mx-auto px-6 py-8">
        {% if flash_html %}
            {{ flash_html | safe }}
        {% endif %}

        {% block content %}{% endblock %}
    </main>

</body>
</html>
```

À retenir :

- `{{ titre | default("Application") }}` affiche un titre si le contrôleur en fournit un ;
- `{{ flash_html | safe }}` affiche les messages flash générés par Forge ;
- `{% block content %}{% endblock %}` réserve l'emplacement que les autres templates vont remplir.

#### 2. Le template de liste

La liste des contacts est générée dans `mvc/views/contact/index.html`.

Extrait simplifié :

```jinja2
{% extends "layouts/app.html" %}
{% block content %}

<div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold text-slate-900">Liste des contacts</h1>

    <a href="/contacts/new"
       class="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded">
        Nouveau contact
    </a>
</div>

{% if contacts %}
    <div class="bg-white border rounded shadow-sm overflow-hidden">
        <table class="w-full">
            <thead class="bg-slate-50 border-b">
                <tr>
                    <th class="px-4 py-3 text-left">Nom</th>
                    <th class="px-4 py-3 text-left">Prénom</th>
                    <th class="px-4 py-3 text-left">Email</th>
                    <th class="px-4 py-3 text-right">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for contact in contacts %}
                <tr class="border-b">
                    <td class="px-4 py-3">{{ contact.Nom }}</td>
                    <td class="px-4 py-3">{{ contact.Prenom }}</td>
                    <td class="px-4 py-3">{{ contact.Email }}</td>
                    <td class="px-4 py-3 text-right">
                        <a href="/contacts/{{ contact.Id }}">Voir</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
{% else %}
    <p class="text-slate-500">Aucun contact pour l'instant.</p>
{% endif %}

{% endblock %}
```

Ici, `contacts` vient du contrôleur. Chaque `contact` est un dictionnaire retourné par la base de données. C'est pour cette raison que la vue utilise les noms de colonnes SQL en PascalCase : `contact.Nom`, `contact.Prenom`, `contact.Email`, `contact.Id`.

#### 3. Le template de formulaire

Le formulaire de création et le formulaire de modification utilisent le même fichier : `mvc/views/contact/form.html`.

Extrait simplifié :

```jinja2
{% extends "layouts/app.html" %}
{% block content %}

<div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold text-slate-900">{{ titre }}</h1>
    <a href="/contacts" class="text-slate-600 hover:underline">← Retour</a>
</div>

{% include "partials/form_errors.html" %}

<div class="bg-white border rounded shadow-sm p-6">
    <form method="post" action="{{ action }}" class="space-y-4">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

        <div>
            <label class="block text-sm font-medium text-slate-700">Nom</label>
            <input
                type="text"
                name="nom"
                value="{{ form.value('nom') }}"
                class="mt-1 w-full border rounded px-3 py-2"
            >
            {% if form.has_error('nom') %}
                <p class="text-red-600 text-sm mt-1">{{ form.error('nom') }}</p>
            {% endif %}
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-700">Email</label>
            <input
                type="text"
                name="email"
                value="{{ form.value('email') }}"
                class="mt-1 w-full border rounded px-3 py-2"
            >
            {% if form.has_error('email') %}
                <p class="text-red-600 text-sm mt-1">{{ form.error('email') }}</p>
            {% endif %}
        </div>

        <div class="flex gap-4 pt-2">
            <button type="submit"
                    class="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded">
                Enregistrer
            </button>
            <a href="/contacts" class="text-slate-600 hover:underline self-center">Annuler</a>
        </div>
    </form>
</div>

{% endblock %}
```

Dans ce template, les champs utilisent les noms Python du JSON canonique : `nom`, `prenom`, `email`, `telephone`.

Il ne faut donc pas confondre :

| Contexte | Noms utilisés | Exemple |
|---|---|---|
| Formulaire HTML | noms Python du JSON | `name="nom"`, `form.value('nom')` |
| Résultat SQL affiché | colonnes SQL retournées par MariaDB | `contact.Nom`, `contact.Email`, `contact.Id` |

#### 4. Le template de détail

La page de détail lit un seul contact et affiche ses champs.

Extrait simplifié de `mvc/views/contact/show.html` :

```jinja2
{% extends "layouts/app.html" %}
{% block content %}

<div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold text-slate-900">Détail contact</h1>

    <div class="space-x-2">
        <a href="/contacts/{{ contact.Id }}/edit"
           class="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded">
            Modifier
        </a>
        <a href="/contacts" class="text-slate-600 hover:underline">← Retour</a>
    </div>
</div>

<div class="bg-white border rounded shadow-sm p-6 space-y-4">
    <div>
        <p class="text-sm text-slate-500">Nom</p>
        <p class="text-slate-900">{{ contact.Nom }}</p>
    </div>

    <div>
        <p class="text-sm text-slate-500">Email</p>
        <p class="text-slate-900">{{ contact.Email }}</p>
    </div>
</div>

<form method="post" action="/contacts/{{ contact.Id }}/delete" class="mt-4">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button type="submit"
            class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded">
        Supprimer
    </button>
</form>

{% endblock %}
```

La suppression se fait volontairement en `POST`. Le starter évite ainsi une suppression déclenchée par un simple lien `GET`.

#### 5. Classes CSS/Tailwind importantes

Les templates générés s'appuient sur des classes utilitaires simples.

| Rôle | Classes utilisées |
|---|---|
| Largeur et espacement | `max-w-5xl`, `mx-auto`, `px-6`, `py-8` |
| Cartes | `bg-white`, `border`, `rounded`, `shadow-sm`, `p-6` |
| Texte principal | `text-slate-900` |
| Texte secondaire | `text-slate-500`, `text-slate-600` |
| Boutons principaux | `bg-orange-600`, `hover:bg-orange-700`, `text-white` |
| Boutons dangereux | `bg-red-600`, `hover:bg-red-700`, `text-white` |
| Mise en page | `flex`, `items-center`, `justify-between`, `grid`, `gap-4`, `space-y-4` |

Ces classes ne font pas partie de la doctrine Forge. Elles donnent seulement une interface lisible pour le starter. Le développeur peut les remplacer par son propre design sans modifier le modèle, le contrôleur ou les routes.

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

Cette dernière étape ne sert pas seulement à lancer l'application. Elle permet de vérifier chaque couche du parcours Forge : configuration, routes, serveur local, base de données, contrôleur, modèle SQL, formulaires et templates.

### 1. Vérifier l'environnement Forge

```bash
forge doctor
```

Cette commande vérifie que le projet Forge est cohérent avant le lancement.

Elle permet notamment de repérer les problèmes classiques :

- environnement mal configuré ;
- variables manquantes dans `env/dev` ;
- dépendances non installées ;
- projet lancé depuis le mauvais dossier ;
- configuration Forge incomplète.

Si `forge doctor` signale une erreur, il faut la corriger avant de continuer. Lancer le serveur alors que cette commande échoue revient à chercher une panne trop tard dans le navigateur.

### 2. Vérifier les routes réellement déclarées

```bash
forge routes:list
```

Cette commande affiche les routes connues par l'application. Elle permet de vérifier que les routes du CRUD Contact ont bien été copiées dans `mvc/routes.py`.

On doit retrouver une liste proche de celle-ci :

```text
GET   /contacts              ContactController.index
GET   /contacts/new          ContactController.new
POST  /contacts              ContactController.create
GET   /contacts/{id}         ContactController.show
GET   /contacts/{id}/edit    ContactController.edit
POST  /contacts/{id}         ContactController.update
POST  /contacts/{id}/delete  ContactController.destroy
```

Point important :

```text
/contacts/new doit apparaître avant /contacts/{id}
```

Sinon, selon l'ordre de résolution des routes, `new` peut être interprété comme une valeur possible de `{id}`.

### 3. Lancer le serveur local

```bash
python app.py
```

Le serveur Forge démarre l'application en local. Pour ce starter, l'accès se fait ensuite en HTTPS local :

```text
https://localhost:8000/contacts
```

Si le navigateur affiche un avertissement de certificat, c'est normal en développement local lorsque le certificat HTTPS est auto-signé.

### 4. Vérifier le comportement complet dans le navigateur

| Test | Action | Résultat attendu |
|---|---|---|
| Liste | Ouvrir `/contacts` | La page de liste s'affiche, même sans contact |
| Formulaire vide | Cliquer sur "Nouveau contact" puis valider sans remplir | Les erreurs de validation apparaissent |
| Création | Remplir un contact valide puis valider | Retour à la liste avec un message flash |
| Détail | Cliquer sur le lien de détail | La fiche du contact s'affiche |
| Modification | Modifier le contact puis valider | Retour à la liste avec confirmation |
| Suppression | Supprimer le contact avec le bouton prévu | Le contact disparaît de la liste |

Cette vérification confirme que les éléments suivants communiquent correctement :

```text
routes → contrôleur → formulaire → modèle SQL → base MariaDB → templates Jinja
```

### 5. Comprendre les erreurs fréquentes

| Symptôme | Cause probable | Fichier ou commande à vérifier |
|---|---|---|
| Page `/contacts` introuvable | Route non copiée ou mauvais ordre des routes | `mvc/routes.py`, `forge routes:list` |
| Erreur indiquant que la table `contact` n'existe pas | SQL non appliqué | `forge db:apply` |
| Erreur de connexion MariaDB | Variables incorrectes dans `env/dev` | `DB_HOST`, `DB_NAME`, `DB_APP_USER`, `DB_APP_PWD` |
| Template introuvable | Vue absente ou mauvais chemin de template | `mvc/views/contact/` |
| Les erreurs de formulaire ne s'affichent pas | Template `form.html` incomplet ou contexte incorrect | `mvc/views/contact/form.html`, `ContactController` |
| Le bouton supprimer ne fonctionne pas | Route `POST` de suppression absente | `mvc/routes.py` |

Une fois ces vérifications terminées, le starter Contact est fonctionnel. Il peut servir de base pour ajouter progressivement une recherche, une pagination, des relations ou une authentification.


## Reconstruction

Le fichier complet de reconstruction est disponible dans [starters/01-contact-simple/rebuild.md](starters/01-contact-simple/rebuild.md).
