# ADR-088 : Contrat unique des réponses d'API JSON

## Statut

Acceptée.
Décision de périmètre et de contrat public ; relève du mainteneur.
Révise sur un point la classification de l'ADR-052, qui rangeait l'API JSON en catégorie 4 sans trancher la forme de ses réponses.

## Date

2026-08-09

## Contexte

Forge expose du JSON par deux voies qui se sont développées séparément, et qui ne produisent pas la même chose.

**La voie déclarée.**
`docs/reference/api-json.md`, quatre cent onze lignes, enseigne une couche d'API complète.
Elle fournit `json_response`, `api_success` et `api_error` dans `core.http`, le décorateur `@require_api_token` dans `core.security.api_auth`, la convention de fichier `mvc/api_routes.py` et sa fonction `register_api_routes`, un tableau des statuts HTTP recommandés, une section de sécurité et un exemple complet.
Cette voie n'est pas seulement documentaire : elle est câblée dans le cœur, `Application.__init__` portant `api_routes_module="mvc.api_routes"` et `core/app/api_routes_loader.py` la chargeant à chaque démarrage.
Sa forme d'erreur est une enveloppe.

```json
{"success": false, "error": {"code": "not_found", "message": "Ressource introuvable"}}
```

**La voie pratiquée.**
Les trois opt-ins qui exposent réellement du HTTP JSON, `forge-mvc-iot`, `forge-mvc-video` et `forge-mvc-audio`, n'emploient aucune de ces briques.
Ils appellent `Response.json` directement, protègent leurs routes par `core.http.bearer`, enregistrent leurs routes par une fonction `register_<opt-in>_routes` explicite, et rendent une forme plate.

```json
{"error": "not_found"}
```

### Ce que l'inventaire établit

`api_error` compte **trois sites d'appel de production**, tous situés dans `core/security/api_auth.py`.
`api_success` n'en compte **aucun**, sa seule occurrence hors tests vivant dans une docstring.
La voie déclarée n'a donc, en pratique, qu'un seul consommateur, et c'est le module qui l'accompagne.

Le cœur porte par ailleurs **deux implémentations de l'authentification Bearer**.
`core/http/bearer.py`, employée par les trois opt-ins, et `core/security/api_auth.py`, employée par personne.
Elles divergent sur la lecture du préfixe, `"Bearer "` avec espace contre `"bearer"` comparé en minuscules, et sur la posture de sécurité : la première rend un refus opaque, la seconde distingue trois causes, `unauthorized`, `invalid_authorization_header` et `invalid_token`, et renseigne donc un attaquant sur l'étape franchie.
Le ticket `CORE-HTTP-BEARER-PRIMITIVE-001` avait extrait la primitive au motif qu'« un correctif de sécurité appliqué à une seule copie laisse les autres vulnérables » ; il a consolidé les trois opt-ins et laissé ce module de côté.

Le ticket `CORE-ROUTE-API-FLAG-001`, livré le 2026-08-09, a enfin rendu actif le drapeau `api` d'une route, qui n'était lu par aucun code.
`docs/reference/api-json.md` affirme toujours que ce drapeau « est déclaratif, il identifie les routes API sans modifier leur comportement ».
La référence contredit donc le code depuis ce jour.

### Le vrai problème

Le problème n'est pas que deux formes existent.
C'est que **Forge a une convention d'API déclarée, câblée dans son cœur, et que ses propres opt-ins ne la suivent pas**, sans qu'aucun document ne dise laquelle des deux fait foi.

Un client d'une application Forge reçoit l'une ou l'autre forme selon la route touchée, et n'a aucun moyen uniforme de distinguer un succès d'un échec.
C'est une violation du principe 11, une seule façon officielle de faire chaque chose, et du principe 10, une API publique est un contrat de complétude.

## Décision

**La forme pratiquée devient le contrat unique. La voie déclarée est retirée.**

Une réponse de succès rend la ressource, sans enveloppe. Le code HTTP porte l'information de succès.

Une réponse d'erreur rend un objet plat.

```json
{"error": "<code>"}
```

Un champ `message` facultatif l'accompagne pour les seules erreurs de validation, où le client a besoin de savoir quoi corriger. Aucune autre erreur ne porte de message.

### Ce qui est retiré

`api_success` et `api_error` de `core/http/helpers.py`, ainsi que leurs exports depuis `core.http`.

`core/security/api_auth.py` en entier, seconde implémentation Bearer, et sa page `core/security/docs/api_auth.md`.

Les sections de `docs/reference/api-json.md` qui enseignent l'enveloppe et `@require_api_token`.

### Ce qui est conservé

`json_response` et `Response.json`, qui ne portent aucune forme et restent la sérialisation canonique.

`core/http/bearer.py`, seule implémentation Bearer.

La convention `mvc/api_routes.py` et son chargement par le cœur, qui relèvent de l'organisation des routes et non de la forme des réponses.

Le tableau des statuts HTTP recommandés, la section de sécurité et la liste des limites, qui restent justes.

### Quatre raisons

**Trois mises en œuvre indépendantes ont choisi autrement.**
Quand le besoin s'est présenté à `iot`, puis à `video`, puis à `audio`, les trois ont écarté la voie déclarée. Un contrat qu'aucune de ses propres briques n'adopte après quinze versions est une intention, pas un contrat.

**L'enveloppe redouble le code HTTP.**
Forge traite par ailleurs le code de statut comme porteur de sens, et l'a renforcé à plusieurs reprises, 405 avec en-tête `Allow`, 503 distinct du 500, 401 distinct de la redirection.
Faire porter la même information par `{"success": true}` contredit ce soin.

**La forme plate a la meilleure posture de sécurité.**
Le refus opaque des opt-ins ne renseigne pas l'attaquant sur l'étape franchie, là où l'enveloppe invite à joindre un `message` à chaque erreur.
Le principe 7 tranche.

**Le retrait coûte peu et le ralliement coûterait cher.**
Cinq des six fonctions d'erreur du dépôt produisent déjà la forme plate, donc le format en sortie ne bouge presque pas.
Rallier l'enveloppe changerait au contraire le format de trois paquets publiés au profit d'une forme que personne n'a choisie.

### Ce que cette décision ne dit pas

Elle ne rouvre pas la question d'un opt-in REST, que l'ADR-052 a classée hors trajectoire 1.x et qui le reste.

Elle ne crée pas de décorateur de garde par jeton.
Si un besoin réel apparaît, sa place est `core/security/decorators.py`, auprès de `require_auth`, `require_csrf` et `require_role`, bâti sur `core/http/bearer.py`, avec un code d'erreur unique et opaque.

Elle ne préjuge pas des tickets futurs listés par la référence, corps JSON entrant, validation de charge utile, pagination, limitation de débit.

## Conséquences

- Une application Forge rend une seule forme d'erreur, quelle que soit la route touchée.
- Le cœur cesse de porter deux implémentations Bearer, dont l'une n'avait pas la posture de sécurité de l'autre.
- Le retrait d'`api_success`, d'`api_error` et de `core.security.api_auth` est une **suppression d'API publique documentée**. Elle intervient avant le tag 1.0.0 stable, donc sans alias de compatibilité, mais le changelog doit donner le remplacement exact, code à l'appui.
- `docs/reference/api-json.md` est réécrite plutôt que supprimée. Sa valeur pédagogique tient au reste, statuts, sécurité, limites, organisation des routes.
- La contradiction laissée par `CORE-ROUTE-API-FLAG-001` sur le caractère déclaratif du drapeau `api` est corrigée dans le même mouvement.
- Un garde-fou refuse désormais toute construction de réponse d'erreur JSON hors de la fonction canonique. Sans lui la divergence recommencerait, puisque c'est ainsi qu'elle est née.
- Trois fichiers de tests, dont un de trois cent quarante lignes, ne testent que l'enveloppe. Ils sont relus ligne à ligne, et ce qui porte sur la sérialisation, l'encodage ou le type de contenu est conservé.

## Alternatives écartées

**Rallier les opt-ins à l'enveloppe déclarée.**
Rejeté : cela change le format en sortie de trois paquets publiés au profit d'une forme dont l'inventaire montre qu'elle n'a aucun adoptant, et conserve une enveloppe qui redouble le code HTTP.
L'argument de l'antériorité ne suffit pas quand l'usage l'a démentie trois fois.

**Garder les deux formes en leur assignant des rôles distincts**, l'enveloppe pour les API écrites par l'application, la forme plate pour les points d'entrée du framework.
Rejeté : la distinction est invisible du client, qui reçoit deux formes selon la route.
C'est exactement le défaut à corriger, habillé d'une justification.

**Ne rien décider et documenter la coexistence.**
Rejeté : le principe 11 n'admet pas deux façons officielles, et une documentation qui décrit un désordre le pérennise au lieu de le nommer.

**Conserver `core/security/api_auth.py` comme adaptateur mince sur `bearer.py`.**
Rejeté : sa seule valeur propre est un décorateur et la lecture d'une variable d'environnement, soit une quinzaine de lignes qu'une application écrit elle-même.
Forge a déjà tranché ce type de cas en annulant la façade `Session` de confort, au motif que le sucre est à la charge du développeur.

**Traiter la question par tickets, sans ADR.**
Rejeté : le retrait touche une API publique exportée, documentée et câblée dans le cœur, et révise la classification de l'ADR-052.
Une décision de cette portée doit être datée et motivée, non déduite d'un message de commit.

## Référence

- ADR-052, stratégie et critères des opt-ins, qui classe l'API JSON dédiée hors trajectoire 1.x.
- ADR-004, périmètre du core minimal strict, qui a retiré OIDC et OAuth du dépôt.
- `CORE-HTTP-BEARER-PRIMITIVE-001`, extraction de la primitive Bearer partagée.
- `CORE-ROUTE-API-FLAG-001`, activation du drapeau `api` d'une route.
- `docs/reference/api-json.md`, la convention déclarée que cette décision révise.
