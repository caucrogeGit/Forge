# forge-mvc-admin

Opt-in Forge pour un **back-office applicatif** (Forge Admin).

> **Statut : livré, en beta.**
> Le paquet fournit un back-office fonctionnel, adossé aux contrats Forge :
> tableau de bord, liste paginée avec recherche et filtres, fiche, création,
> édition, suppression unitaire et suppression groupée.
>
> Ce paragraphe annonçait que « les filtres de liste et les actions en masse
> restent à venir » alors que les filtres étaient livrés et que les actions
> groupées le sont depuis `ADMIN-BULK-ACTIONS-001`. Un README qui décrit un
> état antérieur à son code est pire qu'un README absent : il fait chercher
> ailleurs ce qui est déjà là. Le garde-fou `META-README-COMMANDS-RATCHET-001`
> ferme désormais une partie de cette dérive.

## Positionnement

Forge Admin sert l'application.
Il fournit une interface d'administration des entités d'un projet Forge,
construite depuis les contrats Forge, explicite et modifiable.

Forge Admin est un opt-in.
Il n'est jamais chargé automatiquement par Forge Core, et ses routes ne sont
branchées que par un appel explicite de l'application.

## Installation

```bash
pip install --pre forge-mvc-admin
```

## API publique

| Nom | Rôle |
|---|---|
| `AdminResource` | Contrat d'une entité administrable, validé à la construction |
| `AdminRegistry`, `registry` | Registre explicite des ressources exposées |
| `AdminController` | Contrôleur HTTP du back-office |
| `register_admin_routes` | Branchement explicite des routes sur un routeur Forge |
| `AdminError`, `AdminResourceError`, `AdminRegistryError` | Erreurs du paquet |

## Ce que le back-office sert

- Un tableau de bord listant les ressources déclarées.
- Une liste paginée par ressource, triée par la colonne déclarée.
- Une vue de détail.
- La création, la modification et la suppression avec écran de confirmation.

Les horodatages gérés de l'ADR-081 sont posés par le back-office lorsque la
ressource déclare `timestamps=True`.

## Sécurité

Les routes ne sont pas publiques.
Elles exigent une session authentifiée, vérifiée par l'`AuthMiddleware` et à
nouveau par `@require_auth`, en défense en profondeur.

Une permission RBAC peut être déclarée par route.
Si une permission est déclarée alors que `forge-mvc-rbac` n'est pas installé,
l'accès est refusé plutôt qu'accordé.

## Commandes

| Commande | Rôle |
|---|---|
| `forge admin:init` | Pose la configuration et les gabarits du back-office |
| `forge admin:doctor` | Vérifie que les ressources déclarées existent réellement |

## Documentation

La documentation embarquée vit dans `docs/`.
La roadmap de cadrage d'origine est `docs/roadmap/forge-admin-roadmap.md`.
