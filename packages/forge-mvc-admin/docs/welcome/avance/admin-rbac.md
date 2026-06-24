# Avancé 3 — Exiger une permission

Objectif : réserver le back-office à certains rôles, si le projet utilise RBAC.

## Le point de départ

Par défaut, le back-office demande seulement d'être authentifié.
Pour aller plus loin et exiger une **permission**, le projet active l'option
explicitement.

## Activer la permission

Dans le branchement (`mvc/routes.py`), passez une permission :

```python
register_admin_routes(router, permission="admin.access")
```

Le comportement dépend de la présence de l'opt-in `forge-mvc-rbac` :

- s'il est installé, un utilisateur sans la permission `admin.access` reçoit une
  réponse 403 ;
- s'il n'est pas installé, le back-office reste en authentification seule, et
  `forge doctor` le signale.

Sans ce paramètre, rien ne change : l'authentification seule protège l'admin.

## Déclarer la permission

Avec `forge-mvc-rbac`, ajoutez la permission à un rôle dans le contrat
`mvc/security/rbac.json` :

```json
{
  "schema_version": "1.0",
  "roles": {
    "admin": ["admin.access"]
  }
}
```

## Vérifier la cohérence

`forge admin:doctor` rapproche vos ressources des contrats d'entité (table,
colonnes, clé primaire) et signale les écarts, en lecture seule.

## À retenir

- La permission est un opt-in explicite ; le défaut reste l'authentification.
- Sans `forge-mvc-rbac`, l'admin ne se verrouille pas par surprise.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
