# Intermédiaire 4 : Rendre le facteur obligatoire

Objectif : qu'un administrateur ne puisse pas se passer d'un second facteur.

## Ce que le paquet savait, et ne savait pas

Il savait dire si un utilisateur **a** un facteur actif.
Il ne savait pas dire s'il **devrait** en avoir un.

L'application écrivait donc, dans chaque écran sensible, un « si cet utilisateur est administrateur et n'a pas de MFA, alors refuser ». Elle l'écrivait bien la première fois, et l'oubliait au troisième écran d'administration ajouté six mois plus tard.

## La politique se déclare une fois

```bash
MFA_REQUIRED_ROLES=admin,comptable
```

```python
from forge_mvc_mfa.policy import check_mfa_requirement

exigence = check_mfa_requirement(session, facteurs_de_l_utilisateur)
if exigence.required and not exigence.satisfied:
    return redirect("/mfa/enroll")
```

| Ce que rend `check_mfa_requirement` | Sens |
|---|---|
| `required` | ce compte doit avoir un second facteur |
| `satisfied` | il en a un, actif |

Un seul endroit dit qui doit avoir un second facteur, et le contrôle se pose là où il compte.

!!! danger "La politique n'active rien"
    Rendre un facteur obligatoire ne peut pas le créer à la place de l'utilisateur : le secret doit être scanné par son téléphone.

    Elle dit qu'il en faut un ; c'est à l'application de conduire l'utilisateur vers l'enrôlement, et de décider ce qu'il peut faire en attendant.

!!! warning "Le nom du rôle est comparé sans tenir compte de la casse"
    `admin` et `Admin` désignent le même rôle.

    Sans cela, une majuscule dans un contrat RBAC ferait tomber la politique en silence, et personne ne le verrait avant un audit.

!!! info "Une liste vide n'exige rien"
    Sans `MFA_REQUIRED_ROLES`, aucun rôle n'est concerné, et `required` vaut toujours faux.

    C'est un choix explicite, non une politique par défaut : Forge ne décide pas qui, dans votre application, mérite un second facteur.

## À retenir

- Une variable d'environnement déclare les rôles concernés, une fois.
- `check_mfa_requirement` répond « il en faut un » et « il en a un ».
- Elle n'enrôle personne : conduire l'utilisateur reste votre travail.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
