# Reconstruction — Utilisateurs / authentification

Ce fichier reconstruit un flux applicatif simple : accueil public, login, dashboard, profil et logout.

## 1. Commandes Forge

```bash
forge doctor
forge db:init
forge make:entity Utilisateur --no-input
```

Remplacez `mvc/entities/utilisateur/utilisateur.json` par le JSON ci-dessous.

```bash
forge build:model --dry-run
forge build:model
forge check:model
forge db:apply
```

Le CRUD utilisateur complet n’est pas nécessaire pour ce starter. Le flux d’authentification se code explicitement.

## 2. JSON complet

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

## 3. Routes à copier

```python
from mvc.controllers.auth_controller import AuthController
from mvc.controllers.dashboard_controller import DashboardController
from mvc.controllers.home_controller import HomeController

with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home")
    pub.add("GET", "/login", AuthController.login_form, name="login_form")
    pub.add("POST", "/login", AuthController.login, name="login")

with router.group("") as app:
    app.add("GET", "/dashboard", DashboardController.index, name="dashboard")
    app.add("GET", "/profil", DashboardController.profile, name="profile")
    app.add("POST", "/logout", AuthController.logout, name="logout")
```

`POST /login` et `POST /logout` gardent le CSRF actif par défaut.

## 4. Fichiers à créer ou modifier

Générés :

```text
mvc/entities/utilisateur/utilisateur.json
mvc/entities/utilisateur/utilisateur.sql
mvc/entities/utilisateur/utilisateur_base.py
mvc/entities/utilisateur/utilisateur.py
```

Manuels :

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

## 5. Créer un utilisateur de test

L’auth réelle Forge lit l’utilisateur avec `get_user_by_login(login)` et vérifie `PasswordHash` avec `verifier_mot_de_passe()`. Créez donc un hash avec `hacher_mot_de_passe()` avant insertion.

Si vous conservez `mvc.models.auth_model` tel qu’il est livré par Forge, créez aussi les tables `role` et `utilisateur_role`, par exemple avec :

```bash
python cmd/make.py security:init --env dev
```

Le starter ne donne pas de permissions multi-rôles à l’utilisateur : ces tables existent seulement parce que le modèle d’auth réel lit la liste des rôles.

Script minimal :

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

Identifiants de test :

```text
login    admin
password secret123
```

Si votre connecteur SQL attend `%s` au lieu de `?`, adaptez seulement les placeholders.

## 6. Contrôleur et modèle applicatif

Le contrôleur lit les champs depuis `request.body` :

```python
login = request.body.get("login", [""])[0]
password = request.body.get("password", [""])[0]
```

Le modèle applicatif expose une fonction SQL visible :

```python
def get_user_by_login(login):
    ...
```

La session est manipulée via `core.security.session`. Les messages de navigation utilisent :

```python
return BaseController.redirect_with_flash(request, "/dashboard", "Connexion réussie.")
```

## 7. Vérifications

```bash
forge check:model
python app.py
```

Préparez un utilisateur de test dans la base avec un mot de passe haché selon votre code applicatif.

## 8. Test navigateur

1. Ouvrir `/`.
2. Ouvrir `/dashboard` sans session et vérifier la redirection.
3. Ouvrir `/login`.
4. Tenter une soumission invalide.
5. Se connecter avec l’utilisateur de test.
6. Vérifier le dashboard.
7. Ouvrir `/profil`.
8. Soumettre le formulaire de déconnexion en `POST`.
9. Vérifier que la session est supprimée.

## 9. Points pédagogiques

- Login public ne signifie pas absence de CSRF.
- Logout est une action `POST`.
- Les routes protégées utilisent le comportement par défaut.
- Le starter ne gère pas les rôles.
- La sécurité reste explicite et lisible.
