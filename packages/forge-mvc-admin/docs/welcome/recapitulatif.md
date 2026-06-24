# Récapitulatif — Forge Admin

Ce parcours a couvert l'administration complète d'une entité.

## Ce que vous avez mis en place

- Installation de l'opt-in et branchement explicite de `register_admin_routes`.
- Déclaration d'une ressource administrable (`AdminResource`).
- Consultation : tableau de bord, liste paginée, fiche détail.
- Écriture : création et édition par formulaire, protégées par CSRF.
- Suppression contrôlée, en deux temps.
- Surcharge des templates depuis le projet.
- Permission RBAC optionnelle et diagnostic `forge admin:doctor`.

## Les garanties de Forge Admin

- `/admin` n'est jamais public : l'authentification est toujours exigée.
- Les mutations sont en POST et protégées par CSRF.
- Le SQL est contraint : colonnes en liste blanche, valeurs paramétrées.
- Aucun ORM, aucune introspection : ce que vous déclarez est ce qui est servi.

## Aller plus loin

- Le contrat d'une ressource (champs, table, tri, clé) est détaillé dans la
  page [Contrat de ressource](../resources.md).
- `forge admin:doctor` reste votre point de contrôle quand le schéma évolue.
