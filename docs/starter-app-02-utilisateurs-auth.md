# Starter 2 — Utilisateurs et authentification

Ce parcours transforme le socle de sécurité Forge en petite application navigable : accueil public, connexion, dashboard protégé, profil simple et déconnexion.

## Présentation rapide

### Objectif

Construire un flux applicatif minimal :

- une page d'accueil publique ;
- un formulaire de connexion public ;
- un dashboard accessible uniquement après connexion ;
- une page profil simple ;
- une déconnexion en `POST`.

Le starter explique les sessions, le CSRF, les messages flash et la différence entre routes publiques et routes protégées. Il ne met pas en place de permissions multi-rôles.

### Niveau

Niveau 2 — intermédiaire Forge.

Il suppose que le starter 1 est compris : routes, contrôleurs, formulaires, vues Jinja2 et flash. La nouveauté est la sécurité HTTP et le cycle de session.

### Temps estimé

2h à 3h.

### Résultat attendu

Application avec authentification fonctionnelle — accueil public, formulaire de connexion sécurisé par CSRF, dashboard protégé, page profil et déconnexion en `POST`.

---

## Installation du projet Forge

### Méthode A — installation automatique (recommandée)

```bash
pipx install git+https://github.com/caucrogeGit/Forge.git
forge new AppAuth
cd AppAuth
source .venv/bin/activate
forge doctor
```

### Méthode B — installation manuelle

```bash
git clone https://github.com/caucrogeGit/Forge.git AppAuth
cd AppAuth
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
python forge.py doctor
```

> Si une commande globale `forge ...` échoue, utiliser la commande locale équivalente `python forge.py ...`.

---

## Préparation de la base

```bash
forge db:init
```

Cette commande crée la base de données du projet, l'utilisateur applicatif et applique les droits.

Prérequis :

- MariaDB installé et en cours d'exécution.
- Les identifiants de connexion renseignés dans `env/dev` (`DB_ADMIN_PWD`, `DB_APP_PWD`, etc.).

---

## Développement de l'application

### Ce que l'on apprend

- Déclarer des routes publiques et protégées.
- Garder `POST /logout` derrière un token CSRF.
- Lire les champs de formulaire depuis `request.body`.
- Créer, authentifier et supprimer une session.
- Utiliser `BaseController.redirect_with_flash(request, ...)`.
- Rendre un dashboard protégé avec `BaseController.render(..., request=request)`.
- Ne pas inventer de permissions avancées quand le besoin est seulement "connecté ou non".

### Navigation de l'application

```text
/               accueil public
/login          formulaire de connexion public
/dashboard      page protégée
/profil         profil protégé
/logout         déconnexion en POST
```

`GET /logout` n'est pas proposé : la déconnexion modifie l'état de session et doit rester une action `POST`.

### Charte graphique

La charte reste proche du starter 1 :

- accueil public sobre avec un bouton "Se connecter" ;
- formulaire centré dans une carte ;
- dashboard en deux colonnes simples ;
- profil sous forme de fiche ;
- messages flash visibles après connexion et déconnexion ;
- bouton de déconnexion distinct, en style secondaire ou danger léger.

### Modèle de données

Pour un starter pédagogique, l'utilisateur peut être représenté par une table simple :

```json
{
  "format_version": 1,
  "entity": "Utilisateur",
  "table": "utilisateur",
  "description": "Utilisateur applicatif simple",
  "fields": [
    {
      "name": "utilisateur_id",
      "sql_type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "login",
      "sql_type": "VARCHAR(80)",
      "unique": true,
      "constraints": {
        "not_empty": true,
        "max_length": 80
      }
    },
    {
      "name": "prenom",
      "sql_type": "VARCHAR(80)",
      "nullable": true,
      "constraints": {
        "max_length": 80
      }
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
      "name": "password_hash",
      "sql_type": "VARCHAR(255)",
      "constraints": {
        "not_empty": true,
        "max_length": 255
      }
    },
    {
      "name": "email",
      "sql_type": "VARCHAR(120)",
      "nullable": true,
      "constraints": {
        "max_length": 120
      }
    },
    {
      "name": "actif",
      "sql_type": "BOOLEAN"
    }
  ]
}
```

Le mot de passe en clair ne va jamais dans le JSON ni dans la base. Le starter montre la structure, puis laisse le hachage au code applicatif.

### Commandes Forge

```bash
forge make:entity Utilisateur --no-input
# modifier mvc/entities/utilisateur/utilisateur.json
forge build:model --dry-run
forge build:model
forge check:model
forge db:apply
```

Le CRUD complet utilisateur n'est pas l'objectif de ce starter. On écrit plutôt un `AuthController` et un modèle applicatif SQL visible pour chercher l'utilisateur par login.

### Créer un utilisateur de test

L'auth réelle Forge vérifie le mot de passe avec `core.security.hashing.verifier_mot_de_passe()`. La valeur stockée dans `PasswordHash` doit donc être produite avec `hacher_mot_de_passe()`, au format `sel_hex:hash_hex`.

Si vous utilisez le modèle d'authentification livré avec Forge (`mvc.models.auth_model`), les tables `role` et `utilisateur_role` doivent aussi exister, même sans permission multi-rôles dans ce starter. `python cmd/make.py security:init --env dev` peut les créer. Vous pouvez ensuite insérer ou remplacer l'utilisateur de test avec le script ci-dessous.

Méthode par script minimal :

```python
from core.database.connection import get_connection, close_connection
from core.security.hashing import hacher_mot_de_passe

connection = get_connection()
cursor = connection.cursor()

cursor.execute(
    """
    INSERT INTO utilisateur (Login, Prenom, Nom, Email, PasswordHash, Actif)
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        "admin",
        "Ada",
        "Lovelace",
        "admin@example.test",
        hacher_mot_de_passe("secret123"),
        True,
    ),
)

connection.commit()
cursor.close()
close_connection(connection)
```

Connexion navigateur :

```text
login    admin
password secret123
```

Si votre connecteur SQL utilise `%s` au lieu de `?`, gardez l'idée du script et adaptez uniquement les placeholders à votre connexion.

### Fichiers créés ou modifiés

Fichiers entité :

```text
mvc/entities/utilisateur/utilisateur.json
mvc/entities/utilisateur/utilisateur.sql
mvc/entities/utilisateur/utilisateur_base.py
mvc/entities/utilisateur/utilisateur.py
```

Fichiers applicatifs :

```text
mvc/controllers/auth_controller.py
mvc/controllers/dashboard_controller.py
mvc/models/auth_model.py
mvc/views/auth/login.html
mvc/views/dashboard/index.html
mvc/views/dashboard/profil.html
mvc/views/layouts/app.html
mvc/routes.py
```

### Classes Python utilisées

- `BaseController` pour `render`, `redirect` et `redirect_with_flash`.
- `core.security.session` pour créer, lire, authentifier et supprimer une session.
- `core.security.csrf` via le middleware et le champ `csrf_token`.
- `AuthController` pour login/logout.
- `DashboardController` pour dashboard et profil.
- `Utilisateur` et `UtilisateurBase` pour la structure métier.

Lecture des données de connexion :

```python
login = request.body.get("login", [""])[0]
password = request.body.get("password", [""])[0]
```

Le contrôleur lit les cookies et la session via les helpers de sécurité, pas via un attribut magique sur `request`.

### Tags Jinja utilisés

- `{% extends "layouts/app.html" %}` ;
- `{% block content %}` ;
- `{% if flash %}` ou affichage équivalent selon le contexte du layout ;
- `{{ csrf_token }}` dans les formulaires `POST` ;
- `{{ utilisateur.Nom }}`, `{{ utilisateur.Login }}` et `{{ utilisateur.Email }}` dans le profil si le contexte reçoit directement le dictionnaire SQL ;
- `{% if utilisateur %}` pour adapter la navigation.

### Classes CSS/Tailwind importantes

- `min-h-screen`, `flex`, `items-center`, `justify-center` pour la page login ;
- `max-w-md`, `rounded`, `border`, `shadow-sm` pour la carte de connexion ;
- `bg-orange-600`, `hover:bg-orange-700` pour l'action principale ;
- `bg-slate-100`, `text-slate-700` pour les actions secondaires ;
- `grid`, `gap-6`, `md:grid-cols-2` pour le dashboard.

### Test navigateur

1. Ouvrir `/` et vérifier que l'accueil est public.
2. Ouvrir `/dashboard` sans session et vérifier la redirection vers `/login`.
3. Ouvrir `/login`.
4. Soumettre le formulaire sans token CSRF valide et vérifier le refus.
5. Se connecter avec un utilisateur de test.
6. Vérifier le message flash de connexion.
7. Ouvrir `/dashboard`.
8. Ouvrir `/profil`.
9. Cliquer sur déconnexion, qui soumet `POST /logout`.
10. Vérifier que `/dashboard` redevient inaccessible.

### Limites du starter

- Pas de permissions multi-rôles.
- Pas de réinitialisation de mot de passe.
- Pas d'inscription publique.
- Pas de politique de mot de passe avancée.
- Pas de gestion d'équipe ou d'organisation.
- Le modèle utilisateur est volontairement minimal.

---

## Vérification finale

```bash
forge doctor
forge routes:list
python app.py
```

Ouvrir dans le navigateur :

```text
https://localhost:8000/login
```

## Reconstruction

Le fichier complet de reconstruction est disponible dans [starters/02-utilisateurs-auth/rebuild.md](starters/02-utilisateurs-auth/rebuild.md).
