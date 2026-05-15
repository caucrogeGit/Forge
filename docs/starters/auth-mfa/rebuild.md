# Reconstruction — Auth MFA (TOTP)

[Accueil](../../index.html){ .md-button }

Étapes pour activer le challenge MFA TOTP sur un projet Forge initialisé
avec le profil `auth-mfa`.

## Prérequis

```bash
forge new MonProjet --profile auth-mfa
cd MonProjet
source .venv/bin/activate
forge doctor
forge db:init
```

Vérifier que `forge-mvc-mfa` est installé :

```bash
python -c "import forge_mvc_mfa; print(forge_mvc_mfa.__version__)"
```

## Génération automatique

```bash
forge starter:build 6
```

Alias : `forge starter:build auth-mfa` ou `forge starter:build mfa`.

Ce starter est un **skeleton** : il remplace deux contrôleurs existants sans
modifier les entités ni `mvc/routes.py`.

### Fichiers remplacés

| Fichier | Avant | Après |
|---|---|---|
| `mvc/controllers/auth_controller.py` | Stub standard (login sans MFA) | Version complète avec détection et déclenchement du challenge |
| `mvc/controllers/mfa_challenge_controller.py` | Absent | Nouveau : `GET /login/mfa` + `POST /login/mfa` |

Les routes `/login/mfa` sont câblées automatiquement par le squelette du projet
(`mfa_available()` renvoie `True` après le build).

## Équivalent manuel

Pour reproduire sans `forge starter:build` :

**1.** Copier `auth_controller.py` depuis le starter :

```bash
cp forge_cli/starters/data/auth-mfa/files/mvc/controllers/auth_controller.py \
   mvc/controllers/auth_controller.py
```

**2.** Copier `mfa_challenge_controller.py` :

```bash
cp forge_cli/starters/data/auth-mfa/files/mvc/controllers/mfa_challenge_controller.py \
   mvc/controllers/mfa_challenge_controller.py
```

**3.** Vérifier que `mvc/routes.py` contient le bloc `mfa_available()`. Il doit
être présent dans tout projet créé avec le profil `auth-mfa`.

## Test manuel

1. Lancer l'app : `forge run` (ou `python app.py`)
2. Ouvrir `/login` — connexion normale (MFA désactivé par défaut)
3. Provisionner MFA pour un compte : appeler directement l'API via un script de test

```python
# scripts/setup_mfa_test.py
from forge_mvc_mfa import create_totp_factor
from core.database.db import fetch_one

user = fetch_one("SELECT utilisateur_id FROM utilisateur WHERE login = ?", ("admin",))
factor = create_totp_factor(user_id=user["utilisateur_id"])
print(f"Secret TOTP : {factor.totp_secret}")
print(f"Configurez votre app TOTP avec ce secret (ou un QR code généré depuis ce secret).")
```

4. Se reconnecter : après le mot de passe, `/login/mfa` s'affiche
5. Saisir un code TOTP valide depuis l'app d'authentification
6. Vérifier que la session est ouverte

## Vérifications

```bash
python -c "
from forge_mvc_mfa.model import get_active_mfa_factors
from core.database.db import fetch_one
u = fetch_one('SELECT utilisateur_id FROM utilisateur WHERE login = ?', ('admin',))
print(get_active_mfa_factors(u['utilisateur_id']))
"
```

Résultat attendu : une liste contenant un `AuthMfaFactor` avec `totp_secret` renseigné.

## Limites de cette reconstruction

- Pas de chiffrement applicatif du secret TOTP (planifié 3.1.0)
- Pas de page de setup MFA avec QR code dans ce starter — l'étape de provisionnement est manuelle (script ci-dessus)
- Pas de WebAuthn (planifié post-3.0)
- Pas de SMS / email comme second facteur
