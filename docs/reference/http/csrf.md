# La protection CSRF dans Forge

Ce document explique ce qu'est une attaque **CSRF**, comment Forge s'en protège, quelles requêtes sont vérifiées et comment utiliser le jeton dans vos formulaires.

## 1. Qu'est-ce que le CSRF ?

CSRF (« Cross-Site Request Forgery », falsification de requête entre sites) est une attaque où **un autre site** déclenche, à l'insu du visiteur, une action sur votre site en profitant de sa session ouverte.

Exemple : connecté à votre banque, vous visitez une page piégée ; celle-ci envoie en douce un formulaire vers votre banque.
Comme le navigateur joint automatiquement le cookie de session, la banque croit que la demande vient de vous.
La protection CSRF sert à **distinguer une vraie action de l'utilisateur d'une action déclenchée par un site tiers**.

## 2. Comment Forge protège

Le principe : chaque action qui **modifie des données** doit être accompagnée d'un **jeton secret**, lié à la session du visiteur.
Un site tiers ne connaît pas ce jeton, donc sa requête est rejetée.

Concrètement, Forge :

1. génère un **jeton** propre à chaque session ;
2. l'insère dans vos formulaires (champ caché) ;
3. à la réception, **compare** le jeton envoyé à celui de la session ;
4. **refuse la requête** (`403`) si le jeton manque ou ne correspond pas.

## 3. Quelles requêtes sont vérifiées

Forge ne vérifie le jeton que sur les requêtes qui **changent l'état** :

| Méthodes | Vérifiées ? |
|---|---|
| `GET`, `HEAD`, `OPTIONS` (dites « sûres ») | non : elles ne font que lire |
| `POST`, `PUT`, `PATCH`, `DELETE` (dites « non sûres ») | oui |

La protection est **active par défaut** sur les routes (`csrf=True`).
Une route peut la désactiver explicitement (`csrf=False`), par exemple une API qui s'appuie sur un autre mécanisme d'authentification.

## 4. Le jeton CSRF

- **Génération** : le jeton (`csrf_token`) est créé automatiquement **dans la
  session**, dès sa création. Il n'existe donc que s'il y a une session active.
- **Transmission** : le navigateur le renvoie soit par un **champ de formulaire**
  nommé `csrf_token`, soit par l'en-tête **`X-CSRF-Token`** (pratique pour les
  requêtes JavaScript).
- **Vérification** : Forge compare le jeton reçu à celui de la session avec une
  comparaison **en temps constant** (insensible aux attaques temporelles). En cas
  d'absence ou de différence, la requête reçoit un **`403`**.

## 5. En pratique

Le jeton vit dans la session ; il faut donc une **session active** pour qu'il ne soit pas vide (voir [La session HTTP dans Forge](session.md)).
Dans un gabarit, on place le jeton dans un champ caché :

```html
<form method="post" action="/welcome/form-submit">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label>Prénom : <input type="text" name="name"></label>
    <button type="submit">Envoyer</button>
</form>
```

- En **`GET`** (affichage du formulaire) : aucune vérification ; on garantit la
  session, on pose son cookie, et on passe le jeton au gabarit.
- En **`POST`** (envoi) : Forge vérifie le jeton **avant** d'appeler votre
  contrôleur. Si tout est bon, votre méthode s'exécute ; sinon, le visiteur reçoit
  un `403`.

Le parcours pédagogique montre ce mécanisme étape par étape : [Le jeton CSRF](../../starters/welcome-forge/debutant/csrf.md).

## 6. Le duo CSRF et session

CSRF et session fonctionnent **ensemble** :

- le jeton vit **dans la session** : sans session, `csrf_token` est vide et le
  POST est refusé ;
- la session est retrouvée grâce à son **cookie** (voir
  [Le cookie HTTP dans Forge](cookie.md)).

C'est pourquoi un formulaire protégé commence toujours par **garantir une session** et **poser son cookie**.

## 7. Voir aussi

- [La session HTTP dans Forge](session.md) : où vit le jeton.
- [Le cookie HTTP dans Forge](cookie.md) : comment la session est retrouvée.
- [L'objet Request dans Forge](../../core-http/request.md) : d'où Forge lit le jeton envoyé.
- [Le jeton CSRF](../../starters/welcome-forge/debutant/csrf.md) : la mise en
  pratique guidée.
