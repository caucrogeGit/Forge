# Testing (forge-mvc-testing)

`forge-mvc-testing` est l'infrastructure de test partagée de Forge : la classe `FakeRequest` et un plugin pytest qui configure le noyau et nettoie l'état entre les tests.

C'est un paquet **dev-only** (ADR-041) : jamais une dépendance d'exécution, installé seulement pour les tests.

## En bref

- `FakeRequest` : une `Request` sans serveur HTTP ;
- plugin pytest (point d'entrée `pytest11`) : noyau configuré + fixtures de nettoyage ;
- s'active automatiquement dès qu'il est installé.

## Par où commencer

- [Référence](reference.md) : rôle, contrat, fixtures, vue d'ensemble.
- [Progression Testing](welcome/debutant/testing-welcome.md) : apprendre l'outillage pas à pas.

## Installation

```bash
pip install --pre forge-mvc-testing
```
