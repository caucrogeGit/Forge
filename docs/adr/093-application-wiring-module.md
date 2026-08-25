# ADR-093 : Le câblage de l'application vit dans une source unique

## Statut

Acceptée.
Réalise la cible annoncée par l'[ADR-092](092-wsgi-entrypoint-wiring-parity.md), qui posait un refus en attendant celle ci.
Change la forme du squelette pour les projets futurs ; n'impose rien aux projets existants.

## Date

2026-08-25

## Contexte

L'ADR-092 a fait refuser au chemin WSGI de servir une application désarmée.
Ce refus rend une panne silencieuse bruyante, et il ne répare rien.

La cause reste entière, et elle est simple à énoncer.
Le squelette prescrivait de câbler middlewares et magasin de sessions dans `app.py`.
`build_application()` lit `config.py` et le module de routes, jamais `app.py`.
`config.py` ne porte que des valeurs, jamais des objets construits.

Il y avait donc **deux séquences de construction** pour une seule application, et rien ne pouvait les garder identiques.
La divergence n'était pas un accident : elle était la conséquence mécanique de la structure.

Deux ADR l'attestent, chacun ayant traité un symptôme de la même cause.
L'ADR-092 a posé le refus.
Le pont `from app import application` a rendu le chemin WSGI capable de servir l'application armée, en la lui faisant importer.

Ce pont fonctionne, et il a un coût qui ne se voit pas tout de suite.
Il fait dépendre la production de l'exécution complète de `app.py`, un fichier qui monte un serveur de développement, analyse des arguments de ligne de commande et configure un journal.
Il a d'ailleurs fallu neutraliser cette analyse d'arguments, qui posait `APP_ENV=dev` sur un serveur de production.

## Décision

**Le câblage vit dans un module que les deux points d'entrée lisent, et `app.py` cesse de construire l'application.**

### 1. Un module dédié, à la racine du projet

Le squelette livre `bootstrap.py`, à côté de `app.py` et de `config.py`, avec deux fonctions.

```python
def configure_services() -> None: ...
def build_middlewares() -> list[Any]: ...
```

`configure_services` est appelée avant `build_middlewares` : un middleware peut avoir besoin d'un service, l'inverse ne se produit pas.

Le nom est à la racine, et non sous `mvc/`, parce que ce câblage n'est pas du modèle, pas de la vue, pas du contrôleur.
Il est du même ordre que `config.py` : ce qui décide de la forme de l'application avant qu'elle serve.

### 2. `app.py` délègue à la fabrique

`app.py` ne construit plus.
Il appelle `build_application()`, comme le fait le chemin WSGI.

Il garde ce qui lui est propre, et rien d'autre : le serveur HTTP de développement, ses pages d'erreur, son TLS local.
Les valeurs de `config.py` qu'il importe se réduisent à celles dont ce serveur a besoin.

C'est ce point qui retire la cause, et non le fichier `bootstrap.py` seul.
Tant que deux fichiers construisent, deux fichiers peuvent diverger.

### 3. Un module de câblage absent n'est pas une erreur

Un projet sans `bootstrap.py` obtient le comportement d'avant.
Forge n'écrit jamais dans un projet existant (principe 9), et il n'y a rien à migrer.

### 4. Un module de câblage cassé fait échouer le démarrage

La distinction est le tout de cette décision.

« Le module existe il ? » se demande par `find_spec`, et une réponse négative est légitime.
« Se charge t il ? » se demande par l'import, et une réponse négative est une panne.

Attraper l'`ImportError` de l'import ferait retomber un `bootstrap.py` cassé, un opt-in désinstallé par exemple, sur une application silencieusement désarmée.
Ce serait recréer exactement le défaut que cet ADR corrige, à un endroit de plus.

### 5. Une liste vide reste un choix, pas un défaut

`build_middlewares()` retourne `[AuthMiddleware("/login")]` dans le squelette.
Retourner `[]` retire jusqu'à l'authentification, et le gabarit le dit.

C'est plus explicite que ce qui existait : le défaut d'`Application` posait `AuthMiddleware` sans que personne l'écrive, ce qui est précisément ce qui a fait croire, en production, que l'application était protégée.

## Conséquences

### Ce que cela apporte

Mesuré sur un projet dont `bootstrap.py` câble un middleware métier et un magasin de sessions partagé :

```text
WSGI   middlewares  : ['AuthMiddleware', 'MonGardeMetier']
WSGI   session_store: MonStorePartage
app.py middlewares  : ['AuthMiddleware', 'MonGardeMetier']
app.py session_store: MonStorePartage
```

Le chemin WSGI générique sert l'application armée **sans importer `app.py`**.
La docstring de `create_configured_wsgi_app()`, qui affirmait charger la même configuration que `python app.py`, redevient vraie au lieu d'être retirée.

Le pont de l'ADR-092 reste valable et devient un détail : `app.py` expose toujours `application`, mais les deux voies construisent désormais la même chose.

### Ce que cela coûte

Le squelette change de forme.
Un projet créé avant cet ADR garde deux séquences, et le refus de l'ADR-092 continue de le protéger.

`app.py` perd la moitié de son contenu, et une partie de sa valeur pédagogique : on y lisait la séquence complète d'initialisation.
Elle se lit désormais dans `core/app/app_factory.py`, qui est du framework et non du projet.

C'est un vrai renoncement, et il est assumé : une séquence lisible en double valait moins qu'une séquence unique.

### Limites

Le contrat de `bootstrap.py` est vérifié à l'exécution, par `getattr` et `callable`.
Une faute de frappe sur le nom d'une fonction ne produit aucune erreur : la fonction est simplement ignorée.

`forge doctor` serait le bon endroit pour le dire, et cet ADR ne le fait pas.

## Charte appliquée

- Règle A, retirer la cause : deux séquences de construction deviennent une.
- Principe 3, refuser la magie cachée : le câblage par défaut est écrit dans le projet, au lieu d'être un défaut d'`Application` que personne ne lit.
- Principe 9, pas d'écriture invisible : rien n'est réécrit chez les projets existants, qui restent valides.
- Principe 11, une seule façon officielle : un seul endroit où câbler.

## Liens

- [ADR-092](092-wsgi-entrypoint-wiring-parity.md) : le refus qui précède cette réparation.
- [ADR-024](024-skeleton-bootstrap.md) : bootstrap par squelette dédié.
- [ADR-061](061-optin-project-registry.md) : registre d'opt-ins visible du projet, même esprit de câblage explicite.
