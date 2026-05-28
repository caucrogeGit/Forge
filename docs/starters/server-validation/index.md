# Validation serveur

Objectif : vérifier côté serveur une valeur reçue depuis un
formulaire.

Palier 7 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Premier formulaire POST](../form-post/index.md).

## Ce que ce starter montre

- une route `GET /server-validation`
- une route `POST /server-validation`
- un formulaire HTML minimal
- une lecture avec `request.form(...)`
- une vérification simple côté serveur
- une réponse `422` si la valeur est vide

Aucune base de données.
Aucun CRUD.
Aucun système complet de validation.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Lire le champ envoyé avec `request.form(...)`. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Construire la réponse texte, succès ou erreur (`status=422`). | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | Classe parente du contrôleur. | [BaseController](../../reference/api.md#coremvccontroller) |

## Tester

Depuis le projet Forge déjà créé avec ce starter :

```bash
forge run
```

Ouvrez :

```
http://localhost:8000/server-validation
```

Essayez deux cas :

- **Prénom = `Roger`** → `Bonjour Roger`
- **Prénom vide** → `Le prénom est obligatoire` (HTTP 422)

## Code essentiel

```python
@staticmethod
def submit(request: Request) -> Response:
    name = request.form("name", default="").strip()

    if not name:
        return Response.text("Le prénom est obligatoire", status=422)

    return Response.text(f"Bonjour {name}")
```

### Comprendre ce code

- `request.form("name", default="").strip()` lit la valeur soumise et
  supprime les espaces autour. Le `default=""` évite un `None` à gérer.
- `if not name:` détecte les cas vides (chaîne vide, espaces uniquement).
  C'est la **validation côté serveur** dans sa forme la plus simple.
- Si la donnée est invalide, le contrôleur retourne `422 Unprocessable
  Entity` avec un message d'erreur — pas un `200` trompeur.
- Règle d'or : **le serveur ne fait jamais confiance aux données reçues**.
  Toute requête peut venir d'un client modifié (curl, JS désactivé,
  Postman), donc la validation client doit toujours être doublée
  côté serveur.

## À retenir

- Le navigateur peut envoyer n'importe quelle valeur — même rien,
  même un espace, même un contenu inattendu.
- Le serveur doit toujours vérifier ce qu'il reçoit avant de
  l'utiliser. Ici, on vérifie simplement que `name` n'est pas vide
  après `.strip()`.
- Le statut HTTP `422 Unprocessable Entity` indique « la requête est
  bien formée mais les données ne sont pas exploitables ».
- La validation complète d'une application (règles multiples,
  messages d'erreur réaffichés dans le formulaire, conservation des
  anciennes valeurs) viendra plus tard avec un système dédié — ce
  starter reste le **contrôle minimum**.

## Après ce starter

Passez au palier suivant : **Première base SQL**.

Vous y apprendrez à lire une donnée depuis MariaDB avec du SQL
visible :

```python
from core.database.db import fetch_one

row = fetch_one("SELECT content FROM first_sql_messages ORDER BY id LIMIT 1")
```

[Continuer avec Première base SQL](../first-sql/index.md)
