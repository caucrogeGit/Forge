# ADR-011 — Périmètre du vocabulaire d'audit auth dans le core

## Statut

Acceptée — Forge 1.0.0-beta.3 (ticket AUTH-AUDIT-VOCAB-PERIMETER-001).

---

## Contexte

`core/auth/audit.py` déclare 20+ constantes d'événements d'audit, dont des noms
qui font référence à MFA (`mfa.challenge.required`, `mfa.challenge.failed`, etc.)
et à RBAC (`user_role.added`, `user_role.removed`).

Un contributeur pourrait croire que ces noms constituent une pollution du core par
les modules opt-in `forge-mvc-mfa` et `forge-mvc-rbac`. Ce n'est pas le cas.

Ce document tranche la question une fois pour toutes et établit la règle
opérationnelle qui distingue **vocabulaire d'audit générique acceptable** et
**logique fonctionnelle interdite dans le core**.

---

## Décision

### Règle 1 — Le vocabulaire d'audit MFA/RBAC est assumé dans le core

Les constantes de `core/auth/audit.py` sont des **noms d'événements de sécurité**,
pas des implémentations fonctionnelles. Nommer un événement `mfa.challenge.required`
n'intègre pas la logique TOTP dans le core. Nommer un événement `user_role.added`
n'intègre pas le système de permissions RBAC dans le core.

Ces noms servent à tracer uniformément des événements de sécurité, quel que soit
le backend de persistance — SQL, fichier, agrégateur externe.

**Événements MFA acceptés dans le core :**

```
mfa.challenge.required
mfa.challenge.success
mfa.challenge.failed
mfa.revalidation.success
mfa.revalidation.failed
mfa.rate_limited
mfa.revalidation.identity_mismatch
```

**Événements RBAC acceptés dans le core :**

```
user_role.added
user_role.removed
```

Ces événements sont acceptés parce qu'ils décrivent des faits de sécurité
observables sans nécessiter d'importer la logique MFA ou RBAC complète.

### Règle 2 — La logique fonctionnelle MFA/RBAC reste hors core

Le core ne doit pas intégrer :

- le stockage du secret TOTP ;
- la génération ou la vérification d'un code TOTP ;
- le provisioning MFA ;
- la résolution complète des permissions RBAC ;
- les décorateurs RBAC avancés (`@require_permission`, `@require_user_permission`).

Ces comportements appartiennent aux modules opt-in :

| Fonctionnalité | Module responsable |
|---|---|
| MFA TOTP, codes de récupération, revalidation | `forge-mvc-mfa` |
| Permissions fines, rôles, décorateurs RBAC | `forge-mvc-rbac` |

### Règle 3 — Frontière d'import inviolable

**Le core ne doit jamais importer :**

```python
import forge_mvc_mfa      # interdit dans core/
import forge_mvc_rbac     # interdit dans core/
import pyotp              # interdit dans core/
```

Ces imports sont légitimes dans :

- `packages/forge-mvc-mfa/` — module MFA opt-in
- `packages/forge-mvc-rbac/` — module RBAC opt-in
- `tests/` — tests des modules opt-in (avec `pytest.importorskip`)
- `docs/` — exemples d'utilisation

### Règle 4 — `require_role` est une primitive core légère

`core/security/decorators.require_role(role)` est un décorateur basé sur
`core.security.session.user_has_role()` — il lit le rôle de la session.
Il n'importe pas `forge_mvc_rbac` et ne constitue pas une implémentation RBAC
complète.

C'est une primitive de sécurité basique, documentée comme telle. La frontière
est explicite :

- `require_role(role)` dans `core/security/` → session-based, monolithique, core
- `require_permission(code)` dans `forge_mvc_rbac` → RBAC fin, opt-in

---

## Rappel — Décisions connexes

| ADR | Décision liée |
|---|---|
| ADR-004 | `core/auth/audit.py` reste dans le core (pas dans un opt-in) — voir section « Décision complémentaire » |
| ADR-008 | Architecture de l'audit auth : contrat + émission Python + table SQL latente |

Ces deux ADR établissent que `core/auth/audit.py` est intentionnellement dans le
core pour être consommé par les opt-ins (notamment `forge-mvc-mfa`) sans créer
de dépendance circulaire.

---

## Ce que ce document ne traite pas

- La stratégie de stockage du secret MFA (voir ticket MFA-SECRET-STORAGE-POLICY-001).
- La documentation RBAC light vs RBAC complet opt-in (voir ticket RBAC-LIGHT-VS-FULL-DOC-001).
- La publication des paquets opt-in sur PyPI (voir ticket OPTIN-PACKAGES-PUBLICATION-POLICY-001).
- Le comportement de `forge doctor` pour les dépendances MFA manquantes (voir ticket AUTH-DOCTOR-MFA-MISSING-DEP-WARNING-001).

---

## Conséquences

- Aucun comportement runtime n'est modifié par cet ADR.
- Les noms d'événements MFA/RBAC dans `core/auth/audit.py` sont officiellement
  assumés — ils ne sont pas à supprimer ni à renommer.
- La frontière d'import est vérifiable par un garde-fou méta automatique.
- Toute future constante d'événement en rapport avec MFA ou RBAC est acceptable
  dans `core/auth/audit.py` si elle décrit un fait de sécurité sans intégrer
  de logique fonctionnelle opt-in.
