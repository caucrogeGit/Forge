# ADR-034 : Nommage des identifiants DB générés sans suffixes

## Statut

Acceptée (ticket `NEW-DB-NAMING-NO-SUFFIX-001`).

Précise le comportement de `forge new` (ADR-024) sur la génération des fichiers d'environnement.

### Révision : normalisation sans « _ » ajouté et compte admin par projet

Retour terrain (ticket `NEW-DB-NAMING-NO-UNDERSCORE-001`).
Deux ajustements à la décision initiale :

1. **Normalisation sans séparateur ajouté.** L'ancienne normalisation `_to_snake` insérait un « _ » à la frontière de casse et remplaçait les tirets par des « _ » : `ReferenCiel` devenait `referen_ciel`, `welcome-forge` devenait `welcome_forge`.
   La nouvelle règle met simplement le nom en minuscules sans ajouter de séparateur : `ReferenCiel` donne `referenciel`, `welcome-forge` donne `welcomeforge`.
   Les « _ » réellement saisis sont conservés.
2. **`DB_ADMIN_LOGIN` par projet.** Il valait `forge_admin` (partagé) et n'était jamais substitué.
   Il vaut désormais `<nom normalisé>_admin`, un compte de provisioning distinct du compte applicatif (ADR-033).

La convention s'applique de façon identique à `env/example` et à `env/dev` (les identifiants y sont projet-spécifiques dans les deux fichiers).

---

## Contexte

`forge new <nom>` personnalise `env/example` puis en dérive `env/dev` en substituant le nom du projet.
La règle actuelle ajoute des suffixes :

```text
forge new monprojet
  APP_NAME=monprojet
  DB_NAME=monprojet_db
  DB_APP_LOGIN=monprojet_app
```

Les suffixes `_db` / `_app` sont verbeux et redondants avec le préfixe de la variable (`DB_NAME`, `DB_APP_LOGIN` disent déjà le rôle).

---

## Décision

**`DB_NAME` et `DB_APP_LOGIN` utilisent le nom normalisé du projet, sans suffixe.
`APP_NAME` garde le nom humain.
`DB_ADMIN_LOGIN` est le nom normalisé suffixé de `_admin` (compte de provisioning distinct, ADR-033).**

Normalisation (`_normalize_identifier`) : mise en minuscules, sans séparateur ajouté.
Les « _ » réellement saisis sont conservés ; les autres caractères non alphanumériques (par exemple le tiret) sont retirés sans être remplacés par un « _ ».
Aucun « _ » n'est inséré à une frontière de casse.

Règle :

| Variable | Valeur | Normalisation |
|---|---|---|
| `APP_NAME` | nom humain du projet | aucune (garde tirets, casse) |
| `DB_NAME` | nom normalisé nu | minuscules, sans séparateur ajouté |
| `DB_APP_LOGIN` | nom normalisé nu | identique à `DB_NAME` |
| `DB_ADMIN_LOGIN` | nom normalisé + `_admin` | compte de provisioning distinct (ADR-033) |

Exemples :

```text
forge new ReferenCiel
  APP_NAME=ReferenCiel    DB_NAME=referenciel    DB_APP_LOGIN=referenciel    DB_ADMIN_LOGIN=referenciel_admin

forge new welcome-forge
  APP_NAME=welcome-forge  DB_NAME=welcomeforge   DB_APP_LOGIN=welcomeforge   DB_ADMIN_LOGIN=welcomeforge_admin
```

Le tiret et la casse restent dans `APP_NAME` (nom applicatif humain) ; ils disparaissent dans les identifiants MariaDB (`DB_NAME`, `DB_APP_LOGIN`, `DB_ADMIN_LOGIN`) sans introduire de « _ ».

---

## Conséquences

- Identifiants plus courts et lisibles, fidèles au nom saisi (pas de « _ » surgi d'une frontière de casse).
- `DB_NAME` et `DB_APP_LOGIN` partagent la même valeur.
  Sans danger : base et utilisateur sont des espaces de noms séparés en MariaDB.
  Le suffixe `_admin` de `DB_ADMIN_LOGIN` garde le compte de provisioning distinct du compte applicatif (ADR-033).
- Les noms d'exemple de `mariadb-comptes.md` (`forge_admin`, etc.) restent illustratifs ; l'utilisateur adapte aux valeurs de son `env/dev`, comme aujourd'hui (`mariadb.md` le dit déjà).

---

## Alternatives rejetées

**Garder les suffixes `_db` / `_app`.** Ils sont auto-documentants (le rôle se lit dans le nom), mais le préfixe de variable le dit déjà, et le résultat est plus verbeux.
La lisibilité l'emporte.

---

## Charte appliquée

Principe 11 (une seule façon officielle de faire chaque chose), lisibilité du projet généré.
