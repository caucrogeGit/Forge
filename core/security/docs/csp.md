# Le nonce CSP dans Forge

Ce document décrit le nonce de Content-Security-Policy par requête.

Le fichier de code correspondant est `core/security/csp.py`.

## 1. À quoi sert ce module ?

La CSP de Forge interdit les scripts inline par défaut (`script-src 'self'`).
Pour autoriser un script inline **contrôlé** sans affaiblir la CSP avec `unsafe-inline`, on emploie un **nonce** unique par requête.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `generate_nonce()` | génère un nonce sûr (base64 URL-safe, 128 bits) |
| `set_request_nonce(nonce)` | stocke le nonce de la requête courante (thread-local) |
| `get_request_nonce()` | le nonce courant, ou `None` |
| `clear_request_nonce()` | réinitialise le nonce courant |
| `request_nonce(nonce)` | gestionnaire de contexte : porte le nonce le temps d'une requête puis le remet à zéro |
| `build_csp_header(nonce=None)` | construit l'en-tête `Content-Security-Policy` |

## 3. Usage

Activé par `APP_CSP_NONCE_ENABLED=true`. Dans un gabarit :

```html
<script nonce="{{ csp_nonce() }}">/* script inline autorisé */</script>
```

`unsafe-inline` n'est jamais ajouté automatiquement : seul le nonce autorise un script inline.

## 4. Contextes d'utilisation

- **Script inline contrôlé** : activer le nonce et le poser sur la balise.
- **En-tête** : `build_csp_header(nonce)` injecté dans la réponse.

## 5. Voir aussi

- [Les en-têtes de sécurité](headers.md) : la CSP fait partie des en-têtes posés.
