# CRUD explicite — Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Forge génère un squelette CRUD lisible et modifiable à partir d'une entité JSON. La génération produit un point de départ, pas une cage : chaque fichier est ouvert, explicite, et ne sera jamais écrasé si vous le modifiez.

---

## 1. Doctrine

**Le développeur comprend toujours ce qui est exécuté.**

- Le JSON d'entité est la source canonique
- Le SQL reste visible dans le modèle applicatif
- Le code généré est lisible et modifiable
- Les fichiers existants ne sont jamais écrasés
- `mvc/routes.py` reste un fichier manuel — Forge ne l'écrit pas
- Forge ne génère pas de repository magique ni d'ORM implicite

---

## 2. Cycle `forge make:crud`

```mermaid
flowchart TD
    A["contact.json<br/>défini et validé"] --> B["forge build:model"]
    B --> C["contact.sql + contact_base.py"]
    C --> D["forge db:apply"]
    D --> E["Table contact dans MariaDB"]
    E --> F["forge make:crud Contact --dry-run"]
    F --> G["Prévisualisation"]
    G --> H["forge make:crud Contact"]
    H --> I["Fichiers CRUD créés"]
    I --> J["Copier les routes dans mvc/routes.py"]
    J --> K["forge routes:list"]
    K --> L["python app.py"]
```

### Prérequis avant `forge make:crud`

```bash
forge make:entity Contact         # créer l'entité
# éditer mvc/entities/contact/contact.json
forge build:model                 # générer contact.sql et contact_base.py
forge db:apply                    # créer la table dans MariaDB
```

### Génération

```bash
forge make:crud Contact --dry-run   # prévisualiser sans écrire
forge make:crud Contact             # générer les fichiers
```

Sortie type :

```text
[CRÉÉ]      mvc/controllers/contact_controller.py
[CRÉÉ]      mvc/models/contact_model.py
[CRÉÉ]      mvc/forms/contact_form.py
[CRÉÉ]      mvc/views/layouts/app.html
[CRÉÉ]      mvc/views/contact/index.html
[CRÉÉ]      mvc/views/contact/show.html
[CRÉÉ]      mvc/views/contact/form.html

Routes à ajouter dans mvc/routes.py :
──────────────────────────────────────────────────────────────────────
  from mvc.controllers.contact_controller import ContactController

  with router.group("/contact") as g:
      g.add("GET",  "",               ContactController.index,   name="contact-index")
      g.add("GET",  "/new",           ContactController.new,     name="contact-new")
      g.add("POST", "/create",        ContactController.create,  name="contact-create")
      g.add("GET",  "/show/{id}",     ContactController.show,    name="contact-show")
      g.add("GET",  "/edit/{id}",     ContactController.edit,    name="contact-edit")
      g.add("POST", "/update/{id}",   ContactController.update,  name="contact-update")
      g.add("POST", "/destroy/{id}",  ContactController.destroy, name="contact-destroy")
```

Si un fichier existe déjà, il est marqué `[PRÉSERVÉ]` et non touché. Pour régénérer un fichier modifié manuellement, le supprimer avant de relancer la commande.

---

## 3. Routes

Les routes sont affichées par `forge make:crud` mais jamais injectées automatiquement. Les copier dans `mvc/routes.py` :

```python
from mvc.controllers.contact_controller import ContactController

with router.group("/contact") as g:
    g.add("GET",  "",               ContactController.index,   name="contact-index")
    g.add("GET",  "/new",           ContactController.new,     name="contact-new")
    g.add("POST", "/create",        ContactController.create,  name="contact-create")
    g.add("GET",  "/show/{id}",     ContactController.show,    name="contact-show")
    g.add("GET",  "/edit/{id}",     ContactController.edit,    name="contact-edit")
    g.add("POST", "/update/{id}",   ContactController.update,  name="contact-update")
    g.add("POST", "/destroy/{id}",  ContactController.destroy, name="contact-destroy")
```

!!! warning "Ordre obligatoire"
    `/new` doit être déclaré avant `/{id}`. Le routeur parcourt les routes dans l'ordre — sinon `new` est capturé comme identifiant.

Par défaut, un groupe de routes sans `public=True` est protégé par les middlewares d'authentification.

---

## 4. Formulaires générés

### Structure

```text
core/forms/      ← mécanique générique (Form, Field, cleaned_data, erreurs)
mvc/forms/       ← formulaires applicatifs (ContactForm, LoginForm…)
mvc/validators/  ← règles réutilisables
```

Un formulaire Forge lit les données HTTP, valide, remplit `cleaned_data` et produit des erreurs affichables. Il ne fait pas de requête SQL et ne décide pas d'une redirection.

### Exemple généré

```python
from core.forms import Form, StringField


class ContactForm(Form):
    nom      = StringField(label="Nom",    required=True,  max_length=80)
    prenom   = StringField(label="Prénom", required=True,  max_length=80)
    email    = StringField(label="Email",  required=False, max_length=120)
    telephone = StringField(label="Tél",  required=False, max_length=20)
```

### Utilisation dans un contrôleur

```python
form = ContactForm.from_request(request)

if not form.is_valid():
    return BaseController.validation_error(
        "contact/form.html",
        context={"form": form, "action": "/contact", "titre": "Nouveau contact"},
        request=request,
    )

add_contact(form.cleaned_data)
return BaseController.redirect_with_flash(request, "/contact", "Contact créé.")
```

### Dans un template Jinja2

```jinja2
<input name="nom" value="{{ form.value('nom') }}">
{% if form.has_error('nom') %}
    <p class="text-red-600">{{ form.error('nom') }}</p>
{% endif %}
```

### Mappage SQL → champ de formulaire

| Type SQL | Champ Python généré |
|---|---|
| `VARCHAR(n)`, `CHAR(n)` | `StringField(max_length=n)` |
| `TEXT`, `LONGTEXT` | `StringField()` + `<textarea>` dans le template |
| `INT`, `BIGINT`, `TINYINT` | `IntegerField()` |
| `DECIMAL`, `FLOAT`, `DOUBLE` | `DecimalField()` ; `cleaned_data` contient un `Decimal` |
| `BOOL`, `BOOLEAN` | `BooleanField()` |
| `DATE`, `DATETIME` | `StringField()` + avertissement `[WARN]` |

### Mappage SQL → type d'input HTML

Le générateur déduit le `type` HTML à partir du type SQL **et du nom du champ** :

| Condition | `type` HTML généré |
|---|---|
| `python_type: "date"` ou SQL `DATE` | `date` |
| `python_type: "datetime"` ou SQL `DATETIME`/`TIMESTAMP` | `datetime-local` |
| `python_type: "int"` ou `"float"` | `number` |
| `python_type: "bool"` | `checkbox` |
| Champ nommé `email`, `mail`, `courriel` | `email` |
| Champ nommé `tel`, `telephone`, `phone`, `portable` | `tel` |
| Champ nommé `url`, `site`, `website`, `lien` | `url` |
| SQL `TEXT`, `TINYTEXT`… | `<textarea>` |
| Autres VARCHAR | `text` |

!!! note "Choix numérique"
    Les JSON d'entité gardent `python_type: "float"` pour les types SQL décimaux afin de rester compatibles avec la doctrine initiale. Le formulaire généré utilise toutefois `DecimalField`, plus sûr pour la saisie utilisateur. Si votre classe métier attend strictement un `float`, convertissez explicitement dans le contrôleur ou dans votre code applicatif manuel.

### Relations `many_to_one`

Si `mvc/entities/relations.json` déclare une relation `many_to_one` dont l'entité courante est la source (`from`), `forge make:crud` exploite cette relation dans le formulaire généré.

Exemple : `Contact.ville_id -> Ville.id`.

- le champ FK devient un `ChoiceField` ;
- la vue `form.html` génère un `<select>` ;
- le contrôleur fournit les choix au formulaire ;
- le modèle généré ajoute une fonction simple de lecture des choix ;
- le SQL reste visible et explicite.

Comme le format actuel ne possède pas encore de `label_field`, Forge choisit le libellé affiché avec ce fallback :

1. premier champ texte non-PK de l'entité cible ;
2. sinon clé primaire cible.

Le CRUD sans relation, ou avec un `relations.json` vide, conserve le comportement classique.

---

## 5. Modèle applicatif SQL généré

Le modèle expose des fonctions avec SQL visible et paramétré. Pas d'abstraction cachée.

```python
from core.database.connection import get_connection, close_connection

SELECT_ALL   = "SELECT * FROM contact ORDER BY Id"
SELECT_BY_ID = "SELECT * FROM contact WHERE Id = ?"
INSERT       = "INSERT INTO contact (Nom, Prenom, Email, Telephone) VALUES (?, ?, ?, ?)"
UPDATE       = "UPDATE contact SET Nom = ?, Prenom = ?, Email = ?, Telephone = ? WHERE Id = ?"
DELETE       = "DELETE FROM contact WHERE Id = ?"


def get_contacts():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_ALL)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def add_contact(data):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(INSERT, (data["nom"], data["prenom"], data["email"], data["telephone"]))
        connection.commit()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)
```

Règles appliquées :
- Noms de table et colonnes issus du JSON canonique
- Paramètres `?` — jamais d'interpolation directe
- La clé primaire auto-incrémentée est exclue des `INSERT`
- `INSERT`, `UPDATE`, `DELETE` font un `commit()` explicite
- Connexion et curseur fermés dans un `finally`

### Pagination, recherche et tri

Le modèle généré contient deux fonctions supplémentaires :

```python
_SEARCH_COLS  = ["Nom", "Email"]          # champs VARCHAR/TEXT interrogeables
_ALLOWED_SORT = {"nom": "Nom", "email": "Email", "id": "Id"}
_DEFAULT_SORT = "Id"


def count_contacts(q=None):
    """Nombre d'enregistrements, avec filtre LIKE optionnel."""
    ...

def find_contacts_paginated(q=None, sort=None, direction="asc", limit=10, offset=0):
    """Liste paginée, triée et filtrée."""
    ...
```

- **`_SEARCH_COLS`** — colonnes `VARCHAR`/`CHAR`/`TEXT` ; la recherche est ignorée si la liste est vide.
- **`_ALLOWED_SORT`** — seuls les champs déclarés dans le JSON sont acceptés comme clé de tri. Toute valeur inconnue revient au tri par défaut.
- Le tri est construit par concaténation de chaînes whitelistées (`sort_col` et `sort_dir`), jamais par interpolation de valeurs utilisateur.
- La recherche utilise des `?` paramétrés (`LIKE ?`) — pas d'injection possible.

Le contrôleur généré lit les paramètres GET `page`, `q`, `sort`, `direction` et passe un dictionnaire `pagination` à la vue.

---

## 6. Vues générées

`forge make:crud` crée un layout applicatif et trois vues :

```text
mvc/views/layouts/app.html   ← layout Jinja2 (créé si absent)
mvc/views/contact/index.html ← liste
mvc/views/contact/show.html  ← détail
mvc/views/contact/form.html  ← création et modification
```

Les vues héritent du layout :

```jinja2
{% extends "layouts/app.html" %}

{% block content %}
    ...
{% endblock %}
```

Le champ CSRF est inclus dans tous les formulaires `POST` :

```jinja2
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

---

## 7. Personnalisation après génération

Les fichiers générés sont des points de départ — ils sont lisibles et à adapter librement.

| Fichier | Adaptations typiques |
|---|---|
| `contact_controller.py` | Ajouter `@require_auth`, pagination, tri, règles métier |
| `contact_form.py` | Ajouter `ChoiceField`, validations croisées via `clean()`, remplacer les `StringField` de type `DATE` |
| `contact_model.py` | Ajouter des requêtes métier, des jointures, de la pagination |
| `contact/index.html` | Ajouter des colonnes, la pagination, le tri |
| `layouts/app.html` | Menu de navigation, nom de l'application, styles |

!!! tip "Régénération partielle"
    Pour régénérer un seul fichier modifié, le supprimer puis relancer `forge make:crud Contact`.
    Les autres fichiers du CRUD sont préservés (`[PRÉSERVÉ]`).

---

## 8. Limites du CRUD généré

### Ce que les relations `many_to_one` apportent déjà

Si `mvc/entities/relations.json` déclare une relation `many_to_one` dont l'entité courante est la source (`from`), le CRUD généré exploite cette relation dans le formulaire :

- le champ FK devient un `ChoiceField` ;
- la vue `form.html` génère un `<select>` avec les options de la table cible ;
- le contrôleur fournit les choix via une fonction dédiée ;
- le modèle ajoute `get_{cible}_choices()` — requête SQL visible et explicite.

### Ce que `forge make:crud` ne génère pas encore

`forge make:crud` ne génère pas encore automatiquement :

- les jointures SQL dans les vues liste et détail (le champ FK affiche son ID brut, pas le libellé de la table liée) ;
- les champs `RelatedIdsField` pour les pivots ;
- les permissions fines ;
- le `many_to_many` déclaratif ;
- les relations ordonnées ou principales.

### CRUD média : ce qui est généré et ce qui reste à venir

Les entités déclarant une clé `"media"` bénéficient d'une génération complète :
formulaire multipart avec `ImageField`/`FileField`, upload à la création, remplacement
et suppression explicite à l'édition, preview dans les vues `show` et `edit`, suppression
des fichiers physiques à la destruction de l'entité parente, galerie `multiple=true`
(multi-upload, affichage, suppression individuelle, réorganisation par position, alt_text).

Ce qui reste à venir :

- back-office média intégré ;
- permissions média (accès contrôlé aux fichiers servis via `/media/...`).

Voir [Référence API et CLI](../reference/reference.md) et [Module média](media.md) pour les détails.
