# Vérifier un code TOTP

Objectif : confronter un **code à 6 chiffres** au secret partagé — le contrôle au
cœur du TOTP.

**Ce que vous allez apprendre :** `verify_totp_code(secret, code)` vérifie le code
avec une petite **fenêtre de tolérance** (`valid_window`) pour absorber le décalage
d'horloge. C'est ce contrôle qui se rejoue à chaque connexion MFA.

Troisième palier du **niveau débutant** de la progression MFA.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-mfa` installé (palier « Installation »). Aucune clé
    requise : on travaille sur un secret brut fourni pour la démonstration.

## Ce que ce starter montre

- un formulaire (secret + code) ;
- `verify_totp_code(secret, code)` → valide / invalide ;
- la **fenêtre de tolérance** temporelle intégrée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.verify_totp_code` | Vérifier un code TOTP contre un secret. | [MFA](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-verify`, collez le secret du palier précédent (et
le code calculé par votre application d'authentification).

## Le contrôleur

```python
# mvc/controllers/mfa_verify_controller.py
from forge_mvc_mfa import verify_totp_code


class MfaVerifyController(BaseController):

    @staticmethod
    def check(request: Request) -> Response:
        secret = (request.form("secret") or "").strip()
        code = (request.form("code") or "").strip()
        context = {"csrf_token": BaseController.csrf_token(request), "secret": secret}
        try:
            context["valid"] = bool(verify_totp_code(secret, code))
        except Exception as exc:
            context["error"] = f"Secret invalide : {exc}"
        return BaseController.render("mfa_verify/index.html", context=context, request=request)
```

### Comprendre ce code

- Le code est **dérivé du temps** : il change toutes les ~30 s. La `valid_window`
  accepte le pas précédent/suivant pour tolérer un léger décalage d'horloge.
- On entoure l'appel d'un `try/except` : un secret mal formé ne doit pas planter la
  page.
- Ce contrôle est la **brique** qu'utilisent l'enrôlement et le challenge.

## À retenir

- `verify_totp_code` est le cœur du TOTP : code + secret → valide/invalide.
- Une fenêtre de tolérance absorbe le décalage d'horloge.
- C'est la même vérification qui sera rejouée à chaque connexion.

## Après ce starter

Vous maîtrisez les mécaniques TOTP. La suite (intermédiaire) : enrôler un vrai facteur.

[Bilan du niveau débutant](bilan.md)
