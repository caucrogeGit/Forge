# Starter 6 — Auth MFA (TOTP)

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Starter Forge · Niveau 6</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Auth MFA (TOTP)</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Ajouter un challenge TOTP au flux de connexion d'un projet Forge standard : après le mot de passe, l'utilisateur doit saisir un code temporaire généré par une application d'authentification.</p>
</div>

!!! warning "Module en Pre-Alpha"
    Ce starter repose sur `forge-mvc-mfa`, marqué **Pre-Alpha** (décision T3,
    Scénario C). Le secret TOTP est stocké en clair dans la colonne
    `auth_mfa_factors.totp_secret`. **Non recommandé en production sensible**
    sans chiffrement applicatif additionnel. L'intégration dans `forge-mvc[all]`
    est planifiée après `SEC-MFA-SECRET-ENCRYPTION-001` (série 3.1.0).

## Profil associé

`auth-mfa` — même base que `standard`, avec `forge-mvc-mfa` pré-installé.

```bash
forge new MonProjet --profile auth-mfa
```

## Nature du starter

Ce starter est un **skeleton** : il ne crée pas d'entités. Il **remplace** deux
fichiers contrôleurs dans un projet déjà initialisé avec le profil `auth-mfa` :

| Fichier | Rôle |
|---|---|
| `mvc/controllers/auth_controller.py` | Login avec détection MFA activé / désactivé |
| `mvc/controllers/mfa_challenge_controller.py` | Formulaire `GET /login/mfa` et validation `POST /login/mfa` |

Les routes `/login/mfa` sont automatiquement câblées par le squelette du projet
via `mfa_available()` — aucune modification de `mvc/routes.py` n'est nécessaire.

## Ce que démontre le starter

- Challenge TOTP intercalé entre la validation du mot de passe et l'ouverture de la session
- État temporaire de challenge (clés `_auth_mfa_user_id`, `_auth_mfa_started_at`) — l'utilisateur n'a aucun accès avant validation du code
- Expiration du challenge (10 min par défaut)
- Retour au formulaire de challenge en cas de code invalide (rate-limit actif)
- Audit des événements MFA via `safe_log_auth_event`

## Flux d'authentification

```
mot de passe correct + MFA désactivé  → session ouverte (comportement standard)
mot de passe correct + MFA activé     → état temporaire → GET /login/mfa
code TOTP valide                       → état temporaire supprimé → session ouverte
code TOTP invalide                     → retour formulaire /login/mfa
```

Pour activer MFA sur un compte, l'application doit implémenter un endpoint de
provisionnement (génération du secret + affichage QR code) en appelant directement
`forge_mvc_mfa.create_totp_factor`. Le starter ne fournit pas de page de setup MFA :
il démontre uniquement le challenge à la connexion.

## Modules Python utilisés

| Import | Rôle |
|---|---|
| `forge_mvc_mfa.is_mfa_enabled` | Vérifier si MFA est actif pour l'utilisateur |
| `forge_mvc_mfa.start_mfa_challenge` | Démarrer l'état temporaire de challenge |
| `forge_mvc_mfa.has_pending_mfa_challenge` | Vérifier qu'un challenge est en cours |
| `forge_mvc_mfa.get_mfa_challenge_user_id` | Lire l'identifiant en attente |
| `forge_mvc_mfa.verify_mfa_challenge` | Valider le code TOTP ou de récupération |
| `forge_mvc_mfa.model.get_active_mfa_factors` | Charger les facteurs MFA de l'utilisateur |

## Génération

```bash
forge new MonProjet --profile auth-mfa
cd MonProjet
source .venv/bin/activate
forge doctor
forge db:init
forge starter:build 6
```

Alias acceptés : `forge starter:build auth-mfa`, `forge starter:build mfa`.

Voir [Reconstruction](rebuild.md) pour les étapes détaillées.

## Limites du starter

- Ne fournit pas de page de setup MFA (provisionnement QR code, codes de récupération)
- Ne démontre pas RBAC (voir [Communes & Séjours](../communes-sejours/index.md))
- Ne démontre pas OIDC (retiré du core en ADR-004)
- Ne démontre pas WebAuthn / passkeys (planifié post-3.0)
- Le secret TOTP est stocké en clair — Pre-Alpha
- Pas de SMS / email comme second facteur

Pour le détail technique du flux et l'API complète :
[Documentation de référence MFA](../../reference/auth-mfa.md).
