# La session HTTP dans Forge

Ce document explique ce qu'est une **session**, comment Forge l'implémente, ce qu'elle contient et dans quels contextes on l'utilise.
Il se concentre uniquement sur la session ; le cookie n'apparaît ici que comme moyen de transport de son identifiant.

## 1. Qu'est-ce qu'une session ?

Le protocole HTTP est **sans état** : chaque requête est indépendante, le serveur ne « se souvient » de rien d'une requête à la suivante.
Une **session** est le mécanisme qui ajoute cette mémoire pour un même visiteur, le temps de sa visite.

Le principe est toujours le même :

1. le serveur range les données du visiteur **de son côté** ;
2. il attribue à ces données un **identifiant unique** ;
3. cet identifiant voyage chez le visiteur dans un **cookie** ;
4. à chaque requête suivante, le navigateur renvoie le cookie ; le serveur y lit
   l'identifiant et **retrouve les données** correspondantes.

Le cookie ne contient donc que l'identifiant, jamais les données elles-mêmes.

## 2. La session dans Forge

Voici comment Forge applique ce principe.

**Les données restent sur le serveur.**
Elles sont rangées dans un magasin de sessions (le *store*) ; le navigateur n'en voit jamais le contenu.

**L'identifiant** est une longue chaîne aléatoire de 64 caractères (par exemple `9f3c…a2`), impossible à deviner.
C'est la seule chose qui voyage chez le visiteur.

**Le cookie qui transporte cet identifiant** porte le nom `__Host-session_id`.
C'est simplement le **nom** du cookie, en deux parties :

- `session_id` indique ce qu'il contient : l'identifiant de la session ;
- le préfixe `__Host-` est un **marqueur de sécurité** reconnu par les
  navigateurs. Il les oblige à n'accepter ce cookie que s'il respecte des règles
  strictes (servi en HTTPS, valable sur tout le site, sans domaine élargi).

Forge pose ce cookie avec plusieurs **protections activées par défaut** :

| Protection | Ce qu'elle fait |
|---|---|
| `Secure` | le cookie n'est envoyé qu'en HTTPS, jamais en clair |
| `HttpOnly` | le JavaScript de la page ne peut pas le lire, ce qui empêche son vol |
| `SameSite=Strict` | le navigateur ne l'envoie pas quand la requête vient d'un autre site (protection anti-CSRF) |
| `Path=/` | il est valable sur toutes les pages du site |

**Durée de vie** : par défaut une session expire au bout d'**1 heure**, et ce délai est repoussé à chaque visite du même utilisateur.

En résumé, le navigateur ne détient qu'un cookie illisible contenant un simple numéro ; tout le contenu de la session reste sur le serveur.

## 3. Ce que contient une session

Une session est un dictionnaire.
À sa création, Forge le remplit avec une structure standard, à laquelle s'ajoutent les données applicatives :

| Clé | Type | Rôle |
|---|---|---|
| `csrf_token` | `str` | jeton anti-CSRF (32 hexadécimaux), généré à la création |
| `authenticated` | `bool` | `True` si un utilisateur s'est authentifié |
| `user` | `dict \| None` | données de l'utilisateur connecté, ou `None` |
| `expires_at` | `float` | horodatage d'expiration (timestamp Unix) |
| `flash` | `dict \| None` | message éphémère `{message, level}`, présent uniquement s'il y en a un en attente |

Exemple de session juste après création (visiteur anonyme) :

```python
{
    "csrf_token": "9f3c…",     # 32 caractères hexadécimaux
    "authenticated": False,
    "user": None,
    "expires_at": 1717945200.0,
}
```

Vous pouvez y ajouter vos propres clés (un compteur, une préférence temporaire…) via l'écriture en session, qui **fusionne** sans écraser les clés existantes.

## 4. Où vivent les données : le magasin de sessions

Le contenu est conservé par un *store* conforme au protocole `SessionStore`.
Trois implémentations sont fournies :

| Store | Usage |
|---|---|
| `MemorySessionStore` | défaut, en mémoire, mono-processus (idéal en développement) |
| `FileSessionStore` | persistance sur disque (JSON) |
| `MariaDbSessionStore` | sessions partagées entre plusieurs processus |

Le store actif se choisit à la configuration de l'application :

```python
forge.configure(session_store=MariaDbSessionStore(...))
```

Par défaut (sans configuration), Forge utilise `MemorySessionStore`.

## 5. Contextes d'utilisation

La session sert dès qu'il faut conserver un état entre deux requêtes du même visiteur.
Les cas les plus courants :

- **Protection CSRF** : le `csrf_token` vit dans la session ; le formulaire le
  renvoie, le serveur le compare. Sans session, pas de jeton, et le POST est
  refusé.
- **Messages flash** : un message affiché une seule fois après une action
  (« Enregistré »), stocké dans la session puis consommé à la lecture.
- **Authentification** : l'identité de l'utilisateur connecté est rattachée à la
  session (voir l'API d'authentification dédiée).
- **État temporaire applicatif** : compteur de visites, étape d'un assistant,
  préférence non persistée en base, etc.

## 6. L'API en bref

| Besoin | Fonction | Module |
|---|---|---|
| Créer une session | `get_session_store().create()` | `core.sessions` |
| Lire l'identifiant depuis le cookie | `get_session_id(request)` | `core.security.session` |
| Lire les données | `get_session(session_id)` | `core.security.session` |
| Écrire (fusion) | `get_session_store().set(session_id, data)` | `core.sessions` |
| Poser le cookie de session | `set_session_cookie(response, session_id)` | `core.security.cookies` |

Pour l'**authentification** (connexion, utilisateur courant), l'API canonique est `core.auth.session`, distincte de la manipulation de session brute décrite ici.

## 7. Voir aussi

- [Sessions : store de session Forge](../sessions.md) : le contrat complet du
  store et ses backends.
- [Convention d'inspection HTTP](../http.md) : `Request`, `Response` et le
  masquage des valeurs sensibles.
- [Le jeton CSRF](../../starters/welcome-forge/debutant/csrf.md) : la session en
  pratique, dans le parcours pédagogique.
- [ADR-002 : stratégie de session](../../adr/002-session-strategy.md).
