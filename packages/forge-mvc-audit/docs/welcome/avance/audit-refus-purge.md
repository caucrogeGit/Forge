# Avancé 3 : Les refus d'accès et la rétention

Objectif : voir qui bute sur une permission, et empêcher le journal de grossir sans fin.

## Journaliser les refus du contrôle d'accès

```python
from forge_mvc_audit import audit_permission_denials

audit_permission_denials()
```

Une ligne au câblage, et chaque refus de `forge-mvc-rbac` devient une entrée du journal.

| Champ | Contenu |
|---|---|
| `action` | `acces.refuse` |
| `target_id` | la permission qui manquait |
| `details` | la méthode, le chemin, et la garde qui a refusé |

!!! info "Le second appel ne rebranche pas"
    Deux observateurs écriraient deux lignes par refus, et compter les refus donnerait le double sans que rien ne le signale.

!!! warning "Un refus ne devient jamais une panne"
    Si la base d'audit est indisponible, l'exception est avalée et journalisée, et le refus s'applique quand même.

## Borner la croissance

```bash
forge audit:gc --days 90
forge audit:gc --days 90 --run
```

Sans `--run`, la commande **compte** et n'efface rien.

!!! danger "La rétention est une décision, pas un réglage technique"
    Un journal d'audit sert à répondre à une question posée après coup, parfois des mois plus tard.

    Quatre-vingt-dix jours conviennent à un usage courant ; une obligation légale ou un besoin d'enquête peut demander bien plus. Forge ne choisit pas à votre place.

!!! info "La purge se planifie"
    Lancée à la main, elle ne tourne jamais.

    Le guide de déploiement en donne la minuterie ; la table grossit sinon jusqu'à ce que quelqu'un s'en aperçoive.

## Exporter avant de purger

`iter_audit_rows` parcourt le journal par lots, sans borne silencieuse, ce que demande un export qui doit être complet ou ne pas exister.

## À retenir

- Le branchement des refus tient en une ligne, et ne se double pas.
- `audit:gc` compte par défaut, et n'efface qu'avec `--run`.
- La durée de rétention vous appartient ; la planifier aussi.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
