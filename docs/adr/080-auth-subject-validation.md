# ADR-080 : Validation du sujet authentifié (AuthMiddleware + rendu)

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-13

## Contexte

Retour terrain RéférenCiel 021. Après un rechargement de fixtures qui réassigne les identifiants, une session pointe vers un compte supprimé ou réattribué (un `user_id` en session dont plus aucun compte ne correspond). L'application reste « authentifiée » (menu profil) au lieu de renvoyer au login.

Deux frottements liés :

- **F54** : `AuthMiddleware.check` teste seulement `is_authenticated(request)`, défini comme `get_authenticated_user_id(request) is not None`. Présence d'un `user_id` en session ne prouve pas l'existence du compte. Une session orpheline passe le contrôle. Rediriger sans fermer la session reboucle (`/` vers `/login` vers `/`).
- **F55** : deux définitions de `is_authenticated` dans le contexte de rendu : `BaseController.render` le calcule sur la session (id présent), le provider Jinja RBAC sur `current_user is not None`. Par défaut les deux sont id-based (donc d'accord), mais dès qu'une application câble un `user_loader` d'un côté seulement, elles divergent.

Le cœur possède déjà la brique de validation : `current_user(request, user_loader)` charge le sujet **et** vérifie `is_active`. Elle n'est utilisée que si l'application passe explicitement un loader.

## Décision

Fix **explicite, opt-in, sans état global** ni changement de sémantique d'une fonction publique. On ne modifie pas `is_authenticated(request)` (contrôle bas niveau « un id d'auth est-il en session ? ») : on branche la validation du sujet là où elle compte, via un `user_loader` passé explicitement.

### F54 : AuthMiddleware valide le sujet et ferme la session orpheline

`AuthMiddleware(login_url="/login", *, user_loader=None)` :

- **sans `user_loader`** : comportement inchangé (redirige si aucun id en session, laisse passer sinon) ;
- **avec `user_loader`** : quand un `user_id` est en session mais que `current_user(request, user_loader)` renvoie `None` (compte supprimé, réattribué ou inactif), c'est une **session orpheline** : `logout_user(request)` (retire l'id de la session) **et** purge du cookie de session sur la réponse 302, avant de rediriger vers `login_url`. Fermer la session casse la boucle `/` vers `/login`.

L'application câble le loader dans `app.py` (`AuthMiddleware(user_loader=charger_utilisateur)`), à côté du reste du câblage de middlewares. Visible et relu, pas d'enregistrement caché.

Une fois la session orpheline fermée, la requête suivante n'a plus d'id : toutes les surfaces (y compris `is_authenticated` id-based et le rendu) la voient déconnectée. F54 résout donc le symptôme visible sans toucher au reste.

### F55 : une seule définition autoritaire dans le rendu

Le contexte de rendu a **une** source autoritaire de `is_authenticated` : le provider Jinja auth/RBAC, adossé au **loader** (existence du sujet), cohérent avec `current_user` et `can()`.

- `BaseController.render` pose `is_authenticated` (session, id-based) comme **valeur par défaut** uniquement s'il n'est pas déjà fourni ; les providers Jinja, exécutés ensuite, la **remplacent** par la valeur loader-based quand un loader est câblé. C'est déjà l'ordre de fusion ; on le documente comme contrat : le provider gagne.
- Les providers Jinja RBAC (`make_auth_jinja_context`, `make_contract_jinja_context`) deviennent loader-aware : quand l'application câble un `user_loader`, `is_authenticated` et `current_user` reflètent l'existence du sujet.

Pas de registre global : le loader de rendu est celui que l'application câble sur son provider Jinja, comme elle câble déjà `AuthMiddleware`. Une seule variable applicative, référencée aux deux points de câblage de `app.py`.

## Conséquences

- Une session orpheline est fermée au premier contrôle `AuthMiddleware` et vue déconnectée ensuite ; avec un loader câblé sur le provider Jinja, elle l'est aussi dans le rendu de la requête courante.
- Surface d'API : `AuthMiddleware(..., user_loader=None)` (additif, rétrocompatible). Aucune fonction publique existante ne change de sémantique ; aucun état global ajouté.
- Le coût de validation (un appel loader, souvent une requête BDD) n'est payé que si l'application câble un loader : opt-in.
- La divergence F55 est levée par contrat (provider autoritaire) plutôt que par un mécanisme global ; si un besoin de validation du sujet hors provider apparaît plus tard, un registre pourra être réexaminé (règle B, révéler avant d'élargir).

## Mise en œuvre (phasage)

Tickets distincts :

1. **F54** : `AuthMiddleware(..., user_loader=None)` ; validation du sujet via `current_user` ; fermeture de la session orpheline (logout + purge cookie) avant redirection.
2. **F55** : providers Jinja RBAC loader-aware ; `BaseController.render` documenté comme posant une valeur par défaut que le provider remplace ; test de convergence (session orpheline vue non authentifiée des deux côtés).

Chaque ticket : tests + pyright strict + ruff + `mkdocs --strict` verts, doc à jour.

## Alternatives écartées

- **Registre global de `user_loader` + `is_authenticated` loader-aware partout.**
  Écartée : change la sémantique d'une fonction publique et ajoute un état global pour un gain non prouvé une fois F54 en place (F55 est « à confirmer ») ; contraire au cœur minimal (ADR-004) et à la règle B (révéler avant d'élargir).
- **Rediriger sans fermer la session.**
  Insuffisant : la session orpheline persiste et reboucle (`/` vers `/login`).
- **Valider le sujet systématiquement, sans opt-in.**
  Écartée : impose une requête BDD par requête à toute application ; casse la rétrocompatibilité.

## Référence

- Charte : `CHARTE_DOC.md` (principe 11, une seule façon officielle ; principe 7, sécuriser par défaut ; règle B, révéler avant d'élargir).
- [ADR-004](004-core-perimeter.md) : périmètre du cœur minimal.
- [ADR-010](010-auth-session-canonical-api.md) : API canonique auth/session.
- [ADR-014](014-rbac-contract-location.md), [ADR-056](056-rbac-contract-tooling-extraction.md) : contrat et outillage RBAC.
