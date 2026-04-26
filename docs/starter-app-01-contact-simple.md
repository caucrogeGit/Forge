# Starter 1 — Contact simple

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
forge new ContactSimple
cd ContactSimple
source .venv/bin/activate
forge doctor
```

### Méthode B — installation manuelle

```bash
git clone https://github.com/caucrogeGit/Forge.git ContactSimple
cd ContactSimple
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

Avant d'exécuter `forge db:init`, renseigner dans `env/dev` un compte MariaDB disposant des droits nécessaires pour créer la base, créer l'utilisateur applicatif et appliquer les privilèges.

En développement local, on peut utiliser temporairement un compte administrateur MariaDB existant.

Exemple de variables à vérifier dans `env/dev` :

```env
DB_ADMIN_USER=...
DB_ADMIN_PWD=...

DB_APP_USER=...
DB_APP_PWD=...
DB_NAME=...
```

`DB_ADMIN_USER` sert uniquement à l'initialisation de la base.  
`DB_APP_USER` est l'utilisateur utilisé ensuite par l'application.

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
  "description": "Contact simple du starter niveau 1",
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

Créer l'entité minimale :

```bash
forge make:entity Contact --no-input
```

Modifier ensuite le fichier canonique :

```text
mvc/entities/contact/contact.json
```

Vérifier le modèle :

```bash
forge check:model
```

Prévisualiser la génération :

```bash
forge build:model --dry-run
```

Générer les fichiers `contact.sql` et `contact_base.py` :

```bash
forge build:model
```

Appliquer le SQL sur la base de développement :

```bash
forge db:apply
```

Dans ce starter, `forge db:apply` est utilisé sur une base de développement neuve. Le starter ne présente pas encore un système complet de migrations avancées.

Prévisualiser le CRUD :

```bash
forge make:crud Contact --dry-run
```

Générer le CRUD :

```bash
forge make:crud Contact
```

### Routes à ajouter

Après la génération du CRUD, copier ou vérifier les routes dans `mvc/routes.py`.

```python
from mvc.controllers.contact_controller import ContactController

router.get("/contacts", ContactController.index)
router.get("/contacts/new", ContactController.create)
router.post("/contacts", ContactController.store)

router.get("/contacts/{id}", ContactController.show)
router.get("/contacts/{id}/edit", ContactController.edit)
router.post("/contacts/{id}", ContactController.update)
router.post("/contacts/{id}/delete", ContactController.delete)
```

La route `/contacts/new` doit rester déclarée avant `/contacts/{id}` afin d'éviter que `new` soit interprété comme un identifiant.

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
- `ContactController` : contrôleur MVC généré.
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

### Syntaxe Jinja utilisée

Les vues générées utilisent la syntaxe Jinja2 classique :

- `{% extends "layouts/app.html" %}` pour hériter du layout ;
- `{% block content %}` pour remplir la zone principale ;
- `{% for contact in contacts %}` pour afficher la liste ;
- `{% if form.errors %}` pour afficher les erreurs ;
- `{{ csrf_token }}` dans le champ caché du formulaire ;
- `{{ contact.Nom }}`, `{{ contact.Email }}` et `{{ contact.Id }}` pour les dictionnaires SQL retournés par `cursor(dictionary=True)`.

Les champs de formulaire utilisent les noms Python, par exemple `form.value("nom")`, tandis que les vues de liste et de détail générées affichent les colonnes SQL en PascalCase.

### Classes CSS/Tailwind importantes

Le CRUD généré s'appuie sur des classes utilitaires simples :

- `max-w-5xl`, `mx-auto`, `px-6`, `py-8` pour la largeur et l'espacement ;
- `bg-white`, `border`, `rounded`, `shadow-sm` pour les cartes ;
- `text-slate-900`, `text-slate-500` pour la hiérarchie texte ;
- `bg-orange-600`, `hover:bg-orange-700`, `text-white` pour les actions principales ;
- `grid`, `gap-4`, `flex`, `items-center`, `justify-between` pour la composition.

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

## Vérification finale

```bash
forge doctor
forge routes:list
python app.py
```

Ouvrir dans le navigateur :

```text
https://localhost:8000/contacts
```

## Reconstruction

Le fichier complet de reconstruction est disponible dans [starters/01-contact-simple/rebuild.md](starters/01-contact-simple/rebuild.md).
