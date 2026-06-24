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

## Suivre l'avancement

La feuille de route de cadrage et le découpage en tickets sont décrits dans la
roadmap Forge Admin : `docs/roadmap/forge-admin-roadmap.md`.
