# Forge Admin

`forge-mvc-admin` est un opt-in Forge qui fournira un **back-office applicatif**
pour administrer les entités d'un projet.

!!! warning "Statut : scaffold"
    Le paquet est installable mais ne fournit pas encore de fonctionnalité.
    Cette page documente le **positionnement** de l'opt-in.
    Le châssis d'administration, les vues et les actions seront ajoutés par les
    tickets `ADMIN-*` suivants.

## Positionnement

Forge Admin sert l'application.
Il offre une interface pour lister, consulter, créer, modifier et supprimer les
entités déclarées par un projet Forge.

Trois briques répondent à des besoins distincts.

- **Forge Core** sert le runtime : il reste minimal et autonome.
- **Forge Admin** sert l'application : il administre ses entités.
- **Forge Design** sert le développeur : il aide à produire des templates.

Forge Admin est un opt-in.
Il s'installe séparément et n'est jamais chargé automatiquement par Forge Core.

## Ce que Forge Admin sera

- une interface d'administration construite depuis les contrats d'entités Forge ;
- un code explicite, lisible et modifiable, jamais une couche opaque ;
- une brique sécurisée par défaut : jamais publique, actions protégées, CSRF
  obligatoire, intégration RBAC quand l'opt-in est installé ;
- minimale au départ, enrichie par petits tickets.

## Ce que Forge Admin ne sera pas

- le cœur de Forge ni une dépendance obligatoire ;
- un clone de Symfony EasyAdmin ou un cockpit développeur ;
- un ORM ou une couche d'introspection automatique de la base ;
- une interface magique qui expose les entités sans déclaration explicite.

## Architecture

Forge Admin suit une architecture hybride.

Un châssis runtime mince est porté par le paquet : layout, navigation, rendu
commun, garde-fous de sécurité.
Les contrôleurs de ressource, eux, sont générés côté projet à partir des
contrats d'entités, puis possédés et modifiables par le développeur.

## Installation

```bash
pip install --pre forge-mvc-admin
```

À ce stade, l'installation ne pose que le paquet et son contrat de version.

## Commandes

`forge admin:init` prépare la structure du back-office dans le projet courant.

Elle crée `mvc/admin/__init__.py` et `mvc/admin/resources.py`, où l'application
déclare ses ressources administrables.
La commande est write-if-new : elle ne réécrit jamais un fichier existant et
n'écrase aucun code utilisateur.

```bash
forge admin:init
```

À ce stade du châssis, aucune vue ni template ne sont générés : ils viendront
avec les tickets de dashboard et de rendu.

`forge admin:doctor` vérifie la cohérence des ressources déclarées avec les
contrats d'entité du projet (lecture seule, sans connexion base).

```bash
forge admin:doctor
```

Elle importe `mvc/admin/resources.py` pour lire les ressources, lit les contrats
`mvc/entities/*/*.json`, et signale les écarts (entité introuvable, table ou
colonnes divergentes).
Un écart est un avertissement, pas une erreur : le contrat peut être en retard
sur la base, que l'admin interroge directement.

## Brancher le back-office

Le back-office expose ses routes via `register_admin_routes(router)`, appelé
explicitement par l'application (jamais d'injection automatique).

```python
# optins/admin/routes.py
from forge_mvc_admin import register_admin_routes

def register(router):
    register_admin_routes(router)
```

La première route est `GET /admin` : le **tableau de bord**, qui liste les
ressources déclarées dans le registre.
Elle n'est pas publique : un utilisateur non authentifié est redirigé vers la
page de connexion.

Le tableau de bord rend un template embarqué (`admin/dashboard.html`).
Un projet peut le surcharger en plaçant son propre `mvc/views/admin/dashboard.html`
(l'ordre des loaders donne la priorité au projet).

### Exiger une permission (RBAC, optionnel)

Par défaut, l'accès au back-office demande seulement d'être authentifié.
Un projet qui utilise `forge-mvc-rbac` peut exiger une permission sur toutes les
routes admin, en la passant à `register_admin_routes` :

```python
register_admin_routes(router, permission="admin.access")
```

Si `forge-mvc-rbac` est installé, un utilisateur sans la permission reçoit une
réponse 403.
S'il n'est pas installé, l'admin reste en authentification seule et `forge doctor`
le signale.
Sans ce paramètre, rien ne change : l'admin reste protégé par la seule
authentification.

## Surcharger les templates

Forge Admin embarque ses templates et les rend disponibles au moteur du cœur
(ADR-046). Un projet peut surcharger n'importe lequel en plaçant un fichier de
même chemin sous `mvc/views/admin/` : l'ordre des loaders donne la priorité au
projet, sans configuration.

Templates surchargeables :

- `admin/layout.html` : gabarit de base (en-tête, structure) ;
- `admin/dashboard.html` : tableau de bord ;
- `admin/list.html` : liste paginée d'une ressource ;
- `admin/detail.html` : fiche d'une ligne ;
- `admin/form.html` : formulaire de création et d'édition ;
- `admin/delete.html` : page de confirmation de suppression.

Par exemple, créer `mvc/views/admin/layout.html` dans le projet remplace le
gabarit de base pour tout le back-office, sans toucher au paquet.

## Suivre l'avancement

La feuille de route de cadrage et le découpage en tickets sont décrits dans la
roadmap Forge Admin : `docs/roadmap/forge-admin-roadmap.md`.
