# Intermédiaire 3 : Le client de test

Objectif : appeler une route comme un navigateur, et vérifier ce qu'elle répond.

## Ce que `FakeRequest` ne prouve pas

Appeler `ArticleController.show(fausse_requete)` exécute la méthode, et rien d'autre.
Rien n'y passe par le routeur, ni par les middlewares, ni par la construction d'une requête depuis un environnement WSGI.

Ce test ne dit donc rien du CSRF, de l'authentification, des en-têtes de sécurité, ni même de l'existence de la route.

```python
from core.app.wsgi import create_wsgi_app
from forge_mvc_testing import ForgeTestClient

client = ForgeTestClient(create_wsgi_app(application, emit_prod_warnings=False))

reponse = client.get("/articles")
assert reponse.status == 200
```

## Il passe par le vrai chemin

Le client appelle le callable rendu par `create_wsgi_app`, c'est à dire exactement ce que Gunicorn appelle.

!!! danger "Un client qui reconstruirait sa boucle serait un jumeau"
    Il passerait là où la production échoue, et les deux dériveraient sans que rien ne le signale.

    Forge a déjà payé cette erreur : un serveur de développement répondait là où Gunicorn rendait 404. Un harnais de test qui n'emprunte pas le chemin de production ne teste pas la production.

## Ce qu'il garde entre deux requêtes

Les cookies, donc la session.
Un scénario réaliste enchaîne une connexion, une lecture de formulaire et un envoi, et chaque étape dépend de la précédente.

```python
from forge_mvc_testing import login_as, assert_authenticated

login_as(client, 42, roles=["admin"])
assert_authenticated(client)
assert client.get("/admin").status == 200
```

Rien d'autre n'est gardé : ni état applicatif, ni cache, ni transaction.
C'est un navigateur minimal, pas un environnement.

!!! info "`login_as` pose une vraie session"
    Elle passe par le magasin de sessions et par sa rotation, pas par une écriture de clés à la main.

    Une session fabriquée autrement serait acceptée par le test et refusée par la production.

!!! warning "Les assertions doivent pouvoir échouer"
    `assert_authenticated` après un `logout` échoue, et `assert_not_authenticated` après un `login_as` échoue aussi.

    Une assertion qui ne peut pas échouer affaiblit tout test qui l'emploie, sans que personne ne s'en aperçoive.

## À retenir

- Le client emprunte le chemin WSGI de production, middlewares compris.
- Il garde les cookies, donc la session, et rien d'autre.
- Les assertions fournies échouent quand elles le doivent.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
