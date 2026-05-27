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
| [Bonjour Forge — premier pas](welcome/index.md) | Entrée sans BDD | Aucun (fonctionne sans db:init) | Premier contact avec Forge — `Response.text(...)` → `Response.debug(...)` → `BaseController.render(...)`, sans SQL |
| [1 — Contacts](01-contact-simple/index.md) | Officiel simple | `minimal` / `standard` | Découvrir Forge avec un exemple CRUD simple |
| [2 — Utilisateurs / Auth](02-utilisateurs-auth/index.md) | Auth minimale moderne | `standard` | Comprendre une authentification minimale avec `core.auth` |
| [3 — Carnet de contacts](03-carnet-contacts/index.md) | Officiel relationnel | `standard` | Comprendre les relations entre entités (`many_to_one`, JOIN SQL) |
| [4 — Suivi pédagogique](04-suivi-comportement-eleves/index.md) | Historique / legacy | Aucun profil principal | Consulter un exemple métier historique, non recommandé comme base moderne |
| [5 — Communes & Séjours](communes-sejours/index.md) | Démonstrateur avancé principal | `standard` | Voir une application démonstratrice couvrant les briques modernes de Forge |
| [6 — Auth MFA](auth-mfa/index.md) | Démonstrateur MFA (Alpha) | `auth-mfa` | Ajouter un challenge TOTP au flux de connexion avec `forge-mvc-mfa` (publié sur PyPI depuis `1.0.0-beta.9`) |

## Starter d'entrée (sans base de données)

### Bonjour Forge — premier pas

Le starter d'entrée de Forge. Aucune base de données requise. La
progression pédagogique va du chemin le plus court (`Response.text(...)`)
jusqu'au rendu de templates Jinja2 (`BaseController.render(...)`), en
passant par `request.param(...)` et `Response.debug(request.data)`.

Ce starter est référencé en interne comme `Bienvenue dans Forge` (alias
historique conservé).

Profil recommandé : aucun — fonctionne sans `forge db:init`.

- texte brut puis évolution vers le rendu Jinja2 ;
- `request.param(name, default=...)` introduit simplement ;
- inspection de `request.data` via `Response.debug(obj)` ;
- déclaration des routes dans `mvc/routes.py` ;
- gestion des erreurs 404 illustrée.

**Usage :**

```bash
forge new mon-projet --starter welcome
# alias acceptés : bonjour, bonjour-forge, bienvenue, 7
# ou dans un projet existant :
forge starter:build 7
```

[Présentation](welcome/index.md)

## Starters officiels simples

### Starter 1 — Contacts

Le starter officiel simple de Forge. Une seule entité `Contact`, un CRUD généré, des routes câblées manuellement.

Profil recommandé : `minimal` ou `standard`.

- idéal pour découvrir Forge ;
- aucune relation, aucune authentification ;
- premier parcours Forge.

[Présentation](01-contact-simple/index.md) · [Reconstruction](01-contact-simple/rebuild.md)

### Starter 3 — Carnet de contacts

Le starter officiel relationnel de Forge. Deux entités (`Ville` et `Contact`), une relation `many_to_one`, un `LEFT JOIN` SQL visible.

Profil recommandé : `standard`.

- idéal pour comprendre les relations entre entités ;
- montre `relations.json`, la clé étrangère et la requête JOIN.

[Présentation](03-carnet-contacts/index.md) · [Reconstruction](03-carnet-contacts/rebuild.md)

## Starter Auth minimal moderne

### Starter 2 — Utilisateurs / Auth

Un exemple d'authentification minimale alignée sur le socle `core.auth` de Forge.

Profil recommandé : `standard`.

- login / logout avec sessions CSRF ;
- `@login_required`, `login_user`, `logout_user`, `verify_password` depuis `core.auth` ;
- dashboard protégé, page profil.

!!! info "Limites du starter 2"
    Ce starter ne démontre pas MFA, OIDC, RBAC avancé, reset password complet ou administration utilisateurs.

[Présentation](02-utilisateurs-auth/index.md) · [Reconstruction](02-utilisateurs-auth/rebuild.md)

## Démonstrateur historique

### Starter 4 — Suivi pédagogique

Un exemple pédagogique historique conservé comme référence. Il montre une application métier plus riche : plusieurs entités, relations, seed et un flux d'authentification ancien.

!!! warning "Statut legacy"
    Ce starter n'est plus recommandé comme base pour un nouveau projet. Son implémentation auth est antérieure au socle `core.auth`. Il reste disponible comme trace pédagogique.

[Présentation](04-suivi-comportement-eleves/index.md) · [Reconstruction](04-suivi-comportement-eleves/rebuild.md)

## Démonstrateur avancé principal

### Starter 5 — Communes & Séjours

Le démonstrateur avancé principal de Forge. Il couvre les briques modernes du framework dans une application cohérente.

Ce starter démontre :

- entités et relations ;
- pages publiques (`make:public-page`, `make:public-list`, `make:public-show`, `make:public-form`, `make:public-contact`) ;
- formulaire de contact avec mail ;
- internationalisation (i18n) ;
- seed JSON ;
- médias et fichiers.

[Présentation](communes-sejours/index.md) · [Reconstruction](communes-sejours/rebuild.md)

## Démonstrateur MFA (Alpha)

### Starter 6 — Auth MFA

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

[Présentation](auth-mfa/index.md) · [Reconstruction](auth-mfa/rebuild.md)

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
- un starter peut illustrer un ou plusieurs profils ;
- Communes & Séjours est une vitrine avancée, pas un profil.

Pour choisir un profil : [Profils de projet](../profiles.md).

## Génération automatique

```bash
forge new mon-projet --starter welcome  # Bienvenue (sans BDD) — via forge new
forge starter:build 1        # Contacts
forge starter:build 2        # Utilisateurs / Auth
forge starter:build 3        # Carnet de contacts
forge starter:build 4        # Suivi pédagogique
forge starter:build 5        # Communes & Séjours
forge starter:build 6        # Auth MFA (Alpha)
forge starter:build 7        # Bienvenue dans Forge (sans BDD)
```

Les alias `contacts`, `auth`, `carnet`, `suivi`, `communes-sejours` et leurs variantes sont également supportés.

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
| Contacts | [Présentation](01-contact-simple/index.md) | [rebuild.md](01-contact-simple/rebuild.md) |
| Utilisateurs / Auth | [Présentation](02-utilisateurs-auth/index.md) | [rebuild.md](02-utilisateurs-auth/rebuild.md) |
| Carnet de contacts | [Présentation](03-carnet-contacts/index.md) | [rebuild.md](03-carnet-contacts/rebuild.md) |
| Suivi pédagogique | [Présentation](04-suivi-comportement-eleves/index.md) | [rebuild.md](04-suivi-comportement-eleves/rebuild.md) |
| Communes & Séjours | [Présentation](communes-sejours/index.md) | [rebuild.md](communes-sejours/rebuild.md) |
| Auth MFA | [Présentation](auth-mfa/index.md) | [rebuild.md](auth-mfa/rebuild.md) |

## Statut officiel des starters

| Starter | Statut |
|---|---|
| 1 — Contacts | Starter officiel simple |
| 2 — Utilisateurs / Auth | Auth minimale moderne (`core.auth`) |
| 3 — Carnet de contacts | Starter officiel relationnel |
| 4 — Suivi pédagogique | Exemple pédagogique historique / legacy |
| 5 — Communes & Séjours | Démonstrateur avancé principal |
| 6 — Auth MFA | Démonstrateur MFA (Alpha) |
