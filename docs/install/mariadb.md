# Préparer MariaDB pour Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page explique comment préparer MariaDB pour un projet Forge sur un poste de développement.

Elle complète l’installation de Forge sur Debian, Ubuntu et leurs dérivées.
Une fois MariaDB installé, Forge peut créer la base du projet, préparer les comptes nécessaires et appliquer les migrations SQL.

---

## Objectif

À la fin de cette étape, le poste doit disposer :

* d’un serveur MariaDB installé ;
* d’un service MariaDB démarré ;
* d’un accès administrateur local ;
* d’un projet Forge capable d’exécuter les commandes de base de données.

Les commandes Forge concernées sont principalement :

```bash
forge db:init
forge db:apply
forge migration:status
```

---

## Installer MariaDB

Mettre à jour la liste des paquets :

```bash
sudo apt update
```

Installer MariaDB Server, le client MariaDB et les dépendances nécessaires au connecteur Python :

```bash
sudo apt install -y \
  mariadb-server \
  mariadb-client \
  libmariadb-dev \
  pkg-config
```

Démarrer MariaDB et l’activer au démarrage de la machine :

```bash
sudo systemctl enable --now mariadb
```

Vérifier que le service est actif :

```bash
systemctl status mariadb --no-pager
```

---

## Vérifier l’accès administrateur local

Sur Debian, Ubuntu et Linux Mint, l’accès administrateur MariaDB se fait souvent avec le compte système `root`, via `sudo`.

Ouvrir une console MariaDB administrateur :

```bash
sudo mariadb
```

Vous devez obtenir une invite MariaDB :

```text
MariaDB [(none)]>
```

Quitter ensuite la console :

```sql
exit;
```

---

## Vérifier la dépendance native MariaDB

Forge utilise le connecteur Python `mariadb`.

Ce connecteur peut avoir besoin de l’outil système `mariadb_config` pour s’installer correctement.
Cet outil est fourni par `libmariadb-dev`.

Vérifier sa présence :

```bash
mariadb_config --version
```

Si cette commande affiche une version, la dépendance native MariaDB est prête.

---

## Préparer les comptes du projet

Forge distingue deux niveaux d’accès à la base :

* un compte d’administration du projet ;
* un compte applicatif utilisé par l’application.

Cette séparation évite d’utiliser `root` comme compte applicatif et limite les droits utilisés par l’application au quotidien.

Le détail complet de cette configuration est donné dans la page :

[Configurer les comptes MariaDB d’un projet Forge](mariadb-comptes.md)

Pour un projet de développement, le principe recommandé est le suivant :

```text
root         → administration locale du serveur MariaDB
forge_admin  → création et migration de la base du projet
forge_app    → accès applicatif en lecture/écriture
```

---

## Configurer le projet Forge

Dans le projet Forge, les variables de connexion se trouvent dans :

```text
env/dev
```

Exemple de configuration :

```env
DB_ADMIN_LOGIN=forge_admin
DB_ADMIN_PWD=<mot_de_passe_admin_du_projet>

DB_NAME=mon_projet
DB_APP_LOGIN=forge_app
DB_APP_PWD=<mot_de_passe_applicatif>
```

Les mots de passe doivent être propres au poste ou au projet.

Ils ne doivent pas être committés dans Git.

---

## Initialiser la base du projet

Depuis le dossier du projet Forge :

```bash
source .venv/bin/activate
```

Vérifier d’abord l’état du projet :

```bash
forge doctor
```

Initialiser la base :

```bash
forge db:init
```

Appliquer les migrations disponibles :

```bash
forge db:apply
```

Vérifier l’état des migrations :

```bash
forge migration:status
```

---

## Rôle des commandes Forge

### `forge db:init`

Prépare la base du projet.

Cette commande initialise la structure attendue par Forge et crée notamment la table technique :

```text
forge_migrations
```

Cette table permet à Forge de savoir quelles migrations SQL ont déjà été appliquées.

### `forge db:apply`

Applique les migrations SQL du projet.

Les fichiers de migration sont lus dans :

```text
mvc/migrations/
```

Forge applique les migrations locales en attente dans l’ordre croissant de version.

### `forge migration:status`

Affiche les migrations connues et leur état.

Cette commande permet de vérifier ce qui est déjà appliqué et ce qui reste en attente.

---

## Travailler avec les migrations SQL

Forge garde les migrations SQL visibles.

Le développeur peut donc relire, adapter et versionner les fichiers SQL générés avant de les appliquer.

Le workflow complet est détaillé ici :

[Migrations SQL](../features/migrations.md)

Forge peut aider à produire des migrations, mais il ne remplace pas la relecture humaine du SQL.

---

## Point de vigilance sur les migrations

MariaDB ne garantit pas toujours un rollback complet des opérations DDL.

Une migration qui modifie la structure d’une table doit donc être relue avant application, surtout en production ou sur une base contenant des données importantes.

Forge arrête l’exécution au premier échec, mais ne prétend pas annuler automatiquement tout ce que MariaDB a déjà exécuté.

---

## Vérification finale

À la fin de la préparation MariaDB, les commandes suivantes doivent fonctionner :

```bash
mariadb_config --version
systemctl status mariadb --no-pager
```

Dans le projet Forge :

```bash
forge doctor
forge db:init
forge db:apply
forge migration:status
```

---

## Poursuivre la configuration

MariaDB est maintenant prêt pour un projet Forge local.

Pour continuer l’installation selon votre besoin, poursuivez avec les pages suivantes :

* [Configurer les comptes MariaDB d’un projet Forge](mariadb-comptes.md) : créer proprement les comptes `forge_admin` et `forge_app`.
* [Migrations SQL](../features/migrations.md) : comprendre le cycle complet des migrations Forge.
* [Installation sur Debian, Ubuntu et leurs dérivées](poste-linux.md) : revenir à l’installation générale du poste Linux.
* [Déploiement production](production.md) : préparer un serveur destiné à héberger une application Forge.
