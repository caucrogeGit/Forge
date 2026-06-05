# Limiter les uploads

Objectif : protéger une route d'upload contre les abus avec un **rate-limit par
IP**.

**Ce que vous allez apprendre :** `is_upload_rate_limited(ip)` indique si une IP a
atteint le quota (fenêtre glissante en mémoire), `record_upload_attempt(ip)`
enregistre une tentative. Au-delà du quota, la route répond `429`.

Deuxième palier du **niveau intermédiaire** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé (palier « Installation »).

## Ce que ce starter montre

- la vérification du quota avec `is_upload_rate_limited(request.ip)` ;
- l'enregistrement d'une tentative avec `record_upload_attempt(request.ip)` ;
- une réponse `429` au-delà de la limite.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.is_upload_rate_limited` | Tester le quota d'uploads de l'IP. | [Médias](../../../features/media.md) |
| `forge_mvc_files.record_upload_attempt` | Enregistrer une tentative. | [Médias](../../../features/media.md) |
| `request.ip` | IP cliente résolue (proxies de confiance pris en compte). | [Request](../../../reference/http.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-rate-limit` et envoyez plus de 10 fois en moins
d'une minute : la route bascule en `429`.

## Le contrôleur

```python
# mvc/controllers/file_rate_limit_controller.py
from forge_mvc_files import is_upload_rate_limited, record_upload_attempt, save_upload, UploadError


class FileRateLimitController(BaseController):

    @staticmethod
    def upload(request: Request) -> Response:
        context = {"csrf_token": BaseController.csrf_token(request)}
        if is_upload_rate_limited(request.ip):
            context["rate_limited"] = True
            return BaseController.render("file_rate_limit/index.html", context=context, request=request, status=429)
        record_upload_attempt(request.ip)
        # … puis save_upload normal
```

### Comprendre ce code

- On teste **avant** d'enregistrer la tentative, et on n'enregistre que les
  requêtes effectivement traitées.
- Le compteur est **en mémoire** (fenêtre glissante) : simple, sans base, isolé des
  compteurs de connexion.
- `request.ip` est l'IP **résolue** (un proxy de confiance ne masque pas le client).

## À retenir

- Une route d'upload publique se **protège** par rate-limit.
- `is_upload_rate_limited` / `record_upload_attempt` : tester puis enregistrer.
- Au-delà du quota → `429`, sans toucher au disque.

## Après ce starter

La route est protégée. La suite : supprimer un fichier proprement.

[Supprimer un fichier](file-delete.md)
