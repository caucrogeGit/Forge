# Avancé 5 : Journaliser les refus

Objectif : voir qu'un compte essaie une à une les routes protégées.

## Ce qu'un refus laissait derrière lui

Rien.
Une énumération de droits, quelqu'un qui tente chaque route pour voir laquelle cède, ne laissait aucune trace. L'exploitant n'avait aucun moyen de la voir, ni même de savoir qu'un compte butait sur une permission mal attribuée.

Les **cinq** gardes du paquet annoncent désormais leurs refus, et l'application décide de ce qu'elle en fait.

## Le branchement livré

```python
from forge_mvc_audit import audit_permission_denials

audit_permission_denials()
```

Une ligne au câblage, dans `bootstrap.py`. Chaque refus devient une entrée du journal d'audit.

| Champ de la ligne | Contenu |
|---|---|
| `action` | `acces.refuse` |
| `actor` | l'utilisateur, ou `None` s'il ne l'était pas |
| `target_id` | la permission refusée |
| `details` | la méthode, le chemin, et la garde qui a refusé |

!!! info "Un visiteur anonyme est journalisé lui aussi"
    C'est même souvent celui qu'on veut voir : une énumération se mène rarement en étant connecté.

!!! warning "La garde qui refuse est retenue, et ce n'est pas un détail"
    Un refus contractuel et un refus de permissions chargées en base ne se corrigent pas au même endroit.

    Sans `source`, le journal répond « quelqu'un a été refusé » et rien de plus.

!!! danger "Un refus ne devient jamais une panne"
    Si la base d'audit est indisponible, l'exception est avalée et journalisée, et le refus s'applique quand même.

    Transformer un 403 en 500 parce que le journal est en panne ferait d'un contrôle d'accès qui fonctionne une panne du site.

## Votre propre destinataire

`forge-mvc-rbac` n'importe aucun autre opt-in : il **annonce**, il ne journalise pas.

```python
from forge_mvc_rbac import on_permission_denied

on_permission_denied(lambda refus: metrique.increment("rbac.refus", tag=refus.source))
```

Une métrique, une alerte, un journal maison : `DenialEvent` porte la permission, l'acteur, le chemin, la méthode et la garde.

## À retenir

- Les cinq gardes annoncent leurs refus ; rien n'est journalisé sans branchement.
- `audit_permission_denials()` est le branchement livré, en une ligne.
- Un observateur qui échoue ne casse pas la réponse.

## Étape suivante

[Suivant : exporter le contrat](rbac-export.md)
