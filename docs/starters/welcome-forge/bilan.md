# Bilan — starter Bonjour Forge

Vous venez de terminer les **11 paliers** du starter de découverte
*Bonjour Forge*. Cette page récapitule **ce que vous avez validé** :
chaque ligne est une compétence acquise et réutilisable dans n'importe
quel projet Forge.

## Ce que vous avez validé

| Palier | Compétence validée |
|--------|--------------------|
| 1 — [Bonjour Forge](welcome.md) | Le cycle requête → contrôleur → réponse ; `Response.text(...)`. |
| 2 — [Paramètres d'URL](query-params.md) | Lire la *query string* avec `request.param("k", default=...)`. |
| 3 — [Première vue HTML](first-html-view.md) | Rendre un template avec `BaseController.render(...)`. |
| 4 — [Route dynamique](dynamic-route.md) | Lire un segment d'URL avec `request.route_param("id")`. |
| 5 — [Inspecter une requête](request-debug.md) | Explorer la requête en dev (`request.data`, `Response.debug(...)`). |
| 6 — [Réponse JSON](json-response.md) | Renvoyer des données structurées avec `Response.json({...})`. |
| 7 — [Le jeton CSRF](csrf.md) | Protéger les formulaires (`BaseController.csrf_token(...)`). |
| 8 — [Premier formulaire POST](form-post.md) | Traiter un POST et lire `request.form("k", default=...)`. |
| 9 — [Validation serveur](server-validation.md) | Refuser une valeur invalide avec un statut `422`. |
| 10 — [Première base SQL](first-sql.md) | Lire en base avec du SQL visible (`fetch_one`). |
| 11 — [Écrire en base](first-sql-write.md) | Insérer une ligne avec `insert(...)`. |

## À garder sous la main

L'[aide-mémoire de la progression](recapitulatif.md) rassemble toutes ces
API (réponses, requête, base de données, sécurité) sur une seule page.

## Prochain starter

Vous maîtrisez les fondamentaux : HTTP, vues, formulaires protégés,
validation et SQL en lecture/écriture. Il vous manque une seule chose
pour une vraie application : **structurer ces opérations en un CRUD
complet**.

[Prochain starter : First CRUD](../crud/first-crud.md)
