# Inspecter une requête

Objectif : afficher la structure d'une requête avec `request.data` et
`Response.debug(...)`.

Palier 5 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Route dynamique](../dynamic-route/index.md).

## Ce que ce starter montre

- une route `/request-debug`
- un contrôleur `RequestDebugController`
- l'accès global `request.data`
- un rendu de debug avec `Response.debug(...)`

Aucune vue HTML.
Aucune base de données.
Aucun formulaire.
Aucun CRUD.

## Tester

Depuis le projet Forge déjà créé avec ce starter :

```bash
forge run
```

Ouvrez :

```
http://localhost:8000/request-debug?name=Roger
```

Vous devez voir une page de debug HTML contenant les informations de la
requête : méthode, chemin, paramètres, headers (les valeurs sensibles
sont masquées automatiquement).

## Code essentiel

```python
@staticmethod
def index(request: Request) -> Response:
    return Response.debug(request.data)
```

## À retenir

- `request.data` donne une vue globale et stable de la requête, avec
  les clés sensibles (`Authorization`, `Cookie`, `password`, `csrf`…)
  remplacées par `[masked]`.
- `Response.debug(...)` sert à explorer un objet en développement —
  c'est un outil de compréhension, pas un affichage public de
  production.
- En `APP_ENV=prod`, `Response.debug(...)` refuse et retourne `404`
  sans aucun détail. Le starter reste donc sûr à laisser branché en
  développement, mais n'expose rien en production.

## Après ce starter

Le palier suivant est le **Starter Premier formulaire POST** (à venir
— ticket `STARTER-FORM-POST-001`) qui introduit l'envoi de données
depuis un formulaire HTML.

Voir la
[Progression recommandée des starters](../index.md#progression-recommandee)
pour la feuille de route complète.

[Vue d'ensemble des starters](../index.md) · [Route dynamique — palier 4](../dynamic-route/index.md)
