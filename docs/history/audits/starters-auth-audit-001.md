# STARTERS-AUTH-AUDIT-001 — Audit Auth des starters

## Résumé

Audit des 5 starters Forge pour vérifier la conformité à ADR-001 (core.auth = API officielle Forge 2.x, Argon2id = format officiel).

Un seul starter utilise l'API legacy PBKDF2 (`suivi-comportement-eleves`). Il a été corrigé dans ce ticket.

## Tableau des starters

| Starter | Auth présente ? | Hash utilisé avant audit | Module utilisé avant audit | Action |
|---|---|---|---|---|
| 1 — contact-simple | Non | — | — | Aucune |
| 2 — utilisateurs-auth | Oui | Argon2id | `core.auth` (hash_password, verify_password) | Aucune — déjà conforme |
| 3 — carnet-contacts | Non | — | — | Aucune |
| 4 — suivi-comportement-eleves | Oui | PBKDF2 | `core.security.hashing` | **Corrigé** |
| 5 — communes-sejours | Non | — | — | Aucune |

## Usages legacy trouvés

Starter `suivi-comportement-eleves` — 2 fichiers :

### `files/scripts/create_auth_user.py`

```python
# Avant
from core.security.hashing import hacher_mot_de_passe
...
hacher_mot_de_passe(PASSWORD)
```

Ce script crée l'utilisateur de démo à la première installation. Le hash produit était PBKDF2.

### `files/mvc/controllers/auth_controller.py`

```python
# Avant
from core.security.hashing import enregistrer_tentative, est_limite, verifier_mot_de_passe
...
and verifier_mot_de_passe(password, utilisateur["PasswordHash"])
```

Le contrôleur vérifiait les mots de passe en PBKDF2 uniquement.

## Corrections appliquées

### `files/scripts/create_auth_user.py`

```python
# Après
from core.auth.password import hash_password
...
hash_password(PASSWORD)
```

Les nouveaux utilisateurs créés par le script de démo sont désormais en Argon2id.

### `files/mvc/controllers/auth_controller.py`

```python
# Après
from core.auth.password import verify_password
...

def _check_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe. Argon2id en priorité (core.auth), PBKDF2 en repli legacy."""
    if verify_password(password, password_hash):
        return True
    return verifier_mot_de_passe(password, password_hash)

...
and _check_password(password, utilisateur["PasswordHash"])
```

Le contrôleur utilise désormais Argon2id en priorité, avec repli PBKDF2 pour les
comptes existants (conforme ADR-001 : "Les hashes PBKDF2 existants doivent rester vérifiables").

### `tests/test_starter_cli.py`

```python
# Avant
assert "hacher_mot_de_passe(PASSWORD)" in script

# Après
assert "hash_password(PASSWORD)" in script
```

## Limites restantes

1. **Table `utilisateur` vs table `users`** : le starter `suivi-comportement-eleves` utilise la
   table `utilisateur` (ancienne structure avec colonnes `Login`, `PasswordHash`, `Actif`),
   différente de la table `users` utilisée par `forge auth:user:create` (colonnes `email`,
   `password_hash`, `is_active`). Cette divergence de schéma SQL est hors périmètre de ce ticket.
   Ticket prévu : `AUTH-LEGACY-BOUNDARY-001`.

2. **Comptes PBKDF2 existants** : les installations déjà effectuées du starter 4 ont des
   comptes en PBKDF2. Le repli `_check_password` les prend en charge. La migration
   automatique vers Argon2id est hors périmètre : ticket `AUTH-HASH-MIGRATION-001`.

3. **Starter `suivi-comportement-eleves` est legacy** : ce starter est documenté comme
   exemple pédagogique historique. Les corrections restent minimales et ne changent pas
   sa logique métier.

## Validation

```bash
grep -rn "hacher_mot_de_passe\|verifier_mot_de_passe\|core.security.hashing" forge_cli/starters/data/
# → aucune occurrence après correction

pytest tests/test_starter*.py       # starters verts
pytest tests/test_auth*.py          # Auth verts
pytest                               # suite complète verte
```
