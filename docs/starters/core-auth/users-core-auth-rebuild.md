# Reconstruction — Utilisateurs / authentification

[Accueil](../../index.html){ .md-button }

Ce fichier reconstruit un flux applicatif simple : accueil public, login, dashboard, profil et logout.

## 1. Commandes Forge

Génération automatique :

```bash
forge doctor
forge db:init
forge starter:build 2
python scripts/create_auth_user.py
```

Prévisualisation :

```bash
forge starter:build 2 --dry-run
```

`--public` n'est pas applicable à ce starter : les routes publiques et protégées font partie de l'exemple.

Flux manuel équivalent :

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

with router.group("", public=True) as pub:
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
scripts/create_auth_user.py
mvc/routes.py
```

## 5. Créer un utilisateur de test

Le starter génère `scripts/create_auth_user.py` qui utilise `core.auth.hash_password` (argon2). Le modèle `mvc/models/auth_model.py` expose `get_user_by_login`, `get_user_by_id` et `build_auth_user`.

```bash
python scripts/create_auth_user.py
```

Script minimal équivalent :

```python
from core.auth import hash_password
from core.database.connection import get_connection, close_connection

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
        hash_password("secret123"),
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

Après vérification CSRF, il utilise les API Auth/User modernes :

```python
from core.auth import login_user, logout_user, normalize_auth_user, verify_password
from mvc.models.auth_model import get_user_by_login

if utilisateur and utilisateur.get("Actif") and verify_password(password, utilisateur["PasswordHash"]):
    login_user(request, normalize_auth_user(utilisateur))
    ...
```

Le dashboard est protégé par le décorateur `@login_required` :

```python
from core.auth import get_authenticated_user_id, login_required

@login_required(redirect_to="/login")
def index(request):
    user_id = get_authenticated_user_id(request)
    utilisateur = get_user_by_id(user_id)
    ...
```

La gestion du cycle de session HTTP (CSRF, cookies) reste assurée par `core.security.session`.

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
