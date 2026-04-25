# CRUD explicite — Forge

Cette page décrit la doctrine CRUD de Forge et son état actuel dans la version **V1.0**.

Historiquement, ce document servait à fixer la forme manuelle idéale du CRUD. Depuis Forge **V1.0**, une première génération CRUD est disponible avec la commande :

```bash
forge make:crud <Entité>
```

La génération reste volontairement limitée : elle produit un squelette lisible, modifiable et explicite. Elle ne transforme pas Forge en ORM, en admin automatique ou en générateur magique.

## Doctrine

Forge applique une règle simple : **le développeur doit toujours comprendre ce qui est exécuté**.

Doctrine associée :

- le JSON d'entité reste la source canonique ;
- le SQL reste visible ;
- le code généré est lisible ;
- les fichiers existants ne sont jamais écrasés ;
- `routes.py` reste un fichier manuel ;
- Forge ne génère pas de repository magique ;
- Forge ne cache pas la persistance derrière un ORM implicite ;
- le développeur reste propriétaire du contrôleur, du formulaire, du modèle SQL et des vues.

Le CRUD généré par Forge est donc un **point de départ**, pas une cage.

## Commande `forge make:crud`

La commande crée un CRUD minimal à partir d'une entité déclarée dans :

```text
mvc/entities/<entité>/<entité>.json
```

Exemple :

```bash
forge make:entity Contact --no-input
forge build:model
forge make:crud Contact
```

La commande lit :

```text
mvc/entities/contact/contact.json
```

et génère, si les fichiers n'existent pas déjà :

```text
mvc/controllers/contact_controller.py
mvc/models/contact_model.py
mvc/forms/contact_form.py
mvc/views/layouts/app.html
mvc/views/contact/index.html
mvc/views/contact/show.html
mvc/views/contact/form.html
```

Si un fichier existe déjà, il est préservé :

```text
[PRÉSERVÉ]  mvc/controllers/contact_controller.py  ← fichier existant, non touché
```

C'est un point central de Forge : **la génération n'écrase pas le travail manuel**.

## Simulation avec `--dry-run`

Avant de créer les fichiers, il est possible de simuler la génération :

```bash
forge make:crud Contact --dry-run
```

En mode dry-run, Forge :

- lit l'entité ;
- calcule les fichiers qui seraient créés ou préservés ;
- affiche le bloc de routes à ajouter ;
- n'écrit aucun fichier.

Exemple de sortie :

```text
[CRÉÉ]      mvc/controllers/contact_controller.py
[CRÉÉ]      mvc/models/contact_model.py
[CRÉÉ]      mvc/forms/contact_form.py
[CRÉÉ]      mvc/views/layouts/app.html
[CRÉÉ]      mvc/views/contact/index.html
[CRÉÉ]      mvc/views/contact/show.html
[CRÉÉ]      mvc/views/contact/form.html
[DRY-RUN]   Aucun fichier modifié.
```

## Routes proposées, jamais injectées

`forge make:crud` n'écrit pas dans `mvc/routes.py`.

À la place, la commande affiche un bloc à copier manuellement :

```python
from mvc.controllers.contact_controller import ContactController

# Routes protégées par défaut.
# Pour un CRUD public, adaptez explicitement la déclaration du groupe.
with router.group("/contacts") as g:
    g.add("GET",  "",              ContactController.index,   name="contact_index")
    g.add("GET",  "/new",          ContactController.new,     name="contact_new")
    g.add("POST", "",              ContactController.create,  name="contact_create")
    g.add("GET",  "/{id}",         ContactController.show,    name="contact_show")
    g.add("GET",  "/{id}/edit",    ContactController.edit,    name="contact_edit")
    g.add("POST", "/{id}",         ContactController.update,  name="contact_update")
    g.add("POST", "/{id}/delete",  ContactController.destroy, name="contact_destroy")
```

L'ordre est important : la route fixe `/new` doit être déclarée avant la route dynamique `/{id}`.

Par défaut, un groupe de routes non marqué `public=True` est protégé par les middlewares applicatifs, notamment l'authentification si elle est active dans le projet.

## Formulaires

Structure recommandée :

```text
core/forms/        # mécanique générique : Form, Field, errors, cleaned_data
mvc/forms/         # formulaires applicatifs : ContactForm, LoginForm, etc.
mvc/validators/    # règles réutilisables existantes
```

Un formulaire Forge transforme une requête en données validées et erreurs affichables.

Un formulaire Forge ne doit pas :

- faire de requête SQL ;
- créer un objet métier en base ;
- porter des règles métier lourdes ;
- décider d'une redirection.

Il doit seulement :

- lire les données HTTP ;
- nettoyer ou convertir les champs ;
- valider ;
- remplir `cleaned_data` ;
- produire des erreurs affichables.

Exemple généré :

```python
from core.forms import Form, StringField


class ContactForm(Form):
    nom = StringField(label="Nom", required=True, max_length=100)
    email = StringField(label="Email", required=False, max_length=150)
```

Utilisation dans un contrôleur :

```python
form = ContactForm.from_request(request)

if not form.is_valid():
    return BaseController.validation_error(
        "contact/form.html",
        context={"form": form, "action": "/contacts", "titre": "Nouveau contact"},
        request=request,
    )
```

Dans le template :

```html
<input name="nom" value="{{ form.value('nom') }}">
{% if form.has_error('nom') %}
    <p class="text-red-600">{{ form.error('nom') }}</p>
{% endif %}
```

## Mappage des champs

Le générateur utilise les champs non-PK de l'entité.

| Type SQL | Champ de formulaire généré |
|---|---|
| `VARCHAR(n)`, `CHAR(n)` | `StringField(max_length=n)` |
| `TEXT`, `LONGTEXT`, `MEDIUMTEXT` | `StringField()` + affichage `textarea` dans le template |
| `INT`, `BIGINT`, `SMALLINT`, `MEDIUMINT`, `TINYINT` | `IntegerField()` |
| `DECIMAL`, `NUMERIC`, `FLOAT`, `DOUBLE` | `DecimalField()` |
| `BOOL`, `BOOLEAN` | `BooleanField()` |
| `DATE`, `DATETIME`, `TIMESTAMP` | `StringField()` en V1.0 |

Les relations complexes, les champs de type fichier et les `ChoiceField` automatiques restent hors périmètre de la première génération CRUD.

## Cas d'une entité sans champ métier

Une entité créée avec :

```bash
forge make:entity Contact --no-input
```

peut ne contenir qu'une clé primaire auto-incrémentée.

Dans ce cas, Forge génère un squelette prudent et affiche un avertissement. Le générateur évite notamment de produire un SQL invalide du type :

```sql
UPDATE contact SET WHERE Id = ?
```

Le CRUD reste un squelette de départ. Il est recommandé d'ajouter des champs métier dans le JSON de l'entité, puis de relancer :

```bash
forge build:model
forge make:crud Contact
```

Les fichiers CRUD déjà présents seront préservés. Si vous voulez régénérer un fichier, supprimez-le explicitement avant de relancer la commande.

## Contrôleur généré

Le contrôleur généré suit le flux classique :

```text
GET  /contacts           → index
GET  /contacts/new       → new
POST /contacts           → create
GET  /contacts/{id}      → show
GET  /contacts/{id}/edit → edit
POST /contacts/{id}      → update
POST /contacts/{id}/delete → destroy
```

Il utilise :

- `BaseController.render()` ;
- `BaseController.validation_error()` ;
- `BaseController.redirect_with_flash()` ;
- le formulaire généré ;
- le modèle applicatif SQL généré.

La conversion entre les noms de colonnes SQL et les noms de champs Python est gérée dans le contrôleur généré afin que le formulaire d'édition reçoive les bonnes clés.

## Modèle applicatif SQL généré

Nom recommandé : **modèle applicatif SQL**, pas repository générique.

Fichier généré :

```text
mvc/models/contact_model.py
```

Règles appliquées :

- les noms de table et de colonnes viennent du JSON canonique ;
- les requêtes utilisent des paramètres `?` — jamais d'interpolation directe ;
- la clé primaire auto-incrémentée est exclue des `INSERT` ;
- `INSERT`, `UPDATE` et `DELETE` font un `commit()` explicite ;
- curseur et connexion sont fermés dans un bloc `finally`.

Exemple généré pour une entité `Contact` avec les champs `nom` et `email` :

```python
from core.database.connection import get_connection, close_connection

SELECT_ALL   = "SELECT * FROM contact ORDER BY Id"
SELECT_BY_ID = "SELECT * FROM contact WHERE Id = ?"
INSERT       = "INSERT INTO contact (Nom, Email) VALUES (?, ?)"
UPDATE       = "UPDATE contact SET Nom = ?, Email = ? WHERE Id = ?"
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


def get_contact_by_id(id):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_BY_ID, (id,))
        return cursor.fetchone()
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
        cursor.execute(INSERT, (data["nom"], data["email"]))
        connection.commit()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def update_contact(id, data):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(UPDATE, (data["nom"], data["email"], id))
        connection.commit()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def delete_contact(id):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(DELETE, (id,))
        connection.commit()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)
```

Le fichier généré est immédiatement lisible et modifiable. Il ne contient aucune abstraction cachée.

## Vues générées

Depuis V1.0, `forge make:crud` crée un layout Jinja2 applicatif :

```text
mvc/views/layouts/app.html
```

Les vues CRUD générées l'étendent :

```jinja2
{% extends "layouts/app.html" %}

{% block content %}
    ...
{% endblock %}
```

Le layout généré est volontairement simple et modifiable. Il sert de base pédagogique et applicative.

## CSRF automatique

Règle Forge :

| Cas | Comportement |
|-----|--------------|
| `POST`, `PUT`, `PATCH`, `DELETE` | CSRF requis par défaut |
| `GET`, `HEAD`, `OPTIONS` | CSRF ignoré |
| `csrf=False` | exemption explicite |
| API / webhook | exemption déclarée, jamais implicite |

Une route publique avec formulaire POST, comme `/login`, reste protégée par CSRF.

```python
pub.add("POST", "/login", AuthController.login, name="login")
api.add("POST", "/api/webhook", WebhookController.receive, csrf=False, api=True)
```

En Forge V1.0, le CSRF est vérifié avant les middlewares applicatifs sur les routes unsafe qui l'exigent. Ainsi, une requête `POST` avec un token CSRF invalide est rejetée avant d'atteindre les middlewares d'authentification.

## Method override

Les formulaires HTML peuvent exprimer une intention `PUT`, `PATCH` ou `DELETE` via un `POST` explicite.

```html
<form method="post" action="/contacts/12">
    <input type="hidden" name="_method" value="DELETE">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button>Supprimer</button>
</form>
```

Forge applique l'override avant le routage et avant la vérification CSRF effective. La requête ci-dessus matche donc `DELETE /contacts/12` et reste protégée par CSRF.

## Messages flash et redirections

Flux recommandé pour un POST réussi :

```text
POST /contacts
validation OK
création du contact
flash success
redirect /contacts
```

En cas d'erreur :

```text
POST /contacts
validation KO
render form.html avec erreurs + anciennes valeurs
```

Exemple :

```python
return BaseController.redirect_with_flash(
    request,
    "/contacts",
    "Contact créé avec succès.",
)
```

## Erreurs HTTP

Forge fournit des réponses HTTP standardisées :

```python
BaseController.bad_request()      # 400
BaseController.forbidden()        # 403
BaseController.not_found()        # 404
BaseController.validation_error() # 422
BaseController.server_error()     # 500
```

Le statut recommandé pour un formulaire invalide est `422`.

Forge V1.0 retourne aussi une réponse `413` lorsque le corps de requête dépasse la limite configurée de 1 Mo.

## Formulaires de pivot explicite

Forge ne masque pas les relations de type many-to-many. Elles restent modélisées par une entité pivot explicite.

Doctrine :

- une entité pivot Forge est une entité normale ;
- un formulaire Forge peut manipuler une liste d'identifiants liés ;
- un formulaire Forge ne devine pas la relation ;
- un formulaire Forge n'écrit pas dans la base ;
- le modèle applicatif SQL reste responsable de la persistance ;
- le SQL reste visible.

### `RelatedIdsField`

`RelatedIdsField` couvre les sélections simples autour d'une entité pivot explicite.

Son rôle :

- lire une liste d'identifiants depuis un formulaire HTML ;
- convertir en entiers ;
- supprimer les doublons ;
- valider par rapport à une liste autorisée reçue ;
- produire `cleaned_data`.

Il ne va jamais chercher les identifiants autorisés en base.

Exemple :

```python
from core.forms import Form, RelatedIdsField, StringField


class ContactForm(Form):
    nom = StringField(required=True)
    groupe_ids = RelatedIdsField(
        required=False,
        allowed_ids_key="allowed_group_ids",
    )
```

Dans le contrôleur, les identifiants autorisés sont fournis explicitement :

```python
form = ContactForm.from_request(
    request,
    allowed_group_ids=GroupeModel.allowed_ids(),
)

if form.is_valid():
    contact_id = ContactModel.create(form.cleaned_data)
    ContactGroupeModel.replace_for_contact(
        contact_id,
        form.cleaned_data["groupe_ids"],
    )
```

Le SQL reste visible dans le modèle applicatif SQL.

Règle d'or :

- `RelatedIdsField` prépare une sélection ;
- le modèle applicatif SQL applique les changements.

## Transactions explicites

Les écritures multiples, notamment avec un pivot explicite, doivent être groupées dans une transaction visible.

```python
from core.database.transaction import transaction


with transaction() as tx:
    contact_id = ContactModel.create(form.cleaned_data, tx=tx)
    ContactGroupeModel.replace_for_contact(
        contact_id,
        form.cleaned_data["groupe_ids"],
        tx=tx,
    )
```

Le développeur choisit où la transaction commence et où elle finit. Forge fournit l'outil, pas la décision métier.

## Pagination standardisée

`Pagination` expose les attributs utiles pour les requêtes SQL paginées :

```python
pagination = Pagination(request, ContactModel.count(), par_page=20)
contacts = ContactModel.list(limit=pagination.limit, offset=pagination.offset)
```

Le contexte historique reste disponible, avec un bloc `pagination` standard :

```python
context = {
    "contacts": contacts,
    **pagination.context,
}
```

La pagination n'est pas encore générée automatiquement par `forge make:crud`.

## Diagnostic des routes

La commande suivante affiche les routes déclarées :

```bash
forge routes:list
```

Elle montre la méthode, le chemin, le nom, le statut public, le CSRF effectivement requis, le marqueur API et le handler.

Dans les templates, les routes nommées sont disponibles via `url_for` :

```html
<a href="{{ url_for('contact_show', id=contact.Id) }}">Voir</a>
```

Côté contrôleur, si une méthode de redirection par nom de route est utilisée dans le projet, elle doit rester explicite. Le CRUD généré par défaut utilise pour l'instant des chemins simples.

## Limites actuelles du CRUD généré

`forge make:crud` V1.0 ne gère pas encore automatiquement :

- les relations many-to-many ;
- les relations one-to-many avec sélection automatique ;
- les champs `ChoiceField` générés depuis une table ;
- les uploads de fichiers ;
- la pagination automatique ;
- la recherche ;
- le tri dynamique ;
- les permissions fines ;
- les migrations avancées ;
- l'administration automatique ;
- Forge Design.

Ces limites sont volontaires : la génération CRUD doit rester un squelette modifiable, sans couche magique.

## Évolutions envisagées

Cette section décrit des outils ou comportements en cours d'étude, **non encore disponibles** dans Forge V1.0.

### `FormSet` (non disponible en V1.0)

`FormSet` est envisagé pour couvrir les pivots enrichis avec plusieurs lignes de formulaire, par exemple une commande avec des lignes `produit_id`, `quantite`, `prix_unitaire`.

Convention HTML pressentie :

```text
lignes-0-produit_id
lignes-0-quantite
lignes-1-produit_id
lignes-1-quantite
lignes-TOTAL_FORMS=2
```

`FormSet` n'est pas une API stable de Forge. Son design définitif est en cours de réflexion. En attendant, les formulaires de pivot enrichi sont à implémenter manuellement via le modèle applicatif SQL explicite.
