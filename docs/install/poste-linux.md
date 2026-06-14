# Installer Forge sur Linux et créer un projet

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page décrit le parcours complet pour préparer un poste Linux puis créer un nouveau projet Forge.

Elle vise Debian, Ubuntu, Linux Mint et les distributions compatibles avec `apt`.
Pour les autres distributions, le principe reste le même, seuls les noms de paquets système changent.

---

## Objectif

Aller d'un poste Linux propre à un projet Forge qui démarre en développement avec MariaDB.

À la fin de ce parcours, vous disposez :

* des outils système nécessaires ;
* de Forge installé avec `pipx` ;
* de Git configuré sur le poste ;
* de MariaDB installé et démarré ;
* d'un nouveau projet Forge créé ;
* d'un dépôt Git local versionné et poussé sur GitHub ;
* d'`env/dev` configuré et cohérent avec MariaDB ;
* de la base initialisée et des migrations appliquées ;
* du serveur de développement lancé.

---

## Vue d'ensemble

Cette page est organisée en deux parties.

La première prépare le poste Linux.
Elle se fait une seule fois sur une machine neuve.

La seconde crée et configure un projet Forge.
Elle se refait pour chaque nouveau projet.

Si Forge, Git, `pipx` et MariaDB sont déjà installés sur votre poste, vous pouvez aller directement à la partie **Créer et configurer un projet Forge**.

---

## Ce que cette page installe

| Partie | Domaine | À refaire ? |
|---|---|---|
| Préparer le poste Linux | système, `pipx`, Forge, Git global, MariaDB Server | une fois par machine |
| Créer et configurer un projet Forge | `forge new`, `env/dev`, Git local, GitHub, base MariaDB, migrations, `forge run` | à chaque nouveau projet |

Les pages [Préparer MariaDB](mariadb.md) et [Comptes MariaDB d'un projet](mariadb-comptes.md) restent des références pour approfondir ou dépanner.
Vous n'avez pas besoin d'y aller pour terminer une installation standard.

---

## Prérequis

* Un poste Linux à jour, avec un accès `sudo`.
* Une connexion réseau.
* Un compte GitHub si vous souhaitez héberger le dépôt distant.

---

## Partie 1 — Préparer le poste Linux

Cette partie prépare la machine.
Elle se fait une seule fois sur un poste neuf, ou lorsqu'un outil système manque.

### 1. Mettre à jour le système

```bash
sudo apt update
sudo apt upgrade -y
```

---

### 2. Installer les paquets nécessaires

```bash
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  pipx \
  git \
  openssl \
  build-essential \
  python3-dev \
  libmariadb-dev \
  pkg-config
```

Le paquet `libmariadb-dev` fournit `mariadb_config`, requis par le connecteur Python `mariadb`.
Vérifiez sa présence :

```bash
mariadb_config --version
```

Si cette commande échoue, l'installation de Forge peut échouer avec une erreur du type `mariadb_config not found`.

---

### 3. Activer pipx

`pipx` installe la commande `forge` dans un environnement isolé du Python système.

```bash
pipx ensurepath
exec $SHELL -l
```

Vérifiez que `pipx` répond :

```bash
pipx --version
```

---

### 4. Installer Forge

Forge est publié sur PyPI sous la version :

```text
{{forge_version}}
```

Comme il s'agit d'une version bêta, l'option `--pre` est transmise à `pip` :

```bash
pipx install --pip-args="--pre" forge-mvc
```

Vérifiez l'installation :

```bash
forge --version
```

Pour mettre à jour Forge plus tard :

```bash
pipx upgrade --pip-args="--pre" forge-mvc
```

---

### 5. Configurer Git sur le poste

Cette configuration identifie l'auteur des commits sur la machine.
Elle est globale et ne concerne pas encore un projet précis.

`forge new` crée un commit initial : Git doit donc connaître votre identité, sinon ce commit échoue.

```bash
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@example.com"
git config --global init.defaultBranch main
```

Vérifiez :

```bash
git config --global --list
```

---

### 6. Installer et démarrer MariaDB

MariaDB Server appartient à la préparation du poste.
Il n'a pas besoin d'être réinstallé à chaque projet.

```bash
sudo apt install -y \
  mariadb-server \
  mariadb-client
```

Démarrez MariaDB et activez-le au démarrage de la machine :

```bash
sudo systemctl enable --now mariadb
```

Vérifiez que le service est actif :

```bash
systemctl status mariadb --no-pager
```

---

### 7. Vérifier l'accès administrateur MariaDB local

Sur Debian, Ubuntu et leurs dérivées, l'administration locale se fait souvent avec le compte système `root`, via `sudo`.

```bash
sudo mariadb
```

Vous devez obtenir une invite :

```text
MariaDB [(none)]>
```

Quittez ensuite la console :

```sql
exit;
```

Le compte `root` MariaDB sert uniquement à l'administration locale via `sudo mariadb`.
Il ne sert pas à faire tourner l'application.

---

### 8. Vérifier que le poste est prêt

Sur le poste, ces commandes doivent répondre :

```bash
forge --version
pipx --version
git --version
mariadb_config --version
systemctl status mariadb --no-pager
```

Si ces commandes fonctionnent, le poste est prêt pour créer des projets Forge.

---

## Partie 2 — Créer et configurer un projet Forge

Cette partie se refait pour chaque nouveau projet Forge.

Elle part du principe que le poste Linux est déjà prêt : Forge, Git, `pipx` et MariaDB sont installés.

### 9. Créer un nouveau projet Forge

Choisissez un nom de projet.
Remplacez `NOM_PROJET` par votre nom réel, par exemple `boutique`, `blog`, `welcome-forge` ou `gestion-stock`.

```bash
forge new NOM_PROJET
cd NOM_PROJET
```

`forge new` prépare un projet complet : squelette, environnement Python, certificat de développement, puis un dépôt Git avec un commit initial.

Activez l'environnement Python du projet :

```bash
source .venv/bin/activate
```

---

### 10. Lire le fichier env/dev généré

`forge new` a généré le fichier de configuration de développement :

```text
env/dev
```

Ce fichier contient les valeurs réelles de votre projet.

Ne déduisez pas les noms MariaDB à partir d'un exemple.
Lisez directement les valeurs générées dans `env/dev`, en particulier :

* `DB_NAME` ;
* `DB_APP_LOGIN` ;
* `DB_ADMIN_LOGIN`.

Ces valeurs dépendent du projet créé par `forge new` et doivent être reprises exactement dans les commandes MariaDB.

`APP_NAME` indique le nom applicatif du projet.

Exemple générique, juste après la création :

```env
APP_NAME=NOM_PROJET
APP_ROUTES_MODULE=mvc.routes

DB_ADMIN_HOST=localhost
DB_ADMIN_PORT=3306
DB_ADMIN_LOGIN=forge_admin
DB_ADMIN_PWD=

DB_NAME=NOM_BASE
DB_CHARSET=utf8mb4
DB_COLLATION=utf8mb4_unicode_ci

DB_APP_HOST=localhost
DB_APP_PORT=3306
DB_APP_LOGIN=NOM_UTILISATEUR_APP
DB_APP_PWD=
DB_POOL_SIZE=5
```

Points importants :

* `DB_ADMIN_LOGIN` est le compte d'administration utilisé par les commandes CLI de provisioning.
* `DB_ADMIN_PWD` est vide au départ et doit être complété.
* `DB_NAME` dépend du projet généré.
* `DB_APP_LOGIN` peut reprendre le nom du projet, mais la valeur exacte à utiliser est celle présente dans `env/dev`.
* `DB_APP_PWD` est vide au départ et doit être complété.
* Les comptes MariaDB créés plus loin doivent correspondre exactement à ce fichier.

```text
Ne copiez pas un nom de projet d'exemple sans vérifier votre propre env/dev.
```

---

### 11. Vérifier le dépôt Git local du projet

`forge new` initialise en général le dépôt Git et crée un premier commit.
Vérifiez d'abord l'état :

```bash
git status
git log --oneline -5
```

Selon la version de Forge et le starter utilisé, le dépôt Git peut déjà être initialisé.
Vérifiez d'abord avec `git status`.

Si aucun dépôt n'est initialisé, ou si aucun commit n'a été créé, faites-le vous-même :

```bash
git init
git add .
git commit -m "Initialisation du projet Forge"
```

Ne refaites pas de commit initial si Forge en a déjà créé un.

---

### 12. Créer ou associer un dépôt GitHub

Le dépôt Git local et le dépôt GitHub sont deux choses distinctes.
Le dépôt local vit dans votre projet.
Le dépôt GitHub est le dépôt distant qui héberge votre code.

Choisissez l'une des deux options.

#### Option A — Avec l'interface GitHub

1. Créez un nouveau dépôt vide sur GitHub.
2. N'ajoutez ni README, ni `.gitignore`, ni licence si votre projet local en contient déjà.
3. Copiez l'URL SSH ou HTTPS du dépôt.
4. Vérifiez qu'aucun remote `origin` n'existe déjà :

```bash
git remote -v
```

Si un remote `origin` est déjà présent, ne le recréez pas : vérifiez son URL avec `git remote -v`.

5. Associez le dépôt local et poussez :

```bash
git remote add origin git@github.com:UTILISATEUR/NOM_DU_DEPOT.git
git branch -M main
git push -u origin main
```

Remplacez `UTILISATEUR` et `NOM_DU_DEPOT` par vos valeurs réelles.

#### Option B — Avec GitHub CLI, si installé

GitHub CLI (`gh`) n'est pas obligatoire.
Cette option suppose que `gh` est installé et authentifié.

```bash
gh repo create NOM_DU_DEPOT --private --source=. --remote=origin --push
```

Pour un dépôt public :

```bash
gh repo create NOM_DU_DEPOT --public --source=. --remote=origin --push
```

---

### 13. Créer la base et les comptes MariaDB du projet

Cette étape appartient au projet.
Elle se refait pour chaque nouveau projet Forge, car chaque projet a sa base et son compte applicatif.

Ouvrez une console MariaDB administrateur :

```bash
sudo mariadb
```

Forge sépare trois niveaux d'accès :

```text
root                   → administration locale du serveur, avec sudo
forge_admin            → préparation de la base et application des migrations
NOM_UTILISATEUR_APP    → accès applicatif au runtime, en lecture/écriture
```

`forge db:init` se connecte avec le compte indiqué dans `DB_ADMIN_LOGIN`.
Ce compte doit déjà exister : Forge ne le crée pas.
Le compte recommandé est `forge_admin`.

Dans un projet généré, `DB_APP_LOGIN` peut reprendre le nom du projet.
La valeur exacte à utiliser est celle présente dans `env/dev`.

Remplacez :

* `NOM_BASE` par la valeur réelle de `DB_NAME` ;
* `NOM_UTILISATEUR_APP` par la valeur réelle de `DB_APP_LOGIN` ;
* `mot_de_passe_admin_local` par le mot de passe choisi pour `DB_ADMIN_PWD` ;
* `mot_de_passe_app_local` par le mot de passe choisi pour `DB_APP_PWD`.

Exécutez ensuite les commandes SQL suivantes :

```sql
CREATE DATABASE IF NOT EXISTS `NOM_BASE`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'forge_admin'@'localhost'
  IDENTIFIED BY 'mot_de_passe_admin_local';

CREATE USER IF NOT EXISTS 'NOM_UTILISATEUR_APP'@'localhost'
  IDENTIFIED BY 'mot_de_passe_app_local';

GRANT CREATE USER ON *.* TO 'forge_admin'@'localhost';

GRANT CREATE, ALTER, DROP, INDEX, REFERENCES,
      SELECT, INSERT, UPDATE, DELETE
ON `NOM_BASE`.* TO 'forge_admin'@'localhost'
WITH GRANT OPTION;

GRANT SELECT, INSERT, UPDATE, DELETE
ON `NOM_BASE`.* TO 'NOM_UTILISATEUR_APP'@'localhost';

FLUSH PRIVILEGES;
```

Quittez ensuite la console :

```sql
exit;
```

Précisions :

* Si `DB_NAME` contient un tiret, les backticks sont indispensables : `` `mon-projet` ``.
* Si `DB_APP_LOGIN` contient un tiret, gardez les quotes SQL : `'mon-projet'@'localhost'`.

Pour la justification des droits et leur vérification, voir [Comptes MariaDB d'un projet](mariadb-comptes.md).

---

### 14. Compléter env/dev

Renseignez maintenant les mots de passe dans `env/dev`, à l'identique des comptes créés.

Exemple générique, cohérent avec les commandes SQL ci-dessus :

```env
DB_ADMIN_HOST=localhost
DB_ADMIN_PORT=3306
DB_ADMIN_LOGIN=forge_admin
DB_ADMIN_PWD=mot_de_passe_admin_local

DB_NAME=NOM_BASE
DB_CHARSET=utf8mb4
DB_COLLATION=utf8mb4_unicode_ci

DB_APP_HOST=localhost
DB_APP_PORT=3306
DB_APP_LOGIN=NOM_UTILISATEUR_APP
DB_APP_PWD=mot_de_passe_app_local
DB_POOL_SIZE=5
```

`NOM_BASE` et `NOM_UTILISATEUR_APP` ne sont pas des valeurs à garder telles quelles.
Ils doivent être remplacés par les valeurs présentes dans votre propre fichier `env/dev`.

Les mots de passe d'`env/dev` doivent correspondre exactement à ceux définis dans MariaDB.

---

### 15. Vérifier le projet avec forge doctor

```bash
forge doctor
```

Cette commande diagnostique le projet et signale les points à corriger avant l'initialisation.

---

### 16. Initialiser la base avec forge db:init

```bash
forge db:init
```

Cette commande prépare la base du projet et crée la table technique `forge_migrations`, qui mémorise les migrations déjà appliquées.

Si la commande s'arrête sur :

```text
[ERREUR] Connexion MariaDB admin impossible. Vérifiez DB_ADMIN_* dans env/dev.
```

Forge n'a pas pu se connecter avec le compte indiqué dans `DB_ADMIN_LOGIN`.
À vérifier :

* le compte existe dans MariaDB ;
* le mot de passe correspond à `DB_ADMIN_PWD` ;
* `DB_ADMIN_HOST` est correct, généralement `localhost` ;
* `DB_ADMIN_PORT` est correct, généralement `3306` ;
* le compte a été créé avec le même hôte que celui utilisé par Forge ;
* `DB_ADMIN_PWD` n'est pas resté vide dans `env/dev`.

Sur Debian, Ubuntu et leurs dérivées, le compte `root` MariaDB utilise souvent l'authentification `unix_socket`, ce qui peut échouer en connexion TCP.
Le parcours recommandé reste donc de créer un compte `forge_admin`.

---

### 17. Appliquer les migrations

```bash
forge db:apply
```

Cette commande applique le SQL du projet sur la base.
Comme `db:init`, elle modifie la structure : elle se connecte avec `DB_ADMIN_*`, pas avec le compte applicatif.

Vérifiez l'état des migrations :

```bash
forge migration:status
```

---

### 18. Lancer le serveur de développement

```bash
forge run
```

Par défaut, `forge run` démarre le projet en mode développement.

---

### 19. Vérification finale du projet

Dans le projet Forge :

```bash
forge doctor
forge migration:status
forge run
```

Si ces commandes passent, le projet est installé et fonctionnel.
Les étapes 16 et 17 (`forge db:init`, `forge db:apply`) restent les commandes qui préparent réellement la base ; elles n'ont pas à être relancées ici comme simples vérifications.

---

## Poursuivre

* [Préparer MariaDB](mariadb.md) : installation détaillée et dépannage de MariaDB.
* [Comptes MariaDB d'un projet](mariadb-comptes.md) : séparation des comptes, droits et vérifications.
* [Migrations SQL](../features/migrations.md) : cycle complet des migrations Forge.
* [Installer les opt-ins Forge](opt-ins.md) : ajouter les extensions officielles.
* [Préparer un déploiement en production](production.md) : prérequis serveur, WSGI et reverse proxy.
* [Installer Forge depuis les sources GitHub](github.md) : travailler depuis le dépôt source pour contribuer.