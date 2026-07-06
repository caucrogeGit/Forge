# ADR-033 : `forge db:apply` applique les migrations avec `DB_ADMIN_*`

## Statut

Acceptée (mise en œuvre à suivre, ticket `DB-APPLY-ADMIN-CREDS-001`).

Renforce la doctrine de séparation des comptes de [ADR-008](008-auth-audit-architecture.md) et la politique des comptes décrite dans `docs/install/mariadb-comptes.md`.
Corrige une contradiction doc/code et un défaut fonctionnel.

---

## Contexte

Forge sépare deux comptes base de données :

| Compte | Rôle voulu |
|---|---|
| `DB_ADMIN_*` (`forge_admin`) | provisioning, migrations, structure |
| `DB_APP_*` (`forge_app`) | runtime applicatif (DML seulement) |

`docs/install/mariadb-comptes.md` est explicite : `forge_app` reçoit **uniquement** `SELECT, INSERT, UPDATE, DELETE` sur la base du projet, et **ne doit pas** recevoir `CREATE`, `ALTER`, `DROP`, `INDEX`, `REFERENCES`.

Or `forge db:apply` (et `migration:status`, lecture du schéma) se connectent via un unique `_connect_db()` dans `cli/entities/migrations.py`, qui utilise les identifiants **`DB_APP_*`** :

```python
def _connect_db():
    ...
    return mariadb.connect(
        host=config.DB_APP_HOST, port=config.DB_APP_PORT,
        user=config.DB_APP_LOGIN, password=config.DB_APP_PWD, ...
    )
```

`_apply_one_migration()` exécute alors le DDL des migrations (`CREATE TABLE`, `ALTER`, `DROP`…) **sur cette connexion `forge_app`**.

Conséquences :

1. **Défaut fonctionnel.**
   Un utilisateur qui suit `mariadb-comptes.md` (`forge_app` en DML seul) voit `forge db:apply` **échouer** (`CREATE command denied to 'forge_app'`).
2. **Contradiction de doctrine.**
   Pour que `db:apply` marche, il faut élargir `forge_app` au DDL (le commentaire `DB_APP_PRIVILEGES=...,CREATE,ALTER,DROP,...` de `env/example`), ce qui contredit « `forge_app` = runtime à privilèges minimaux » et affaiblit la sécurité (le compte runtime peut modifier la structure et supprimer des tables).

`forge db:init` se connecte déjà correctement en `DB_ADMIN_*` (création base, utilisateur applicatif, grants).
L'incohérence est isolée à la chaîne migrations.

---

## Décision

**`forge db:apply`, `forge migration:status` et la lecture de schéma se connectent en `DB_ADMIN_*`.**
Les migrations sont des changements de structure, elles relèvent du compte d'administration du projet.

`_connect_db()` dans `migrations.py` lit `DB_ADMIN_HOST/PORT/LOGIN/PWD` (au lieu de `DB_APP_*`) et `DB_NAME`.
`forge_admin` détient déjà `CREATE, ALTER, DROP, INDEX, REFERENCES, SELECT, INSERT, UPDATE, DELETE` sur `forge_db.*` (cf. `mariadb-comptes.md`), donc il applique les migrations sans élargir `forge_app`.

---

## Conséquences

**Positives :**

- `forge db:apply` fonctionne avec les comptes tels que documentés (`forge_app` en DML seul) : la doc et le code redeviennent cohérents.
- `forge_app` reste **minimal** (DML) : il ne peut plus modifier la structure ni supprimer des tables.
  Gain de sécurité net.
- Le commentaire `DB_APP_PRIVILEGES=...,CREATE,ALTER,DROP,...` disparaît de `env/example` (il n'a plus de raison d'être).
- Doctrine alignée : `forge_admin` n'est utilisé que pour le provisioning et les migrations ; l'application runtime tourne en `forge_app`.

**À assumer :**

- `forge db:apply` / `migration:status` exigent désormais `DB_ADMIN_*` dans l'environnement.
  En dev c'est déjà le cas (`env/dev`).
  En production, les migrations sont exécutées au déploiement avec les identifiants admin disponibles, conformément à « `forge_admin` utilisé uniquement pendant les migrations » (variante stricte de `mariadb-comptes.md`).
- Les messages d'erreur « Vérifiez `DB_APP_*` / `DB_NAME` » deviennent « Vérifiez `DB_ADMIN_*` / `DB_NAME` ».

---

## Mise en œuvre (ticket `DB-APPLY-ADMIN-CREDS-001`)

1. Garde d'abord : test vérifiant que `_connect_db()` lit `DB_ADMIN_*` (et non `DB_APP_*`).
2. `migrations.py` : `_connect_db()` utilise `DB_ADMIN_HOST/PORT/LOGIN/PWD` ; adapter les messages d'erreur (`DB_ADMIN_*`).
3. `db_init.py` : `DEFAULT_APP_PRIVILEGES` resserré au DML (le provisioning n'accorde plus `CREATE/ALTER/DROP/INDEX/REFERENCES` à `forge_app` par défaut ; un override explicite via `DB_APP_PRIVILEGES` reste possible).
   `env/example` (squelette + dogfood) : retirer la ligne commentée `DB_APP_PRIVILEGES=...` (le runtime n'a plus besoin de DDL).
4. `docs/install/mariadb-comptes.md` : préciser que `forge_admin` applique les migrations ; confirmer `forge_app` en DML strict (déjà le cas) ; retirer toute suggestion d'élargir `forge_app` au DDL.
5. `docs/install/mariadb.md` et la doc migrations : indiquer que `db:apply` utilise `DB_ADMIN_*`.
6. Tests : mettre à jour ceux qui assertaient les identifiants ou messages `DB_APP_*` de la chaîne migrations (la plupart injectent une connexion `db=` et ne sont pas affectés).

**Validations :**

```bash
python -m pytest -x -q
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

---

## Suivi (ticket `DB-APPLY-ADMIN-CREDS-FIX-001`)

La première mise en œuvre (`DB-APPLY-ADMIN-CREDS-001`) a corrigé la chaîne `migrations.py` (`migration:apply`, `migration:status`, lecture de schéma), mais **pas** la commande `forge db:apply` elle-même, qui passe par un code distinct (`cli/entities/db_apply.py`, application du SQL des entités).
Ce chemin continuait de se connecter en `DB_APP_*` et échouait donc sur le `CREATE TABLE` des entités dès que `forge_app` était resserré au DML.

Le ticket `DB-APPLY-ADMIN-CREDS-FIX-001` aligne `db_apply.py` sur la même décision : `load_db_apply_config()` lit `DB_ADMIN_*` + `DB_NAME`, et le message d'erreur renvoie « Vérifiez `DB_ADMIN_*` / `DB_NAME` ».
Les deux commandes qui appliquent du DDL (`db:apply` pour les entités, `migration:apply` pour les migrations) utilisent désormais le compte d'administration, conformément au titre et à la décision de cet ADR.

---

## Alternatives rejetées

**Garder `db:apply` sur `DB_APP_*` et accorder le DDL à `forge_app`.**
C'est l'état actuel (compromis).
Rejeté : le compte runtime obtient des droits de structure, ce qui contredit la doctrine et la documentation, et augmente la surface en cas de compromission de l'application.

**Ajouter un troisième compte « migrations ».**
Rejeté : `forge_admin` couvre déjà ce rôle (il a le DDL sur la base du projet).
Un compte de plus complexifierait sans bénéfice.

---

## Charte appliquée

Principe 5 (garder le SQL visible), principe 7 (sécuriser par défaut), principe 10 (API/contrat clair), règle B (révéler avant de corriger : la contradiction est nommée, pas masquée).
