# Audit AUTH-SECURITY-AUDIT-001

## Résumé

Conclusion : **Cas B — Phase 4.5 saine avec corrections mineures**.

La chaîne Auth/User avancée est globalement saine : les mots de passe sont
hachés, les tokens bruts ne sont pas stockés, les flux email/reset/MFA/OIDC
restent explicites, l'audit et le rate limit n'ont pas d'effet de bord, et la
séparation Auth/User ↔ RBAC est cohérente.

Aucun risque critique bloquant n'a été trouvé. Un point de cohérence doit
toutefois être traité avant de reprendre `REL-M2M-002` : la roadmap marque
`AUTH-ADMIN-003` comme terminé alors que les commandes `auth:user:role:add`,
`auth:user:role:remove` et `auth:user:roles` n'étaient pas dispatchées par la
CLI inspectée pendant l'audit. La documentation de référence corrigeait déjà
cette limite, mais la roadmap et l'état réel du code devaient être réconciliés
dans un ticket court.

Note de suivi : ce point a été traité ensuite par `AUTH-ADMIN-ROLE-CLI-001`,
qui rend les trois commandes réellement dispatchables et aligne la
documentation ainsi que la roadmap.

## Surface auditée

Domaines vérifiés :

- users ;
- passwords ;
- sessions ;
- tokens ;
- email verification ;
- reset password ;
- MFA ;
- OIDC ;
- user_roles / RBAC ;
- CLI admin ;
- audit log ;
- rate limit ;
- docs ;
- tests.

Fichiers inspectés dans le périmètre demandé :

- `core/auth/` ;
- `core/security/rbac.py` ;
- `core/security/session.py` ;
- `forge_cli/auth.py` ;
- `forge.py` ;
- `mvc/models/sql/` ;
- tests liés à auth, RBAC, sécurité et CLI auth ;
- `docs/auth.md` ;
- `docs/rbac.md` ;
- `docs/reference.md` ;
- `docs/roadmap.md` ;
- `docs/audits/`.

## Résultat par domaine

### Users

Correct :

- `AuthUser` reste minimal et explicite ;
- `users.sql` stocke `email`, `password_hash`, `is_active`,
  `email_verified_at`, `last_login_at`, `created_at`, `updated_at` ;
- aucun rôle, token ou secret MFA n'est mélangé dans `users`.

Risque :

- aucun risque critique relevé.

Manque :

- pas d'interface utilisateur générée automatiquement, limite volontaire.

Ticket correctif nécessaire : non.

### Passwords

Correct :

- `hash_password` utilise Argon2id via `argon2.PasswordHasher` ;
- `verify_password` retourne `False` en cas de mot de passe invalide ou de hash
  invalide ;
- les tests vérifient que le mot de passe clair n'apparaît pas dans le hash ;
- les commandes CLI admin ne réaffichent pas le mot de passe ni le hash.

Risque :

- la politique de robustesse minimale du nouveau mot de passe reste simple
  (`len >= 8`) ; c'est cohérent avec le périmètre Forge mais à renforcer côté
  application si nécessaire.

Manque :

- pas de politique de complexité avancée ni de vérification de mot de passe
  compromis.

Ticket correctif nécessaire : non.

### Sessions

Correct :

- `login_user` stocke uniquement l'identifiant Auth/User en session ;
- `logout_user` retire cette clé ;
- `current_user` recharge l'utilisateur via un loader applicatif ;
- `login_required` renvoie `401` ou redirige selon la configuration ;
- la session historique génère des identifiants avec `secrets.token_hex` et
  régénère la session à l'authentification.

Risque :

- le stockage de session historique est en mémoire et documenté comme adapté au
  développement, aux petites applications et au mono-processus.

Manque :

- pas de store de session distribué ni de politique globale de cookies dans ce
  ticket.

Ticket correctif nécessaire : non.

### Tokens

Correct :

- les tokens bruts sont générés avec `secrets.token_urlsafe` ;
- seul `token_hash` est stockable dans `AuthToken` et `auth_tokens.sql` ;
- la vérification utilise `compare_digest` ;
- expiration, `used_at` et `purpose` sont validés ;
- les helpers email/reset retournent le token brut uniquement à l'appelant.

Risque :

- le hash de token est SHA-256 déterministe ; ce choix reste acceptable pour des
  tokens aléatoires forts, mais la durée de vie courte reste importante.

Manque :

- pas de rotation automatique ni purge automatique, volontairement hors
  périmètre.

Ticket correctif nécessaire : non.

### Email verification

Correct :

- `create_email_verification_token` produit un token brut et un `AuthToken`
  hashé ;
- `verify_email_verification_token` vérifie purpose, expiration, usage et hash ;
- `email_verification_timestamp` centralise l'horodatage ;
- aucun envoi email automatique et aucune écriture DB directe.

Risque :

- aucun risque critique relevé.

Manque :

- l'application doit persister le token hashé, envoyer l'email et marquer le
  token comme utilisé.

Ticket correctif nécessaire : non.

### Reset password

Correct :

- `create_password_reset_request` produit un token brut à usage applicatif et un
  enregistrement `AuthToken` hashé ;
- `reset_password_with_token` vérifie le token puis retourne un nouveau
  `password_hash` et `used_at` sans écrire directement en base ;
- le token brut n'est pas stocké dans le résultat final.

Risque :

- la politique de mot de passe reste minimale, comme noté plus haut.

Manque :

- pas de branchement automatique dans une route, pas d'email automatique, pas de
  rate limit automatique.

Ticket correctif nécessaire : non.

### MFA

Correct :

- les facteurs MFA sont représentés par `AuthMfaFactor` ;
- les codes de récupération sont stockables sous forme `code_hash` ;
- les codes bruts de récupération ne sont retournés qu'à la création ;
- le challenge MFA et la revalidation sont stockés en session via des clés
  dédiées ;
- les tests couvrent TOTP, recovery codes, challenge et revalidation.

Risque :

- le champ SQL `secret_hash` contient le secret TOTP vérifiable, pas un hash
  irréversible. C'est nécessaire pour vérifier TOTP mais le nom du champ peut
  être trompeur ; la documentation précise déjà que cette valeur doit être
  protégée comme un secret serveur.

Manque :

- pas de chiffrement applicatif des secrets TOTP, pas de WebAuthn/passkeys.

Ticket correctif nécessaire : non bloquant, à considérer en durcissement futur
si Forge veut imposer une politique de chiffrement applicatif.

### OIDC

Correct :

- le flux local génère `state`, `nonce` et PKCE ;
- le callback vérifie le provider, le state, l'expiration et nettoie la session
  après succès ou expiration ;
- `auth_oidc_accounts.sql` et `auth_oidc_identities.sql` ne stockent pas
  `access_token`, `refresh_token` ni `id_token` ;
- aucun échange réseau ni validation JWT n'est faussement implémenté.

Risque :

- les URLs `http://` sont acceptées au niveau contrat pour laisser un usage
  local ; la documentation doit rester claire sur l'exigence HTTPS en
  production.

Manque :

- pas d'échange token OIDC, pas de validation JWT, pas de stockage token OIDC.

Ticket correctif nécessaire : non.

### User roles / RBAC

Correct :

- `user_roles.sql` reste optionnel et relie `users` à `roles` ;
- `get_user_permissions` lit le flux `user_roles -> roles -> role_permissions
  -> permissions` ;
- `require_user_permission` retourne `401` sans utilisateur connecté et `403`
  sans permission ;
- `@require_permission` historique ne lit pas automatiquement `user_roles` ;
- `can(...)` Jinja reste un helper d'affichage, pas une protection serveur.

Risque :

- aucun risque critique relevé sur la séparation des deux modes.

Manque :

- l'administration CLI des associations `user_roles` était annoncée terminée
  dans la roadmap mais non dispatchée dans la CLI inspectée pendant l'audit.

Ticket correctif nécessaire : oui, ticket court de cohérence CLI/roadmap.

### CLI admin

Correct :

- les commandes disponibles (`auth:user:create`, `auth:user:list`,
  `auth:user:show`, `auth:user:disable`, `auth:user:enable`,
  `auth:user:password`) n'affichent pas de secret ;
- la création et le changement de mot de passe hachent avec l'API Auth ;
- les sorties publiques masquent `password_hash`, `token_hash` et `secret_hash`
  dans les tests ;
- `auth:init` crée ou préserve les SQL optionnels sans appliquer le SQL.

Risque :

- la CLI ne dispatch pas les commandes de rôle utilisateur indiquées comme
  terminées par `AUTH-ADMIN-003`.

Manque :

- `auth:user:role:add`, `auth:user:role:remove`, `auth:user:roles` doivent être
  soit implémentées, soit reclassées explicitement dans la roadmap.

Ticket correctif nécessaire : oui.

### Audit log

Correct :

- `AuthAuditEvent` est une dataclass sans effet de bord ;
- `create_auth_audit_event` ne fait aucun accès DB, fichier, notification ou
  branchement automatique ;
- `sanitize_auth_audit_metadata` retire les clés sensibles connues ;
- `auth_audit_log.sql` contient les colonnes et index attendus.

Risque :

- la sanitation porte sur les clés de premier niveau ; les métadonnées
  imbriquées doivent rester sous contrôle de l'application.

Manque :

- pas de stockage automatique, pas de consultation CLI/HTML.

Ticket correctif nécessaire : non.

### Rate limit

Correct :

- `AuthRateLimitAttempt`, `AuthRateLimitRule` et `AuthRateLimitDecision`
  modélisent le calcul sans effet de bord ;
- `check_auth_rate_limit` compte uniquement les échecs `success=False` sur
  `action + key`, dans la fenêtre temporelle ;
- les succès, autres actions, autres clés et tentatives hors fenêtre sont
  ignorés ;
- `auth_rate_limit_attempts.sql` stocke `rate_key` et non `key` ;
- aucun branchement automatique dans login/reset/MFA/OIDC.

Risque :

- le calcul dépend de tentatives chargées correctement par l'application.

Manque :

- pas de purge, pas de middleware global, pas de stockage automatique.

Ticket correctif nécessaire : non.

### Docs

Correct :

- `docs/auth.md` présente la brique Auth/User comme optionnelle, explicite et
  sans ORM ;
- `docs/rbac.md` clarifie la séparation RBAC historique / Auth/User RBAC ;
- `docs/reference.md` liste les commandes Auth réellement dispatchables et
  indique que `auth:user:role:*` n'est pas exposé actuellement.

Risque :

- `docs/roadmap.md` contenait encore `AUTH-SECURITY-AUDIT-001` comme prochain
  ticket et `AUTH-ADMIN-003` comme terminé malgré l'écart CLI.

Manque :

- roadmap à mettre à jour avec la conclusion de cet audit.

Ticket correctif nécessaire : oui pour la cohérence `AUTH-ADMIN-003`.

### Tests

Correct :

- les contrats Auth/User sont couverts ;
- les cas invalides sont largement testés ;
- l'absence d'accès DB direct est testée pour les briques qui doivent rester
  pures ;
- l'absence de branchement automatique audit/rate limit est testée ;
- l'absence de routes/templates/interfaces non prévues est testée ;
- la CLI admin est testée pour éviter l'affichage de secrets.

Risque :

- aucun test ne prouve l'existence des commandes `auth:user:role:*`, ce qui
  confirme l'écart roadmap/code plutôt qu'un simple oubli documentaire.

Manque :

- couverture à ajouter dans le ticket correctif si les commandes de rôles sont
  implémentées.

Ticket correctif nécessaire : oui, lié au ticket CLI/roadmap.

## Points critiques

Vérifications explicites :

- aucun mot de passe clair stocké : **OK** ;
- aucun token brut stocké : **OK** ;
- aucun secret TOTP exposé inutilement : **OK avec vigilance** sur le champ
  `secret_hash`, qui contient le secret TOTP vérifiable et doit être protégé ;
- aucun recovery code brut stocké : **OK** ;
- aucun `access_token`, `refresh_token` ou `id_token` stocké dans
  `auth_oidc_accounts` : **OK** ;
- les décorateurs `401` / `403` restent cohérents : **OK** ;
- `require_user_permission` ne casse pas `@require_permission` : **OK** ;
- Jinja `can(...)` ne remplace pas la protection serveur : **OK** ;
- rate limit non annoncé comme automatique : **OK** ;
- audit log ne stocke pas de secrets dans metadata : **OK au premier niveau** ;
- `auth:init` ne crée pas de données réelles : **OK** ;
- les SQL optionnels restent visibles et audités : **OK**.

## Documentation

`docs/auth.md`, `docs/rbac.md` et `docs/reference.md` ne promettent pas de flux
automatiques inexistants pour login/reset/MFA/OIDC/audit/rate limit.

La documentation de référence est plus exacte que la roadmap sur les commandes
de rôles utilisateur : elle indique explicitement que `auth:user:role:*` n'est
pas exposé par la CLI actuelle. La roadmap est donc mise à jour par ce ticket
pour refléter l'audit et recommander un ticket correctif ciblé.

## Tests

Couverture constatée :

- contrats : users, tokens, reset, MFA, OIDC, audit, rate limit, user_roles ;
- cas invalides : identifiants, types, secrets, tokens, règles rate limit ;
- absence d'accès DB direct : password, audit, rate limit, diagnostics CLI ;
- absence de branchement automatique : audit et rate limit ;
- absence de routes/templates/interfaces : audit et rate limit ;
- CLI admin : pas d'affichage de mot de passe, hash, token ou secret.

Aucun test fonctionnel n'a été ajouté dans ce ticket d'audit. Le seul écart
trouvé appelle un ticket correctif dédié plutôt qu'un test documentaire isolé.

## Conclusion

### Cas B — Phase 4.5 saine avec corrections mineures

La Phase 4.5 est saine sur le socle Auth/User : les briques de sécurité sont
explicites, testées et correctement bornées. Il n'y a pas de risque critique
nécessitant de bloquer pour vulnérabilité immédiate.

Avant de reprendre la Phase 5 avec `REL-M2M-002`, Forge devrait traiter un
ticket court de cohérence sur l'administration CLI des rôles utilisateur :
réconcilier `AUTH-ADMIN-003`, la CLI réelle, les tests et la roadmap.

## Tickets recommandés

| Ticket | Priorité | Objectif |
|---|---|---|
| AUTH-ADMIN-ROLE-CLI-001 | traité | Aligner les commandes CLI de rôles utilisateur avec `AUTH-ADMIN-003`, la documentation et les tests. |
