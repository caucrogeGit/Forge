# Premier pas — Bienvenue dans Forge

> Ce starter est le point d'entrée recommandé pour découvrir Forge sans base de données.

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Starter 7 — Sans base de données</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:1.6rem;line-height:1.15;color:#0F172A;">Cycle HTTP illustré</h2>
  <p style="margin:0;color:#334155;font-size:1rem;">Découvrez le traitement d'une requête HTTP dans Forge. Cycle HTML : Request → Router → Controller → View → Response HTML. Cycle JSON : Request → Router → Controller → Response JSON. Sans SQL, sans BDD, sans entités.</p>
</div>

## Pourquoi commencer ici ?

Ce starter vous montre **comment Forge traite une requête HTTP**, de sa réception jusqu'à la réponse envoyée au navigateur, sans aucune base de données. C'est le cycle fondamental de tout framework MVC : le comprendre, c'est comprendre Forge.

Vous n'avez pas besoin de configurer MariaDB, de créer des entités ni d'initialiser une base. Un simple `python app.py` suffit pour voir les 6 pages pédagogiques s'ouvrir.

## Ce que vous allez comprendre

- Le traitement d'une requête HTTP de bout en bout
- La différence entre cycle HTML (avec View) et cycle JSON (sans View)
- Le rôle de chaque composant : Request, Router, Controller, View, Response
- Comment déclarer des routes dans `mvc/routes.py`
- Comment le Controller choisit sa réponse

## Les deux cycles HTTP

Forge distingue deux types de réponses. Ils partagent le même début (Request → Router → Controller) mais divergent ensuite.

### Cycle HTML — via la View

```
┌─────────────────┐   ┌────────────┐   ┌───────────────────┐   ┌────────────┐   ┌───────────────────┐
│    Request      │──▶│   Router   │──▶│    Controller     │──▶│    View    │──▶│  Response HTML    │
│ GET /welcome    │   │ routes.py  │   │ WelcomeController │   │ index.html │   │  200 OK + HTML    │
└─────────────────┘   └────────────┘   └───────────────────┘   └────────────┘   └───────────────────┘
```

**Request → Router → Controller → View → Response HTML**

Quand le Controller appelle `self.render("welcome/index.html")`, Forge charge le template Jinja2, le remplit avec les données fournies, et renvoie du HTML au navigateur.

### Cycle JSON — sans View

```
┌─────────────────┐   ┌────────────┐   ┌───────────────────┐   ┌───────────────────┐
│    Request      │──▶│   Router   │──▶│    Controller     │──▶│  Response JSON    │
│ GET /api/data   │   │ routes.py  │   │  méthode()        │   │  200 OK + JSON    │
└─────────────────┘   └────────────┘   └───────────────────┘   └───────────────────┘
```

**Request → Router → Controller → Response JSON**

Quand le Controller retourne `JSONResponse({"clé": "valeur"})`, la View est court-circuitée. La réponse JSON est construite directement, sans passer par un template.

## Les composants en détail

### Request — la requête entrante

L'objet `request` est créé par Forge pour chaque requête HTTP reçue. Il regroupe tout ce que le navigateur a envoyé :

- `request.method` — méthode HTTP (`GET`, `POST`, …)
- `request.path` — chemin demandé (`/welcome/request`)
- `request.params` — paramètres de l'URL (`?page=2`)
- `request.form` — données POST d'un formulaire
- `request.headers` — en-têtes HTTP
- `request.session` — session utilisateur courante

La page `/welcome/request` inspecte cet objet en direct pour que vous voyiez ses valeurs réelles sur votre propre requête.

### Router — la table de routage

Le Router lit `mvc/routes.py` au démarrage de l'application. Pour chaque requête, il cherche quelle méthode de contrôleur correspond au couple `(méthode HTTP, chemin)`.

```python
# mvc/routes.py — déclaration explicite, pas de magie
router.get("/welcome", WelcomeController, "index")
router.get("/welcome/cycle", WelcomeController, "cycle")
```

Si aucune route ne correspond, Forge déclenche automatiquement une réponse 404. La page `/welcome/routing` montre la déclaration complète des 6 routes du starter.

### Controller — la logique applicative

Le Controller reçoit la requête et décide quoi répondre. Il peut lire des données, préparer un contexte de template, et choisir parmi trois formes de réponse :

| Appel | Résultat |
|---|---|
| `self.render("chemin/vue.html", contexte)` | Réponse HTML via View |
| `self.redirect("/autre-route")` | Redirection HTTP 302 |
| `return JSONResponse({...})` | Réponse JSON sans View |

`WelcomeController` illustre ces trois formes dans ses 6 méthodes pédagogiques.

### View — le template Jinja2

La View est un fichier `.html` dans `mvc/views/`. Elle reçoit le contexte préparé par le Controller et produit le HTML final grâce à Jinja2.

La View ne touche pas à la base de données. Elle ne contient pas de logique métier. Son seul rôle : la mise en forme du contenu.

```
Controller → View → Response HTML   (cycle HTML)
Controller          → Response JSON  (cycle JSON, sans View)
```

La page `/welcome/cycle` détaille ce point avec des exemples de code des deux cycles côte à côte.

### Response — la réponse HTTP

Forge construit automatiquement les en-têtes HTTP appropriés (`Content-Type`, `Set-Cookie`, CSRF…). Vous ne gérez que le contenu :

- `self.render(...)` → `200 OK` avec le HTML rendu par la View
- `self.redirect(...)` → `302 Found` vers une autre URL
- `JSONResponse(...)` → `200 OK` avec du JSON, `Content-Type: application/json`

La page `/welcome/response` présente les trois types de réponses avec le code source réel du Controller.

## Structure du projet déployé

```
mvc/
├── controllers/
│   └── welcome_controller.py    ← WelcomeController (6 méthodes)
└── views/
    └── welcome/
        ├── index.html             ← page d'accueil, liens vers les 5 démos
        ├── cycle.html             ← cycles HTML et JSON illustrés
        ├── request_example.html   ← objet Request inspecté en direct
        ├── response_example.html  ← les trois types de réponses
        ├── routing_example.html   ← déclaration des routes
        └── not_found_demo.html    ← gestion 404 et erreurs
mvc/routes.py                      ← 6 routes injectées par le starter
```

## Routes — correspondance route / concept / fichier

| Méthode | URL | Concept illustré | Fichier de vue |
|---|---|---|---|
| GET | `/welcome` | Page d'accueil et navigation | `index.html` |
| GET | `/welcome/cycle` | Les deux cycles HTTP | `cycle.html` |
| GET | `/welcome/request` | Objet Request inspecté | `request_example.html` |
| GET | `/welcome/response` | Types de réponses Forge | `response_example.html` |
| GET | `/welcome/routing` | Déclaration des routes | `routing_example.html` |
| GET | `/welcome/404-demo` | Gestion des erreurs 404 | `not_found_demo.html` |

## Parcours de lecture recommandé

Voici l'ordre suggéré pour tirer le meilleur de ce starter :

1. **/welcome** — lisez l'introduction et les liens vers les démos
2. **/welcome/cycle** — comprenez les deux cycles avant tout le reste
3. **/welcome/routing** — regardez comment les routes sont déclarées dans `mvc/routes.py`
4. **/welcome/request** — inspectez l'objet Request en direct sur votre propre requête
5. **/welcome/response** — découvrez les trois façons de répondre
6. **/welcome/404-demo** — voyez comment Forge gère les routes inconnues

Ensuite, ouvrez `mvc/controllers/welcome_controller.py` dans votre éditeur pour lire le code source du Controller.

## Démarrer

```bash
# Nouveau projet avec le starter pré-appliqué (recommandé)
forge new mon-projet --starter welcome
cd mon-projet
source .venv/bin/activate
python app.py
# → Ouvrir http://localhost:8000/welcome
```

Ou dans un projet Forge existant :

```bash
forge starter:build 7
python app.py
```

## Ce que ce starter ne fait pas

Ce starter est volontairement limité au cycle HTTP de base. Il n'illustre **pas** :

- la connexion à une base de données (MariaDB) ;
- la création d'entités JSON ni leur synchronisation (`sync:entity`) ;
- les migrations SQL (`db:apply`) ;
- l'authentification, les sessions protégées, le CSRF actif ;
- les formulaires POST avec validation ;
- les relations entre entités ;
- les fichiers, médias ou uploads.

Ces sujets sont traités dans les starters suivants, chacun introduisant un concept supplémentaire.

## Après ce starter

Une fois le cycle HTTP assimilé, passez au **Starter 1 — Contacts** pour un premier CRUD complet avec base de données.

```bash
forge starter:build 1 --init-db
```

[Starter 1 — Contacts](../01-contact-simple/index.md) · [Vue d'ensemble des starters](../index.md)
