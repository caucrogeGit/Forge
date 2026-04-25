# Reconstruction — Suivi comportement élèves

Ce fichier reconstruit le starter métier : élèves, cours, observations de comportement et tableau récapitulatif.

## 1. Commandes Forge

```bash
forge doctor
forge db:init
forge make:entity Eleve --no-input
forge make:entity Cours --no-input
forge make:entity ObservationCours --no-input
```

Remplacez les trois JSON générés par les modèles ci-dessous.

```bash
forge build:model --dry-run
forge build:model
forge make:relation
forge make:relation
forge sync:relations
forge check:model
forge db:apply
forge make:crud Eleve
forge make:crud Cours
```

La saisie des observations est créée manuellement : c’est l’écran métier du starter.

## 2. JSON complets

### `mvc/entities/eleve/eleve.json`

```json
{
  "format_version": 1,
  "entity": "Eleve",
  "table": "eleve",
  "fields": [
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "nom", "sql_type": "VARCHAR(80)", "constraints": { "not_empty": true, "max_length": 80 } },
    { "name": "prenom", "sql_type": "VARCHAR(80)", "constraints": { "not_empty": true, "max_length": 80 } },
    { "name": "classe", "sql_type": "VARCHAR(40)", "constraints": { "not_empty": true, "max_length": 40 } },
    { "name": "actif", "sql_type": "BOOLEAN" }
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
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "date_cours", "sql_type": "DATE", "constraints": { "not_empty": true } },
    { "name": "titre", "sql_type": "VARCHAR(120)", "constraints": { "not_empty": true, "max_length": 120 } },
    { "name": "classe", "sql_type": "VARCHAR(40)", "constraints": { "not_empty": true, "max_length": 40 } }
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
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "eleve_id", "sql_type": "INT" },
    { "name": "cours_id", "sql_type": "INT" },
    { "name": "ne_travaille_pas", "sql_type": "BOOLEAN" },
    { "name": "bavarde", "sql_type": "BOOLEAN" },
    { "name": "dort", "sql_type": "BOOLEAN" },
    { "name": "telephone", "sql_type": "BOOLEAN" },
    { "name": "perturbe", "sql_type": "BOOLEAN" },
    { "name": "refuse_consigne", "sql_type": "BOOLEAN" },
    { "name": "remarque", "sql_type": "TEXT", "nullable": true }
  ]
}
```

## 3. Relations à déclarer

```json
[
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
```

## 4. Routes à copier

Copiez les routes CRUD générées pour `Eleve` et `Cours`, puis ajoutez les routes métier :

```python
from mvc.controllers.observation_cours_controller import ObservationCoursController

with router.group("/cours") as g:
    g.add("GET", "/{id}/observations", ObservationCoursController.edit_for_course, name="cours_observations")
    g.add("POST", "/{id}/observations", ObservationCoursController.save_for_course, name="cours_observations_save")
    g.add("GET", "/{id}/recapitulatif", ObservationCoursController.summary, name="cours_summary")
```

Si les routes CRUD de `Cours` contiennent `/{id}`, gardez les routes fixes ou spécifiques avant les routes génériques quand elles partagent le même préfixe.

## 5. Fichiers à créer ou modifier

Générés :

```text
mvc/entities/eleve/eleve.sql
mvc/entities/cours/cours.sql
mvc/entities/observation_cours/observation_cours.sql
mvc/entities/*/*_base.py
mvc/entities/relations.sql
mvc/controllers/eleve_controller.py
mvc/controllers/cours_controller.py
mvc/forms/eleve_form.py
mvc/forms/cours_form.py
mvc/models/eleve_model.py
mvc/models/cours_model.py
```

Manuels métier :

```text
mvc/controllers/observation_cours_controller.py
mvc/models/observation_cours_model.py
mvc/forms/observation_cours_form.py
mvc/views/cours/observations.html
mvc/views/cours/recapitulatif.html
mvc/routes.py
```

## 6. Formulaire métier

Les cases à cocher correspondent directement aux colonnes booléennes :

```python
from core.forms import BooleanField, Form, StringField


class ObservationCoursForm(Form):
    ne_travaille_pas = BooleanField(label="Ne travaille pas")
    bavarde = BooleanField(label="Bavarde")
    dort = BooleanField(label="Dort")
    telephone = BooleanField(label="Utilise son téléphone")
    perturbe = BooleanField(label="Perturbe le cours")
    refuse_consigne = BooleanField(label="Refuse une consigne")
    remarque = StringField(label="Remarque", required=False, max_length=500)
```

Une case absente du `POST` devient `False`. La remarque libre est stockée dans `remarque`.

## 7. Vérifications

```bash
forge check:model
python app.py
```

Vérifiez aussi que les deux relations sont présentes dans `mvc/entities/relations.sql`.

## 8. Test navigateur

1. Créer trois élèves actifs dans la même classe.
2. Créer un cours pour cette classe.
3. Ouvrir `/cours/{id}/observations`.
4. Cocher `bavarde` pour un élève.
5. Cocher `telephone` et `refuse_consigne` pour un autre.
6. Ajouter une remarque libre.
7. Enregistrer.
8. Ouvrir `/cours/{id}/recapitulatif`.
9. Vérifier les coches et les remarques.
10. Modifier une observation et revérifier le récapitulatif.

## 9. Points pédagogiques

- Les booléens sont adaptés aux cases à cocher.
- Le tableau final est simple parce que les colonnes sont explicites.
- La logique de saisie reste dans le contrôleur, le formulaire et le modèle applicatif.
- Les JSON ne contiennent pas de logique métier.
