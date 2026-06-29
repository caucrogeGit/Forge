# Bilan du niveau intermédiaire

Vous savez tester un contrôleur avec des fixtures propres.

## Ce que vous avez appris

- le plugin pytest s'active tout seul (`pytest11`) ;
- les fixtures autouse configurent le noyau et nettoient l'état ;
- la fixture `fake_request` fabrique des requêtes ;
- on teste une action en inspectant la `Response`.

## Points clés

- aucune configuration `conftest` requise ;
- isolation des tests par défaut ;
- seul le transport HTTP est simulé, la logique est réelle.

## Après ce niveau

Place au niveau avancé : tester vos opt-ins et comprendre le dev-only.

[Niveau avancé : Tester un opt-in](../avance/testing-optin.md)
