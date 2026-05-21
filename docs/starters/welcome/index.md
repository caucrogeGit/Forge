# Starter 7 — Bienvenue dans Forge

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Starter 7 — Sans base de données</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:1.6rem;line-height:1.15;color:#0F172A;">Cycle HTTP illustré</h2>
  <p style="margin:0;color:#334155;font-size:1rem;">Découvrez le traitement d'une requête HTTP dans Forge : Request → Router → Controller → Response. Sans SQL, sans BDD, sans entités.</p>
</div>

## Usage

```bash
# Créer un nouveau projet avec le starter welcome pré-appliqué
forge new mon-projet --starter welcome
cd mon-projet
source .venv/bin/activate
python app.py
# → Ouvrir https://localhost:8000/welcome
```

Ou dans un projet existant :

```bash
forge starter:build 7
```

## Ce que ce starter fournit

- **6 routes publiques** sous `/welcome/`
- **`WelcomeController`** avec 6 méthodes pédagogiques
- **6 vues HTML** illustrant chaque concept
- **Aucune base de données** — fonctionne dès `python app.py`

### Routes

| Méthode | URL | Contenu |
|---|---|---|
| GET | `/welcome` | Page d'accueil — liens vers les 5 démos |
| GET | `/welcome/cycle` | Cycle HTTP complet illustré pas à pas |
| GET | `/welcome/request` | Objet `Request` inspecté en direct |
| GET | `/welcome/response` | Types de réponses Forge avec exemples de code |
| GET | `/welcome/routing` | Déclaration des routes dans `mvc/routes.py` |
| GET | `/welcome/404-demo` | Gestion des routes inconnues et des erreurs |

## Structure déployée

```
mvc/
  controllers/
    welcome_controller.py    ← WelcomeController (6 méthodes)
  views/
    welcome/
      index.html             ← page d'accueil
      cycle.html             ← cycle HTTP
      request_example.html   ← objet Request
      response_example.html  ← objet Response
      routing_example.html   ← déclaration des routes
      not_found_demo.html    ← gestion 404
```

`mvc/routes.py` reçoit les 6 routes injectées par le starter. La route `/` est redirigée vers `/welcome` via `home_route`.

## Principe pédagogique

Ce starter ne nécessite aucune entité JSON, aucune migration SQL, aucun profil spécifique.
Il illustre les mécanismes fondamentaux de Forge :

- le cycle **Request → Router → Controller → Template → Response** ;
- la lecture des attributs de l'objet `request` ;
- les différents types de réponses (`render`, `redirect`, `JSONResponse`) ;
- la déclaration explicite des routes dans `mvc/routes.py`.

## Prochaines étapes

Une fois le cycle HTTP assimilé, passez au [Starter 1 — Contacts](../01-contact-simple/index.md) pour un premier CRUD complet avec base de données.

```bash
forge starter:build 1 --init-db
```
