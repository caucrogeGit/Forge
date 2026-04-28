# Préparer MariaDB

[Accueil](index.html){ .md-button } <button class="md-button" onclick="window.history.back()">← Retour</button>

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

En Forge 1.0.1, le compte applicatif reste compatible avec le flux pédagogique
`db:init` puis `db:apply`. En production, utilisez un compte de migration séparé
et un compte applicatif limité à `SELECT`, `INSERT`, `UPDATE`, `DELETE`.
