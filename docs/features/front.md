# Front et CSS

## Position officielle

Tailwind est le framework CSS officiel de Forge pour les templates générés.

Forge ne maintient pas plusieurs variantes Bootstrap, Bulma, Foundation ou
autres frameworks CSS. Ce choix garde le socle front simple, lisible et
prévisible.

Un développeur peut remplacer Tailwind dans son projet, mais cette
personnalisation sort du chemin standard généré par Forge.

## Pourquoi Tailwind

Forge privilégie :

- des templates HTML explicites ;
- peu de couches cachées ;
- un CSS généré de façon reproductible ;
- une structure compréhensible par un développeur débutant ou intermédiaire ;
- un choix unique pour éviter la multiplication des générateurs.

Tailwind répond à ce besoin : les classes utilisées dans les vues restent
visibles, et le fichier CSS compilé reste servi comme un fichier statique normal.

## Fichiers utilisés

Le fichier source Tailwind est :

```text
static/src/input.css
```

Le fichier compilé servi par Forge est :

```text
static/tailwind.css
```

Les vues générées chargent ce fichier avec :

```html
<link rel="stylesheet" href="/static/tailwind.css">
```

Le dossier JavaScript applicatif standard est :

```text
static/js/
```

Le point d'entrée prévu pour le code JavaScript propre à l'application est :

```text
static/js/app.js
```

Ce fichier reste volontairement minimal. Il prépare un emplacement clair pour le
JavaScript applicatif futur, sans ajouter HTMX, Alpine.js ou autre dépendance
front dans le socle standard.

Les layouts standards chargent ce fichier en bas de page :

```html
<script src="/static/js/app.js" defer></script>
```

Ils exposent aussi un bloc Jinja pour les scripts propres à une page :

```jinja
{% block scripts %}{% endblock %}
```

Ce bloc permet d'ajouter explicitement des scripts locaux dans un layout enfant.
Forge ne charge pas automatiquement HTMX ou Alpine.js tant que les layouts ne
sont pas étendus pour le faire.

## Layouts standard

Forge fournit trois layouts dans `mvc/views/layouts/` :

- `public.html` — layout sans navigation, destiné aux pages visiteurs (accueil,
  connexion, page d'erreur).
- `admin.html` — layout avec barre de navigation et bouton de déconnexion,
  destiné aux pages CRUD et d'administration.
- `base.html` — layout historique conservé pour compatibilité avec les starters
  existants.

Les layouts `public.html` et `admin.html` exposent un bloc de titre personnalisable :

```jinja
{% block title %}{{ app_name | default("Forge") }}{% endblock %}
```

Exemple d'utilisation de `public.html` pour une page de connexion :

```jinja
{% extends "layouts/public.html" %}

{% block title %}Connexion{% endblock %}

{% block content %}
<h1>Connexion</h1>
{% endblock %}
```

Exemple d'utilisation de `admin.html` pour une page CRUD :

```jinja
{% extends "layouts/admin.html" %}

{% block title %}Liste des contacts{% endblock %}

{% block content %}
<h1>Contacts</h1>
{% endblock %}
```

Tous les layouts chargent `tailwind.css` et exposent les blocs `{% block content %}`
et `{% block scripts %}`.

## Templates publics

`forge make:public-page accueil` génère une page visiteur simple sous
`mvc/views/public/accueil.html`, l'associe à une route publique `/accueil` et
ajoute le handler correspondant dans `PublicPagesController`.

`forge make:public-list Hebergement` génère une liste publique simple sous
`mvc/views/public/hebergements/index.html`, un contrôleur public dédié et une
route `/hebergements`. Cette liste lit l'entité JSON canonique, affiche les
champs simples non sensibles et reste distincte du CRUD admin.

`forge make:public-show Hebergement` complète ce contrôleur public avec une fiche
de consultation sous `mvc/views/public/hebergements/show.html` et une route
`/hebergements/{id}`. La fiche affiche les mêmes champs publics simples et
renvoie une 404 si l'élément demandé n'existe pas.

`forge make:public-form DemandeSejour` génère un formulaire de saisie public sous
`mvc/views/public/demande_sejours/form.html`, avec un contrôleur dédié et deux
routes : `GET /demande_sejours/new` (affichage) et `POST /demande_sejours`
(traitement). Le formulaire lit les champs non sensibles de la définition JSON,
applique une validation serveur sur les champs requis, exécute un INSERT SQL
visible et redirige avec un message flash après succès. Non destructif : si le
contrôleur public existe déjà (généré par `make:public-list`), les méthodes
`new()` et `create()` sont ajoutées sans écraser les méthodes existantes.

Les templates publics reposent sur cette convention :

```text
mvc/views/layouts/public.html
mvc/views/public/
mvc/views/components/
```

`layouts/public.html` est le layout visiteur. Il ne contient pas de navigation
admin, ne dépend pas du CRUD et expose les blocs Jinja stables suivants :

```jinja
{% block title %}{% endblock %}
{% block content %}{% endblock %}
{% block scripts %}{% endblock %}
```

Les pages générées par `make:public-page` étendent `layouts/public.html` et
utilisent les blocs `title` et `content`. Le bloc `scripts` reste disponible si
un projet l'utilise explicitement, mais Forge n'ajoute pas de JavaScript dans ce
ticket.

Une page publique n'est pas une vue CRUD admin publiée aux visiteurs. Les listes
et fiches publiques ne génèrent aucun bouton modifier/supprimer, aucune route
CRUD, aucune recherche, aucune pagination, aucun slug et aucune relation complexe.
Les formulaires publics ne génèrent pas d'envoi d'email, de captcha, de workflow,
d'upload ni d'interface admin associée. HTMX, Alpine.js et i18n restent optionnels :
le layout public ne les impose pas.

`forge make:public-contact` génère une page contact publique statique sous
`mvc/views/public/contact.html`. Elle ajoute une méthode `contact()` à
`PublicPagesController` et une route `GET /contact`. Le template contient un
titre, un texte d'introduction, un bloc coordonnées (email + téléphone) et un
bloc adresse. Ce n'est pas un formulaire de contact : aucun traitement serveur,
aucun envoi de mail, aucun INSERT. Non destructif et idempotent.

## Compatibilité i18n des pages publiques

Les templates générés par les commandes publiques utilisent `{{ trans('key') }}`
pour les chaînes génériques. Si la clé existe dans `translations/fr.json`,
la valeur traduite est affichée. Si la clé est absente, `trans()` retourne la
clé elle-même — la page reste fonctionnelle.

**Clés publiques ajoutées dans `translations/fr.json` :**

| Clé | Valeur par défaut |
|---|---|
| `public.page.generated` | Page publique générée par Forge. |
| `public.list.empty` | Aucun élément public à afficher. |
| `public.show.back` | Retour |
| `public.show.not_found` | Élément public introuvable. |
| `public.form.submit` | Envoyer |
| `public.form.success` | Votre demande a été envoyée. |
| `public.contact.title` | Contact |
| `public.contact.intro` | Vous pouvez nous contacter… |
| `public.contact.coordinates` | Coordonnées |
| `public.contact.address` | Adresse |
| `public.contact.email_label` | Email |
| `public.contact.phone` | Téléphone |
| `public.contact.address_placeholder` | Adresse à compléter |

**Ce qui n'est PAS traduit automatiquement :** noms d'entités, routes, noms de
fichiers. Les textes propres à l'entité (titre de liste, champs) restent
en clair dans les templates. L'i18n reste optionnelle : les pages publiques
fonctionnent sans catalogue si les clés sont absentes (la clé s'affiche à la
place). HTMX, Alpine.js et l'i18n avancée (détection de langue, middleware)
ne sont pas imposés.

## Médias dans les pages publiques

`forge make:public-list` et `forge make:public-show` intègrent automatiquement
les médias déclarés dans la définition JSON de l'entité (clé `media`).

**Liste publique** — si l'entité déclare au moins un champ `field: image`, la
liste générée affiche une colonne miniature (thumbnail) pour le premier rôle
image trouvé. Le contrôleur enrichit chaque ligne avec `get_cover_media` après
la requête SQL principale. Aucune image n'est ajoutée pour les entités sans
déclaration `media` ou avec uniquement des fichiers.

**Fiche publique** — la fiche affiche l'ensemble des médias déclarés, dans
l'ordre de la définition :

- Image unique (`multiple: false`, `field: image`) → balise `<img>` avec
  thumbnail si disponible, URL originale sinon.
- Galerie (`multiple: true`, `field: image`) → boucle de `<img>` dans une grille.
- Fichier unique (`multiple: false`, `field: file`) → lien vers le fichier.
- Fichiers multiples (`multiple: true`, `field: file`) → liste de liens.

Les helpers réutilisés sont `get_cover_media` (éléments uniques) et
`list_media_for_entity` (galeries), issus de `forge_mvc_images`. Aucun upload,
aucune suppression, aucun formulaire ni aucun carrousel JavaScript n'est généré
côté public.

Exemple de déclaration dans `mvc/entities/hebergement/hebergement.json` :

```json
"media": [
  {
    "name": "cover",
    "field": "image",
    "role": "cover",
    "label": "Image principale",
    "variants": true,
    "multiple": false
  },
  {
    "name": "photos",
    "field": "image",
    "role": "photos",
    "label": "Galerie photos",
    "multiple": true
  }
]
```

La commande `forge make:public-list Hebergement` générera alors un contrôleur
qui charge `cover_media` par ligne dans la liste et exposera les deux sections
dans la fiche publique.

## Formulaire public

`forge make:public-form <Entite>` génère un formulaire de saisie public non
destructif. Génère `mvc/views/public/{plural}/form.html` et la classe controller
`Public{Plural}Controller` dans `mvc/controllers/public_{plural}_controller.py`.

**Routes générées :**

- `GET /{plural}/new` — affichage du formulaire vide (méthode `new`)
- `POST /{plural}` — traitement et INSERT (méthode `create`)

**Champs inclus** — tous les champs non sensibles de l'entité, hors clé primaire,
clés étrangères (`_id`) et champs systèmes (`created_at`, `updated_at`,
`password*`, `token*`, `secret*`, `is_admin`, `is_active`…).

**Types de champ détectés automatiquement :**

| SQL / python_type | `input_type` généré |
|---|---|
| sql_type contient `TEXT` | `textarea` |
| `python_type: bool` | `checkbox` |
| `python_type: int` ou `float` | `number` |
| `python_type: date` | `date` |
| `python_type: datetime` | `datetime-local` |
| nom contient `email` | `email` |
| nom contient `url`, `website` ou `site` | `url` |
| nom contient `phone` | `tel` |
| autre | `text` |

**Comportement non destructif :** si un contrôleur public existe déjà (par
exemple créé par `make:public-list`), les méthodes `new()` et `create()` ainsi que
les constantes `INSERT_PUBLIC_FORM` et `FORM_FIELDS` sont ajoutées sans toucher aux
méthodes existantes.

**Hors périmètre :** envoi d'email, captcha, workflow, upload, HTMX, Alpine.js,
exposition de routes admin, pagination, i18n.

## Composants Jinja

Forge fournit un dossier de composants HTML/Jinja réutilisables dans
`mvc/views/components/`. Chaque composant est un fragment HTML simple, lisible
et sans logique métier.

### Composants disponibles

| Composant | Rôle | Variables attendues |
|---|---|---|
| `button.html` | Bouton ou lien avec variantes de style | `label`, `type`, `variant`, `href` |
| `alert.html` | Message d'alerte coloré | `message`, `type` |
| `form_field.html` | Champ de formulaire avec label et erreur | `label`, `name`, `value`, `type`, `error` |
| `table.html` | Tableau HTML structuré | `headers`, `rows` |
| `badge.html` | Badge/étiquette coloré | `label`, `variant` |
| `pagination.html` | Navigation de pagination | `pagination` |

Les variantes de `button.html` sont `primary` (défaut), `secondary` et
`danger`. Les variantes de `alert.html` sont `info` (défaut), `success`,
`warning` et `error`. Les variantes de `badge.html` sont `success`,
`warning`, `danger`/`error`, et gris par défaut.

Le composant `button.html` rend un `<button>` par défaut. Si la variable
`href` est définie, il rend un `<a href>` avec le même style. Usage recommandé :

- `primary` — action principale : créer, enregistrer
- `secondary` — action neutre : annuler, retour sous forme de bouton
- `danger` — action destructrice : supprimer

Les liens de navigation (`← Retour`) et les actions inline de tableau
(Voir, Modifier, Supprimer) restent des text-links légers, non soumis au
composant.

Notes sur les composants moins utilisés :

- `components/form_field.html` — n'est pas branché automatiquement dans les templates `make:crud` ; les champs y sont générés en HTML inline.
- `table.html` — non utilisé dans les vues liste générées ; celles-ci contiennent leur tableau en HTML inline.
- `badge.html` — générique, sans logique métier ; aucun variant n'est lié à une valeur applicative.
- `pagination.html` — composant serveur classique ; la pagination HTMX optionnelle des CRUD générés passe par leur partial `_pagination.html`.

### Inclure un composant

Les composants s'incluent avec `{% include %}`. Pour leur passer des
variables spécifiques, utiliser `{% with %}` :

```jinja
{# Bouton submit primary #}
{% with type="submit", variant="primary", label=trans('common.save') %}
    {% include "components/button.html" %}
{% endwith %}

{# Lien secondary (href déclenche le rendu <a>) #}
{% with href="/contacts", variant="secondary", label=trans('common.cancel') %}
    {% include "components/button.html" %}
{% endwith %}

{# Bouton danger dans un formulaire de suppression #}
{% with type="submit", variant="danger", label=trans('crud.delete') %}
    {% include "components/button.html" %}
{% endwith %}
```

```jinja
{% with message=flash_message, type="success" %}
    {% include "components/alert.html" %}
{% endwith %}
```

```jinja
{% with label="Statut", variant="success" %}
    {% include "components/badge.html" %}
{% endwith %}
```

```jinja
{% with headers=["Nom", "Email"], rows=data %}
    {% include "components/table.html" %}
{% endwith %}
```

```jinja
{% with label="Prénom", name="first_name", value=contact.first_name %}
    {% include "components/form_field.html" %}
{% endwith %}
```

Le composant `pagination.html` utilise l'objet `pagination` directement
depuis le contexte de la vue :

```jinja
{% include "components/pagination.html" %}
```

### Règles Forge pour les composants

- Les composants restent lisibles dans leur source HTML.
- Aucun composant ne contient de logique métier.
- Aucun composant ne charge HTMX ou Alpine.js automatiquement.
- Les variables attendues sont explicites dans le template — aucun composant n'est opaque.
- Les composants ne forment pas un mini-framework front.
- Les templates générés (`make:crud`, starters) restent compréhensibles sans connaître les composants.
- Les noms métier restent dans l'application, jamais dans les composants.

### Boutons dans les templates CRUD

Les templates générés par `make:crud` utilisent `components/button.html`
pour les boutons standalone :

| Action | Vue | Variant |
|---|---|---|
| Nouveau (lien) | Index | `primary` |
| Modifier (lien) | Show | `primary` |
| Supprimer (submit) | Show | `danger` |
| Enregistrer (submit) | Form | `primary` |
| Annuler (lien) | Form | `secondary` |

Les actions inline dans les lignes du tableau (Voir, Modifier, Supprimer)
restent des text-links légers (`text-sm text-blue-600 hover:underline` ou
`text-sm font-medium text-red-600 hover:text-red-800`).

Les liens de navigation `← Retour` restent des text-links (`text-gray-600
hover:underline`).

### Limites actuelles

- Tous les composants ne sont pas encore utilisés dans tous les templates générés.
- `make:crud` utilise uniquement `button.html` pour les boutons standalone.
- `alert.html` est utilisé par `render_flash_html()` pour les messages flash.
- Les états vides sont rendus directement dans le template, pas via un composant dédié.
- Aucune modale Alpine n'est générée par `make:crud`.
- Aucun comportement HTMX n'est ajouté aux composants ni aux templates générés.
- Les enrichissements dynamiques (HTMX, Alpine) viendront dans les futurs tickets CRUD-HTMX/templates.
- Ces composants ne remplacent pas les partials existants dans `mvc/views/partials/`.

### Messages flash dans les layouts

Les layouts `admin.html`, `public.html` et `base.html` affichent
automatiquement les messages flash quand la variable `flash_html` est
présente dans le contexte de la vue.

La zone flash est placée dans `<main>`, avant `{% block content %}` :

```jinja
{% if flash_html %}
    {{ flash_html | safe }}
{% endif %}
```

La variable `flash_html` est une chaîne HTML pré-rendue par
`mvc/helpers/flash.py`. Le helper `render_flash_html(request)` lit le
message flash de la session (lecture destructive), puis le rend via le
composant `components/alert.html`.

Usage standard dans un contrôleur :

```python
from mvc.helpers.flash import render_flash_html

context = {
    "flash_html": render_flash_html(request),
    # autres variables...
}
```

Les niveaux supportés sont `success`, `info`, `warning` et `error` — ils
correspondent directement aux variants de `components/alert.html`. Le
niveau `danger` est traité comme `error`.

TPL-004 standardise uniquement l'affichage. La logique applicative
(stocker un flash après une action, rediriger) reste dans les
contrôleurs via `BaseController.redirect_with_flash()`. Aucun nouveau
système de session ou de stockage n'est créé.

### États vides dans les listes CRUD

Les vues liste générées par `make:crud` affichent un état vide standard
quand la collection est vide :

```jinja
{% if contacts %}
    {# tableau #}
{% else %}
<div class="rounded-xl border border-dashed border-gray-300 bg-white p-6 text-center text-gray-600">
    {{ trans("crud.empty") }}
</div>
{% endif %}
```

L'état vide utilise la clé i18n `crud.empty` ("Aucun élément à afficher.").
Il est générique — il n'affiche pas le nom de l'entité ni ne dépend de
logique métier. Les messages flash sont distincts des états vides : un flash
passe par la session et `render_flash_html()`, un état vide est rendu
directement dans le template selon l'état de la liste.

### Confirmations de suppression

Les formulaires de suppression générés par `make:crud` (vue liste et vue détail)
affichent une confirmation native avant soumission :

```html
<form method="post" action="/contacts/{{ contact.id }}/delete"
      onsubmit="return confirm('{{ trans("crud.confirm_delete") }}')">
```

La clé i18n `crud.confirm_delete` ("Confirmer la suppression ?") est injectée
par Jinja2 au rendu. Aucune dépendance JavaScript supplémentaire n'est requise —
`window.confirm()` est natif au navigateur.

## Recompiler le CSS

Après modification des classes ou du fichier source Tailwind :

```bash
npm install
npm run build:css
```

Le script `build:css` est défini dans `package.json` :

```json
"build:css": "tailwindcss -i ./static/src/input.css -o ./static/tailwind.css --minify"
```

## Node.js et npm

Node.js et npm sont nécessaires uniquement pour installer l'outillage front et
recompiler `static/tailwind.css`.

Ils ne sont pas nécessaires pour exécuter le serveur Python Forge quand le CSS
compilé existe déjà.

`forge new` tente d'installer les dépendances front et de compiler Tailwind si
npm est disponible. Si npm est absent, le projet est créé quand même et Forge
affiche un avertissement.

## Initialiser HTMX

HTMX est le JavaScript recommandé par Forge pour améliorer progressivement le
HTML rendu côté serveur. Il reste optionnel : Forge MVC continue de fonctionner
sans HTMX, sans SPA et sans JavaScript obligatoire.

La commande dédiée est :

```bash
forge js:init htmx
```

Elle prépare HTMX de manière explicite :

- ajoute la dépendance npm officielle `htmx.org` dans `package.json` ;
- crée le dossier `static/vendor/htmx/` ;
- conserve `static/js/app.js` pour le JavaScript applicatif du projet ;
- copie `node_modules/htmx.org/dist/htmx.min.js` vers
  `static/vendor/htmx/htmx.min.js` si le paquet est déjà installé.

Workflow recommandé :

```bash
forge js:init htmx
npm install
forge js:init htmx
```

Le fichier servi localement est alors :

```text
static/vendor/htmx/htmx.min.js
```

Cette étape ne modifie pas les layouts et ne charge pas automatiquement HTMX
dans les pages. Utilisez le bloc `{% block scripts %}` pour charger ce fichier
explicitement dans une page ou un layout enfant. Alpine.js n'est pas concerné
par cette commande.

## Initialiser Alpine.js

Alpine.js est complémentaire à HTMX. Il sert aux petits états locaux d'une page :
menu, modale, accordéon, confirmation ou onglets simples. Le HTML rendu par le
serveur reste la base ; Alpine.js ne transforme pas une application Forge en SPA.

La commande dédiée est :

```bash
forge js:init alpine
```

Elle prépare Alpine.js de manière explicite :

- ajoute la dépendance npm officielle `alpinejs` dans `package.json` ;
- crée le dossier `static/vendor/alpine/` ;
- conserve `static/js/app.js` pour le JavaScript applicatif du projet ;
- conserve les fichiers HTMX déjà préparés ;
- copie `node_modules/alpinejs/dist/cdn.min.js` vers
  `static/vendor/alpine/alpine.min.js` si le paquet est déjà installé.

Workflow recommandé :

```bash
forge js:init alpine
npm install
forge js:init alpine
```

Le fichier servi localement est alors :

```text
static/vendor/alpine/alpine.min.js
```

Cette étape ne modifie pas les layouts et ne charge pas automatiquement Alpine.js
dans les pages. Utilisez le bloc `{% block scripts %}` pour charger ce fichier
explicitement dans une page ou un layout enfant. HTMX et Alpine.js peuvent
coexister, et la commande combinée `htmx-alpine` est décrite ci-dessous.

## Initialiser HTMX et Alpine.js ensemble

La commande combinée est :

```bash
forge js:init htmx-alpine
```

Elle est un raccourci pratique : elle exécute la même préparation que
`forge js:init htmx`, puis la même préparation que `forge js:init alpine`.
Ce n'est pas un troisième framework.

Elle prépare :

```text
static/vendor/htmx/htmx.min.js
static/vendor/alpine/alpine.min.js
```

HTMX sert aux échanges serveur et aux fragments HTML. Alpine.js sert aux petits
états locaux. Les deux peuvent coexister dans une application Forge, tout en
gardant le HTML serveur comme base.

Comme les commandes séparées, `htmx-alpine` ne modifie pas les layouts, ne
charge aucun script automatiquement et ne génère aucun comportement dynamique.
Le bloc `{% block scripts %}` permet de charger explicitement les fichiers
vendor quand une page en a besoin.

## Utiliser HTMX avec Forge

HTMX est optionnel. Il sert à enrichir une application HTML rendue côté serveur,
pas à remplacer le modèle MVC de Forge.

Avec Forge, les contrôleurs Python restent responsables des routes, des
validations, des accès SQL et du choix de la réponse. HTMX ajoute seulement une
manière déclarative de demander une ressource HTTP depuis le HTML.

Une route appelée par HTMX peut renvoyer :

- une page complète, comme une route Forge classique ;
- un fragment HTML, si la page cible doit seulement remplacer une zone.

Le choix doit rester explicite dans le contrôleur.

Pour charger HTMX dans une page ou un layout enfant, utilisez le bloc standard :

```jinja
{% block scripts %}
    <script src="/static/vendor/htmx/htmx.min.js" defer></script>
{% endblock %}
```

Forge ne charge pas HTMX automatiquement. Le fichier local doit avoir été préparé
avec `forge js:init htmx` ou `forge js:init htmx-alpine`.

Exemple simple : charger un fragment HTML dans une zone de la page.

```html
<button
    hx-get="/admin/contacts/fragment"
    hx-target="#resultat"
    hx-swap="innerHTML">
    Charger
</button>

<div id="resultat"></div>
```

Le contrôleur associé peut retourner un fragment Jinja dédié :

```python
from core.http.helpers import html


def contacts_fragment(request):
    contacts = find_contacts()
    return html(
        "contacts/_liste.html",
        context={"contacts": contacts},
    )
```

Le template `contacts/_liste.html` reste un fragment HTML lisible :

```html
<ul>
    {% for contact in contacts %}
        <li>{{ contact.nom }}</li>
    {% endfor %}
</ul>
```

Convention du CRUD généré : la recherche reste un formulaire GET classique. Si
HTMX est chargé dans la page, la soumission remplace seulement le bloc de
résultats.

```html
<form
    method="get"
    action="/contacts"
    hx-get="/contacts"
    hx-target="#crud-results"
    hx-swap="innerHTML"
    hx-push-url="true">
    <input type="search" name="q">
</form>

<div id="crud-results">
    {% include "contact/_results.html" %}
</div>
```

Dans le CRUD généré actuel, les liens de pagination restent HTML classiques et
reçoivent aussi une amélioration HTMX optionnelle. Sans HTMX, le `href` recharge
la page complète ; avec HTMX, seul `#crud-results` est remplacé.

```html
<a
    href="/contacts?page=2"
    hx-get="/contacts?page=2"
    hx-target="#crud-results"
    hx-swap="innerHTML"
    hx-push-url="true">
    Page suivante
</a>
```

Exemple avec un formulaire : le formulaire reste HTML, et le serveur garde la
validation.

```html
<form
    hx-post="/contacts"
    hx-target="#form-result"
    hx-swap="innerHTML">
    <input type="text" name="nom">
    <button type="submit">Enregistrer</button>
</form>

<div id="form-result"></div>
```

Dans ce cas, le contrôleur peut renvoyer un fragment de succès ou le formulaire
avec ses erreurs. Forge ne génère pas encore automatiquement ces comportements :
ils doivent être écrits explicitement par l'application.

Exemple de suppression avec confirmation dans le CRUD généré : l'action reste
un formulaire HTML classique, avec CSRF, et HTMX l'améliore progressivement.

```html
<form
    method="post"
    action="/contacts/12/delete?page=1"
    hx-post="/contacts/12/delete?page=1"
    hx-target="#crud-results"
    hx-swap="innerHTML"
    hx-confirm="Confirmer la suppression ?">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button type="submit">Supprimer</button>
</form>
```

Attributs HTMX de base :

- `hx-get` déclenche une requête HTTP GET ;
- `hx-post` déclenche une requête HTTP POST ;
- `hx-delete` déclenche une requête HTTP DELETE ;
- `hx-target` indique l'élément à remplacer ;
- `hx-swap` indique comment intégrer le HTML reçu ;
- `hx-trigger` précise l'événement qui déclenche la requête ;
- `hx-confirm` demande une confirmation avant l'action.

Cette page ne remplace pas la documentation complète de HTMX. Elle décrit
seulement la façon recommandée de l'utiliser dans une application Forge.

### Règles Forge pour HTMX

- le HTML serveur reste la base ;
- les routes HTMX restent des routes Forge normales ;
- les fragments restent dans `mvc/views/` ;
- la logique métier reste dans les contrôleurs, modèles ou services Python ;
- les requêtes SQL et validations restent visibles côté serveur ;
- garder une version non-JS quand c'est raisonnable, par exemple un vrai
  attribut `href` sur un lien de pagination ;
- ne pas exposer un CRUD public brut sans contrôle d'accès ;
- vérifier CSRF pour les actions sensibles comme `hx-post` ou `hx-delete` ;
- ne pas faire de HTMX une SPA déguisée.

### Limites actuelles

- HTMX reste optionnel et n'est jamais chargé automatiquement ;
- `make:crud` enrichit seulement la recherche, la pagination et la suppression de liste ;
- Forge ne génère ni recherche live, ni JavaScript personnalisé, ni `hx-delete` ;
- Alpine.js est documenté séparément dans FRONT-007.

Bonnes pratiques complémentaires :

- garder les URLs HTMX lisibles ;
- garder les fragments dans `mvc/views/` ;
- nommer les fragments avec une convention claire, par exemple `_liste.html` ;
- ne pas déplacer la logique métier dans le JavaScript ;
- ne pas masquer les requêtes SQL ou les validations côté serveur ;
- utiliser HTMX pour améliorer une page, pas pour transformer Forge en SPA.

## Utiliser Alpine.js avec Forge

Alpine.js est optionnel. Il sert aux petits états locaux côté interface :
afficher ou masquer un bloc, ouvrir une modale, fermer un menu, gérer un
accordéon, changer d'onglet ou demander une confirmation locale.

Alpine.js ne remplace pas les contrôleurs Python, ne porte pas la logique métier
et ne transforme pas Forge en application front-end. Forge reste MVC côté
serveur : les routes, les validations importantes, les accès SQL et les actions
sensibles restent côté Python.

Pour charger Alpine.js dans une page ou un layout enfant, utilisez le bloc
standard :

```jinja
{% block scripts %}
    <script src="/static/vendor/alpine/alpine.min.js" defer></script>
{% endblock %}
```

Forge ne charge pas Alpine automatiquement. Le fichier local doit avoir été
préparé avec `forge js:init alpine` ou `forge js:init htmx-alpine`.

Exemple simple : afficher ou masquer un bloc local.

```html
<div x-data="{ ouvert: false }">
    <button type="button" x-on:click="ouvert = !ouvert">
        Afficher les détails
    </button>

    <div x-show="ouvert">
        Contenu détaillé
    </div>
</div>
```

Exemple de menu déroulant :

```html
<div x-data="{ ouvert: false }">
    <button type="button" x-on:click="ouvert = !ouvert">
        Menu
    </button>

    <nav x-show="ouvert">
        <a href="/admin">Administration</a>
        <a href="/">Accueil</a>
    </nav>
</div>
```

Exemple d'accordéon simple :

```html
<div x-data="{ section: null }">
    <button type="button" x-on:click="section = section === 1 ? null : 1">
        Section 1
    </button>

    <div x-show="section === 1">
        Contenu de la section 1
    </div>
</div>
```

Exemple de confirmation locale avant une action serveur :

```html
<form method="post" action="/admin/contacts/12/delete"
      x-data
      x-on:submit="if (!confirm('Supprimer ce contact ?')) $event.preventDefault()">
    <button type="submit">
        Supprimer
    </button>
</form>
```

Attributs Alpine de base :

- `x-data` déclare l'état local d'un élément ;
- `x-show` affiche ou masque un élément selon une expression ;
- `x-on` écoute un événement, par exemple `x-on:click` ;
- `x-bind` lie dynamiquement un attribut HTML ;
- `x-model` lie une valeur de formulaire à un état local ;
- `$event` donne accès à l'événement courant.

Cette page ne remplace pas la documentation complète d'Alpine.js. Elle décrit
seulement la façon recommandée de l'utiliser dans une application Forge.

### Règles Forge pour Alpine.js

- Alpine.js est réservé aux petits états locaux ;
- la logique métier reste côté Python ;
- les formulaires sensibles restent protégés côté serveur ;
- les validations importantes restent côté serveur ;
- Alpine.js peut améliorer l'ergonomie, mais ne doit pas devenir une
  application front-end ;
- ne pas dupliquer un contrôleur Python dans du JavaScript ;
- conserver un HTML lisible ;
- éviter les composants Alpine trop longs dans les templates.

### Limites actuelles

- Forge prépare Alpine.js mais ne génère pas encore de comportements Alpine ;
- les templates CRUD n'utilisent pas Alpine pour les confirmations (confirm() natif) ;
- les templates CRUD ne génèrent pas encore de modales ou menus Alpine ;
- les composants Jinja liés à Alpine viendront plus tard ;
- HTMX est documenté séparément ;
- `htmx-alpine` prépare les deux librairies mais ne crée pas encore de
  comportements combinés.

## Remplacer Tailwind manuellement

Vous pouvez remplacer Tailwind dans une application générée :

- en modifiant les liens CSS dans vos layouts ;
- en supprimant ou remplaçant le script `build:css` ;
- en adaptant vos templates manuels.

Cette personnalisation devient alors propre à votre application. Forge ne
garantit pas que les générateurs futurs produiront des variantes Bootstrap,
Bulma, Foundation ou autre.

## Ce que Forge ne maintient pas officiellement

Forge ne maintient pas officiellement :

- Bootstrap ;
- Bulma ;
- Foundation ;
- DaisyUI ;
- Flowbite ;
- une option de choix CSS dans `forge new`.

Ces outils peuvent être intégrés manuellement dans une application finale, mais
ils ne font pas partie du chemin standard maintenu par Forge.

## Statut de la phase 3 — Socle front léger

La phase 3 est clôturée. Les blocs suivants sont stables :

- **CSS** — Tailwind compilé, fichier statique, script `build:css`.
- **JS** — `app.js` point d'entrée, `js:init htmx/alpine` optionnels.
- **i18n** — `trans()` Python et Jinja, catalogue `fr.json`, commandes `i18n:init` et `i18n:check`.
- **Layouts** — `public.html`, `admin.html`, `base.html` ; flash, scripts block, Tailwind.
- **Composants** — 6 composants Jinja dans `mvc/views/components/` ; aucun comportement dynamique.
- **make:crud** — libellés i18n, boutons standardisés, états vides, confirmations natives.

Limites restantes (hors périmètre phase 3) :

- HTMX et Alpine ne sont pas encore utilisés dans les CRUD dynamiques ;
- les composants ne sont pas tous utilisés dans tous les templates générés ;
- aucun catalogue `en.json` ou `es.json` n'est fourni ;
- aucune gestion de langue par requête ou session ;
- la phase 4 RBAC n'a pas encore commencé.
