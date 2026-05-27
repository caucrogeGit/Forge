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
