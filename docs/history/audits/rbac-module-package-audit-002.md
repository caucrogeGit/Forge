# Audit — Package RBAC opt-in existant

**Ticket** : RBAC-MODULE-002-AUDIT-AND-LOCK-EXISTING-RBAC-PACKAGE
**Date** : 2026-05-20
**Statut** : audit terminé, package verrouillé

---

## 1. Résumé

Le package `forge-mvc-rbac` (version `1.0.0b5`) est substantiellement implémenté.
Il expose une API publique complète : `has_permission`, `require_permission`,
`require_user_permission`, `PermissionDenied`, `make_can`, helpers Jinja,
resolver SQL, modèles `Role` / `Permission`.

274 tests passent dans `tests/` (aucun dans `packages/forge-mvc-rbac/` — les
tests du package vivent dans le répertoire de tests principal du monorepo).

Le seul chaînon absent : la lecture de `mvc/security/rbac.json` au runtime.
Toute la résolution de permissions passe aujourd'hui par les tables SQL
(`roles`, `permissions`, `role_permissions`, `user_roles`) ou par la session.

---

## 2. Contexte

RBAC-MODULE-001 a conclu que le module existait avec des fonctionnalités
substantielles, et que le chaînon manquant était le chargement du contrat
déclaratif `mvc/security/rbac.json`. Ce ticket vérifie et verrouille cet état.

---

## 3. Méthode d'audit

### Commandes exécutées

```bash
find packages/forge-mvc-rbac -maxdepth 4 -type f | sort
cat packages/forge-mvc-rbac/pyproject.toml
cat packages/forge-mvc-rbac/forge_mvc_rbac/__init__.py
cat packages/forge-mvc-rbac/forge_mvc_rbac/rbac.py
cat packages/forge-mvc-rbac/forge_mvc_rbac/authorization.py
cat packages/forge-mvc-rbac/forge_mvc_rbac/resolver.py
cat packages/forge-mvc-rbac/forge_mvc_rbac/jinja.py
cat packages/forge-mvc-rbac/forge_mvc_rbac/user_rbac.py
python -m pytest packages/forge-mvc-rbac -q
python -m pytest tests/test_rbac_models.py tests/test_rbac_authorization.py \
  tests/test_rbac_jinja.py tests/test_rbac_security.py tests/test_rbac_sql.py \
  tests/test_auth_user_rbac.py tests/test_auth_user_rbac_resolver.py \
  tests/test_auth_user_rbac_route.py tests/test_make_crud_rbac.py \
  tests/test_crud_rbac_ui.py -q
```

### Zones auditées

- Structure complète de `packages/forge-mvc-rbac/`
- Tous les modules Python du package
- SQL fourni par le package
- Tests RBAC dans `tests/`

---

## 4. Structure du package

| Élément | État | Commentaire |
|---|---|---|
| `packages/forge-mvc-rbac/` | Présent | Package autonome dans le monorepo |
| `pyproject.toml` | Présent | version `1.0.0b5`, dépend de `forge-mvc>=1.0.0b5` |
| `forge_mvc_rbac/__init__.py` | Présent | API publique complète, auto-enregistrement Jinja |
| `forge_mvc_rbac/rbac.py` | Présent | Modèles, normalisation, `has_permission`, `require_permission`, `PermissionDenied`, `make_can` |
| `forge_mvc_rbac/authorization.py` | Présent | `auth_user_can`, `require_user_permission` (Auth/User) |
| `forge_mvc_rbac/resolver.py` | Présent | `user_has_permission`, `get_user_permissions`, `get_user_role_ids` — résolution SQL |
| `forge_mvc_rbac/user_rbac.py` | Présent | `AuthUserRole`, association user ↔ role |
| `forge_mvc_rbac/jinja.py` | Présent | `make_auth_jinja_context`, `make_auth_jinja_can`, `AuthJinjaUser` |
| `sql/rbac.sql` | Présent | Tables `roles`, `permissions`, `role_permissions` |
| `sql/user_roles.sql` | Présent | Table `user_roles` (pivot user ↔ role) |
| Tests dans `packages/` | Absent | Les tests vivent dans `tests/` du monorepo |
| Distributions `dist/` | Présentes | `1.0.0b4` et `1.0.0b5` en `.whl` et `.tar.gz` |

---

## 5. API publique existante

### Fonctions et classes exposées par `__init__.py`

| Symbole | Module source | Rôle |
|---|---|---|
| `has_permission(request, code)` | `rbac.py` | Retourne `True` si la permission est présente |
| `require_permission(code)` | `rbac.py` | Décorateur → `Response(403)` si absent (session legacy) |
| `require_user_permission(code)` | `authorization.py` | Décorateur → `Response(403)` si absent (Auth/User) |
| `auth_user_can(request, permission)` | `authorization.py` | Helper boolean Auth/User |
| `PermissionDenied` | `rbac.py` | Exception définie (non levée par `require_permission`) |
| `RbacValidationError` | `rbac.py` | Validation des codes et slugs |
| `Role` | `rbac.py` | Modèle de rôle sans ORM |
| `Permission` | `rbac.py` | Modèle de permission sans ORM |
| `normalize_role_slug(name)` | `rbac.py` | `"Super Admin"` → `"super-admin"` |
| `normalize_permission_code(code)` | `rbac.py` | `"Posts.Edit"` → `"posts.edit"` |
| `validate_role(name, slug)` | `rbac.py` | Lève `RbacValidationError` si invalide |
| `validate_permission(code)` | `rbac.py` | Lève `RbacValidationError` si invalide |
| `make_can(request)` | `rbac.py` | Retourne `can(code) -> bool` pour Jinja |
| `get_request_permissions(request)` | `rbac.py` | Résout les permissions depuis session/injection |
| `user_has_permission(user_id, code)` | `resolver.py` | Résolution SQL (via tables `user_roles`, `role_permissions`) |
| `get_user_permissions(user_id)` | `resolver.py` | Toutes les permissions effectives d'un utilisateur |
| `get_user_role_ids(user_id)` | `resolver.py` | IDs de rôles d'un utilisateur |
| `AuthUserRbacResolverError` | `resolver.py` | Erreur de résolution SQL |
| `FetchAll` | `resolver.py` | Type callable pour injecter la lecture SQL |
| `AuthJinjaUser` | `jinja.py` | Représentation publique d'un utilisateur pour templates |
| `sanitize_jinja_user(user)` | `jinja.py` | Nettoie un utilisateur pour exposition Jinja |
| `get_jinja_current_user(request)` | `jinja.py` | Utilisateur courant pour templates |
| `make_auth_jinja_can(request)` | `jinja.py` | Helper `can` pour templates |
| `make_auth_jinja_context(request)` | `jinja.py` | Contexte complet `{current_user, is_authenticated, can}` |
| `make_auth_jinja_context_with_can(request)` | `jinja.py` | Wrapper pour registre core |
| `AuthUserRole` | `user_rbac.py` | Association user ↔ role (dataclass) |
| `create_auth_user_role(user_id, role_id)` | `user_rbac.py` | Construit une association validée |
| `auth_user_role_key(association)` | `user_rbac.py` | Clé stable `user_id:role_id` |
| `auth_user_roles_match(left, right)` | `user_rbac.py` | Compare deux associations |
| `is_valid_auth_user_role(association)` | `user_rbac.py` | Validateur booléen |

### Détail `require_permission`

```python
def require_permission(permission_code: str):
    # Valide le code à la décoration, retourne Response(403) si absent.
    # NE lève PAS PermissionDenied — retourne un objet Response.
```

`require_permission` retourne `Response(403)` directement. `PermissionDenied` est
défini comme classe d'exception mais n'est pas levé par ce décorateur — il est
disponible pour l'usage applicatif.

### Auto-enregistrement Jinja

```python
try:
    from core.mvc.controller.registry import register_jinja_context_provider
    from forge_mvc_rbac.jinja import make_auth_jinja_context_with_can
    register_jinja_context_provider(make_auth_jinja_context_with_can)
except ImportError:
    pass
```

Le module s'auto-enregistre dans le registre de contexte Jinja de core
à l'import, sans exception si core n'est pas disponible.

---

## 6. Tests existants ou ajoutés

### Tests dans `tests/` (monorepo)

| Fichier | Tests | Ce qu'il couvre |
|---|---|---|
| `test_rbac_models.py` | 37 | `Role`, `Permission`, normalisation, validation |
| `test_rbac_authorization.py` | 24 | `has_permission`, `require_permission`, `PermissionDenied` |
| `test_rbac_security.py` | 40 | Intégration sécurité RBAC |
| `test_rbac_jinja.py` | 23 | Helpers Jinja, `make_can`, `AuthJinjaUser` |
| `test_rbac_sql.py` | 23 | Schémas SQL (tables, colonnes, contraintes) |
| `test_auth_user_rbac.py` | 30 | `AuthUserRole`, associations user ↔ role |
| `test_auth_user_rbac_resolver.py` | 26 | `user_has_permission`, `get_user_permissions` |
| `test_auth_user_rbac_route.py` | 15 | `require_user_permission` sur routes |
| `test_make_crud_rbac.py` | 34 | Génération CRUD avec guards RBAC |
| `test_crud_rbac_ui.py` | 22 | Interface CRUD avec permissions |
| **Total** | **274** | **tous passent** |

### Tests dans `packages/forge-mvc-rbac/`

Aucun — les tests du package vivent dans `tests/` du monorepo. Comportement
attendu pour un monorepo Forge (conforme au pattern établi pour les autres
packages opt-in).

### Tests ajoutés dans ce ticket

Aucun test supplémentaire ajouté. L'API existante est déjà verrouillée par
274 tests qui passent.

---

## 7. Packaging et dépendances

| Élément | Valeur |
|---|---|
| Nom PyPI | `forge-mvc-rbac` |
| Version | `1.0.0b5` |
| Python | `>=3.12` |
| Dépendances | `forge-mvc>=1.0.0b5,<2` — uniquement le core Forge |
| Build system | `setuptools>=77.0.3` |
| Distributions buildées | `dist/forge_mvc_rbac-1.0.0b4-py3-none-any.whl`, `1.0.0b5-py3-none-any.whl` |
| Licence | Propriétaire Forge |

Aucune dépendance externe (pas de `jsonschema`, pas de `sqlalchemy`, pas de
bibliothèque tiers). Le package dépend uniquement de `forge-mvc`.

---

## 8. Limites actuelles

| Limite | Description |
|---|---|
| `mvc/security/rbac.json` non chargé | Le module ne lit pas le contrat déclaratif au runtime |
| Résolution uniquement SQL | Les permissions sont résolues depuis les tables `roles`/`permissions`/`user_roles` ou la session, pas depuis le fichier RBAC |
| Non branché aux routes Forge | Aucune route Forge n'applique le RBAC automatiquement |
| `make:crud` core reste neutre | Le CRUD core ne lit pas `mvc/security/rbac.json` |
| `rbac:validate` valide sans appliquer | La commande CLI valide le contrat mais ne le charge pas au runtime |
| `require_permission` retourne `Response(403)` | Ne lève pas `PermissionDenied` — distinction à documenter |
| Tests dans `packages/` | Aucun test dans le répertoire du package lui-même |

---

## 9. Décision

**Le package `forge-mvc-rbac` existant est conservé comme base du module RBAC
opt-in de Forge.**

L'API est stable, bien testée (274 tests) et couvre les besoins fondamentaux.
Le prochain ticket doit connecter le module au contrat `mvc/security/rbac.json`
sans perturber l'API existante.

---

## Mise en œuvre partielle — RBAC-MODULE-007

RBAC-MODULE-007 documente l'usage applicatif complet du RBAC opt-in : contrat,
validation, audit, helpers Python, guards opt-in et limites.

- Nouvelle page : `docs/security/rbac-usage.md` — guide complet en 7 étapes
- `docs/security/rbac-contract.md` mis à jour : sections obsolètes corrigées,
  lien vers le guide d'usage, limites actualisées
- `mkdocs.yml` mis à jour : page `RBAC — Usage applicatif` ajoutée
- 17 tests documentaires dans `tests/meta/test_rbac_application_usage_docs_007.py`
- Aucun runtime modifié — documentation uniquement

---

## Mise en œuvre partielle — RBAC-MODULE-006

RBAC-MODULE-006 ajoute la commande `forge rbac:audit` pour auditer la cohérence
fonctionnelle du contrat `mvc/security/rbac.json`.

- Nouveau module : `forge_cli/rbac_audit.py`
- Dispatch ajouté dans `forge.py` : `rbac:audit`
- Aide mise à jour dans `forge_cli/help.py`
- 21 tests ajoutés dans `tests/test_rbac_audit_command.py`
- Documentation mise à jour dans `docs/security/rbac-contract.md`
- Codes d'avertissement : `missing_roles`, `missing_entities`, `empty_role`,
  `entity_without_permissions`, `missing_crud_action`, `role_permission_not_declared`,
  `entity_permission_unused`
- Contrat absent → exit 0 (RBAC optionnel)
- Contrat invalide → exit 1
- Contrat valide (avec ou sans avertissements) → exit 0
- `make:crud` core inchangé — audit uniquement opt-in

---

## Mise en œuvre partielle — RBAC-MODULE-005

RBAC-MODULE-005 ajoute un helper opt-in permettant d'utiliser les permissions
contractuelles dans une route ou un contrôleur.

- `get_request_roles(request)` — extrait les rôles depuis `request.roles` ou la session
- `require_contract_permission_for_request(request, permission, project_root)` — helper direct
- `contract_permission_required(permission, project_root)` — décorateur
- 27 tests ajoutés dans `tests/test_rbac_contract_guards.py`
- `make:crud` core inchangé — protection uniquement opt-in

---

## Mise en œuvre partielle — RBAC-MODULE-004

RBAC-MODULE-004 connecte le contrat chargé au service de permissions contractuelles.

- Nouvelles fonctions dans `forge_mvc_rbac/contract.py` :
  `get_contract_permissions`, `has_contract_permission`, `require_contract_permission`
- Nouveaux exports publics dans `__init__.py`
- 35 tests ajoutés dans `tests/test_rbac_contract_permissions.py`
- `require_contract_permission` retourne `None` (accordé) ou `Response(403)` (refusé)
- `has_permission` et `require_permission` existants inchangés

---

## Mise en œuvre partielle — RBAC-MODULE-003

RBAC-MODULE-003 ajoute le chargement validé de `mvc/security/rbac.json` depuis
le module `forge-mvc-rbac`.

- Nouveau module : `forge_mvc_rbac/contract.py`
- Nouveaux exports publics : `load_rbac_contract`, `RbacContractResult`, `RbacContractError`
- 30 tests ajoutés dans `tests/test_rbac_contract_loader.py`
- Le chargeur est lecture seule : aucun fichier créé ni modifié
- La limite "mvc/security/rbac.json non chargé" ci-dessus est levée

---

## 10. Tickets futurs proposés

| Ticket | Objectif |
|---|---|
| RBAC-MODULE-003 | ~~Charger et valider `mvc/security/rbac.json` depuis le module~~ — livré |
| RBAC-MODULE-004 | ~~Connecter le contrat chargé au service de permissions~~ — livré |
| RBAC-MODULE-005 | ~~Brancher les permissions sur routes / contrôleurs en opt-in~~ — livré |
| RBAC-MODULE-006 | ~~Ajouter la commande `forge rbac:audit`~~ — livré |
| RBAC-MODULE-007 | ~~Documenter l'usage RBAC applicatif complet~~ — livré |
| RBAC-MODULE-CLOSE-001 | ~~Clôturer le bloc RBAC applicatif~~ — livré |

---

## Clôture — RBAC-MODULE-CLOSE-001

**Date** : 2026-05-20
**Statut** : terminé.

Le bloc RBAC applicatif opt-in est clôturé après livraison de :

- **RBAC-MODULE-001** — définition du rôle du module RBAC opt-in ;
- **RBAC-MODULE-002** — audit et verrouillage du package `forge-mvc-rbac` ;
- **RBAC-MODULE-003** — chargement de `mvc/security/rbac.json` depuis le module (`load_rbac_contract`) ;
- **RBAC-MODULE-004** — connexion du contrat au service de permissions (`has_contract_permission`, `require_contract_permission`) ;
- **RBAC-MODULE-005** — guards opt-in pour routes / contrôleurs (`require_contract_permission_for_request`, `contract_permission_required`) ;
- **RBAC-MODULE-006** — commande `forge rbac:audit` ;
- **RBAC-MODULE-007** — documentation d'usage applicatif (`docs/security/rbac-usage.md`).

### État final

| Élément | Statut |
|---|---|
| `mvc/security/rbac.json` | contrat RBAC applicatif (optionnel, validable) |
| `rbac.schema.json` | présent dans les registres `schemas/` et `forge_cli/schemas/` |
| `forge rbac:validate` | opérationnel — valide la structure JSON |
| `forge rbac:audit` | opérationnel — audite la cohérence fonctionnelle |
| `load_rbac_contract` | exporté par `forge_mvc_rbac` |
| `has_contract_permission` | exporté par `forge_mvc_rbac` |
| `require_contract_permission_for_request` | exporté par `forge_mvc_rbac` |
| `contract_permission_required` | exporté par `forge_mvc_rbac` |
| `make:crud` core | neutre — ne lit pas `mvc/security/rbac.json` |
| Routes automatiquement protégées | NON — guards opt-in explicites uniquement |
| Cache applicatif RBAC | NON — lecture directe du contrat à chaque appel |
| Publication PyPI | NON effectuée dans ce bloc |
| Tag créé | NON |

### Traces intentionnelles restantes

| Fichier | Trace | Justification |
|---|---|---|
| `forge_cli/entities/make_crud.py` | `definition.get("rbac")` | Mécanisme interne existant, indépendant du contrat séparé |
| `forge_cli/entities/validation.py` | `ALLOWED_ROOT_KEYS` inclut `rbac` | Pipeline interne du format d'entité |
| `forge_cli/entities/crud/controller_builder.py` | Guards `@require_permission` | Génération conditionnelle depuis le format interne |
| `tests/test_make_crud_rbac.py` | 34 tests format interne | Garde-fous actifs pour le mécanisme A |
| `tests/test_crud_rbac_ui.py` | 22 tests guards UI | Garde-fous actifs pour le mécanisme A |
