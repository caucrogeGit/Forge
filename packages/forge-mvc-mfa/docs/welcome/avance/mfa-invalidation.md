# Avancé 4 : Fermer les sessions à l'activation

Objectif : qu'activer un second facteur mette dehors qui était déjà entré.

## Le trou que cela ferme

Activer un facteur protège les connexions **à venir**.
Les sessions déjà ouvertes, elles, continuent : quelqu'un qui s'était introduit avant l'activation reste dedans, et le second facteur ne l'en déloge pas.

C'est précisément le scénario où l'on active un MFA : parce qu'on soupçonne que quelqu'un est entré.

```python
from core.sessions.manager import get_session_store

confirm_totp_factor(facteur, code)

magasin = get_session_store()
magasin.delete_for_user(utilisateur.id, except_session_id=get_session_id(request))
```

!!! danger "Épargnez la session depuis laquelle l'activation se fait"
    Sans `except_session_id`, activer un second facteur déconnecte celui qui vient de l'activer.

    Cela ne protège de rien, et transforme une bonne pratique en geste que les utilisateurs évitent.

!!! warning "L'ordre compte"
    Fermez les sessions **après** que le facteur est confirmé, jamais avant.

    Déconnecter tout le monde puis échouer à confirmer laisserait le compte sans facteur et sans session, pour rien.

!!! info "La même primitive sert au changement de mot de passe"
    `delete_for_user` révoque l'accès d'un compte d'un seul geste : activation d'un facteur, changement de mot de passe, déconnexion à distance depuis un écran de sécurité.

    Une session anonyme n'est jamais touchée : seules celles qui portent l'identité du compte le sont.

## Le vérifier

L'écran des sessions du back-office montre le nombre de sessions actives.
Il tombe à une après l'activation, celle que vous avez épargnée.

## À retenir

- Activer un facteur ne ferme rien de lui même ; c'est un geste explicite.
- Épargnez la session courante, sans quoi l'utilisateur se déconnecte lui même.
- Confirmez le facteur d'abord, fermez ensuite.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
