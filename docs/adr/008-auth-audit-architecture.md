# ADR-008 — Architecture de l'audit auth

## Statut

Acceptée — Forge 2.10.0 (ticket AUTH-AUDIT-CLARIFY-ARCHITECTURE-001).

---

## Contexte

Forge fournit un mécanisme d'audit pour les événements d'authentification :
connexions, échecs, déconnexions, changements de mot de passe, challenges MFA,
opérations d'administration, etc.

Plusieurs niveaux d'infrastructure sont possibles :

1. **Logging Python seul** — vers stdout, fichier, agrégateur configuré par l'app.
2. **Persistance SQL** — table dédiée alimentée par Forge à chaque événement.
3. **Stream externe** — Kafka, Loki, Sentry, ou tout handler Python logging.

Chaque niveau a des contraintes opérationnelles différentes : rétention, performance,
interrogeabilité, conformité RGPD, reporting, purge.

La question de ce ticket : à quoi Forge s'engage-t-il exactement, et où commence
la responsabilité de l'application ?

L'architecture existait déjà avant ce ticket, mais n'était pas documentée.
Un développeur découvrant la table SQL `auth_audit_log` sans documentation
pouvait croire que Forge la remplissait automatiquement. Ce n'est pas le cas —
et ce n'est pas un oubli, c'est une décision.

---

## Décision

Forge fournit **trois briques distinctes**, sans les assembler automatiquement :

### Brique 1 — Contrat d'événement (`core.auth.audit.AuthAuditEvent`)

Structure validée, 20+ types d'événements normalisés. Garantie de format pour
tout consommateur d'audit, qu'il soit SQL, fichier, ou agrégateur externe.

Constantes disponibles via `core.auth.audit` :

```
login.success          login.failed           logout
password_reset.requested  password_reset.completed  email.verified
mfa.challenge.required    mfa.challenge.success     mfa.challenge.failed
mfa.revalidation.success  mfa.revalidation.failed   mfa.rate_limited
mfa.revalidation.identity_mismatch
user.disabled          user.enabled           user.password_changed
user_role.added        user_role.removed      user.not_found
oidc.account_linked
```

### Brique 2 — Émission Python (`safe_log_auth_event`, `log_auth_event`)

Les événements sont émis vers le logger Python `forge.auth.audit`.
La configuration du handler — et donc du destinataire final — est **applicative**.

Par défaut, les événements INFO/WARNING remontent au logging Python standard
(visible via `journalctl`, `stderr`, ou tout handler configuré par l'app).

Forge ne configure aucun handler. L'application choisit où vont les événements.

### Brique 3 — Table SQL latente (`auth_audit_log`)

Le fichier `mvc/models/sql/auth_audit_log.sql` définit un schéma prêt à
recevoir des audits persistants.

**Forge n'écrit pas dans cette table.** La table est fournie comme infrastructure
optionnelle — l'application décide si elle veut persister, quand, et comment.

---

## Ce que Forge ne fait pas

- Forge ne décide pas de la rétention (combien de temps garder les audits).
- Forge ne décide pas du destinataire (fichier, base, Sentry, Kafka...).
- Forge ne fait pas de purge automatique.
- Forge ne fournit pas d'API de lecture ou de recherche d'audits.
- Forge ne configure pas de handler logging pour `forge.auth.audit`.

Ces choix sont **applicatifs**, pas frameworkiques.

---

## Comment une application Forge persiste ses audits

### Approche A — Handler Python logging qui insère en base

L'application configure le logger `forge.auth.audit` avec un handler SQL :

```python
import logging
import json


class AuditSqlHandler(logging.Handler):
    """Handler logging qui persiste les événements d'audit en base."""

    def emit(self, record):
        try:
            # record.msg est l'AuthAuditEvent émis par log_auth_event
            event = record.msg
            insert_auth_audit(
                event_type=event.event_type,
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                metadata_json=json.dumps(event.metadata or {}),
            )
        except Exception:
            # Ne jamais bloquer le login en cas d'échec d'audit
            self.handleError(record)


logging.getLogger("forge.auth.audit").addHandler(AuditSqlHandler())
```

`insert_auth_audit` est une fonction de l'application qui fait l'INSERT.

### Approche B — Wrapper applicatif explicite

L'application crée son propre `audit_and_persist(event_type, **kwargs)` qui :
1. Appelle `safe_log_auth_event(...)` (logging Python)
2. Insère dans `auth_audit_log` (SQL)

Les contrôleurs de l'application utilisent ce wrapper à la place de la fonction
Forge directement. Avantage : lisibilité, testabilité, pas de couplage via les
handlers logging.

### Approche C — Stream externe (Loki, Sentry, Kafka)

Configurer un handler logging qui pousse les événements vers le système externe.
La table SQL Forge n'est pas utilisée. Convient aux architectures avec un bus
d'événements centralisé.

---

## Conséquences

- Forge reste minimal (principe 8) : pas de table dynamiquement remplie,
  pas de purge à gérer, pas d'API de lecture.
- L'application a toute liberté sur sa stratégie d'audit (principe 1).
- Une application qui ne fait rien aura quand même un audit Python
  fonctionnel (capturable via `journalctl`, `stderr`, ou un handler basique).
- Documentation explicite requise pour que le développeur ne croie pas
  que Forge persiste les audits par défaut (principe 3, refuser la magie cachée).

---

## Vérification

Le test `tests/test_auth_audit_table.py` garantit que Forge ne génère pas de
code `INSERT INTO auth_audit_log` dans ses modules productifs :

```python
assert "INSERT INTO auth_audit_log" not in generated
```

Le test `tests/test_auth_audit_architecture_001.py` vérifie que cette ADR existe,
que `core/auth/audit.py` ne fait pas d'INSERT, et que la documentation décrit
l'architecture.

---

## Alternatives considérées

**Fournir un `persist_auth_audit_event()` dans `core/`** — rejeté. La persistance
est applicative par définition : rétention, index, purge, conformité RGPD, choix
du backend. Forge ne peut pas décider à la place de l'application.

**Remplir `auth_audit_log` automatiquement dans les contrôleurs Forge** — rejeté.
Cela forcerait toutes les applications à avoir une table d'audit SQL, même celles
qui utilisent un agrégateur externe. Viole le principe 8 (noyau minimal) et le
principe 1 (séparation framework / application métier).

**Supprimer `auth_audit_log.sql`** — non retenu. La table est utile comme point
de départ pour les applications qui veulent persister en SQL. La fournir évite
aux développeurs de la recréer manuellement.

---

## Tickets dépendants

- `AUTH-AUDIT-CLARIFY-ARCHITECTURE-001` — ce ticket (documentation)
- `AUTH-AUDIT-001` — implémentation initiale du contrat et du logging
- Futur `forge-mvc-audit-sql` (post-3.x) — module optionnel officiel de persistance
  SQL, si la demande le justifie
