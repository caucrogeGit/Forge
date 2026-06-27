# Configurer les comptes MariaDB d'un projet Forge

Ce document fixe la direction recommandée pour configurer MariaDB dans un
projet Forge. Il complète [Préparer MariaDB](mariadb.md) (installation et
initialisation) en détaillant la **séparation des comptes**.

L'objectif est de ne pas utiliser `root` comme utilisateur applicatif, ni même
comme compte courant dans `env/dev`. Forge distingue clairement :

- `root`, administration serveur MariaDB, secours uniquement ;
- `forge_admin`, administration du projet Forge ;
- `forge_app`, utilisateur applicatif utilisé par l'application au runtime.

Cette séparation évite de donner à l'application des droits trop larges, et
correspond au check **Sécurité prod** de [`forge doctor`](../deployment/production-checklist.md).

---

## 1. Principe général

Pour un projet Forge nommé ici `forge_db`, on utilise :

```text
root         → administration MariaDB globale, utilisé seulement avec sudo mariadb
forge_admin  → création / migration / structure de la base Forge
forge_app    → lecture et écriture applicative uniquement
```

Dans `env/dev`, on évite donc `DB_ADMIN_LOGIN=root` et on préfère :

```env
DB_ADMIN_LOGIN=forge_admin
DB_APP_LOGIN=forge_app
```

---

## 2. Rôle des comptes

### `root`

Réservé aux interventions d'administration serveur :

- installation MariaDB ;
- réparation de comptes ;
- récupération d'accès ;
- création initiale de l'utilisateur `forge_admin` ;
- diagnostic serveur.

Il ne doit pas être utilisé par l'application Forge.

```bash
sudo mariadb
```

### `forge_admin`

Compte technique utilisé par Forge pour administrer la base du projet. Il peut :
créer la base, créer/ajuster l'utilisateur applicatif `forge_app`, créer et
modifier les tables, appliquer les migrations, créer les index, gérer les
contraintes.

Il ne doit **pas** recevoir tous les droits globaux de MariaDB.

### `forge_app`

Utilisateur de l'application au runtime. Il peut uniquement lire, insérer,
modifier et supprimer des données. Il ne doit **pas** pouvoir : créer des
utilisateurs, supprimer des tables, modifier la structure, administrer
MariaDB, ni accéder aux autres bases.

---

## 3. Variables `env/dev` recommandées

```env
# Administration MariaDB du projet
DB_ADMIN_HOST=localhost
DB_ADMIN_PORT=3306
DB_ADMIN_LOGIN=forge_admin
DB_ADMIN_PWD=mot_de_passe_long_admin_local

# Base projet
DB_NAME=forge_db
DB_CHARSET=utf8mb4
DB_COLLATION=utf8mb4_unicode_ci

# Utilisateur applicatif du projet
DB_APP_HOST=localhost
DB_APP_PORT=3306
DB_APP_LOGIN=forge_app
DB_APP_PWD=mot_de_passe_long_app_local
DB_POOL_SIZE=5
```

Les mots de passe doivent être propres au projet et ne pas être réutilisés
ailleurs.

---

## 4. Création complète depuis `root`

```bash
sudo mariadb
```

```sql
CREATE DATABASE IF NOT EXISTS forge_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'forge_admin'@'localhost'
  IDENTIFIED BY 'mot_de_passe_long_admin_local';

CREATE USER IF NOT EXISTS 'forge_app'@'localhost'
  IDENTIFIED BY 'mot_de_passe_long_app_local';

GRANT CREATE USER ON *.*
  TO 'forge_admin'@'localhost';

GRANT CREATE, ALTER, DROP, INDEX, REFERENCES,
      SELECT, INSERT, UPDATE, DELETE
  ON forge_db.*
  TO 'forge_admin'@'localhost'
  WITH GRANT OPTION;

GRANT SELECT, INSERT, UPDATE, DELETE
  ON forge_db.*
  TO 'forge_app'@'localhost';
```

---

## 5. Pourquoi ne pas donner `ALL PRIVILEGES ON *.*`

```sql
GRANT ALL PRIVILEGES ON *.* TO 'forge_admin'@'localhost' WITH GRANT OPTION;
```

Cette commande est trop large : elle donne à `forge_admin` un pouvoir proche
de `root`. Pour Forge, ce n'est pas nécessaire, `forge_admin` doit administrer
la base du projet, pas tout le serveur MariaDB.

---

## 6. Droits recommandés pour `forge_admin`

Droits projet :

```sql
GRANT CREATE, ALTER, DROP, INDEX, REFERENCES,
      SELECT, INSERT, UPDATE, DELETE
  ON forge_db.*
  TO 'forge_admin'@'localhost'
  WITH GRANT OPTION;
```

Droit global minimal nécessaire pour créer l'utilisateur applicatif :

```sql
GRANT CREATE USER ON *.* TO 'forge_admin'@'localhost';
```

Ce droit global est à surveiller : utile pour `forge db:init`, il ne doit pas
être confondu avec un accès root complet.

---

## 7. Droits recommandés pour `forge_app`

```sql
GRANT SELECT, INSERT, UPDATE, DELETE
  ON forge_db.*
  TO 'forge_app'@'localhost';
```

`forge_app` ne doit **pas** recevoir : `CREATE`, `ALTER`, `DROP`, `INDEX`,
`REFERENCES`, `CREATE USER`, `GRANT OPTION`.

---

## 8. Vérifier les droits

```sql
SHOW GRANTS FOR 'forge_admin'@'localhost';
SHOW GRANTS FOR 'forge_app'@'localhost';
```

Attendu pour `forge_admin` :

```text
GRANT CREATE USER ON *.* TO `forge_admin`@`localhost`
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, REFERENCES, INDEX, ALTER
  ON `forge_db`.* TO `forge_admin`@`localhost` WITH GRANT OPTION
```

Attendu pour `forge_app` :

```text
GRANT SELECT, INSERT, UPDATE, DELETE ON `forge_db`.* TO `forge_app`@`localhost`
```

---

## 9. Tester les connexions

```bash
mariadb -u forge_admin -p forge_db   # puis : SHOW TABLES;
mariadb -u forge_app   -p forge_db   # puis : SHOW TABLES;
```

---

## 10. Tester que `forge_app` ne peut pas modifier la structure

Connecté avec `forge_app` :

```sql
CREATE TABLE test_forbidden (id INT PRIMARY KEY);
```

Résultat attendu (refus normal et souhaité) :

```text
ERROR 1142 ... CREATE command denied
```

---

## 11. Réinitialiser les mots de passe

```sql
ALTER USER 'forge_admin'@'localhost' IDENTIFIED BY 'nouveau_mot_de_passe_admin';
ALTER USER 'forge_app'@'localhost'   IDENTIFIED BY 'nouveau_mot_de_passe_app';
```

Mettre ensuite `env/dev` à jour.

---

## 12. Supprimer proprement les comptes d'un projet

À utiliser seulement si le projet doit être détruit, **supprime la base et
les comptes** :

```sql
DROP USER IF EXISTS 'forge_app'@'localhost';
DROP USER IF EXISTS 'forge_admin'@'localhost';
DROP DATABASE IF EXISTS forge_db;
```

---

## 13. Variante stricte pour la production

En production, `forge_admin` ne doit pas être utilisé par l'application :

```text
forge_admin  → utilisé uniquement pendant les migrations
forge_app    → utilisé par l'application en production
```

Après application des migrations, l'application tourne uniquement avec
`forge_app`. On peut même ne pas stocker le mot de passe `forge_admin` dans le
fichier d'environnement courant de l'application, mais le réserver à une
procédure d'exploitation. Voir la
[checklist de production](../deployment/production-checklist.md).

---

## 14. Résumé

| Compte | Usage | Droits |
|---|---|---|
| `root` | secours et administration serveur | tous les droits, hors application |
| `forge_admin` | création base, migrations, structure | structure + données sur `forge_db.*`, `CREATE USER` minimal |
| `forge_app` | application runtime | `SELECT`, `INSERT`, `UPDATE`, `DELETE` seulement |

```text
root ne sert pas à faire tourner Forge.
forge_admin prépare et maintient la base.
forge_app exécute l'application avec des droits limités.
```
