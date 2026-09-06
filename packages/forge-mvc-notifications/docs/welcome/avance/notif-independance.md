# Indépendance du cœur

Objectif : comprendre pourquoi les notifications sont un opt-in, et non une brique du cœur.

**Ce que vous allez apprendre :** Forge Core ne dépend pas de `forge-mvc-notifications`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Le paramètre `db=` rend les fonctions testables, et le schéma visible via la migration rendue.

Deuxième palier du **niveau avancé** de la progression Notifications.

## Ce que ce starter montre

- la règle de dépendance de l'opt-in ;
- l'injection de connexion via `db=` ;
- le schéma visible via la migration rendue.

## La règle

```text
Forge Core ne sait rien des notifications.
forge-mvc-notifications fournit une API explicite.
L'application décide ce qu'elle notifie et où elle l'affiche.
```

- Aucun fichier du cœur n'importe `forge_mvc_notifications`, ce qui est verrouillé par un test.
- Le paquet importe le cœur pour accéder à la base : l'opt-in dépend du cœur, c'est le sens autorisé.
- Retirer le paquet ne casse pas le cœur : il n'en a jamais dépendu.

## Injecter une connexion pour les tests

```python
from forge_mvc_notifications import notify, get_notifications, TABLE_NAME

# Chaque fonction accepte db= pour cibler une connexion précise.
notify("eleve.42", "Test", db=connexion_de_test)
notifications = get_notifications("eleve.42", db=connexion_de_test)

# Le schéma de la table est exposé comme constante.
print(TABLE_NAME)
```

### Comprendre ce code

- Chaque fonction (`notify`, `get_notifications`, `unread_count`, `mark_read`, `mark_all_read`) accepte `db=`.
- Sans `db=`, les fonctions utilisent la connexion configurée par le cœur.
- Avec `db=`, vous ciblez une connexion précise, par exemple une base de test isolée.
- Le schéma vit dans la migration écrite par `forge notifications:init`, rendue pour le backend installé et relue avant application.

## Ce que cela vous apporte

- Vous n'embarquez les notifications que si vous installez le paquet.
- Le cœur reste minimal et auditable, fidèle au périmètre défini par l'ADR-004.
- Le paramètre `db=` rend l'API testable sans dépendre d'une configuration globale.

## À retenir

- L'opt-in dépend du cœur, le cœur ignore l'opt-in.
- Toutes les fonctions acceptent `db=` pour injecter une connexion.
- La migration rendue documente le schéma et sert à le reproduire.

## Après ce starter

Vous avez fait le tour du socle.
Place au bilan du niveau avancé.

[Suivant : relayer vers un autre canal](notif-relais.md)
