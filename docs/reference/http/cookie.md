# Le cookie HTTP dans Forge

Ce document explique ce qu'est un **cookie**, comment Forge l'utilise (surtout pour la session), ce qu'il contient et comment on le pose, l'efface ou le lit.

## 1. Qu'est-ce qu'un cookie ?

Le protocole HTTP est sans état : le serveur ne se souvient de rien d'une requête à la suivante.
Un **cookie** est un petit couple `nom=valeur` que le serveur demande au navigateur de **conserver**.
À chaque requête suivante vers le même site, le navigateur **renvoie automatiquement** ce cookie.
C'est le moyen le plus courant de relier plusieurs requêtes d'un même visiteur.

Le cookie voyage dans deux sens :

- du serveur vers le navigateur, via l'en-tête de réponse `Set-Cookie` (« garde
  ce cookie ») ;
- du navigateur vers le serveur, via l'en-tête de requête `Cookie` (« voici les
  cookies que tu m'as donnés »).

## 2. Le cookie dans Forge

Forge utilise un cookie surtout pour **la session** : le cookie ne transporte que l'identifiant de la session, et toutes les données restent sur le serveur (voir [La session HTTP dans Forge](session.md)).
Ce cookie s'appelle `__Host-session_id`.

Vous manipulez donc rarement les cookies directement : la plupart du temps, c'est Forge qui pose et lit le cookie de session pour vous.
Pour vos **propres** cookies applicatifs (un thème, une préférence…), c'est à votre application de les gérer.

## 3. Ce qu'il contient

Un cookie, c'est un `nom=valeur` accompagné d'**attributs** qui disent au navigateur comment le traiter :

| Élément | Rôle |
|---|---|
| `nom=valeur` | la donnée elle-même (pour la session : le nom `__Host-session_id` et, en valeur, l'identifiant) |
| `Path` | les URLs où le cookie est renvoyé (`/` = tout le site) |
| `Max-Age` / `Expires` | la durée de vie ; `Max-Age=0` supprime le cookie |
| `Secure` | le cookie n'est envoyé qu'en HTTPS |
| `HttpOnly` | le JavaScript de la page ne peut pas le lire (protège contre le vol) |
| `SameSite` | si le navigateur l'envoie depuis un autre site (`Strict` = jamais, protection anti-CSRF) |

Le **préfixe `__Host-`** dans le nom est un marqueur de sécurité reconnu par les navigateurs : ils n'acceptent un cookie ainsi nommé que s'il est `Secure`, avec `Path=/` et sans domaine élargi.
Forge **vérifie** ces règles et refuse une configuration qui les violerait.

## 4. Poser et effacer le cookie de session

Forge fournit deux fonctions dédiées, qui appliquent les protections par défaut (`Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`) :

| Fonction | Rôle |
|---|---|
| `set_session_cookie(response, session_id)` | pose le cookie de session sur la réponse |
| `clear_session_cookie(response)` | efface le cookie de session (au logout) ; revient à le poser avec `Max-Age=0` |

Ces deux fonctions vivent dans `core.security.cookies`.

## 5. Lire un cookie

Les cookies envoyés par le navigateur arrivent dans l'en-tête `Cookie` de la **requête**.
Pour la session, Forge le lit pour vous via `get_session_id(request)` ; vous n'avez pas à analyser l'en-tête vous-même.

Côté **réponse**, la propriété `response.cookies` renvoie seulement les **noms** des cookies posés (jamais les valeurs), pour l'inspection :

```python
response.cookies        # ex. ['__Host-session_id']
```

## 6. Contextes d'utilisation

- **Session et CSRF** : c'est l'usage principal, géré par Forge via le cookie
  `__Host-session_id` (voir [La session HTTP](session.md)).
- **Cookies applicatifs** (thème, préférence…) : à la charge de votre
  application. Le noyau ne fournit pas d'accesseur cookie générique ; vous lisez
  l'en-tête `Cookie` ou écrivez un petit helper.

!!! warning "Un seul cookie par réponse"
    `response.headers` est un dictionnaire : il ne peut porter qu'un seul
    `Set-Cookie`. Évitez donc de poser un cookie applicatif sur une réponse qui
    pose déjà le cookie de session, l'un des deux serait perdu.

## 7. Voir aussi

- [La session HTTP dans Forge](session.md) : l'usage principal du cookie.
- [L'objet Request dans Forge](../../core-http/references/request.md) : d'où viennent les cookies reçus.
- [L'objet Response dans Forge](../../core-http/references/response.md) : où se posent les cookies envoyés.
- [Convention d'inspection HTTP](../http.md) : le masquage des valeurs sensibles.
