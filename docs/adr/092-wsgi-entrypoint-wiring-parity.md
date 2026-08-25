# ADR-092 : Le chemin WSGI refuse de servir une application désarmée

## Statut

Acceptée.
Pose un refus immédiat et nomme la cible.
Le déplacement du câblage, qui supprimera la cause, fera l'objet d'un ADR distinct.

## Date

2026-08-25

## Contexte

Forge a deux points d'entrée, et ils ne construisent pas la même application.

Le serveur de développement passe par `app.py`, où le squelette prescrit lui même le câblage.

> Les middlewares (auth, RBAC, ...) se câblent ICI, dans app.py, pas dans mvc/.

La production passe par `create_configured_wsgi_app()`, qui appelle `build_application()`.
Or `build_application()` lit `config.py` et le module de routes, jamais `app.py`.
`config.py` ne porte que des valeurs, jamais des objets construits : la fabrique générique ne peut donc pas voir un middleware, et rien ne le signale.

Mesuré le 2026-08-24 sur une application en production, puis reproduit dans le dépôt.

```text
WSGI   middlewares  : ['AuthMiddleware']
WSGI   session_store: None
app.py middlewares  : ['AuthMiddleware', 'MonGardeMetier']
app.py session_store: MonStorePartage
```

L'authentification survit, `Application` posant `AuthMiddleware` par défaut.
Tout ce qui vient après tombe : contrôle d'accès par rôle, filtrage au niveau de la ligne, portes applicatives.
Un utilisateur authentifié atteint des routes qu'aucune garde ne protège plus.

Le magasin de sessions tombe avec, et l'unité générée lance quatre travailleurs.
Un `MemorySessionStore` par processus, c'est une connexion qui réussit une fois sur quatre.

Ce qui rend ce défaut coûteux n'est pas sa gravité, c'est sa discrétion.
L'application démarre, répond 200, authentifie, et laisse simplement passer ce que les gardes suivantes auraient refusé.
Aucune erreur, aucune trace au journal, aucun code de retour anormal.
Personne ne cherche, parce que rien n'indique qu'il y ait à chercher.

Le cœur savait pourtant le dire.
`emit_memory_store_warning_if_needed` existe et part dans un logger, au démarrage, là où personne ne le lit.

## Décision

**`create_configured_wsgi_app()` refuse de construire une application dont le câblage lui échappe.**

### 1. Le refus est une erreur au démarrage, jamais un avertissement

Un avertissement dans un journal de démarrage a déjà été essayé, et il n'a rien empêché.
La panne étant silencieuse par nature, seule une panne bruyante la révèle.

Le service ne démarre pas, l'exploitant lit la cause, et l'écart se règle avant la première requête plutôt qu'après le premier incident.

### 2. La détection est statique et n'exécute rien

`create_configured_wsgi_app()` ne peut pas importer `app.py` pour savoir ce qu'il câble.
Ce serait exécuter précisément ce que le chemin WSGI cherche à éviter, effets de bord compris, dont l'analyse d'arguments en tête de fichier.

La détection lit donc le source et l'analyse avec `ast`, sans jamais l'exécuter.
L'arbre syntaxique, plutôt qu'une recherche de texte : le squelette livre un exemple de câblage **en commentaire**, qu'un `grep` prendrait pour une déclaration, et refuserait alors de démarrer tout projet nu.

### 3. Le refus ne s'applique qu'au chemin générique

`create_wsgi_app(application)` reçoit une application déjà construite : il n'a rien à vérifier, et reste la voie de celui qui construit la sienne.

### 4. Ce refus n'est pas la réparation

La cause reste entière : `build_application()` ne peut pas voir un objet construit dans `app.py`.

**La cible est de déplacer le câblage dans une source que les deux points d'entrée lisent**, ce qui rendra vraie l'affirmation de `create_configured_wsgi_app()` au lieu de la retirer.
Elle change la forme du squelette pour tous les projets futurs et demande sa propre décision.

Ce refus la précède pour une raison qui lui survit : **les projets existants ne migrent pas.**
Celui qui a engendré son squelette en `rc4` et ne le remontera jamais garde le défaut, corrigé pour les autres.
Le refus est la seule des deux mesures qui les protège, et la moins chère des deux.

## Conséquences

### Ce que cela apporte

Un écart entre développement et production cesse d'être invisible.
La classe entière de pannes du 2026-08-24 avait cette forme : les deux chemins ne servaient pas la même application, et rien ne le disait.

Le garde-fou de parité que ce refus demande est aussi la vérification la plus utile d'un pré-vol de déploiement.
Il est écrit une fois, ici.

### Ce que cela coûte

Une application en production dont le `wsgi.py` appelle la fabrique générique et dont `app.py` câble des middlewares **cesse de démarrer** à la montée de version.

C'est délibéré, et c'est le sujet.
Elle servait jusque là sans ses gardes ; elle refuse désormais de servir en le disant.
Le message nomme les deux voies : servir l'application déjà armée, ou construire la sienne.

### Limites

La détection voit ce que `app.py` déclare, pas ce qu'il exécute.
Un câblage construit dynamiquement, hors d'un appel littéral, lui échappe.

C'est assumé : le refus vise le câblage que le squelette prescrit, qui est celui que tout le monde écrit.
Il n'a pas à comprendre un `app.py` arbitraire, seulement à ne jamais laisser passer en silence celui qu'il comprend.

## Charte appliquée

- Principe 3, refuser la magie cachée : une application désarmée en silence était de la magie, et le refus la nomme.
- Principe 7, sécuriser par défaut : entre démarrer sans gardes et ne pas démarrer, le défaut est de ne pas démarrer.
- Règle B, révéler avant de corriger : ce refus révèle, l'ADR de déplacement du câblage corrigera.

## Liens

- [ADR-004](004-core-perimeter.md) : périmètre du cœur minimal.
- [ADR-024](024-skeleton-bootstrap.md) : bootstrap par squelette dédié.
- [ADR-053](053-deploy-extraction.md) : outillage de déploiement en opt-in.
