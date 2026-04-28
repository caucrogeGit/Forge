# Starter 3 — Carnet de contacts

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Starter Forge · Niveau 3</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Carnet de contacts</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Un carnet relationnel simple : `Ville`, `Contact`, relation `many_to_one`, formulaire avec sélection et SQL visible en `LEFT JOIN`.</p>
</div>

<div class="grid cards" markdown>

-   **Objectif**

    ---

    Comprendre une relation Forge V1 sans ORM implicite.

-   **Génération**

    ---

    Disponible avec `forge starter:build 3`.

-   **Modèle**

    ---

    Deux entités, une relation globale, un SQL de relation visible.

-   **Résultat**

    ---

    Contacts liés optionnellement à une ville.

</div>

!!! success "Génération automatique disponible"
    Ce starter est générable avec `forge starter:build 3`, `forge starter:build carnet` ou `forge starter:build carnet-contacts`.

!!! note "Périmètre actuel"
    La génération automatique crée `Ville`, `Contact` et la relation `Contact.ville_id -> Ville.id`. Elle ne génère pas encore `Groupe`, `ContactGroupe` ni de many-to-many explicite.

## Prérequis

### Prérequis généraux

- Python 3.11 ou supérieur
- Git
- `pipx` (recommandé) ou environnement virtuel Python
- MariaDB installé et démarré
- Accès à un compte administrateur MariaDB (pour `forge db:init`)
- Fichier `env/dev` configuré avec les identifiants MariaDB

### Prérequis spécifiques au starter

- Starters 1 et 2 compris, ou au moins le cycle entité → SQL → CRUD
- Projet Forge vierge, ou scaffold adoptable (le starter détecte et adopte un `relations.json` vide)
- Support des relations Forge : `relations.json` et `relations.sql` (générés automatiquement)
- Utiliser `--force` uniquement si le starter est déjà partiellement présent dans le projet

---

## Partie 1 — Installer Forge sur une VM Debian vierge

> Si Forge est déjà installé et configuré sur votre machine, passez directement à la [Partie 2 — Construire l'application starter](#partie-2-construire-lapplication-starter).

### 1. Mettre à jour Debian

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Installer les dépendances système

```bash
sudo apt install -y \
  git \
  curl \
  ca-certificates \
  build-essential \
  pkg-config \
  python3 \
  python3-venv \
  python3-pip \
  pipx \
  mariadb-server \
  mariadb-client \
  libmariadb-dev \
  openssl
```

### 3. Activer pipx dans le PATH

```bash
pipx ensurepath
exec $SHELL -l
```

Vérifier que les outils sont disponibles :

```bash
python3 --version
git --version
pipx --version
mariadb --version
mariadb_config --version
openssl version
```

Si une commande échoue, la machine n'est pas encore prête.

### 4. Démarrer MariaDB

```bash
sudo systemctl enable --now mariadb
sudo systemctl status mariadb
```

### 5. Vérifier l'accès administrateur MariaDB

> Sur certaines installations Debian, le compte `root` MariaDB peut être configuré avec l'authentification système `unix_socket`. Dans ce cas, `mariadb -u root -p` peut échouer alors que `sudo mariadb` fonctionne.
> Dans cette procédure Forge, on suppose que le compte `root` MariaDB est configuré avec un mot de passe.

```bash
mariadb -u root -p
```

Entrer le mot de passe `root` MariaDB lorsqu'il est demandé. Une invite `MariaDB [(none)]>` confirme que l'accès fonctionne. Saisir `exit` pour quitter.

Le fichier `env/dev` devra ensuite contenir :

```env
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=<mot_de_passe_root_mariadb>
```

!!! note "Recommandation"
    Pour un environnement pédagogique simple, l'utilisation du compte `root` MariaDB avec mot de passe est acceptable afin de simplifier la procédure.

    Pour un environnement plus sécurisé, il est préférable de créer un compte administrateur dédié à Forge, par exemple `forge_admin`, et de l'utiliser dans `DB_ADMIN_LOGIN` / `DB_ADMIN_PWD`.

### 6. Installer Forge avec pipx

```bash
pipx install forge-mvc
forge --version
```

Si `forge` n'est pas trouvé après l'installation :

```bash
pipx ensurepath
exec $SHELL -l
forge --version
```

---

## Partie 2 — Construire l'application starter

## Présentation rapide

Le starter construit une application de carnet de contacts avec :

- une liste de contacts enrichie par leur ville ;
- un formulaire Contact avec `<select name="ville_id">` ;
- une page détail Contact ;
- une liste simple des villes ;
- un script de seed pour les villes de test ;
- des requêtes SQL visibles dans le modèle applicatif.

```mermaid
flowchart LR
    A["Contact"] -->|"ville_id nullable"| B["Ville"]
    C["contact_model.py"] -->|"LEFT JOIN visible"| A
    C --> B
    D["relations.json"] -->|"many_to_one"| A
```

## Générer le starter

Depuis un projet Forge vierge ou préparé :

Vérifier d'abord que `env/dev` contient les identifiants administrateur MariaDB :

```env
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=<mot_de_passe_root_mariadb>
```

!!! note "Compte administrateur MariaDB"
    La procédure utilise `root` avec mot de passe. Pour un environnement plus sécurisé, remplacer `root` par un compte dédié, par exemple `forge_admin`.

```bash
forge doctor
forge starter:build 3 --dry-run
forge starter:build 3 --init-db
python scripts/seed_villes.py
```

Alias équivalents :

```bash
forge starter:build carnet
forge starter:build carnet-contacts
```

`--init-db` lance explicitement l'initialisation MariaDB. Sans cette option, la base doit déjà être prête.

`--force` reconstruit les fichiers du starter 3 et le bloc de routes marqué. Il préserve les fichiers manuels d'entité comme `contact.py`, `ville.py` et les `__init__.py` existants.

## Modèle généré

Entités :

```text
Ville
Contact
```

Relation globale :

```text
Contact.ville_id -> Ville.id
```

Colonnes SQL importantes :

| Entité | Champs Python | Colonnes SQL |
|---|---|---|
| `Ville` | `id`, `nom`, `code_postal` | `VilleId`, `Nom`, `CodePostal` |
| `Contact` | `id`, `nom`, `prenom`, `email`, `telephone`, `ville_id` | `ContactId`, `Nom`, `Prenom`, `Email`, `Telephone`, `VilleId` |

`ville_id` est nullable pour permettre :

```sql
ON DELETE SET NULL
```

## JSON Et Relations

Le starter injecte deux JSON canoniques :

```text
mvc/entities/ville/ville.json
mvc/entities/contact/contact.json
```

Il injecte aussi la source canonique relationnelle :

```text
mvc/entities/relations.json
```

Forge génère ensuite :

```text
mvc/entities/ville/ville.sql
mvc/entities/contact/contact.sql
mvc/entities/relations.sql
```

??? example "Relation générée"

    ```json
    {
      "name": "contact_ville",
      "type": "many_to_one",
      "from_entity": "Contact",
      "to_entity": "Ville",
      "from_field": "ville_id",
      "to_field": "id",
      "foreign_key_name": "fk_contact_ville",
      "on_delete": "SET NULL",
      "on_update": "CASCADE"
    }
    ```

## SQL Visible

Le modèle `mvc/models/contact_model.py` utilise une jointure visible :

```python
SELECT
    contact.ContactId,
    contact.Nom,
    contact.Prenom,
    contact.Email,
    contact.Telephone,
    contact.VilleId,
    ville.Nom AS VilleNom,
    ville.CodePostal AS VilleCodePostal
FROM contact
LEFT JOIN ville ON ville.VilleId = contact.VilleId
ORDER BY contact.Nom, contact.Prenom
```

Il n'y a pas d'ORM implicite : le modèle applicatif porte explicitement les requêtes nécessaires à l'écran.

## Fichiers Créés

```text
mvc/entities/ville/
mvc/entities/contact/
mvc/entities/relations.json
mvc/entities/relations.sql
mvc/controllers/contact_controller.py
mvc/controllers/ville_controller.py
mvc/models/contact_model.py
mvc/models/ville_model.py
mvc/forms/contact_form.py
mvc/views/layouts/app.html
mvc/views/contact/index.html
mvc/views/contact/form.html
mvc/views/contact/show.html
mvc/views/ville/index.html
scripts/seed_villes.py
```

## Routes

```text
GET   /contacts
GET   /contacts/new
POST  /contacts
GET   /contacts/{id}
GET   /contacts/{id}/edit
POST  /contacts/{id}
POST  /contacts/{id}/delete
GET   /villes
```

Les routes sont injectées entre marqueurs :

```python
# forge-starter:carnet-contacts:start
# ...
# forge-starter:carnet-contacts:end
```

Elles sont publiques et sans CSRF automatique, car ce starter ne met pas en place d'authentification ni de session utilisateur.

!!! warning "Choix pédagogique — pas une bonne pratique générale"
    Le starter 3 est volontairement public pour rester centré sur les relations entre entités. Il ne traite pas encore l'authentification.
    Dans une application réelle, les routes d'écriture (`POST /contacts`, `POST /contacts/{id}`, `POST /contacts/{id}/delete`, `POST /villes`) devront être protégées et la protection CSRF conservée.

## Données De Test

Après génération :

```bash
python scripts/seed_villes.py
```

Le script insère de manière idempotente :

| Ville | Code postal |
|---|---|
| Dreux | 28100 |
| Chartres | 28000 |
| Paris | 75000 |
| Lyon | 69000 |
| Nantes | 44000 |

## Vérification finale

```bash
forge check:model
forge routes:list
python app.py
```

Ouvrir :

```text
https://localhost:8000/contacts
https://localhost:8000/villes
```

Tester :

1. créer un contact avec ville ;
2. afficher son détail ;
3. modifier sa ville ;
4. supprimer le contact ;
5. vérifier la liste des villes.

## Suite pédagogique

Le many-to-many explicite avec `Groupe` et `ContactGroupe` reste une évolution possible du parcours. Il doit rester modélisé par une entité pivot explicite et deux relations `many_to_one`, pas par une magie ORM.

## Reconstruction

Le fichier court de reconstruction est disponible dans [starters/03-carnet-contacts/rebuild.md](starters/03-carnet-contacts/rebuild.md).

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
