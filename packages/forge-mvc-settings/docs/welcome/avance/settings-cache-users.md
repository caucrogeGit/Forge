# Avancé 3 : Le cache et les paramètres par utilisateur

Objectif : ne pas relire la base à chaque affichage, et laisser chacun régler son thème.

## Un cache à invalidation explicite

```python
from forge_mvc_settings import enable_settings_cache, clear_settings_cache

enable_settings_cache()
```

Une écriture passant par `set_setting` ou `delete_setting` invalide la clé d'elle même.

!!! danger "Une écriture faite hors de l'API n'invalide rien"
    Un `UPDATE` en SQL direct, ou une écriture depuis un autre processus, laisse le cache périmé jusqu'au prochain `clear_settings_cache()`.

    Le cache vit dans le processus : sous plusieurs travailleurs, chacun a le sien, et ils peuvent diverger.

!!! info "Le cache est facultatif, et par défaut absent"
    Sans `enable_settings_cache()`, chaque lecture va en base.

    C'est le comportement le plus simple à raisonner, et il convient tant que les paramètres ne sont pas lus à chaque requête.

## Les paramètres par utilisateur

```python
from forge_mvc_settings import set_user_setting, get_user_settings

set_user_setting(utilisateur.id, "theme", "sombre")
reglages = get_user_settings(utilisateur.id)
```

Ils vivent dans la même table, sous un préfixe réservé.

!!! danger "Le préfixe est réservé, pas seulement conventionnel"
    Une clé globale nommée `user.42.theme` désignerait la même ligne que le paramètre de l'utilisateur 42.

    `set_setting` refuse donc ce préfixe, et un identifiant contenant un point est refusé lui aussi : sans cela, deux utilisateurs pourraient viser la même clé.

!!! warning "Un écran de réglages ne montre que les paramètres globaux"
    `describe_settings` et `get_all_settings` excluent l'espace des utilisateurs.

    Les mêler ferait afficher les préférences de tous les comptes, adresses comprises, sur une page d'administration.

## À retenir

- Le cache s'active explicitement, et une écriture hors API le laisse périmé.
- Les paramètres par utilisateur vivent sous un préfixe réservé.
- Les écrans de réglages ne voient jamais cet espace.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
