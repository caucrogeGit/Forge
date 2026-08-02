# Avancé 2 : Surcharger un template

Objectif : adapter l'apparence du back-office à votre projet.

## Le principe

Forge Admin embarque ses templates par défaut.
Votre projet peut en remplacer n'importe lequel en plaçant un fichier de même chemin sous `mvc/views/admin/`.
L'ordre des loaders donne la priorité au projet : votre fichier l'emporte.

## Un exemple

Pour personnaliser le gabarit de base, créez `mvc/views/admin/layout.html` :

```html
{# mvc/views/admin/layout.html #}
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{% block title %}Administration{% endblock %} - Mon projet</title>
  <link rel="stylesheet" href="/static/admin.css">
</head>
<body>
  <header><h1>Back-office Mon projet</h1></header>
  <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

Rechargez `/admin` : votre gabarit remplace celui du paquet, sans toucher au module.

## Templates surchargeables

- `admin/layout.html` : gabarit de base ;
- `admin/dashboard.html` : tableau de bord ;
- `admin/list.html` : liste ;
- `admin/detail.html` : fiche ;
- `admin/form.html` : formulaire ;
- `admin/delete.html` : confirmation de suppression.

## À retenir

- La surcharge est explicite : un fichier projet de même chemin gagne.
- Vous n'éditez jamais le paquet ; vous le complétez.

## Étape suivante

[Suivant : permissions](admin-rbac.md)
