# Bilan du niveau avancé

Vous savez tester vos opt-ins et vous comprenez le statut dev-only.

## Ce que vous avez appris

- tester un contrôleur d'opt-in avec `FakeRequest` ;
- injecter un faux exécuteur pour les opt-ins à base ;
- pourquoi le paquet reste dev-only (ADR-041) et ne fuite jamais en production.

## Points clés

- l'outillage couvre le noyau (fixtures) ; la base se simule par injection ou base jetable ;
- dépendance de développement uniquement ;
- aucune importation dans le code applicatif.

## Fin du parcours

Vous maîtrisez l'infrastructure de test partagée de Forge.

[Aide-mémoire](../recapitulatif.md)
