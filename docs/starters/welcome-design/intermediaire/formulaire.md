# Le formulaire

**Objectif** : ajouter une page d'ajout de contact, servie par le contrôleur,
avec les composants de saisie.

**Ce que vous allez apprendre :** les macros de `components/forms.html` et le
branchement route + contrôleur + vue du formulaire. Les macros produisent les
champs ; la balise `<form>` et le jeton CSRF restent à votre charge.

## La route et le contrôleur

Ajoutez une méthode `new` (affiche le formulaire) et `store` (recevra l'envoi) à
`ShowcaseController` :

```python
    @staticmethod
    def new(request: Request) -> Response:
        return BaseController.render("showcase/form.html", request=request,
                                     context={"values": {}})

    @staticmethod
    def store(request: Request) -> Response:
        nom = request.form("nom", default="").strip()
        email = request.form("email", default="").strip()
        _CONTACTS.append({"nom": nom, "email": email, "academie": "Paris", "statut": "actif"})
        return BaseController.redirect("/showcase", request=request, flash="Contact ajouté.")
```

Déclarez les routes :

```python
public.add("GET",  "/showcase/new",   ShowcaseController.new,   name="showcase-new")
public.add("POST", "/showcase/store", ShowcaseController.store, name="showcase-store")
```

## La vue du formulaire

Créez `mvc/views/showcase/form.html` :

```jinja
{% extends "layouts/base.html" %}
{% from "components/ui.html" import page_header %}
{% from "components/forms.html" import field, select_field, radio_group, checkbox, fieldset, submit %}

{% block title %}Nouveau contact · {{ app_name }}{% endblock %}

{% block content %}
  {{ page_header("Nouveau contact") }}

  <form method="post" action="/showcase/store">
    {% include "partials/csrf.html" %}

    {% call fieldset("Identité") %}
      {{ field("nom", label="Nom", value=values.get("nom", ""), required=True) }}
      {{ field("email", label="Courriel", type="email", value=values.get("email", ""), required=True) }}
    {% endcall %}

    {{ select_field("academie", label="Académie",
         options=[("paris", "Paris"), ("lyon", "Lyon"), ("lille", "Lille")]) }}
    {{ radio_group("statut", label="Statut",
         options=[("actif", "Actif"), ("archive", "Archivé")], selected="actif") }}
    {{ checkbox("newsletter", "Recevoir les actualités", checked=True) }}

    {{ submit("Enregistrer le contact") }}
  </form>
{% endblock %}
```

Le contrôleur passe `values` (vide ici) ; les champs réaffichent ces valeurs,
ce qui servira à la validation au palier suivant. Le jeton CSRF est injecté
automatiquement dans le contexte par `render` ; `partials/csrf.html` le pose.

## Le catalogue des champs

| Macro | Usage |
|---|---|
| `field(name, label, type, value, required, help)` | texte, courriel, nombre... (via `type`) |
| `textarea_field(name, label, rows)` | texte multi-lignes |
| `select_field(name, label, options, selected)` | liste déroulante |
| `radio_group(name, label, options, selected)` | choix exclusif |
| `checkbox(name, label, checked)` | case à cocher |
| `file_field(name, label, accept)` | envoi de fichier |
| `search_field(name, placeholder)` | champ de recherche |
| `fieldset(legend)` | regroupe des champs (`{% call %}`) |
| `submit(label)` | bouton d'envoi |

??? note "À retenir"
    - Une page = une route + une méthode de contrôleur + une vue.
    - Les macros produisent les champs ; vous écrivez `<form>` et incluez le CSRF.
    - Le contrôleur passe `values` ; les champs les réaffichent.

Au palier suivant, nous validons l'envoi et affichons les erreurs.

[Continuer avec La validation](validation.md)
