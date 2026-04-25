# Starter 1 — Contact simple

Premier parcours Forge : une seule entité `Contact`, un CRUD généré, puis un câblage manuel des routes.

## Objectif de l’application

Construire une petite application de gestion de contacts avec :

- une liste simple, enrichissable ensuite ;
- une page de création ;
- une page de détail ;
- une page de modification ;
- une suppression en `POST` ;
- des messages flash après création, modification ou suppression.

Le starter sert à comprendre le flux Forge minimal : JSON canonique, SQL visible, modèle Python généré, CRUD MVC explicite et routes copiées manuellement.

## Niveau de difficulté

Niveau 1 — débutant Forge.

Le parcours ne contient ni relation, ni authentification métier spécifique, ni logique complexe. Il est conçu pour vérifier que le projet, la base de données, les formulaires, les vues Jinja2 et les routes fonctionnent ensemble.

## Ce que l’on apprend

- Créer une entité avec `forge make:entity`.
- Compléter le JSON canonique après `--no-input`.
- Prévisualiser la génération avec `forge build:model --dry-run`.
- Générer `contact.sql` et `contact_base.py`.
- Appliquer le SQL avec `forge db:apply`.
- Générer un CRUD avec `forge make:crud Contact`.
- Copier les routes dans `mvc/routes.py`.
- Lire et adapter les fichiers générés sans attendre d’admin magique.

## Navigation de l’application

```text
/contacts           liste des contacts
/contacts/new       formulaire de création
/contacts/{id}      détail d’un contact
/contacts/{id}/edit formulaire de modification
```

`/contacts/new` doit rester déclaré avant `/{id}` dans les routes afin d’éviter que `new` soit interprété comme un identifiant.

## Charte graphique

Le starter utilise une charte volontairement simple :

- fond clair pour les pages de formulaire et de liste ;
- barre supérieure sobre dans `mvc/views/layouts/app.html` ;
- boutons orange Forge pour les actions principales ;
- boutons secondaires gris pour retour et annulation ;
- cartes blanches bordées pour les formulaires et les détails ;
- messages flash visibles au-dessus du contenu.

Le but n’est pas de créer un thème complet, mais d’obtenir une interface lisible et facile à modifier.

## Modèle de données

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

## Commandes Forge

```bash
forge doctor
forge db:init
forge make:entity Contact --no-input
# modifier mvc/entities/contact/contact.json avec les champs métier
forge build:model --dry-run
forge build:model
forge check:model
forge db:apply
forge make:crud Contact
```

`forge make:crud Contact --dry-run` peut être utilisé pour vérifier les fichiers que le CRUD créerait sans écrire.

## Fichiers créés ou modifiés

Fichiers canoniques et générés :

```text
mvc/entities/contact/contact.json       source canonique à modifier
mvc/entities/contact/contact.sql        généré
mvc/entities/contact/contact_base.py    généré
mvc/entities/contact/contact.py         manuel, préservé
mvc/entities/contact/__init__.py        manuel, préservé
```

Fichiers CRUD créés s’ils sont absents :

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

## Classes Python utilisées

- `ContactBase` : classe générée depuis le JSON.
- `Contact` : classe métier manuelle qui hérite de `ContactBase`.
- `ContactForm` : formulaire généré, basé sur `core.forms.Form`.
- `ContactController` : contrôleur MVC généré.
- `BaseController` : rendu HTML, redirections, flash et erreurs de validation.

Le contrôleur généré lit les formulaires via l’API réelle Forge :

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

## Tags Jinja utilisés

Les vues générées utilisent les tags Jinja2 classiques :

- `{% extends "layouts/app.html" %}` pour hériter du layout ;
- `{% block content %}` pour remplir la zone principale ;
- `{% for contact in contacts %}` pour afficher la liste ;
- `{% if form.errors %}` pour afficher les erreurs ;
- `{{ csrf_token }}` dans le champ caché du formulaire ;
- `{{ contact.Nom }}`, `{{ contact.Email }}` et `{{ contact.Id }}` pour les dictionnaires SQL retournés par `cursor(dictionary=True)`.

Les champs de formulaire utilisent les noms Python, par exemple `form.value("nom")`, tandis que les vues de liste et de détail générées affichent les colonnes SQL en PascalCase.

## Classes CSS/Tailwind importantes

Le CRUD généré s’appuie sur des classes utilitaires simples :

- `max-w-5xl`, `mx-auto`, `px-6`, `py-8` pour la largeur et l’espacement ;
- `bg-white`, `border`, `rounded`, `shadow-sm` pour les cartes ;
- `text-slate-900`, `text-slate-500` pour la hiérarchie texte ;
- `bg-orange-600`, `hover:bg-orange-700`, `text-white` pour les actions principales ;
- `grid`, `gap-4`, `flex`, `items-center`, `justify-between` pour la composition.

Ces classes peuvent être remplacées par votre propre design sans modifier la doctrine Forge.

## Test navigateur

1. Lancer `python app.py`.
2. Ouvrir `/contacts`.
3. Cliquer sur “Nouveau contact”.
4. Soumettre le formulaire vide et vérifier l’affichage des erreurs.
5. Créer un contact valide.
6. Vérifier le retour à la liste et le message flash.
7. Ouvrir le détail du contact.
8. Modifier le contact.
9. Supprimer le contact avec le bouton prévu.
10. Vérifier que la liste est cohérente après suppression.

## Limites du starter

- Pas d’authentification dédiée.
- Pas de recherche avancée.
- Pas de pagination générée automatiquement.
- Pas de validation métier au-delà des contraintes simples.
- Pas de relation : ce starter est volontairement mono-entité.
- Pas d’ORM : les requêtes SQL restent visibles dans `mvc/models/contact_model.py`.

## Reconstruction

Le fichier complet de reconstruction est disponible dans [starters/01-contact-simple/rebuild.md](starters/01-contact-simple/rebuild.md).
