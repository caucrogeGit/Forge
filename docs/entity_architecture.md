# Architecture des entités Forge

## Objectif

Cette architecture vise à fournir un modèle d'entités lisible, durable et régénérable, sans magie excessive. L'objectif est de séparer clairement :

* la description canonique du modèle,
* les projections techniques générées,
* le code métier manuel du développeur.

Forge doit rester proche du code et garder le développeur au centre. L'outil aide à générer et synchroniser, mais ne doit pas masquer l'architecture.

---

## Doctrine générale

Pour chaque entité, Forge utilise un petit module dédié sous `mvc/entities/`.

Exemple :

```text
mvc/
└── entities/
    ├── relations.json
    ├── relations.sql
    └── contact/
        ├── __init__.py
        ├── contact.json
        ├── contact.sql
        ├── contact_base.py
        └── contact.py
```

## Convention de nommage

Forge applique les conventions suivantes :

* dossier d'entité : `snake_case`
* nom de table (`table`) : `snake_case`
* nom de classe (`entity`) : `PascalCase`
* nom de champ Python (`field.name`) : `snake_case`
* nom de colonne SQL (`field.column`) : convention SQL du projet, ici `PascalCase`

Exemple :

* dossier : `contact`
* table : `contact`
* classe : `Contact`
* champ Python : `id`
* colonne SQL : `Id`

Cette convention doit être respectée par la CLI, la génération et la validation.

### Source canonique

* `*.json` = source canonique de description
* `*.sql` = projection SQL générée
* `*_base.py` = projection Python générée
* `*.py` = code métier manuel

### Règle stricte

* `contact.py` n'est jamais régénéré automatiquement.
* `contact_base.py` est régénérable et ne doit pas être modifié manuellement en usage normal.
* `contact.sql` est régénérable.
* `relations.sql` est régénérable.

---

## Structure d'une entité

Chaque entité possède son propre dossier.

Exemple :

```text
mvc/entities/contact/
├── __init__.py
├── contact.json
├── contact.sql
├── contact_base.py
└── contact.py
```

### `contact.json`

Source canonique locale de l'entité.

Contient :

* la version du format,
* le nom de l'entité,
* le nom de la table,
* une description optionnelle,
* la liste des champs,
* les types Python,
* les types SQL,
* la nullabilité,
* la clé primaire,
* l'auto-incrément,
* les contraintes simples,
* éventuellement une valeur par défaut,
* éventuellement l'unicité.

### `contact.sql`

Projection SQL locale de l'entité.

Contient :

* le `CREATE TABLE IF NOT EXISTS`,
* les colonnes,
* la clé primaire,
* les contraintes locales (`UNIQUE KEY`, etc.),
* le moteur et le charset.

Ne contient pas les relations inter-entités.

### `contact_base.py`

Classe Python générée, régénérable.

Contient :

* la classe `ContactBase`,
* le constructeur `__init__`,
* les propriétés,
* les setters,
* les décorateurs de validation,
* `to_dict()`,
* `from_dict()`,
* `__repr__`.

Ne contient pas la logique métier manuelle.

### `contact.py`

Classe métier finale, manuelle.

Contient :

* la classe `Contact(ContactBase)`,
* les méthodes métier,
* les surcharges éventuelles,
* des commentaires/zones guidées.

Ce fichier ne doit jamais être écrasé par Forge. Il est créé uniquement s'il est absent et n'est jamais régénéré ni fusionné automatiquement.

### `__init__.py`

Expose la classe finale.

Exemple :

```python
from .contact import Contact
```

Ce fichier est créé uniquement s'il est absent et n'est jamais régénéré ni fusionné automatiquement.

---

## Structure globale des relations

Les relations entre entités sont décrites globalement, et non dans chaque entité individuellement.

Fichiers :

```text
mvc/entities/
├── relations.json
└── relations.sql
```

### `relations.json`

Source canonique globale des relations du modèle.

### `relations.sql`

Projection SQL globale des relations.

Contient uniquement les contraintes relationnelles :

* `ALTER TABLE`
* `ADD CONSTRAINT`
* `FOREIGN KEY`
* `REFERENCES`
* `ON DELETE`
* `ON UPDATE`

---

## Format canonique V1 d'une entité

Exemple :

```json
{
  "entity": "Contact",
  "fields": [
    {
      "name": "id",
      "sql_type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "nom",
      "sql_type": "VARCHAR(100)",
      "constraints": {
        "not_empty": true,
        "max_length": 100
      }
    }
  ]
}
```

### Clés racine

Obligatoires :

* `entity`
* `fields`

Optionnelles avec valeur par défaut implicite :

* `format_version`
* `table`
* `description`

### Clés par champ

Obligatoires :

* `name`
* `sql_type`

Optionnelles :

* `column`
* `python_type`
* `nullable`
* `primary_key`
* `auto_increment`
* `constraints`
* `default`
* `unique`

## Valeurs par défaut implicites

Tout attribut absent prend sa valeur par défaut. Le JSON auteur ne contient que les écarts au comportement standard.

Valeurs injectées automatiquement à la racine :

* `format_version = 1`
* `table = entity` converti en `snake_case`
* `description = ""`

Valeurs injectées automatiquement pour chaque champ :

* `nullable = false`
* `primary_key = false`
* `auto_increment = false`
* `constraints = {}`
* `column = name` converti en `PascalCase` SQL
* `python_type =` déduit depuis `sql_type` quand la déduction est possible

Précisions importantes :

* la dérivation automatique de `column` ne préserve pas les acronymes métier
* par exemple `montant_ttc` devient `MontantTtc`
* si une casse spécifique est voulue, `column` doit être renseigné explicitement

Exemple :

```json
{
  "entity": "Contact",
  "fields": [
    {
      "name": "id",
      "sql_type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "nom",
      "sql_type": "VARCHAR(100)",
      "constraints": {
        "not_empty": true,
        "max_length": 100
      }
    }
  ]
}
```

## Sémantique de `default`

La clé `default` est optionnelle.

Règles :

* absence de clé `default` = aucune valeur par défaut déclarée
* présence de `default: null` = valeur par défaut explicite `None`
* `default: null` n'est autorisé que si `nullable: true`
* les valeurs par défaut V1 sont limitées aux valeurs simples :

  * `str`
  * `int`
  * `float`
  * `bool`
  * `null`

Les valeurs par défaut SQL complexes n'entrent pas dans la V1.

Pour les types temporels V1 :

* `python_type: "date"` est supporté
* `python_type: "datetime"` est supporté
* dans le JSON canonique, `default` reste une chaîne simple
* `date` → chaîne ISO compatible `date.fromisoformat(...)`
* `datetime` → chaîne ISO compatible `datetime.fromisoformat(...)`
* aucune expression SQL complexe n'est autorisée

---

## Contraintes V1 retenues

### Contraintes structurelles

Portées directement par le champ :

* `nullable`
* `primary_key`
* `auto_increment`
* `default`
* `unique`

### Contraintes métier simples

Dans `constraints` :

* `not_empty`
* `min_length`
* `max_length`
* `min_value`
* `max_value`
* `pattern`

### Ce qui n'entre pas en V1

* logique métier complexe,
* dépendances entre champs,
* relations dans le JSON d'entité,
* validations conditionnelles,
* enum avancé,
* hooks,
* logique UI.

---

## Décorateurs V1

Les décorateurs de validation vivent dans :

```text
core/validation/
├── __init__.py
├── exceptions.py
└── decorators.py
```

### Décorateurs retenus

* `@typed(type_)`
* `@nullable`
* `@not_empty`
* `@min_length(n)`
* `@max_length(n)`
* `@min_value(n)`
* `@max_value(n)`
* `@pattern(regex)`

### Doctrine des décorateurs

* un décorateur = une responsabilité,
* validation uniquement,
* aucune transformation implicite,
* `None` est refusé par défaut au niveau de la propriété,
* `@nullable` est le seul décorateur qui autorise explicitement `None`,
* les autres décorateurs ne décident pas de la nullabilité et ne doivent pas échouer sur `None`,
* les décorateurs lèvent `ValidationError`,
* les messages d'erreur doivent inclure le nom de la propriété,
* `typed(int)` doit refuser `bool`.

### Mapping JSON → décorateurs

* `python_type` → `@typed(...)`
* `nullable: true` → `@nullable`
* `constraints.not_empty` → `@not_empty`
* `constraints.min_length` → `@min_length(...)`
* `constraints.max_length` → `@max_length(...)`
* `constraints.min_value` → `@min_value(...)`
* `constraints.max_value` → `@max_value(...)`
* `constraints.pattern` → `@pattern(...)`

En V1, `@typed(...)` peut notamment porter :

* `int`
* `str`
* `float`
* `bool`
* `date`
* `datetime`

---

## Doctrine des classes Python générées

### `contact_base.py`

Le constructeur `__init__` doit être cohérent avec les contraintes.

Un champ devient paramètre obligatoire s'il est :

* non nullable,
* sans valeur par défaut,
* non auto_increment.

Exemple logique :

```python
def __init__(self, nom, prenom, email=None, telephone=None, actif=True, id=None):
    ...
```

Pas :

```python
def __init__(self, id=None, nom="", prenom="", email=None):
    ...
```

### `to_dict()`

Retourne un dictionnaire utilisant les noms Python des champs.

Pour `date` et `datetime`, la sérialisation V1 utilise `isoformat()`.

### `from_dict()`

Version V1 permissive : lecture via `data.get(...)`.

Pour `date` et `datetime`, la reconstruction V1 utilise :

* `date.fromisoformat(...)`
* `datetime.fromisoformat(...)`

### `__repr__`

Généré pour faciliter le debug.

### `contact.py`

Le fichier manuel doit contenir :

* l'héritage depuis `ContactBase`,
* une docstring claire,
* des zones/commentaires guidés,
* `pass` tant qu'aucune logique métier n'a été ajoutée.

---

## Format canonique V1 des relations

Exemple :

```json
{
  "format_version": 1,
  "relations": [
    {
      "name": "commande_client",
      "type": "many_to_one",
      "from_entity": "Commande",
      "to_entity": "Client",
      "from_field": "client_id",
      "to_field": "id",
      "foreign_key_name": "fk_commande_client",
      "on_delete": "RESTRICT",
      "on_update": "CASCADE"
    }
  ]
}
```

### Doctrine V1 des relations

* fichier global unique,
* `many_to_one` seulement en V1,
* `from_field` et `to_field` utilisent les noms de champ du modèle Forge,
* la clé cible doit être la clé primaire de l'entité cible,
* `on_delete` et `on_update` sont toujours explicites.

### Doctrine officielle Forge V1

Forge V1 supporte officiellement les relations `many_to_one` uniquement.
Forge ne fournit pas de `many_to_many` direct ou implicite.

Un `many_to_many` se modélise via une entité pivot explicite décrite comme toute autre entité Forge.
Cette entité pivot possède sa propre clé primaire locale `id` et des clés étrangères explicites sous la forme `<entity>_id`.
Le lien global est alors représenté par deux relations `many_to_one` dans `mvc/entities/relations.json`.

Cette approche conserve un JSON canonique visible, un SQL généré compréhensible et évite toute abstraction magique.

Note V1.0 côté formulaires :

* les formulaires peuvent faciliter la manipulation des identifiants liés à une entité pivot explicite ;
* `RelatedIdsField` prépare une liste d'identifiants validés ;
* le formulaire ne devine pas la relation et n'écrit pas dans la base ;
* le modèle applicatif SQL reste responsable de la persistance dans la table pivot.

→ Voir le guide complet : [CRUD explicite — Forge](crud.md)

### Exemple canonique de pivot explicite

Entité pivot `ContactGroupe` :

```json
{
  "entity": "ContactGroupe",
  "fields": [
    {
      "name": "id",
      "sql_type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "contact_id",
      "sql_type": "INT"
    },
    {
      "name": "groupe_id",
      "sql_type": "INT"
    }
  ]
}
```

Relations globales associées :

```json
{
  "format_version": 1,
  "relations": [
    {
      "name": "contact_groupe_contact",
      "type": "many_to_one",
      "from_entity": "ContactGroupe",
      "to_entity": "Contact",
      "from_field": "contact_id",
      "to_field": "id",
      "foreign_key_name": "fk_contact_groupe_contact",
      "on_delete": "CASCADE",
      "on_update": "CASCADE"
    },
    {
      "name": "contact_groupe_groupe",
      "type": "many_to_one",
      "from_entity": "ContactGroupe",
      "to_entity": "Groupe",
      "from_field": "groupe_id",
      "to_field": "id",
      "foreign_key_name": "fk_contact_groupe_groupe",
      "on_delete": "CASCADE",
      "on_update": "CASCADE"
    }
  ]
}
```

En pratique :

* `ContactGroupe.id` = clé primaire locale du pivot,
* `ContactGroupe.contact_id -> Contact.id`,
* `ContactGroupe.groupe_id -> Groupe.id`.

---

## Doctrine SQL

### SQL d'entité

Chaque entité génère un fichier `*.sql` local.

Exemple :

```sql
CREATE TABLE IF NOT EXISTS contact (
    Id INT NOT NULL AUTO_INCREMENT,
    Nom VARCHAR(100) NOT NULL,
    Prenom VARCHAR(100) NOT NULL,
    Email VARCHAR(150) NULL,
    Telephone VARCHAR(20) NULL,
    Actif BOOLEAN NOT NULL DEFAULT 1,
    PRIMARY KEY (Id),
    UNIQUE KEY uk_contact_email (Email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Règles SQL locales

* mots-clés SQL en majuscules,
* 4 espaces d'indentation,
* une colonne par ligne,
* une contrainte locale par ligne,
* ordre des colonnes conforme au JSON,
* `PRIMARY KEY` en contrainte de table,
* `UNIQUE KEY` en contrainte de table,
* `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`.

Compatibilités minimales V1 entre `python_type` et `sql_type` :

* `bool` ↔ `BOOL`
* `bool` ↔ `BOOLEAN`
* `date` ↔ `DATE`
* `datetime` ↔ `DATETIME`
* `datetime` ↔ `TIMESTAMP`

Précision V1 :

* Forge ne convertit pas implicitement `TINYINT(1)` en booléen
* pour obtenir un booléen, il faut utiliser `BOOL` ou `BOOLEAN`

### SQL des relations

Les relations sont générées dans `relations.sql` uniquement.

`relations.sql` ne doit contenir que des contraintes relationnelles globales.

Règles strictes :

* aucun `CREATE TABLE` ne doit apparaître dans `relations.sql`
* aucune clé étrangère inter-entité ne doit apparaître dans un `*.sql` d'entité
* `relations.sql` contient uniquement des blocs `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY ...`

Exemple :

```sql
ALTER TABLE commande
    ADD CONSTRAINT fk_commande_client
    FOREIGN KEY (ClientId)
    REFERENCES client (Id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;
```

### Règles SQL relationnelles

* un bloc `ALTER TABLE` par relation,
* ligne vide entre deux relations,
* noms de table issus de `table`,
* noms de colonne issus de `column`,
* toujours générer `ON DELETE` et `ON UPDATE`.

### Contraintes SQL hors V1

Certaines contraintes utiles ne sont pas déclarables dans le JSON canonique V1.

Exemples :

* contrainte d'unicité composée,
* index métier composé,
* contrainte SQL spécifique à une application.

Règle stricte :

* ne jamais ajouter ces contraintes dans un `*.sql` d'entité généré ;
* ne jamais les ajouter dans `relations.sql` ;
* les porter dans un script SQL applicatif séparé, hors `mvc/entities/`, exécuté après `forge db:apply` selon l'organisation du projet.

---

## Politique de génération

Avant toute utilisation de la CLI `forge`, activez votre environnement virtuel puis installez le package en mode editable :

```bash
source .venv/bin/activate
pip install -e .
```

> La commande `forge` n'est disponible qu'après installation du package en mode editable.
> Sans `pip install -e .`, la commande `forge` ne sera pas trouvée.

### Génération d'une entité

Commande :

```bash
forge make:entity Contact
```

Cette commande :

* lance un assistant interactif dans le terminal,
* pose les questions utiles pour construire l'entité,
* écrit un JSON auteur court confirmé par l'utilisateur,
* génère `contact.sql`,
* génère `contact_base.py`,
* crée `contact.py`,
* crée `__init__.py`.

### JSON minimal non interactif

Exemple :

```json
{
  "entity": "Contact",
  "fields": [
    {
      "name": "id",
      "sql_type": "INT",
      "primary_key": true,
      "auto_increment": true
    }
  ]
}
```

### Génération interactive

Commande :

```bash
forge make:entity Contact
```

Cette commande :

* construit `contact.json` via un assistant CLI,
* puis génère les fichiers dérivés.

Exemple de parcours :

```text
$ forge make:entity Contact
Nom de la table (Entrée = convention par défaut) :
Nom du champ primaire [id] :
Type SQL du champ primaire [INT, BIGINT, VARCHAR, CHAR, TEXT, DATE, DATETIME, BOOLEAN, DECIMAL] [INT] :
Auto increment ? [O/n] :
Ajouter un autre champ ? [o/N] : o
Nom du champ : nom
Type SQL [INT, BIGINT, VARCHAR, CHAR, TEXT, DATE, DATETIME, BOOLEAN, DECIMAL] : varchar
Longueur SQL : 100
Autoriser NULL ? [o/N] :
Champ unique ? [o/N] :
Ajouter not_empty ? [o/N] : o
min_length [vide = aucun] :
max_length [vide = aucun] : 100
Validation regex [vide = aucune, ex: ^[A-Z]+$ ou ^[^@]+@[^@]+\\.[^@]+$] :
Confirmer l'écriture des fichiers ? [O/n] :
```

### Génération non interactive

Pour un usage scriptable, le mode non interactif reste disponible :

```bash
forge make:entity Contact --no-input
```

Ce mode écrit directement un squelette court minimal, sans assistant ni confirmation.

---

## Politique de régénération

### `forge sync:entity Contact`

Relit `contact.json` et régénère :

* `contact.sql`
* `contact_base.py`

Ne touche jamais à :

* `contact.py`
* `__init__.py`

### `forge sync:relations`

Relit `relations.json` et régénère :

* `relations.sql`

### `forge make:relation`

Commande :

```bash
forge make:relation
```

Cette commande :

* guide la saisie interactive d'une relation,
* écrit ou met à jour `mvc/entities/relations.json`,
* n'écrit jamais directement `relations.sql`,
* reste limitée aux relations `many_to_one` supportées officiellement en V1.

Le flux officiel détaillé est :

1. créer ou modifier les entités ;
2. lancer `forge sync:entity <Entity>` pour chaque entité modifiée ;
3. ajouter les relations avec `forge make:relation` ;
4. lancer `forge sync:relations` ;
5. lancer `forge check:model` ;
6. lancer `forge db:apply`.

Pour un modèle complet ou plusieurs entités modifiées ensemble, `forge build:model` peut remplacer les synchronisations individuelles.

Pour un `many_to_many`, la commande ne fournit pas de magie dédiée :

* créer d'abord une entité pivot explicite,
* puis décrire deux relations `many_to_one`.

### `forge build:model`

Valide et régénère tout le modèle :

1. validation des JSON d'entité,
2. validation de `relations.json`,
3. validation croisée globale,
4. génération des SQL d'entité,
5. génération des `*_base.py`,
6. création des fichiers manuels absents,
7. génération de `relations.sql`.

---

## Ordre d'exécution SQL

L'ordre correct est :

1. tous les `*.sql` des entités,
2. `relations.sql`.

Jamais l'inverse.

---

## Validation interne

Forge doit bloquer toute génération si la validation échoue.

### Validation d'entité

* structure obligatoire,
* noms valides,
* unicité des champs,
* unicité des colonnes,
* une seule clé primaire,
* compatibilité `python_type` / `sql_type`,
* compatibilité des contraintes avec le type,
* compatibilité des valeurs par défaut.

Types Python supportés en V1 :

* `int`
* `str`
* `float`
* `bool`
* `date`
* `datetime`

### Validation des relations

* structure obligatoire,
* entités existantes,
* champs existants,
* type de relation valide,
* clé cible primaire,
* types compatibles,
* unicité des noms de relation.

### Validation globale

* unicité des entités,
* unicité des tables,
* cohérence dossier / entité (`ContactClient` → `contact_client`),
* table personnalisable mais obligatoirement `snake_case` et unique,
* aucune génération si une incohérence existe.

---

## Non-objectifs de cette architecture

Cette architecture n'a pas pour but de :

* construire un ORM complet,
* masquer le SQL réel,
* générer de la logique métier,
* déduire automatiquement des comportements complexes,
* multiplier les sources de vérité.

## Limites de la V1

La première version de cette architecture reste volontairement limitée.

### Retenu en V1

* une seule clé primaire par entité,
* source canonique JSON,
* relations globales,
* `many_to_one` seulement,
* décorateurs simples,
* SQL MariaDB/MySQL centré sur InnoDB,
* pas de repository généré.

### Hors V1

* clés composites,
* `many_to_many` direct ou implicite,
* `one_to_one`,
* logique métier dans le JSON,
* hooks de cycle de vie,
* navigation objet automatique,
* ORM complet,
* génération de repository,
* contraintes conditionnelles,
* valeurs par défaut SQL complexes.

---

## Commandes CLI

### Commandes actuellement disponibles

Interface officielle :

Après l'installation editable décrite dans la politique de génération, l'interface officielle est :

```bash
forge make:entity Contact
forge make:relation
forge sync:entity Contact
forge sync:relations
forge build:model
forge db:init
forge db:apply
forge check:model
```

La forme officielle est toujours :

```bash
forge <commande>
```

et jamais :

```bash
python3 forge.py <commande>
```

---

## Conclusion

Cette architecture donne à Forge :

* une source canonique claire,
* une génération déterministe,
* une séparation nette entre généré et manuel,
* une validation forte,
* une base solide pour Forge Design plus tard,
* un modèle lisible, durable et sans magie excessive.
