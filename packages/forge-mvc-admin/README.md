# forge-mvc-admin

Opt-in Forge pour un **back-office applicatif** (Forge Admin).

> **Statut : scaffold.**
> Ce paquet est installable mais ne fournit pas encore de fonctionnalité.
> Il pose le paquet et son contrat de version (ticket `ADMIN-OPTIN-PACKAGE-001`).
> Le châssis d'administration, le registre de ressources et les vues seront
> ajoutés par les tickets `ADMIN-*` suivants.

## Positionnement

Forge Admin sert l'application : il fournira une interface d'administration des
entités d'un projet Forge, construite depuis les contrats Forge, explicite et
modifiable.

Forge Admin est un opt-in : il n'est jamais chargé automatiquement par Forge
Core.

Voir la roadmap de cadrage : `docs/roadmap/forge-admin-roadmap.md`.

## Installation

```bash
pip install --pre forge-mvc-admin
```

## Contenu actuel

- `__version__` : version du paquet, alignée sur la série Forge.

Aucune autre API publique n'est exposée à ce stade.
