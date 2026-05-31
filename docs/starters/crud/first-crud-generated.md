# First CRUD (généré)

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 55%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Starter Forge · Starter autonome avancé</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">First CRUD (généré)</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Le pendant <strong>généré</strong> du starter <a href="first-crud.md">First CRUD</a> (écrit à la main) : un CRUD complet échafaudé par <code>forge make:crud</code> depuis un manifeste d'entité <strong>neutre</strong> <code>Message</code>, puis un câblage manuel des routes. Même entité neutre, deux méthodes — la paire didactique du sujet CRUD.</p>
</div>

!!! warning "Synthèse avancée — starter autonome"
    Ce starter est une **synthèse avancée**, pas une étape immédiate
    après Bonjour Forge. Avant de l'aborder, il est recommandé d'avoir
    suivi les **11 paliers de découverte** puis le starter
    [First CRUD](first-crud.md), c'est-à-dire de maîtriser :

    - les routes et `Response.text(...)` (palier 1 — `Bonjour Forge`) ;
    - les paramètres d'URL avec `request.param(...)` (palier 2 — `query-params`) ;
    - le rendu HTML avec `BaseController.render(...)` (palier 3 — `first-html-view`) ;
    - les routes dynamiques `/{id}` avec `request.route_param(...)` (palier 4 — `dynamic-route`) ;
    - l'inspection de la requête (palier 5 — `request-debug`) ;
    - la réponse JSON (palier 6 — `json-response`) ;
    - la protection CSRF des formulaires (palier 7 — `csrf`) ;
    - les formulaires POST (palier 8 — `form-post`) ;
    - la validation serveur minimale (palier 9 — `server-validation`) ;
    - le SQL visible en lecture avec `core.database.db.fetch_one` (palier 10 — `first-sql`) ;
    - l'écriture en base avec `core.database.db.insert` (palier 11 — `first-sql-write`) ;
    - le CRUD complet à SQL visible écrit à la main (starter `first-crud`).

    Voir la
    [Progression recommandée des starters](../index.md#progression-recommandee)
    pour le détail.

<div class="grid cards" markdown>

-   **Objectif**

    ---

    Voir Forge **générer** un CRUD complet depuis un manifeste d'entité
    neutre `Message` — le pendant échafaudé de `first-crud` écrit à la main.

-   **Niveau**

    ---

    Avancé. Ce starter assemble toutes les briques vues aux paliers
    pédagogiques précédents (entité canonique, modèle SQL généré,
    contrôleur, formulaire, vues HTML, routes).

-   **Temps estimé**

    ---

    1 h à 2 h.

-   **Résultat attendu**

    ---

    Liste, création, détail, modification, suppression et messages flash,
    le tout produit par `forge make:crud`.

</div>

!!! abstract "Ce que ce starter doit faire comprendre"
    Le but n'est pas seulement d'obtenir une page `/messages` fonctionnelle. Ce starter sert surtout à voir le **mécanisme de génération** : à partir d'un seul manifeste canonique, Forge produit le SQL, la classe Python, le contrôleur, le formulaire, le modèle SQL et les templates Jinja, puis le développeur câble les routes manuellement.

---

## Prérequis

### Prérequis généraux

- Python {{python_min}} ou supérieur
- Git
- `pipx` (recommandé) ou environnement virtuel Python
- MariaDB installé et démarré
- Accès à un compte administrateur MariaDB (pour `forge db:init`)
- Fichier `env/dev` configuré avec les identifiants MariaDB

### Prérequis spécifiques au starter

- Projet Forge vierge (créé via `forge new` ou `git clone`)
- Commandes `forge make:entity`, `forge build:model`, `forge db:apply` et `forge make:crud` disponibles (incluses dans l'installation Forge)

---

## Partie 1 — Installer Forge sur une VM Debian vierge

> Si Forge est déjà installé et configuré sur votre machine, passez directement à la [Partie 2 — Construire l'application starter](#partie-2-construire-lapplication-starter).

La procédure complète est documentée sur la page [Installation sur VM Debian vierge](../../install/vm-debian.md).

Elle couvre en 7 étapes : mise à jour du système, dépendances Python/MariaDB, Node.js optionnel, configuration de pipx, démarrage de MariaDB, vérification de l'accès administrateur et installation de Forge via pipx.

Une fois que `forge --version` s'affiche correctement, revenez ici pour construire l'application.

---

## Partie 2 — Construire l'application starter

!!! tip "Profil recommandé"
    Ce starter officiel correspond au profil `minimal` ou `standard`.
    Voir [Profils de projet](../../features/profiles.md) pour choisir le bon
    profil au moment de `forge new`. Pour le **premier** contact
    avec Forge, démarrer plutôt par
    [Bonjour Forge](../welcome/welcome.md) (palier 1, sans BDD).

## 1. Présentation rapide

### 1.1 Objectif

Voir Forge **générer** un CRUD complet sur une entité neutre `Message` :

- une liste simple, enrichissable ensuite ;
- une page de création ;
- une page de détail ;
- une page de modification ;
- une suppression en `POST` ;
- des messages flash après création, modification ou suppression.

Le starter sert à comprendre le flux de **génération** Forge : manifeste canonique, SQL visible, modèle Python généré, CRUD MVC échafaudé puis routes copiées manuellement.

### 1.2 Parcours général

```mermaid
flowchart TD
    A([Navigateur]) -->|"GET /messages, POST /messages…"| B["mvc/routes.py"]
    B --> C[MessageController]
    C -->|"lit et valide"| D[MessageForm]
    C -->|"lit / écrit"| E[message_model.py]
    E --> F[(MariaDB)]
    C -->|"rend"| G[Vue Jinja2]
    G --> H([HTML affiché])
```

!!! tip "Lecture du schéma"
    Une requête web ne va jamais directement en base. Elle passe par une route, un contrôleur, éventuellement un formulaire, puis un modèle SQL. La réponse revient ensuite sous forme de vue Jinja2 rendue en HTML.

---

## 2. Installation du projet Forge

Les deux méthodes arrivent au même résultat : un projet Forge local avec un environnement Python actif et une commande `forge` utilisable.

!!! tip "Si vous avez suivi la Partie 1"
    `forge` est déjà installé via `pipx install forge-mvc`. Dans l'onglet "Installation automatique" ci-dessous, ignorez la ligne `pipx install ...` et commencez directement par `forge new MonProjet`.

!!! note "Installation Forge"
    Cette page suppose que vous êtes **déjà** dans un projet Forge
    créé avec ce starter et que `forge doctor` ne signale aucun
    problème bloquant. Si Forge n'est pas encore installé, voir les
    parcours d'installation officiels : [Installation Forge — vue
    d'ensemble](../../install/index.md) (pipx, développeur du core,
    Windows + WSL, VM Debian…).

!!! note "CLI officielle"
    La documentation utilisateur suppose la CLI officielle `forge`, disponible après installation du package.

### 2.1 Schéma d'installation

```mermaid
flowchart LR
    A1["Méthode A<br/>pipx install"] --> A2["forge new MonProjet"] --> P["Projet Forge prêt"]
    B1["Méthode B<br/>git clone"] --> B2["python -m venv .venv"] --> B3["pip install -r requirements.txt<br/>pip install -e ."] --> P
```

<div class="grid cards" markdown>

-   **Contrôle à faire**

    ---

    ```bash
    forge doctor
    ```

-   **Répertoire attendu**

    ---

    ```text
    MonProjet/
    ├── app.py
    ├── env/dev
    ├── mvc/
    └── core/
    ```

</div>

---

## 3. Préparation de la base

### 3.1 Configurer l'administrateur MariaDB du projet

Avant d'exécuter `forge db:init`, renseigner dans `env/dev` un compte MariaDB disposant des droits nécessaires pour :

- créer la base de données du projet ;
- créer l'utilisateur applicatif ;
- appliquer les privilèges nécessaires.

En développement local, on peut utiliser temporairement un compte administrateur MariaDB existant.

!!! warning "Ne pas confondre les deux comptes"
    `DB_ADMIN_LOGIN` prépare la base avec `forge db:init`.
    `DB_APP_LOGIN` est utilisé ensuite par l'application pendant son fonctionnement normal.

Exemple de configuration :

```env
DB_ADMIN_HOST=localhost
DB_ADMIN_PORT=3306
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=<mot_de_passe_root_mariadb>

DB_NAME=first_crud_generated

DB_APP_HOST=localhost
DB_APP_PORT=3306
DB_APP_LOGIN=app_user
DB_APP_PWD=AppUser_2026!
```

!!! note "Compte administrateur MariaDB"
    La procédure utilise `root` avec mot de passe comme compte administrateur MariaDB. Ce choix simplifie la procédure pour un environnement pédagogique.

    Pour un environnement plus sécurisé, remplacer `root` par un compte dédié, par exemple `forge_admin`, dans `DB_ADMIN_LOGIN` / `DB_ADMIN_PWD`.

| Variable | Rôle | Moment d'utilisation |
|---|---|---|
| `DB_ADMIN_HOST` | Adresse du serveur MariaDB pour l'administration | Pendant `forge db:init` |
| `DB_ADMIN_PORT` | Port MariaDB pour l'administration | Pendant `forge db:init` |
| `DB_ADMIN_LOGIN` | Compte qui crée la base et les droits | Uniquement pendant `forge db:init` |
| `DB_ADMIN_PWD` | Mot de passe du compte administrateur | Uniquement pendant `forge db:init` |
| `DB_NAME` | Base de données du projet | Créée par `forge db:init` |
| `DB_APP_HOST` | Adresse du serveur MariaDB pour l'application | Exécution et `forge db:apply` |
| `DB_APP_PORT` | Port MariaDB pour l'application | Exécution et `forge db:apply` |
| `DB_APP_LOGIN` | Compte applicatif limité | Utilisé par l'application |
| `DB_APP_PWD` | Mot de passe du compte applicatif | Utilisé par l'application |

### 3.2 Schéma : rôle des comptes MariaDB

```mermaid
flowchart TD
    A["forge db:init"] --> B["DB_ADMIN_LOGIN"]
    B --> C["crée la base DB_NAME"]
    B --> D["crée DB_APP_LOGIN"]
    B --> E["donne les droits nécessaires"]

    F["python app.py"] --> G["DB_APP_LOGIN"]
    G --> H["lit et écrit uniquement<br/>dans la base du projet"]
```

### 3.3 Initialiser la base

```bash
forge db:init
```

Cette commande crée la base de données du projet, l'utilisateur applicatif et applique les droits.

!!! success "Avant de continuer"
    Vérifier que MariaDB est installé, démarré, et que les variables `DB_ADMIN_HOST`, `DB_ADMIN_PORT`, `DB_ADMIN_LOGIN`, `DB_ADMIN_PWD`, `DB_APP_HOST`, `DB_APP_PORT`, `DB_APP_LOGIN`, `DB_APP_PWD` et `DB_NAME` sont bien renseignées dans `env/dev`.

---

## 4. Génération de l'application

Cette section détaille pas à pas ce que Forge **génère** pour ce
starter — chaque artefact (entité, modèle, contrôleur, formulaire,
vues, routes) est expliqué dans l'ordre où vous le rencontrez en
développement.

### 4.1 Ce que l'on apprend

<div class="grid cards" markdown>

-   **Manifeste canonique**

    ---

    Créer une entité avec `forge make:entity`, puis compléter `message.json`.

-   **Génération contrôlée**

    ---

    Prévisualiser avec `--dry-run`, puis générer `message.sql` et `message_base.py`.

-   **Base de données**

    ---

    Appliquer le SQL avec `forge db:apply` sur une base de développement.

-   **CRUD généré**

    ---

    Générer contrôleur, modèle SQL, formulaire et templates avec `forge make:crud Message`.

</div>

### 4.2 Parcours de génération

```mermaid
flowchart TD
    A["forge make:entity"] --> B["édition de message.json"]
    B --> C["forge check:model"]
    C --> D["forge build:model --dry-run"]
    D --> E["forge build:model"]
    E --> F["message.sql + message_base.py"]
    F --> G["forge db:apply"]
    G --> H["forge make:crud --dry-run"]
    H --> I["forge make:crud"]
    I --> J["contrôleur · modèle · formulaire · templates"]
    J --> K["copie des routes → mvc/routes.py"]
```

!!! tip "Principe Forge"
    Forge ne saute pas directement à une application terminée. Il produit des fichiers lisibles, puis le développeur les câble explicitement.

---

## 5. Navigation de l'application

### 5.1 Routes fonctionnelles attendues

| Route | Méthode | Rôle |
|---|---:|---|
| `/messages` | `GET` | Liste des messages |
| `/messages/new` | `GET` | Formulaire de création |
| `/messages` | `POST` | Création d'un message |
| `/messages/{id}` | `GET` | Détail d'un message |
| `/messages/{id}/edit` | `GET` | Formulaire de modification |
| `/messages/{id}` | `POST` | Mise à jour d'un message |
| `/messages/{id}/delete` | `POST` | Suppression d'un message |

!!! warning "Ordre des routes"
    `/messages/new` doit rester déclaré avant `/messages/{id}` dans les routes afin d'éviter que `new` soit interprété comme un identifiant.

### 5.2 Schéma de navigation

```mermaid
flowchart TD
    A["/messages<br/>liste"] -->|"Nouveau message"| B["/messages/new<br/>formulaire de création"]
    A -->|"Voir"| C["/messages/{id}<br/>détail"]
    A -->|"Modifier"| D["/messages/{id}/edit<br/>formulaire de modification"]
    C -->|"Supprimer en POST"| E["/messages/{id}/delete"]
```

---

## 6. Charte graphique

Le starter utilise une charte volontairement simple. Les couleurs ci-dessous correspondent aux classes Tailwind utilisées dans les vues générées.

| Usage | Couleur | Code | Aperçu |
|---|---|---:|---|
| Fond des pages de formulaire et de liste | Slate très clair | `#F8FAFC` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #CBD5E1;background:#F8FAFC;border-radius:0.25rem;"></span> |
| Barre supérieure dans `mvc/views/layouts/app.html` | Slate très foncé | `#0F172A` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #0F172A;background:#0F172A;border-radius:0.25rem;"></span> |
| Actions principales | Orange Forge | `#EA580C` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #C2410C;background:#EA580C;border-radius:0.25rem;"></span> |
| Survol des actions principales | Orange Forge foncé | `#C2410C` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #9A3412;background:#C2410C;border-radius:0.25rem;"></span> |
| Actions secondaires : retour, annulation | Gris clair | `#E2E8F0` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #CBD5E1;background:#E2E8F0;border-radius:0.25rem;"></span> |
| Texte principal | Slate foncé | `#0F172A` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #0F172A;background:#0F172A;border-radius:0.25rem;"></span> |
| Texte secondaire | Slate moyen | `#64748B` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #475569;background:#64748B;border-radius:0.25rem;"></span> |
| Cartes de formulaire et de détail | Blanc | `#FFFFFF` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #CBD5E1;background:#FFFFFF;border-radius:0.25rem;"></span> |
| Bordures des cartes | Slate clair | `#E2E8F0` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #CBD5E1;background:#E2E8F0;border-radius:0.25rem;"></span> |
| Message flash de succès | Vert clair | `#DCFCE7` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #86EFAC;background:#DCFCE7;border-radius:0.25rem;"></span> |
| Message flash d'erreur | Rouge clair | `#FEE2E2` | <span style="display:inline-block;width:4rem;height:1.25rem;border:1px solid #FCA5A5;background:#FEE2E2;border-radius:0.25rem;"></span> |

!!! note "Objectif de la charte"
    Le but n'est pas de créer un thème complet, mais d'obtenir une interface lisible et facile à modifier.

---

## 7. Modèle de données

### 7.1 Fichier canonique

Fichier à modifier :

```text
mvc/entities/message/message.json
```

```json
{
  "schema_version": "1.0",
  "name": "Message",
  "table": "message",
  "description": "Entité neutre — starter first-crud-generated (CRUD généré)",
  "fields": [
    {
      "name": "content",
      "type": "string",
      "max_length": 255,
      "nullable": false
    }
  ],
  "options": {
    "timestamps": false,
    "soft_delete": false
  }
}
```

!!! note "Champ `id` implicite"
    La clé primaire `id` (entière, auto-incrémentée) est ajoutée
    automatiquement par `forge build:model`. Le manifeste ne déclare que
    les champs métier — ici un unique champ neutre `content`.

### 7.2 Ce que Forge génère depuis ce JSON

```mermaid
flowchart TD
    A["message.json<br/>source canonique"] --> B["forge build:model"]
    B --> C["message.sql<br/>structure SQL visible"]
    B --> D["message_base.py<br/>classe Python régénérable"]
    A -.-> E["message.py<br/>logique métier manuelle préservée"]
```

!!! tip "Règle de modification"
    On modifie le JSON et le fichier manuel `message.py`. On évite de modifier directement les fichiers régénérables comme `message.sql` et `message_base.py`.

---

## Sous le capot — ce que Forge a produit

=== "Commandes"

    ### Vue synthétique

    | Étape | Commande | Produit ou vérifie |
    |---:|---|---|
    | 1 | `forge make:entity Message --no-input` | Structure de l'entité |
    | 2 | Modifier `message.json` | Manifeste canonique complet |
    | 3 | `forge check:model` | Cohérence des JSON |
    | 4 | `forge build:model --dry-run` | Prévisualisation du modèle généré |
    | 5 | `forge build:model` | `message.sql` et `message_base.py` |
    | 6 | `forge db:apply` | Table SQL dans MariaDB |
    | 7 | `forge make:crud Message --dry-run` | Prévisualisation du CRUD |
    | 8 | `forge make:crud Message` | Contrôleur, modèle SQL, formulaire et vues |

    ### make:entity

    ```bash
    forge make:entity Message --no-input
    ```

    Crée la structure de départ. Le fichier manuel `message.py` n'est pas écrasé lors des régénérations.

    ```text
    mvc/entities/message/
    ├── __init__.py
    ├── message.json
    ├── message.sql
    ├── message_base.py
    └── message.py
    ```

    ### check:model et build:model

    ```bash
    forge check:model               # vérifie sans écrire
    forge build:model --dry-run     # prévisualise
    forge build:model               # génère message.sql et message_base.py
    ```

    SQL produit :

    ```sql
    CREATE TABLE IF NOT EXISTS message (
        Id INT NOT NULL AUTO_INCREMENT,
        Content VARCHAR(255) NOT NULL,
        PRIMARY KEY (Id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ```

    !!! danger "Fichier régénérable"
        `message_base.py` est régénérable — ne pas y écrire de logique métier. La logique va dans `message.py`.

    ### db:apply

    ```bash
    forge db:apply
    ```

    Applique `message.sql` sur la base MariaDB configurée dans `env/dev`.

    ### make:crud

    === "Prévisualiser"

        ```bash
        forge make:crud Message --dry-run
        ```

    === "Générer"

        ```bash
        forge make:crud Message
        ```

    ```mermaid
    flowchart TD
        A["forge make:crud Message"] --> B["message_controller.py"]
        A --> C["message_model.py"]
        A --> D["message_form.py"]
        A --> E["views/message/*.html"]
        B --> B1["reçoit les requêtes<br/>et choisit la réponse"]
        C --> C1["contient les requêtes<br/>SQL explicites"]
        D --> D1["lit et valide<br/>les données du formulaire"]
        E --> E1["affiche la liste,<br/>le formulaire et le détail"]
    ```

    Requêtes SQL générées dans `message_model.py` :

    ```python
    SELECT_ALL   = "SELECT * FROM message ORDER BY Id"
    SELECT_BY_ID = "SELECT * FROM message WHERE Id = ?"
    INSERT       = "INSERT INTO message (Content) VALUES (?)"
    UPDATE       = "UPDATE message SET Content = ? WHERE Id = ?"
    DELETE       = "DELETE FROM message WHERE Id = ?"
    ```

    !!! note "Responsabilité du développeur"
        Les routes restent à déclarer explicitement dans `mvc/routes.py`.

=== "Routes"

    Copier dans `mvc/routes.py` après la génération du CRUD :

    ```python
    from mvc.controllers.message_controller import MessageController

    # Routes protégées par défaut.
    # Pour un test local sans authentification :
    # with router.group("/messages", public=True, csrf=False) as g:
    with router.group("/messages") as g:
        g.add("GET",  "",              MessageController.index,   name="message_index")
        g.add("GET",  "/new",          MessageController.new,     name="message_new")
        g.add("POST", "",              MessageController.create,  name="message_create")
        g.add("GET",  "/{id}",         MessageController.show,    name="message_show")
        g.add("GET",  "/{id}/edit",    MessageController.edit,    name="message_edit")
        g.add("POST", "/{id}",         MessageController.update,  name="message_update")
        g.add("POST", "/{id}/delete",  MessageController.destroy, name="message_destroy")
    ```

    !!! warning "À ne pas inverser"
        `/new` doit rester déclaré avant `/{id}` pour éviter que `new` soit interprété comme un identifiant.

=== "Fichiers"

    ### Fichiers canoniques et générés

    | Fichier | Nature | Rôle |
    |---|---|---|
    | `mvc/entities/message/message.json` | Canonique | Source à modifier |
    | `mvc/entities/message/message.sql` | Généré | SQL de création de la table |
    | `mvc/entities/message/message_base.py` | Généré | Classe de base régénérable |
    | `mvc/entities/message/message.py` | Manuel | Extension métier préservée |
    | `mvc/entities/message/__init__.py` | Manuel | Initialisation du module |

    ### Fichiers CRUD créés s'ils sont absents

    | Fichier | Rôle |
    |---|---|
    | `mvc/controllers/message_controller.py` | Contrôleur HTTP du CRUD |
    | `mvc/models/message_model.py` | Requêtes SQL explicites |
    | `mvc/forms/message_form.py` | Formulaire et validation |
    | `mvc/views/layouts/app.html` | Layout commun |
    | `mvc/views/message/index.html` | Liste des messages |
    | `mvc/views/message/show.html` | Détail d'un message |
    | `mvc/views/message/form.html` | Création et modification |
    | `mvc/routes.py` | Fichier à modifier manuellement |

    ### Arborescence

    ```text
    mvc/
    ├── entities/
    │   └── message/
    │       ├── message.json        # source canonique
    │       ├── message.sql         # SQL généré
    │       ├── message_base.py     # classe générée
    │       ├── message.py          # classe métier manuelle
    │       └── __init__.py
    │
    ├── controllers/
    │   └── message_controller.py   # logique HTTP du CRUD
    │
    ├── models/
    │   └── message_model.py        # requêtes SQL explicites
    │
    ├── forms/
    │   └── message_form.py         # validation du formulaire
    │
    ├── views/
    │   ├── layouts/
    │   │   └── app.html            # layout commun
    │   └── message/
    │       ├── index.html          # liste
    │       ├── form.html           # création / modification
    │       └── show.html           # détail
    │
    └── routes.py                   # routes à compléter manuellement
    ```

=== "Classes Python"

    | Classe | Origine | Rôle |
    |---|---|---|
    | `MessageBase` | Générée depuis le JSON | Propriétés, validations simples, conversion dictionnaire |
    | `Message` | Manuelle | Logique métier spécifique |
    | `MessageForm` | Générée par le CRUD | Lecture et validation du formulaire |
    | `MessageController` | Généré par le CRUD | Actions `index`, `new`, `create`, `show`, `edit`, `update`, `destroy` |
    | `BaseController` | Core Forge | Rendu HTML, redirections, flash, erreurs de validation |

    ### Cycle d'une création de message

    ```mermaid
    flowchart TD
        A([Navigateur]) -->|"POST /messages"| B["mvc/routes.py"]
        B --> C["MessageController.create(request)"]
        C --> D["MessageForm.from_request(request)"]
        D --> E{"form.is_valid()"}
        E -->|non| F["message/form.html\navec les erreurs"]
        E -->|oui| G["add_message(form.cleaned_data)"]
        G --> H[(MariaDB)]
        H --> I["redirect_with_flash → /messages"]
    ```

    ### Exemple — création

    ```python
    form = MessageForm.from_request(request)

    if not form.is_valid():
        return BaseController.validation_error(
            "message/form.html",
            context={"form": form, "action": "/messages", "titre": "Nouveau message"},
            request=request,
        )

    add_message(form.cleaned_data)
    return BaseController.redirect_with_flash(request, "/messages", "Message créé.")
    ```

    ### Fonctions SQL du modèle

    ```python
    get_messages()
    get_message_by_id(id)
    add_message(data)
    update_message(id, data)
    delete_message(id)
    ```

    !!! tip "À retenir"
        Le formulaire ne va pas directement en base. Il passe par le contrôleur, puis par le modèle SQL.

=== "Templates"

    Quatre fichiers générés par `forge make:crud` :

    ```text
    mvc/views/layouts/app.html
    mvc/views/message/index.html
    mvc/views/message/form.html
    mvc/views/message/show.html
    ```

    ### Héritage Jinja2

    ```mermaid
    flowchart TD
        A["layouts/app.html"] --> D["block content"]
        E["message/index.html"] --> D
        F["message/form.html"] --> D
        G["message/show.html"] --> D
    ```

    ### index.html — liste

    ```jinja2
    {% extends "layouts/app.html" %}

    {% block content %}
    <h1>Messages</h1>
    <a href="/messages/new">Nouveau message</a>

    {% for message in messages %}
        <article>
            <h2>{{ message.Content }}</h2>
            <a href="/messages/{{ message.Id }}">Voir</a>
            <a href="/messages/{{ message.Id }}/edit">Modifier</a>
        </article>
    {% endfor %}
    {% endblock %}
    ```

    Les noms `message.Content`… correspondent aux colonnes SQL retournées par `cursor(dictionary=True)`.

    ### form.html — création et modification

    ```jinja2
    {% extends "layouts/app.html" %}

    {% block content %}
    <h1>{{ titre }}</h1>

    <form method="post" action="{{ action }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

        <label>Contenu</label>
        <input type="text" name="content" value="{{ form.value('content') }}">

        <button type="submit">Enregistrer</button>
    </form>
    {% endblock %}
    ```

    Le nom de champ (`content`) est le nom Python du JSON canonique. La colonne SQL (`Content`) s'utilise dans les vues de liste et de détail.

    ### show.html — détail

    ```jinja2
    {% extends "layouts/app.html" %}

    {% block content %}
    <h1>Message #{{ message.Id }}</h1>

    <p>Contenu : {{ message.Content }}</p>

    <a href="/messages/{{ message.Id }}/edit">Modifier</a>

    <form method="post" action="/messages/{{ message.Id }}/delete">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit">Supprimer</button>
    </form>
    {% endblock %}
    ```

    !!! warning "Suppression en POST"
        La suppression utilise `POST` pour éviter une suppression accidentelle par navigation `GET`.

---

## 13. Test navigateur

### 13.1 Scénario nominal

| Étape | Action | Résultat attendu |
|---:|---|---|
| 1 | Lancer `python app.py` | Serveur HTTPS local lancé |
| 2 | Ouvrir `/messages` | Liste affichée |
| 3 | Cliquer sur "Nouveau message" | Formulaire affiché |
| 4 | Soumettre le formulaire vide | Erreurs visibles |
| 5 | Créer un message valide | Retour à la liste |
| 6 | Vérifier le message flash | Message de succès affiché |
| 7 | Ouvrir le détail du message | Détail affiché |
| 8 | Modifier le message | Données mises à jour |
| 9 | Supprimer le message | Suppression effectuée |
| 10 | Revenir à la liste | Message supprimé absent |

### 13.2 Limites du starter

!!! info "Limites assumées"
    - Pas d'authentification dédiée.
    - Pas de recherche avancée.
    - Pas de pagination générée automatiquement.
    - Pas de validation métier au-delà des contraintes simples.
    - Pas de relation : ce starter est volontairement mono-entité.
    - Pas d'ORM : les requêtes SQL restent visibles dans `mvc/models/message_model.py`.

---

## 14. Vérification finale du starter

La vérification finale sert à contrôler trois choses : l'environnement Forge, les routes et le comportement réel dans le navigateur.

### 14.1 Schéma de vérification

```mermaid
flowchart TD
    A["forge doctor"] --> B["environnement du projet OK"]
    B --> C["forge routes:list"]
    C --> D["routes /messages présentes"]
    D --> E["python app.py"]
    E --> F["serveur HTTPS local lancé"]
    F --> G["navigateur"]
    G --> H["CRUD complet vérifié"]
```

### 14.2 Vérifier l'environnement Forge

```bash
forge doctor
```

Cette commande permet de vérifier que le projet est correctement installé et que Forge trouve les éléments nécessaires à son fonctionnement.

### 14.3 Vérifier les routes

```bash
forge routes:list
```

Les routes suivantes doivent apparaître ou être équivalentes selon l'affichage de Forge :

```text
GET   /messages
GET   /messages/new
POST  /messages
GET   /messages/{id}
GET   /messages/{id}/edit
POST  /messages/{id}
POST  /messages/{id}/delete
```

!!! warning "Erreur classique"
    Si `/messages/new` n'apparaît pas avant `/messages/{id}`, il faut vérifier l'ordre des routes dans `mvc/routes.py`.

### 14.4 Lancer le serveur local

```bash
python app.py
```

Ouvrir ensuite dans le navigateur :

```text
https://localhost:8000/messages
```

### 14.5 Scénario de recette

```text
1. Ouvrir /messages
2. Cliquer sur "Nouveau message"
3. Soumettre le formulaire vide
4. Vérifier l'affichage des erreurs
5. Créer un message valide
6. Vérifier le retour à la liste
7. Vérifier le message flash
8. Ouvrir le détail du message
9. Modifier le message
10. Supprimer le message
11. Vérifier que le message supprimé n'apparaît plus dans la liste
```

### 14.6 Erreurs fréquentes

| Symptôme | Cause probable | Fichier ou commande à vérifier |
|---|---|---|
| `/messages` affiche une erreur 404 | Routes non copiées | `mvc/routes.py` |
| `/messages/new` est interprété comme un identifiant | Ordre des routes incorrect | Placer `/new` avant `/{id}` |
| Erreur de connexion MariaDB | Variables incorrectes | `env/dev` |
| Table `message` absente | SQL non appliqué | `forge db:apply` |
| Erreur sur `message.Content` dans la vue | Colonnes SQL différentes | `message.sql`, `message_model.py`, template Jinja |
| Formulaire sans protection CSRF | Champ caché absent | `message/form.html` |

---

## Reconstruction

La procédure complète de reconstruction du starter (étapes
détaillées, alias disponibles, options `--dry-run` / `--public` /
`--init-db` / `--force`) est documentée dans le fichier
[Reconstruction du starter First CRUD (généré)](first-crud-generated-rebuild.md), pour ne pas
mélanger « ce que ce starter fait » (cette page) et « comment le
régénérer en CLI » (rebuild).

La référence CLI globale est dans
[Commandes CLI](../../reference/cli-commands.md).

---

## Dépannage rapide

| Erreur | Cause probable | Correction |
|---|---|---|
| `forge: command not found` | `pipx` n'est pas dans le PATH | `pipx ensurepath` puis `exec $SHELL -l` |
| `No module named venv` | `python3-venv` absent | `sudo apt install python3-venv` |
| `mariadb_config not found` | dépendances MariaDB dev absentes | `sudo apt install libmariadb-dev pkg-config` |
| `Access denied for user 'root'@'localhost'` | mauvais mot de passe root ou root configuré en `unix_socket` | vérifier le mot de passe, ou tester `sudo mariadb` |
| `mariadb: command not found` | client MariaDB absent | `sudo apt install mariadb-client` |
| erreur de compilation Python | outils de build absents | `sudo apt install build-essential pkg-config libmariadb-dev` |
| erreur certificat HTTPS | `openssl` absent | `sudo apt install openssl` |

---

## Après ce starter

Ce starter montre la **génération** d'un CRUD complet — le pendant
échafaudé du starter [First CRUD](first-crud.md) écrit à la main, sur la
même entité neutre `Message`.

Il rassemble les notions vues dans les paliers précédents : routes,
contrôleurs, vues, formulaires, validation serveur, SQL et
migrations.

Prochain starter : **Auth (API cœur)** — comprendre une
authentification minimale moderne avec `core.auth`.

[Prochain starter : Auth (API cœur)](../core-auth/users-core-auth.md)

[Revenir à la vue d'ensemble des starters](../index.md)
