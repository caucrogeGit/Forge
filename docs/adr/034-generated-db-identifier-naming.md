# ADR-034 : Nommage des identifiants DB générés sans suffixes

## Statut

Acceptée (ticket `NEW-DB-NAMING-NO-SUFFIX-001`).

Précise le comportement de `forge new` (ADR-024) sur la génération des fichiers
d'environnement.

---

## Contexte

`forge new <nom>` personnalise `env/example` puis en dérive `env/dev` en
substituant le nom du projet. La règle actuelle ajoute des suffixes :

```text
forge new monprojet
  APP_NAME=monprojet
  DB_NAME=monprojet_db
  DB_APP_LOGIN=monprojet_app
```

Les suffixes `_db` / `_app` sont verbeux et redondants avec le préfixe de la
variable (`DB_NAME`, `DB_APP_LOGIN` disent déjà le rôle).

---

## Décision

**`DB_NAME` et `DB_APP_LOGIN` utilisent le nom normalisé du projet, sans suffixe.
`APP_NAME` garde le nom humain. `DB_ADMIN_LOGIN` reste `forge_admin`.**

Règle :

| Variable | Valeur | Normalisation |
|---|---|---|
| `APP_NAME` | nom humain du projet | aucune (garde tirets, casse) |
| `DB_NAME` | nom normalisé | `_to_snake` (kebab/Camel → snake) |
| `DB_APP_LOGIN` | nom normalisé | `_to_snake` |
| `DB_ADMIN_LOGIN` | `forge_admin` | compte d'administration partagé |

Exemples :

```text
forge new monprojet
  APP_NAME=monprojet        DB_NAME=monprojet        DB_APP_LOGIN=monprojet

forge new welcome-forge
  APP_NAME=welcome-forge    DB_NAME=welcome_forge    DB_APP_LOGIN=welcome_forge
```

Le tiret reste dans `APP_NAME` (nom applicatif humain) et devient `_` dans
`DB_NAME` / `DB_APP_LOGIN` (identifiants MariaDB).

---

## Conséquences

- Identifiants plus courts et lisibles.
- `DB_NAME` et `DB_APP_LOGIN` partagent la même valeur. Sans danger : base et
  utilisateur sont des espaces de noms séparés en MariaDB. L'asymétrie
  `forge_admin` (partagé) vs `<projet>` (par projet) encode la distinction
  admin/app.
- Les noms d'exemple de `mariadb-comptes.md` (`forge_db` / `forge_app`) restent
  illustratifs ; l'utilisateur adapte aux valeurs de son `env/dev`, comme
  aujourd'hui (`mariadb.md` le dit déjà).

---

## Alternatives rejetées

**Garder les suffixes `_db` / `_app`.** Ils sont auto-documentants (le rôle se
lit dans le nom), mais le préfixe de variable le dit déjà, et le résultat est
plus verbeux. La lisibilité l'emporte.

---

## Charte appliquée

Principe 11 (une seule façon officielle de faire chaque chose), lisibilité du
projet généré.
