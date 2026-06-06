# forge-mvc-pivot

Opt-in Forge pour les **tables pivot enrichies** : associations `many_to_many`
portant des attributs (par exemple `position`, `note`) sur la ligne de jointure.

Extrait du core de Forge (ADR-021) : le core ne contient que les primitives
générales ; le pivot avancé est une brique spécialisée, optionnelle.

## Contenu

- `PivotAdvancedService` : lecture et écriture d'associations pivot avec
  attributs, contraintes déclaratives (`required`, `nullable`, `unique_pair`),
  accès base injectables (`fetch_one`, `fetch_all`, `execute`, `insert_fn`).
- `PivotFieldConstraint`, `PivotRow`, `PivotFormError`, `PivotConstraintError`,
  `pivot_error_to_form_error` : contraintes, résultats et erreurs structurées.
- Générateur `forge make:pivot-crud <EntitéSource> <nomRelation>` : échafaude un
  sous-CRUD pivot à partir d'une relation `many_to_many` déclarée dans
  `relations.json`.

## Installation

```bash
pip install --pre forge-mvc-pivot
```

Le code généré importe `forge_mvc_pivot` : installez le paquet avant de lancer
une application qui s'appuie sur un sous-CRUD pivot.
