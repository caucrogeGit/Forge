# Reconstruction — Starter 4 Suivi pédagogique

Ce fichier détaille la reconstruction manuelle du starter 4 depuis un projet Forge vierge.

> **Note :** `forge starter:build 4` sera disponible dans une prochaine version et automatisera ces étapes.

---

## Prérequis

- Projet Forge initialisé (`forge new SuiviApp` ou clone manuel)
- MariaDB démarré, `env/dev` configuré avec `DB_ADMIN_LOGIN`, `DB_APP_LOGIN`, `DB_NAME`, etc.
- Environnement virtuel activé (`source .venv/bin/activate`)

---

## 1. Initialisation de la base

```bash
forge db:init
```

---

## 2. Création des entités

```bash
forge make:entity Eleve --no-input
forge make:entity Cours --no-input
forge make:entity ObservationCours --no-input
```

Remplacez les JSON générés par les modèles ci-dessous (section 6), puis :

```bash
forge check:model
forge build:model
```

Copiez `relations.json` (section 6) dans `mvc/entities/relations.json`, puis :

```bash
forge db:apply
```

---

## 3. Génération du CRUD de base

```bash
forge make:crud Eleve
forge make:crud Cours
```

`ObservationCours` n'a pas de CRUD généré — son contrôleur, ses vues et ses routes sont écrits manuellement (c'est la partie métier du starter).

---

## 4. Fichiers applicatifs à créer manuellement

### Contrôleurs

```text
mvc/controllers/auth_controller.py
mvc/controllers/suivi_controller.py        ← dashboard protégé
mvc/controllers/observation_cours_controller.py
```

### Modèles SQL

```text
mvc/models/auth_model.py
mvc/models/observation_cours_model.py
```

### Vues

```text
mvc/views/auth/login.html
mvc/views/suivi/dashboard.html
mvc/views/observations/new.html
mvc/views/observations/show.html
mvc/views/observations/edit.html
```

### Scripts

```text
scripts/create_auth_user.py    ← créer le compte enseignant de test
scripts/seed_suivi.py          ← peupler la base avec des données démo
```

---

## 5. Routes à câbler dans `mvc/routes.py`

```python
from mvc.controllers.auth_controller import AuthController
from mvc.controllers.suivi_controller import SuiviController
from mvc.controllers.eleve_controller import EleveController
from mvc.controllers.cours_controller import CoursController
from mvc.controllers.observation_cours_controller import ObservationCoursController

# forge-starter:suivi-comportement-eleves:start
with router.group("", public=True) as pub:
    pub.add("GET",  "/login", AuthController.login_form, name="login_form")
    pub.add("POST", "/login", AuthController.login,      name="login")

router.add("POST", "/logout", AuthController.logout, name="logout")

router.add("GET",  "/suivi",                SuiviController.index,                name="suivi_dashboard")
router.add("GET",  "/eleves",               EleveController.index,                name="eleve_index")
router.add("GET",  "/eleves/{id}",          EleveController.show,                 name="eleve_show")
router.add("GET",  "/cours",                CoursController.index,                name="cours_index")
router.add("GET",  "/cours/{id}",           CoursController.show,                 name="cours_show")
router.add("GET",  "/observations/new",     ObservationCoursController.new,       name="obs_new")
router.add("POST", "/observations",         ObservationCoursController.create,    name="obs_create")
router.add("GET",  "/observations/{id}",    ObservationCoursController.show,      name="obs_show")
router.add("GET",  "/observations/{id}/edit", ObservationCoursController.edit,    name="obs_edit")
router.add("POST", "/observations/{id}",    ObservationCoursController.update,    name="obs_update")
# forge-starter:suivi-comportement-eleves:end
```

---

## 6. JSON canoniques

### `mvc/entities/eleve/eleve.json`

```json
{
  "format_version": 1,
  "entity": "Eleve",
  "table": "eleve",
  "fields": [
    { "name": "id",     "sql_type": "INT",         "primary_key": true, "auto_increment": true },
    { "name": "nom",    "sql_type": "VARCHAR(80)",  "constraints": { "not_empty": true, "max_length": 80 } },
    { "name": "prenom", "sql_type": "VARCHAR(80)",  "constraints": { "not_empty": true, "max_length": 80 } },
    { "name": "classe", "sql_type": "VARCHAR(40)",  "constraints": { "not_empty": true, "max_length": 40 } },
    { "name": "actif",  "sql_type": "BOOLEAN" }
  ]
}
```

### `mvc/entities/cours/cours.json`

```json
{
  "format_version": 1,
  "entity": "Cours",
  "table": "cours",
  "fields": [
    { "name": "id",         "sql_type": "INT",          "primary_key": true, "auto_increment": true },
    { "name": "date_cours", "sql_type": "DATE",         "constraints": { "not_empty": true } },
    { "name": "titre",      "sql_type": "VARCHAR(120)", "constraints": { "not_empty": true, "max_length": 120 } },
    { "name": "classe",     "sql_type": "VARCHAR(40)",  "constraints": { "not_empty": true, "max_length": 40 } }
  ]
}
```

### `mvc/entities/observation_cours/observation_cours.json`

```json
{
  "format_version": 1,
  "entity": "ObservationCours",
  "table": "observation_cours",
  "fields": [
    { "name": "id",               "sql_type": "INT",     "primary_key": true, "auto_increment": true },
    { "name": "eleve_id",         "sql_type": "INT" },
    { "name": "cours_id",         "sql_type": "INT" },
    { "name": "ne_travaille_pas", "sql_type": "BOOLEAN" },
    { "name": "bavarde",          "sql_type": "BOOLEAN" },
    { "name": "dort",             "sql_type": "BOOLEAN" },
    { "name": "telephone",        "sql_type": "BOOLEAN" },
    { "name": "perturbe",         "sql_type": "BOOLEAN" },
    { "name": "refuse_consigne",  "sql_type": "BOOLEAN" },
    { "name": "remarque",         "sql_type": "TEXT",    "nullable": true }
  ]
}
```

### `mvc/entities/relations.json`

```json
{
  "format_version": 1,
  "relations": [
    {
      "name": "observation_cours_eleve",
      "type": "many_to_one",
      "from_entity": "ObservationCours",
      "to_entity": "Eleve",
      "from_field": "eleve_id",
      "to_field": "id",
      "foreign_key_name": "fk_observation_cours_eleve",
      "on_delete": "CASCADE",
      "on_update": "CASCADE"
    },
    {
      "name": "observation_cours_cours",
      "type": "many_to_one",
      "from_entity": "ObservationCours",
      "to_entity": "Cours",
      "from_field": "cours_id",
      "to_field": "id",
      "foreign_key_name": "fk_observation_cours_cours",
      "on_delete": "CASCADE",
      "on_update": "CASCADE"
    }
  ]
}
```

---

## 7. Création de l'utilisateur et seed

```bash
python scripts/create_auth_user.py
python scripts/seed_suivi.py
```

---

## 8. Vérification

```bash
forge check:model
forge routes:list
python app.py
```

Ouvrir `https://localhost:8000/login`, se connecter avec le compte créé à l'étape 7, vérifier le dashboard `/suivi` et la navigation.
