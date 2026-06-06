# Préparer MariaDB

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Forge utilise MariaDB pour les applications générées et les starters.

## Installer MariaDB

```bash
sudo apt update
sudo apt install -y mariadb-server mariadb-client libmariadb-dev pkg-config
sudo systemctl enable --now mariadb
```

## Vérifier l'accès administrateur

```bash
mariadb -u root -p
```

Dans `env/dev`, configurez ensuite les variables `DB_ADMIN_*` et `DB_APP_*`.

```env
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=<mot_de_passe_root_mariadb>

DB_NAME=mon_projet
DB_APP_LOGIN=mon_projet_app
DB_APP_PWD=<mot_de_passe_applicatif>
```

## Initialiser la base du projet

```bash
forge db:init
forge db:apply
```

`forge db:init` crée aussi la table technique `forge_migrations` avec
`CREATE TABLE IF NOT EXISTS`. `forge migration:make` crée des fichiers SQL vides
dans `mvc/migrations/`; avec `--from-entity`, elle peut aussi copier le SQL déjà
généré d'une entité, et avec `--from-entities`, concaténer tous les SQL
d'entités générés. Avec `--from-diff`, elle peut générer une migration prudente
pour une table absente ou des colonnes manquantes, mais refuse les colonnes
modifiées ou extra. Le développeur relit et adapte toujours le SQL lui-même.
`forge migration:status` compare ensuite ces fichiers avec les lignes
enregistrées. `forge migration:diff --entity <Entite>` compare en lecture seule
le JSON d'entité avec les colonnes MariaDB. `forge migration:apply` applique les
migrations locales en attente dans l'ordre croissant de version.

Le workflow complet est détaillé dans [Migrations SQL](../features/migrations.md).

MariaDB ne garantit pas un rollback complet des DDL. Relisez les migrations SQL
avant application ; Forge arrête au premier échec sans prétendre annuler tout ce
que MariaDB a déjà exécuté.

En Forge 1.3.0, le compte applicatif reste compatible avec le flux pédagogique
`db:init` puis `db:apply`. En production, utilisez un compte de migration séparé
et un compte applicatif limité à `SELECT`, `INSERT`, `UPDATE`, `DELETE`.
