# ADR-080 : Validation du sujet authentifié (is_authenticated adossé au loader)

## Statut

Proposée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-13

## Contexte

Retour terrain RéférenCiel 021. Après un rechargement de fixtures qui réassigne les identifiants, une session pointe vers un compte supprimé ou réattribué (un `user_id` en session dont plus aucun compte ne correspond). L'application reste « authentifiée » (menu profil) au lieu de renvoyer au login.

Deux frottements liés :

- **F54** : `AuthMiddleware.check` teste seulement `is_authenticated(request)`, défini comme `get_authenticated_user_id(request) is not None`. Présence d'un `user_id` en session ≠ existence du compte. Une session orpheline passe le contrôle. La simple redirection ne suffirait pas : sans fermer la session, on reboucle (`/` vers `/login` vers `/`).
- **F55** : deux définitions de `is_authenticated` dans le contexte de rendu : `BaseController.render` le calcule sur la session (id présent), le provider Jinja RBAC sur `current_user is not None`. Par défaut les deux sont id-based (donc d'accord), mais dès qu'une application câble un `user_loader` d'un côté seulement, elles divergent.

Le cœur possède déjà la brique de validation : `current_user(request, user_loader)` charge le sujet **et** vérifie `is_active`. Elle n'est utilisée que si l'application passe explicitement un loader, à chaque appel. Aucun point ne valide l'existence du sujet par défaut.

## Décision

Le cœur expose un **user_loader d'authentification optionnel et enregistrable**, source unique consultée partout où l'on décide « cet utilisateur est-il authentifié ? ».

### 1. Registre du loader (`core.auth`)

- `register_user_loader(loader: Callable[[int], Any] | None) -> None` : l'application l'enregistre **une fois** au démarrage (bootstrap `app.py`).
- `get_user_loader() -> Callable[[int], Any] | None` : renvoie le loader enregistré, ou `None`.

Registre explicite, opt-in, à l'image des registres existants (providers Jinja, routeur). Rien n'est enregistré par défaut.

### 2. `is_authenticated` adossé au sujet

`core.auth.session.is_authenticated(request)` devient :

- **loader enregistré** : `current_user(request, loader) is not None` (le sujet existe et est actif) ;
- **aucun loader** : comportement actuel, `get_authenticated_user_id(request) is not None` (id présent).

Une seule définition, un seul point de vérité (principe 11). Rétrocompatible : sans loader enregistré, le comportement est inchangé.

### 3. AuthMiddleware valide le sujet et ferme la session orpheline (F54)

`AuthMiddleware(login_url="/login", *, user_loader=None)` :

- résout le loader : celui passé au constructeur, sinon le loader enregistré ;
- si un loader est disponible et que le sujet est introuvable/inactif **alors qu'un `user_id` est en session** (session orpheline) : `logout_user(request)` (retire l'id) **et** purge du cookie de session sur la réponse 302, avant de rediriger vers `login_url` ;
- sinon, comportement inchangé (redirige si non authentifié, laisse passer sinon).

Fermer la session avant de rediriger casse la boucle `/` vers `/login`.

### 4. Contexte de rendu unifié (F55)

`BaseController.render` calcule `is_authenticated` via le même `is_authenticated(request)` (donc loader-aware si enregistré). Les providers Jinja RBAC (`make_auth_jinja_context_with_can`, `make_contract_jinja_context_with_can`) consultent le **loader enregistré** pour `current_user` et `is_authenticated`. Toutes les surfaces convergent vers la même définition, cohérente avec `can()` / `current_user`.

## Conséquences

- Une session orpheline (id sans compte) est traitée comme **non authentifiée** partout : middleware, `is_authenticated`, contexte de rendu, `can()`.
- Surface d'API élargie (additive, opt-in) : `core.auth.register_user_loader` / `get_user_loader` ; `AuthMiddleware(..., user_loader=None)`. Sans enregistrement ni argument, tout se comporte comme aujourd'hui (id-based).
- La validation du sujet a un coût (un appel loader, souvent une requête BDD) par requête protégée et par rendu. Acceptable, et à la main de l'application (opt-in).
- Cohérent avec ADR-010 (API canonique auth/session) : `is_authenticated` devient l'unique porte, adossée au sujet quand l'application le demande.

## Mise en œuvre (phasage)

Tickets distincts :

1. **F54** : registre `register_user_loader`/`get_user_loader` ; `is_authenticated` loader-aware ; `AuthMiddleware` valide le sujet, ferme la session orpheline (logout + purge cookie) avant de rediriger.
2. **F55** : `BaseController.render` et les providers Jinja RBAC consultent le loader enregistré ; convergence vérifiée par test (session orpheline vue non authentifiée des deux côtés).

Chaque ticket : tests + pyright strict + ruff + `mkdocs --strict` verts, doc à jour.

## Alternatives écartées

- **Passer le loader à chaque appel (statu quo).**
  Écartée : impossible d'unifier `AuthMiddleware`, `is_authenticated` et le contexte de rendu sans le répéter partout ; c'est la source de la divergence F55.
- **Valider le sujet systématiquement, sans opt-in.**
  Écartée : impose une requête BDD par requête à toute application, même celles qui n'en ont pas besoin ; casse la rétrocompatibilité.
- **Fermer la session par une simple redirection, sans logout.**
  Insuffisant : la session orpheline persiste et reboucle (`/` vers `/login`).

## Référence

- Charte : `CHARTE_DOC.md` (principe 11, une seule façon officielle ; principe 7, sécuriser par défaut).
- [ADR-010](010-auth-session-canonical-api.md) : API canonique auth/session.
- [ADR-014](014-rbac-contract-location.md) et [ADR-056](056-rbac-contract-tooling-extraction.md) : contrat et outillage RBAC.
