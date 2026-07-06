# Avancé 1 : Supprimer une ligne

Objectif : supprimer un article, sans risque de clic accidentel.

## Une suppression en deux temps

La fiche détail propose un lien « Supprimer ».
Il mène à une **page de confirmation** (`GET /admin/articles/<id>/delete`) qui n'efface rien : elle affiche la ligne et un bouton de confirmation.

La suppression effective n'a lieu qu'à la soumission du formulaire (`POST /admin/articles/<id>/delete`).

## Pourquoi ce détour

La mutation est strictement en POST, protégée par CSRF.
Aucune suppression ne peut être déclenchée par un simple lien ou un GET.
C'est la garantie « suppression contrôlée ».

La requête exécutée est ciblée :

```sql
DELETE FROM articles WHERE id = ? LIMIT 1
```

En cas de succès, le back-office redirige vers la liste avec un message de confirmation.

## À retenir

- La confirmation est en lecture seule ; seule la soumission POST supprime.
- La suppression est ciblée par la clé primaire et protégée par CSRF.

## Étape suivante

[Suivant : surcharger un template](admin-override.md)
