# Starters Forge

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Parcours applicatifs</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Vue d'ensemble des starters</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Des parcours progressifs pour apprendre Forge, reconstruire vite et adapter à un vrai projet.</p>
</div>

## Principe

Un **starter** Forge est un exemple applicatif générable avec `forge starter:build`. Il fournit un point de départ fonctionnel pour comprendre les mécaniques du framework, construire une base métier ou produire rapidement une démonstration.

Un starter n'est pas un profil. Voir [Différence entre profil et starter](#difference-entre-profil-et-starter).

## Tableau de synthèse

| Starter | Statut | Profil associé | Usage recommandé |
|---|---|---|---|
| [Bonjour Forge — premier pas](welcome-forge/debutant/welcome.md) | Entrée sans BDD | Aucun (fonctionne sans db:init) | Premier contact minimal avec Forge — `Response.text(...)` et `request.param(...)`, deux routes, aucune vue HTML, aucune base de données |
| [Paramètres d'URL](welcome-forge/debutant/query-params.md) | Pédagogique sans BDD | Aucun (fonctionne sans db:init) | Palier 2 de la progression — lire une valeur d'URL avec `request.param("name", default=...)`, deux routes, aucune vue HTML, aucune base de données |
| [Première vue HTML](welcome-forge/debutant/first-html-view.md) | Pédagogique sans BDD | Aucun (fonctionne sans db:init) | Palier 3 de la progression — rendre une page HTML avec `BaseController.render(...)`, une route, une vue, aucune base de données |
| [Route dynamique](welcome-forge/debutant/dynamic-route.md) | Pédagogique sans BDD | Aucun (fonctionne sans db:init) | Palier 4 de la progression — lire un paramètre de route avec `request.route_param("id")`, une route `/dynamic-route/articles/{id}`, aucune vue HTML, aucune base de données |
| [Inspecter une requête](welcome-forge/debutant/request-debug.md) | Pédagogique sans BDD | Aucun (fonctionne sans db:init) | Palier 5 de la progression — explorer `request.data` avec `Response.debug(...)`, une route `/request-debug`, aucune vue HTML, aucune base de données |
| [Premier formulaire POST](welcome-forge/debutant/form-post.md) | Pédagogique sans BDD | Aucun (fonctionne sans db:init) | Palier 6 de la progression — afficher un formulaire HTML minimal (avec CSRF), envoyer un POST, lire la valeur avec `request.form("name", ...)`, aucune base de données |
| [Validation serveur](welcome-forge/debutant/server-validation.md) | Pédagogique sans BDD | Aucun (fonctionne sans db:init) | Palier 7 de la progression — refuser une valeur vide avec `Response.text(..., status=422)`, contrôle minimum côté serveur, aucune base de données |
| [Première base SQL](welcome-forge/debutant/first-sql.md) | Pédagogique avec BDD | `minimal` / `standard` | Palier 8 de la progression — table SQL minimale + migration visible, lecture avec `core.database.db.fetch_one`, SQL visible, aucun CRUD |
| [Lister des enregistrements](welcome-forge/intermediaire/list-records.md) | Intermédiaire (avec BDD) | `minimal` / `standard` | Niveau **intermédiaire**, palier 1 — lire **plusieurs** lignes avec `core.database.db.fetch_all` et les afficher dans une vue avec une boucle Jinja `{% for %}` |
| [Rechercher / filtrer](welcome-forge/intermediaire/filter-list.md) | Intermédiaire (avec BDD) | `minimal` / `standard` | Niveau **intermédiaire**, palier 2 — filtrer une liste avec `request.param("q")` et une clause SQL `WHERE content LIKE ?` paramétrée |
| [Paginer une liste](welcome-forge/intermediaire/pagination.md) | Intermédiaire (avec BDD) | `minimal` / `standard` | Niveau **intermédiaire**, palier 3 — `LIMIT ? OFFSET ?` piloté par `request.param("page")` + `COUNT(*)`, liens précédent/suivant |
| [Héritage de gabarit](welcome-forge/intermediaire/layout-template.md) | Intermédiaire (sans BDD) | Aucun | Niveau **intermédiaire**, palier 4 — factoriser l'enveloppe HTML avec `{% extends %}` + `{% block %}` (gabarit partagé) |
| [Modifier un enregistrement](welcome-forge/intermediaire/update-record.md) | Intermédiaire (avec BDD) | `minimal` / `standard` | Niveau **intermédiaire**, palier 5 — formulaire pré-rempli + `core.database.db.execute("UPDATE … WHERE id = ?")`, POST protégé CSRF |
| [Supprimer un enregistrement](welcome-forge/intermediaire/delete-record.md) | Intermédiaire (avec BDD) | `minimal` / `standard` | Niveau **intermédiaire**, palier 6 — suppression `POST` + CSRF + `core.database.db.execute("DELETE … WHERE id = ?")` |
| [Mémoriser un état en session](welcome-forge/intermediaire/session-state.md) | Intermédiaire (sans BDD) | Aucun | Niveau **intermédiaire**, palier 7 — mémoriser un compteur entre requêtes via le store de session + cookie `session_id` durci |
| [Messages flash](welcome-forge/intermediaire/flash-messages.md) | Intermédiaire (sans BDD) | Aucun | Niveau **intermédiaire**, palier 8 — confirmer une action via un message flash one-shot (`set_flash`/`get_flash`), motif POST-Redirect-GET |
| [Relations entre tables](welcome-forge/avance/relations.md) | Avancé (avec BDD) | `minimal` / `standard` | Niveau **avancé**, palier 1 — deux tables liées par une clé étrangère, lecture par jointure SQL `SELECT … FROM articles JOIN categories …` via `core.database.db.fetch_all` |
| [Téléverser un fichier](welcome-forge/avance/file-upload.md) | Avancé (sans BDD) | Aucun | Niveau **avancé**, palier 2 — formulaire `multipart/form-data`, `request.file(...)` + `core.uploads.save_upload` (validation extension / MIME / taille avant écriture disque) |
| [Envoyer un email](welcome-forge/avance/send-email.md) | Avancé (sans BDD) | Aucun | Niveau **avancé**, palier 3 — composer un `MailMessage` et l'envoyer via `Mailer` sur `ConsoleTransport` (affiché en console, aucun SMTP requis) |
| [API JSON protégée](welcome-forge/avance/json-api.md) | Avancé (avec BDD) | `minimal` / `standard` | Niveau **avancé**, palier 4 — `Response.json` derrière un jeton `Authorization: Bearer …` lu via `request.header(...)`, réponse `401` sinon |
| [Écritures transactionnelles](welcome-forge/avance/db-transaction.md) | Avancé (avec BDD) | `minimal` / `standard` | Niveau **avancé**, palier 5 — `with transaction() as tx:` + `insert(..., tx=tx)`, rollback atomique si une écriture échoue |
| [Bonjour Forge IoT](welcome-iot/debutant/iot-welcome.md) | IoT débutant (opt-in, sans broker) | Aucun | Progression **welcome-iot**, niveau débutant palier 1 — premier contact avec `forge-mvc-iot` + inspection de la config MQTT (`load_iot_config`), mot de passe masqué |
| [Lire les événements IoT](welcome-iot/debutant/iot-events.md) | IoT débutant (opt-in, sans broker) | Aucun | Progression **welcome-iot**, niveau débutant palier 2 — lire les derniers événements (`IotEventRepository.list_recent`), réponse `503` pédagogique si la table `iot_events` manque |
| [Les événements d'un capteur](welcome-iot/debutant/iot-device.md) | IoT débutant (opt-in, sans broker) | Aucun | Progression **welcome-iot**, niveau débutant palier 3 — route paramétrée `/iot-device/{site}/{device_id}`, `find_by_device` + `count_by_device` |
| [Simuler une mesure IoT](welcome-iot/intermediaire/iot-simulate.md) | IoT intermédiaire (opt-in, avec BDD, sans broker) | Aucun | Progression **welcome-iot**, niveau intermédiaire palier 1 — composer/valider (`parse_message`) et insérer (`IotEventRepository.insert`) une mesure sans broker |
| [Exposer l'API IoT](welcome-iot/intermediaire/iot-api.md) | IoT intermédiaire (opt-in, avec BDD) | Aucun | Progression **welcome-iot**, niveau intermédiaire palier 2 — brancher l'API HTTP JSON officielle (`register_iot_routes`), 3 routes lecture seule, Bearer optionnel |
| [Tableau de bord IoT](welcome-iot/intermediaire/iot-dashboard.md) | IoT intermédiaire (opt-in, avec BDD) | Aucun | Progression **welcome-iot**, niveau intermédiaire palier 3 — afficher les derniers événements dans une page HTML (`list_recent` + `render`) |
| [Valider un message IoT](welcome-iot/avance/iot-contract.md) | IoT avancé (opt-in, sans broker) | Aucun | Progression **welcome-iot**, niveau avancé palier 1 — valider topic + payload contre le contrat (`parse_message`, `ContractError` avec code) |
| [First CRUD](crud/first-crud.md) | Capstone fondamentaux (avec BDD) | `minimal` / `standard` | Premier starter autonome après la progression — CRUD complet à SQL visible (`SELECT`/`INSERT`/`UPDATE`/`DELETE`) sur l'entité neutre `message`, aucun métier, aucun ORM |
| [1 — First CRUD (généré)](crud/first-crud-generated.md) | Officiel simple | `minimal` / `standard` | Starter autonome avancé — CRUD **généré** via `make:crud` sur l'entité neutre `message` ; pendant échafaudé de First CRUD (à la main), suppose les 11 paliers de découverte + le starter First CRUD acquis |
| [2 — Auth (API cœur)](core-auth/users-core-auth.md) | Auth minimale moderne | `standard` | Comprendre une authentification minimale avec `core.auth` |
| [3 — Auth MFA](optin-mfa/welcome-optin-mfa.md) | Démonstrateur MFA (Alpha) | `auth-mfa` | Ajouter un challenge TOTP au flux de connexion avec `forge-mvc-mfa` (publié sur PyPI depuis `1.0.0-beta.9`) |
| [Bonjour IoT](optin-iot/welcome-optin-iot.md) | Entrée IoT sans broker | Aucun (fonctionne sans db:init ni broker MQTT) | Premier contact avec le module opt-in `forge-mvc-iot` — quatre routes (`/welcome-optin-iot`, `/welcome-optin-iot/inspect`, `/welcome-optin-iot/events`, `/welcome-optin-iot/device/{site}/{device_id}`), inspect masque le mot de passe, lecture pédagogique des événements `iot_events` |
| [Bonjour Vidéo](optin-video/welcome-optin-video.md) | Entrée vidéo sans ffmpeg | Aucun (fonctionne sans db:init ni ffmpeg) | Premier contact avec le module opt-in `forge-mvc-video` — trois routes (`/welcome-optin-video`, `/welcome-optin-video/inspect`, `/welcome-optin-video/list`) + lecture officielle `GET /videos/{uuid}`, inspect masque le token, liste pédagogique des vidéos |

## Progression recommandée

Le starter `Bonjour Forge` est volontairement minimal (deux routes texte,
zéro vue HTML, zéro base de données). **Ne sautez pas directement au
starter First CRUD (généré)** : plusieurs notions intermédiaires permettent
d'aborder le CRUD sereinement. La progression officielle est :

1. **Bonjour Forge** — afficher une réponse texte avec `Response.text(...)`.
   *(livré — starter `welcome`)*
2. **Paramètres d'URL** — lire une valeur simple avec `request.param(...)`.
   *(livré — starter `query-params`, ticket `STARTER-QUERY-PARAMS-001`)*
3. **Première vue HTML** — rendre une page avec `BaseController.render(...)`.
   *(livré — starter `first-html-view`, ticket `STARTER-FIRST-HTML-VIEW-001`)*
4. **Route dynamique** — lire un paramètre de route comme `/articles/{id}`.
   *(livré — starter `dynamic-route`, ticket `STARTER-DYNAMIC-ROUTE-001`)*
5. **Inspecter une requête** — explorer `request.data` avec `Response.debug(...)` en développement.
   *(livré — starter `request-debug`, ticket `STARTER-REQUEST-DEBUG-001`)*
6. **Réponse JSON** — retourner des données structurées avec `Response.json(...)`.
   *(livré — starter `json-response`, ticket `STARTER-JSON-RESPONSE-001`)*
7. **Le jeton CSRF** — comprendre la protection CSRF des formulaires.
   *(livré — starter `csrf`, ticket `STARTER-CSRF-001`)*
8. **Premier formulaire POST** — envoyer des données depuis un formulaire HTML.
   *(livré — starter `form-post`, ticket `STARTER-FORM-POST-001`)*
9. **Validation serveur** — refuser ou accepter les données reçues.
   *(livré — starter `server-validation`, ticket `STARTER-SERVER-VALIDATION-001`)*
10. **Première base SQL** — lire une donnée : MariaDB, migrations et SQL visible.
   *(livré — starter `first-sql`, ticket `STARTER-FIRST-SQL-001`)*
11. **Écrire en base** — insérer une ligne depuis un formulaire avec `db.insert(...)`.
   *(livré — starter `first-sql-write`, ticket `STARTER-FIRST-SQL-WRITE-001`)*

Une fois ces **11 paliers** acquis, vous avez terminé le starter de
découverte *Bonjour Forge*. Le premier **starter autonome** à enchaîner
est [First CRUD](crud/first-crud.md) — un CRUD complet à SQL visible
sur une entité neutre (`message`), livré par `STARTER-PREMIER-CRUD-001`.
Viennent ensuite les exemples : First CRUD (généré), Auth (API cœur), puis le
starter opt-in Auth MFA.

!!! warning "Saut Bonjour Forge → First CRUD (généré)"
    Sauter directement de `welcome` à `first-crud-generated` fait rencontrer
    plusieurs notions (vue, route dynamique, JSON, CSRF, formulaire,
    validation, SQL en lecture et écriture) sans transition. La
    progression ci-dessus solde cette dette pédagogique : suivez les
    paliers dans l'ordre (ticket `STARTER-ROADMAP-PROGRESSION-001`).

Le tableau de synthèse plus haut reste utile comme catalogue exhaustif
des starters disponibles aujourd'hui, mais l'ordre d'apprentissage
recommandé est celui des 11 paliers ci-dessus, suivi des starters
autonomes (First CRUD, puis les exemples métier).

## Starter d'entrée (sans base de données)

### Bonjour Forge — premier pas

Le starter d'entrée minimal de Forge. Aucune base de données, aucune
vue HTML, aucun moteur Jinja2. Deux routes texte qui montrent le
chemin le plus court entre une requête et une réponse.

Ce starter est référencé en interne comme `Bienvenue dans Forge` (alias
historique conservé).

Profil recommandé : aucun — fonctionne sans `forge db:init`.

- `GET /welcome` → `Response.text("Bonjour Forge")` ;
- `GET /welcome/greet?name=Roger` → `Response.text("Bonjour Roger")` ;
- introduction à `request.param(key, default=...)` ;
- déclaration des routes dans `mvc/routes.py`.

**Usage :**

```bash
forge new mon-projet --starter welcome
# alias acceptés : bonjour, bonjour-forge, bienvenue, 7
# ou dans un projet existant :
forge starter:build 7
```

[Présentation](welcome-forge/debutant/welcome.md)

## Premier starter autonome (avec base de données)

### First CRUD

Le capstone des fondamentaux : un CRUD complet (créer, lister, modifier,
supprimer) à **SQL visible**, sur une entité **neutre** (`message`, table
`first_sql_messages`). Premier starter autonome après les 11 paliers de
découverte.

Profil recommandé : `minimal` ou `standard`. Identifiant : `first-crud`
(alias `crud` / `16`).

- prolonge directement les paliers « Première base SQL » et « Écrire en base » ;
- les quatre opérations SQL en clair : `SELECT`, `INSERT`, `UPDATE`, `DELETE` ;
- aucune notion métier, aucun ORM, aucune authentification.

[Vue d'ensemble du sujet](crud/index.md) · [Présentation](crud/first-crud.md)

## Starters officiels simples

### First CRUD (généré)

Le starter officiel simple de Forge. Une entité **neutre** `Message`, un CRUD **généré** via `make:crud`, des routes câblées manuellement. C'est le pendant échafaudé du starter [First CRUD](crud/first-crud.md) (écrit à la main).

Profil recommandé : `minimal` ou `standard`.

- **starter autonome avancé** — synthèse du CRUD généré, entité neutre ;
- aucune relation, aucune authentification, aucune notion métier ;
- suppose acquis les **11 paliers de découverte** puis le starter
  [First CRUD](crud/first-crud.md) (routes, contrôleurs, vues HTML,
  paramètres d'URL, route dynamique, formulaires POST avec CSRF,
  validation serveur, migrations SQL, CRUD à SQL visible).

Pour le **premier** contact avec Forge, démarrer par
[Bonjour Forge](welcome-forge/debutant/welcome.md) (palier 1, sans BDD), pas par ce
starter.

[Présentation](crud/first-crud-generated.md) · [Reconstruction](crud/first-crud-generated-rebuild.md)

## Starter Auth minimal moderne

### Auth (API cœur)

Un exemple d'authentification minimale alignée sur le socle `core.auth` de Forge.

Profil recommandé : `standard`.

- login / logout avec sessions CSRF ;
- `@login_required`, `login_user`, `logout_user`, `verify_password` depuis `core.auth` ;
- dashboard protégé, page profil.

!!! info "Limites du starter 2"
    Ce starter ne démontre pas MFA, OIDC, RBAC avancé, reset password complet ou administration utilisateurs.

Identifiant : `users-core-auth` (starter n°2, alias `auth` / `utilisateurs-auth` / `2`).

[Vue d'ensemble du sujet](core-auth/index.md) · [Présentation](core-auth/users-core-auth.md) · [Reconstruction](core-auth/users-core-auth-rebuild.md)

## Démonstrateur MFA (Alpha)

### Auth MFA

Un skeleton d'authentification multi-facteurs TOTP basé sur le module opt-in
`forge-mvc-mfa`. Remplace deux contrôleurs dans un projet déjà initialisé avec
le profil `auth-mfa`.

Profil recommandé : `auth-mfa`.

- challenge TOTP intercalé entre password et session (`/login/mfa`) ;
- état temporaire de challenge avec expiration 10 min ;
- rate-limit et audit des événements MFA inclus.

!!! info "Module Alpha — publié sur PyPI depuis 1.0.0-beta.9"
    `forge-mvc-mfa` est un opt-in officiel publié sur PyPI au statut
    **Alpha**. Le secret TOTP est **chiffré au repos** via Fernet
    (`FORGE_MFA_SECRET_KEY` obligatoire au démarrage,
    `SEC-MFA-SECRET-ENCRYPTION-001`). Installation :

    ```bash
    pip install --pre forge-mvc-mfa
    ```

    Le passage Alpha → Beta reste un ticket futur, voir
    `packages/forge-mvc-mfa/README.md`.

Identifiant : `welcome-optin-mfa` (starter n°3, alias `mfa` / `auth-mfa` / `3`).

[Vue d'ensemble du sujet](optin-mfa/index.md) · [Présentation](optin-mfa/welcome-optin-mfa.md) · [Reconstruction](optin-mfa/welcome-optin-mfa-rebuild.md)

## Démonstrateur IoT (sans broker requis)

### Bonjour IoT

Premier contact avec le module opt-in `forge-mvc-iot`. Fonctionne
**sans broker MQTT** et **sans table créée** — les routes de lecture
détectent et signalent pédagogiquement quand `iot_events` n'est pas
encore disponible (HTTP 503 avec message clair, pas une trace
technique).

Aucun profil requis. Identifiant : `welcome-optin-iot` (alias `bonjour-iot`
/ `iot` / `12`).

- `GET /welcome-optin-iot` → `Response.text("Bonjour Forge IoT")` ;
- `GET /welcome-optin-iot/inspect` → JSON de la configuration IoT, mot de
  passe masqué (`"***"` ou `null`) ;
- `GET /welcome-optin-iot/events` → derniers événements via
  `IotEventRepository.list_recent`, ou message `iot_storage_not_ready`
  si la table n'existe pas ;
- `GET /welcome-optin-iot/device/{site}/{device_id}` → événements d'un
  capteur précis ;
- en parallèle, l'API HTTP officielle `/api/iot/...` est branchée via
  `register_iot_routes(router)`.

Aucun subscriber MQTT n'est lancé par le starter — c'est de la lecture
seule côté HTTP. Avant de tester, lancer `forge iot:doctor` pour
vérifier que le package, la configuration, la migration et l'API HTTP
sont en place.

[Présentation](optin-iot/welcome-optin-iot.md)

### Bonjour Vidéo

Premier contact avec le module opt-in `forge-mvc-video`. Fonctionne
**sans ffmpeg** et **sans table créée** — la route `list` détecte et
signale pédagogiquement quand la table `videos` n'est pas encore
disponible (HTTP 503 avec message clair, pas une trace technique).

Aucun profil requis. Identifiant : `welcome-optin-video` (alias
`bonjour-video` / `video` / `17`).

- `GET /welcome-optin-video` → `Response.text("Bonjour Forge Video")` ;
- `GET /welcome-optin-video/inspect` → JSON de la configuration vidéo,
  token masqué (`"***"` ou `null`) ;
- `GET /welcome-optin-video/list` → dernières vidéos via
  `VideoRepository.list_recent`, ou message `video_storage_not_ready`
  si la table n'existe pas ;
- en parallèle, la lecture officielle `GET /videos/{uuid}` (streaming
  HTTP Range) est branchée via `register_video_routes(router)`.

Aucun `ffmpeg` n'est lancé par le starter. Avant de traiter une vidéo,
lancer `forge video:doctor` pour vérifier package, configuration,
migration et binaires.

[Présentation](optin-video/welcome-optin-video.md)

## Différence entre profil et starter

Un **profil** définit la base technique d'un projet créé avec `forge new`. Il détermine les composants inclus dans l'environnement de départ.

```bash
forge new MonProjet --profile standard
```

Un **starter** fournit un exemple applicatif générable après la création du projet.

```bash
forge starter:build 5
```

Les profils et les starters sont indépendants :

- un profil ne remplace pas un starter ;
- un starter ne modifie pas le profil du projet ;
- un starter peut illustrer un ou plusieurs profils.

Pour choisir un profil : [Profils de projet](../features/profiles.md).

## Génération automatique

```bash
forge new mon-projet --starter welcome       # Bienvenue (sans BDD) — via forge new
forge starter:build 1        # First CRUD (généré)
forge starter:build 2        # Auth (API cœur)
forge starter:build 3        # Auth MFA (Alpha)
forge starter:build 4        # Bienvenue dans Forge (sans BDD)
```

Pour le starter pédagogique `query-params` (palier 2 de la progression),
voir la page dédiée [Paramètres d'URL](welcome-forge/debutant/query-params.md) — il
s'applique par son identifiant public, pas par un numéro.

Les alias `first-crud-generated`, `auth`, `query-params` et leurs variantes sont également supportés.

`forge starter:list` affiche la liste complète depuis la CLI.

## Démarrer un starter

```bash
forge new MonProjet
cd MonProjet
source .venv/bin/activate
forge doctor
forge db:init
forge starter:build 1        # remplacer 1 par le numéro souhaité
```

Chaque page de starter liste les commandes exactes, le modèle de données et les étapes de reconstruction.

## Fichiers de reconstruction

| Starter | Présentation | Reconstruction |
|---|---|---|
| First CRUD (généré) | [Présentation](crud/first-crud-generated.md) | [rebuild.md](crud/first-crud-generated-rebuild.md) |
| Auth (API cœur) | [Présentation](core-auth/users-core-auth.md) | [rebuild.md](core-auth/users-core-auth-rebuild.md) |
| Auth MFA | [Présentation](optin-mfa/welcome-optin-mfa.md) | [rebuild.md](optin-mfa/welcome-optin-mfa-rebuild.md) |

## Statut officiel des starters

| Starter | Statut |
|---|---|
| 1 — First CRUD (généré) | Starter officiel simple |
| 2 — Auth (API cœur) | Auth minimale moderne (`core.auth`) |
| 3 — Auth MFA | Démonstrateur MFA (Alpha) |
