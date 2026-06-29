# Bilan du niveau débutant

Vous savez fabriquer des requêtes factices pour vos tests.

## Ce que vous avez appris

- `FakeRequest` imite `Request` (accesseurs `query`/`form`/`json`/`file`/`header`) ;
- on simule un formulaire avec `body`, un corps JSON avec `json_body` ;
- la surcharge de méthode `_method` est appliquée comme en vrai.

## Points clés

- pas besoin de serveur HTTP pour tester un contrôleur ;
- `FakeRequest` est fidèle à l'API de `Request` ;
- le paquet est dev-only (ADR-041).

## Après ce niveau

Place au niveau intermédiaire : fixtures et isolation.

[Niveau intermédiaire : Fixtures et isolation](../intermediaire/testing-fixtures.md)
