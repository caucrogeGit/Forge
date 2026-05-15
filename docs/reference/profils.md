# Profils de projet

### Tableau comparatif

| Profil | Intention | Base | HTMX / Alpine | i18n |
|---|---|---|---|---|
| `minimal` | Projet le plus simple, pédagogique | — | non | non |
| `standard` | Application classique recommandée | `minimal` + composants | non | non |
| `dynamic` | Interactions front légères | `standard` + intention HTMX/Alpine | oui (préparé) | non |
| `multilingual` | Prêt pour l'internationalisation | `standard` + intention i18n | non | oui (préparé) |
| `auth-mfa` | MFA (TOTP) activé | `standard` + intention `forge-mvc-mfa` | non | non |

### Commande

```bash
forge new MonProjet --profile minimal
forge new MonProjet --profile standard   # profil par défaut
forge new MonProjet --profile dynamic
forge new MonProjet --profile multilingual
forge new MonProjet --profile auth-mfa
```

### Fichier `forge_profile.txt`

`forge new` écrit le nom du profil dans `forge_profile.txt` à la racine du projet.

### Limites actuelles

- Tous les profils génèrent actuellement la même structure de base.
- La différenciation des squelettes sera renforcée dans des tickets ultérieurs.
- Les profils ne remplacent pas les starters.

Voir [docs/profiles.md](../profiles.md) pour la documentation complète.

---

## Endpoint de santé

```
GET /health  →  200 OK  {"status": "ok"}  application/json
```

Permet à Nginx, systemd, Docker ou un script de supervision de vérifier que le processus Forge répond. Ne vérifie pas la base de données ni les services externes. Inclut les headers de sécurité habituels.

---

