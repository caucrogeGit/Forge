# Guide de démarrage Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Forge est un framework web MVC Python avec HTTPS natif, SQL explicite, templates Jinja2 et génération déterministe du modèle. Ce guide part d'un environnement Forge déjà installé et aboutit à un premier projet fonctionnel avec CRUD généré.

Pour la référence complète (contrôleurs, formulaires, sécurité, CLI), voir [Référence API et CLI](../reference/reference.md).

!!! tip "Forge n'est pas encore installé ?"
    Commencez par le parcours adapté dans le menu Installation :
    [VM Debian vierge](../install/vm-debian.md), [pipx](../install/pipx.md),
    [GitHub](../install/github.md), [mode développement](../install/core-dev.md)
    ou [préparation MariaDB](../install/mariadb.md).

---

## Créer votre premier projet

Deux méthodes selon votre situation.

### Cas A — Via `forge new` (recommandé)

```bash
forge new MonProjet
cd MonProjet
source .venv/bin/activate
```

Un profil peut être précisé avec `--profile` (`minimal`, `standard`, `dynamic`, `multilingual`) — le profil par défaut est `standard`. Voir [Profils de projet](../features/profiles.md).

`forge new` fait tout automatiquement : clonage du squelette, environnement virtuel Python, installation des dépendances, compilation du CSS Tailwind officiel (si npm est présent) et génération des certificats SSL. Un dépôt Git propre est initialisé.

Il reste deux choses manuelles : **renseigner les mots de passe MariaDB** dans `env/dev`, puis lancer `forge db:init`.

### Cas B — Installation manuelle (usage avancé)

```bash
git clone --branch {{forge_tag}} --depth=1 https://github.com/caucrogeGit/Forge.git MonProjet
cd MonProjet
rm -rf .git && git init && git add -A && git commit -m "init: MonProjet"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp env/example env/dev
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
```

---

### 1. Vérifier l'environnement

```bash
forge doctor
```

### 2. Configurer `env/dev`

`forge new` crée `env/dev` depuis `env/example` avec `APP_NAME` et `DB_NAME` déjà renseignés. Il reste à renseigner les mots de passe MariaDB :

```env
# Compte admin MariaDB — utilisé uniquement par forge db:init
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=<mot_de_passe_root_mariadb>

# Compte applicatif — utilisé par l'application et forge db:apply
DB_APP_LOGIN=mon_projet_app
DB_APP_PWD=<mot_de_passe_applicatif>
```

??? info "Toutes les clés de `env/dev`"

    | Clé | Rôle | Valeur par défaut |
    |---|---|---|
    | `APP_NAME` | Nom de l'application (titre, logs) | défini par `forge new` |
    | `APP_ROUTES_MODULE` | Module Python des routes | `mvc.routes` |
    | `DB_ADMIN_HOST` | Hôte MariaDB admin | `localhost` |
    | `DB_ADMIN_PORT` | Port MariaDB admin | `3306` |
    | `DB_ADMIN_LOGIN` | Login administrateur MariaDB | `root` |
    | `DB_ADMIN_PWD` | Mot de passe administrateur | **à renseigner** |
    | `DB_NAME` | Nom de la base du projet | défini par `forge new` |
    | `DB_CHARSET` | Jeu de caractères | `utf8mb4` |
    | `DB_COLLATION` | Collation | `utf8mb4_unicode_ci` |
    | `DB_APP_HOST` | Hôte MariaDB applicatif | `localhost` |
    | `DB_APP_PORT` | Port MariaDB applicatif | `3306` |
    | `DB_APP_LOGIN` | Login applicatif MariaDB | **à renseigner** |
    | `DB_APP_PWD` | Mot de passe applicatif | **à renseigner** |
    | `DB_POOL_SIZE` | Taille du pool de connexions | `5` |
    | `APP_HOST` | Adresse d'écoute du serveur | `127.0.0.1` |
    | `APP_PORT` | Port du serveur | `8000` |
    | `SSL_CERTFILE` | Certificat SSL | `cert.pem` |
    | `SSL_KEYFILE` | Clé SSL | `key.pem` |

!!! warning "Ne pas confondre les deux comptes MariaDB"
    `DB_ADMIN_LOGIN` est utilisé uniquement par `forge db:init` pour créer la base et l'utilisateur applicatif.
    `DB_APP_LOGIN` est utilisé ensuite par l'application en fonctionnement normal et par `forge db:apply` en développement.

### 3. Initialiser la base MariaDB

```bash
forge db:init
```

Crée la base `DB_NAME`, l'utilisateur `DB_APP_LOGIN`, applique les droits
nécessaires et prépare la table technique `forge_migrations`. Cette table
sert au suivi des migrations SQL versionnées. `forge migration:make` crée un
fichier SQL vide, copie le SQL généré d'une entité avec `--from-entity`,
concatène toutes les entités avec `--from-entities`, ou génère un SQL prudent
depuis un diff avec `--from-diff`. `forge migration:status` affiche l'état,
`forge migration:diff --entity Contact` compare le JSON avec les colonnes
MariaDB, et `forge migration:apply` applique les migrations en attente.

Voir aussi : [Migrations SQL](../features/migrations.md).

!!! success "Avant de continuer"
    Vérifier que MariaDB est démarré, que `env/dev` est configuré avec `DB_ADMIN_LOGIN`, `DB_ADMIN_PWD`, `DB_APP_LOGIN`, `DB_APP_PWD` et `DB_NAME`.

### 4. Créer une entité

```bash
forge make:entity Contact
```

La commande lance l'assistant interactif. Pour un usage scriptable :

```bash
forge make:entity Contact --no-input
```

Puis éditer le fichier canonique `mvc/entities/contact/contact.json` :

```json
{
  "$schema": "../../schemas/entity.schema.json",
  "schema_version": "1.0",
  "name": "Contact",
  "table": "contact",
  "fields": [
    { "name": "nom",       "type": "string",  "max_length": 80  },
    { "name": "prenom",    "type": "string",  "max_length": 80  },
    { "name": "email",     "type": "string",  "max_length": 120, "unique": true },
    { "name": "telephone", "type": "string",  "max_length": 20,  "nullable": true }
  ]
}
```

??? info "Anatomie d'un JSON d'entité Forge"

    | Clé | Obligatoire | Description |
    |---|---|---|
    | `schema_version` | **oui** | Toujours `"1.0"` |
    | `name` | **oui** | Nom PascalCase — devient le nom de la classe Python |
    | `table` | non | Nom snake_case — déduit de `name` si absent |
    | `description` | non | Texte libre (documentaire) |
    | `fields` | **oui** | Liste des champs |

    La clé primaire `Id` est générée automatiquement — ne pas la déclarer dans `fields[]`.

    **Chaque champ :**

    | Clé | Obligatoire | Description |
    |---|---|---|
    | `name` | **oui** | Nom snake_case du champ |
    | `type` | **oui** | Type Forge (`string`, `integer`, `boolean`, `date`, `datetime`, `text`, `password`, `decimal`) |
    | `max_length` | non (string) | Longueur maximale |
    | `nullable` | non | `true` / `false` (défaut : `false`) |
    | `unique` | non | `true` / `false` (défaut : `false`) |
    | `default` | non | Valeur par défaut simple (`str`, `int`, `bool`, `null`) |

### 5. Générer et appliquer le modèle

```bash
forge check:model          # vérifier la cohérence du JSON
forge build:model --dry-run  # prévisualiser sans écrire
forge build:model          # générer contact.sql et contact_base.py
forge db:apply             # créer la table dans MariaDB
```

```mermaid
flowchart LR
    A["contact.json<br/>source canonique"] --> B["forge build:model"]
    B --> C["contact.sql"]
    B --> D["contact_base.py"]
    C --> E["forge db:apply"]
    E --> F[("MariaDB")]
```

!!! danger "Ne pas modifier les fichiers générés"
    `contact.sql` et `contact_base.py` sont régénérables — ne pas y écrire de logique manuelle.
    La logique métier va dans `contact.py`, qui n'est jamais écrasé par Forge.

### 6. Générer le CRUD

```bash
forge make:crud Contact --dry-run  # prévisualiser
forge make:crud Contact            # générer
```

Fichiers créés s'ils sont absents :

```text
mvc/controllers/contact_controller.py
mvc/models/contact_model.py
mvc/forms/contact_form.py
mvc/views/layouts/app.html
mvc/views/contact/index.html
mvc/views/contact/_table.html
mvc/views/contact/_pagination.html
mvc/views/contact/_results.html
mvc/views/contact/show.html
mvc/views/contact/form.html
```

!!! tip "Génération non destructive"
    Si un fichier existe déjà, il est marqué `[PRÉSERVÉ]` et non touché.

Les pages liste générées incluent une recherche GET `q` côté serveur sur les champs texte simples de l'entité, avec SQL `LIKE` paramétré et conservation de `q` dans la pagination. Elles incluent aussi un tri simple par colonne, sécurisé par allowlist, une pagination serveur avec taille de page fixe, et des états vides contextuels quand aucune ligne n'est affichée après recherche ou filtres. La table et la pagination sont isolées dans `_table.html` et `_pagination.html`, puis regroupées par `_results.html`. Le formulaire de recherche, les liens de pagination et les formulaires de suppression reçoivent une amélioration HTMX optionnelle : avec HTMX, seul le bloc `#crud-results` est remplacé ; sans HTMX, les formulaires GET/POST et les liens `href` fonctionnent en HTML classique. Les suppressions gardent le champ CSRF et n'utilisent pas `hx-delete`.

### 7. Déclarer les routes

`forge make:crud` affiche le bloc de routes à ajouter dans `mvc/routes.py` — il ne l'écrit jamais automatiquement.

Copier le bloc affiché dans `mvc/routes.py` :

```python
from mvc.controllers.contact_controller import ContactController

with router.group("/contact") as g:
    g.add("GET",  "",               ContactController.index,   name="contact-index")
    g.add("GET",  "/new",           ContactController.new,     name="contact-new")
    g.add("POST", "/create",        ContactController.create,  name="contact-create")
    g.add("GET",  "/show/{id}",     ContactController.show,    name="contact-show")
    g.add("GET",  "/edit/{id}",     ContactController.edit,    name="contact-edit")
    g.add("POST", "/update/{id}",   ContactController.update,  name="contact-update")
    g.add("POST", "/destroy/{id}",  ContactController.destroy, name="contact-destroy")
```

!!! warning "Ordre des routes"
    `/new` doit être déclaré avant `/{id}`. Sinon le routeur capture `new` comme identifiant.

Vérifier les routes déclarées :

```bash
forge routes:list
```

### 8. Lancer l'application

```bash
python app.py
```

Ouvrir dans le navigateur :

```text
https://localhost:8000/contact
```

---

## Structure du projet

```text
MonProjet/
├── app.py                    # Point d'entrée — serveur HTTPS
├── config.py                 # Chargement de env/dev
│
├── core/                     # Framework Forge — ne pas modifier
│   ├── application.py        # Dispatcher : middlewares + routage
│   ├── http/                 # Request, Response, Router
│   ├── security/             # Sessions, CSRF, hashing, décorateurs
│   ├── forms/                # Form, Field, cleaned_data, erreurs
│   ├── database/             # Pool MariaDB, sql_loader
│   ├── mvc/                  # BaseController, Pagination
│   └── templating/           # Contrat Renderer + singleton
│
├── mvc/                      # Application — c'est ici que vous travaillez
│   ├── routes.py             # Déclaration des routes (manuel)
│   ├── entities/             # JSON canoniques + fichiers générés
│   │   ├── relations.json
│   │   ├── relations.sql
│   │   └── contact/
│   │       ├── contact.json      # source canonique
│   │       ├── contact.sql       # projection SQL générée
│   │       ├── contact_base.py   # base Python générée
│   │       └── contact.py        # classe métier manuelle
│   ├── controllers/
│   ├── models/
│   ├── forms/
│   ├── validators/
│   ├── helpers/
│   └── views/
│
├── env/
│   ├── example               # commité — valeurs par défaut
│   ├── dev                   # ignoré par git
│   └── prod                  # ignoré par git
│
├── tests/
└── static/
```

La règle fondamentale : `core/` appartient à Forge, `mvc/` appartient à votre application.

---

## Cycle de développement standard

```mermaid
flowchart TD
    A["forge make:entity"] --> B["Éditer le JSON canonique"]
    B --> C["forge check:model"]
    C --> D["forge build:model --dry-run"]
    D --> E["forge build:model"]
    E --> F["forge db:apply"]
    F --> G["forge make:crud --dry-run"]
    G --> H["forge make:crud"]
    H --> I["Copier les routes dans mvc/routes.py"]
    I --> J["python app.py"]
    J --> K["forge routes:list"]
```

| Commande | Rôle |
|---|---|
| `forge doctor` | Diagnostique l'environnement |
| `forge make:entity Nom` | Crée l'entité (assistant interactif) |
| `forge check:model` | Valide tous les JSON sans écrire |
| `forge build:model` | Génère `.sql` et `_base.py` depuis les JSON |
| `forge db:init` | Crée la base et l'utilisateur applicatif |
| `forge db:apply` | Applique les SQL générés dans MariaDB |
| `forge migration:make` | Crée un fichier SQL de migration vide |
| `forge migration:make --from-diff Nom` | Génère une migration prudente depuis les colonnes manquantes |
| `forge migration:status` | Affiche les migrations SQL appliquées, en attente, modifiées ou manquantes |
| `forge migration:diff --entity Nom` | Compare une entité JSON avec les colonnes MariaDB |
| `forge migration:apply` | Applique les migrations SQL locales en attente |
| `forge make:crud Nom` | Génère contrôleur, modèle, formulaire, vues |
| `forge routes:list` | Affiche les routes déclarées |

Pour les commandes avancées et la référence complète des paramètres, voir [Référence API et CLI](../reference/reference.md).

---

## Dépannage rapide

| Erreur | Cause probable | Correction |
|---|---|---|
| `forge: command not found` | `pipx` n'est pas dans le PATH | `pipx ensurepath` puis `exec $SHELL -l` |
| `No module named venv` | `python3-venv` absent | `sudo apt install python3-venv` |
| `mariadb_config not found` | dépendances MariaDB dev absentes | `sudo apt install libmariadb-dev pkg-config` |
| `Access denied for user 'root'@'localhost'` | mauvais mot de passe ou root en `unix_socket` | vérifier le mot de passe, ou tester `sudo mariadb` |
| `mariadb: command not found` | client MariaDB absent | `sudo apt install mariadb-client` |
| erreur de compilation Python | outils de build absents | `sudo apt install build-essential pkg-config libmariadb-dev` |
| `forge doctor` signale des FAIL | configuration incomplète | lire les messages FAIL et corriger |
| table absente après `db:apply` | `build:model` non lancé avant | relancer `forge build:model` puis `forge db:apply` |
| routes absentes dans `routes:list` | bloc de routes non copié | copier le bloc affiché par `forge make:crud` dans `mvc/routes.py` |
