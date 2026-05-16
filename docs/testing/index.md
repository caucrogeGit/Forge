# Pack — Roadmap Forge Tests terrain v3

Ce pack contient les documents de pilotage de la campagne de tests terrain progressive de Forge.

Version corrigée v3.2 : ajout du verrou explicite `documentation officielle erronée pendant un ticket de test`.

Rappel v3.1 : ajout de la capitalisation documentaire `ticket FT validé → tutoriel Forge`.

## Fichiers

1. `01-document-pilotage-campagne-tests-terrain-forge.md`  
   Règles générales, verrous, niveaux de guidage, gravité, preuves, statuts et transformation des retours en tickets correctifs.

2. `02-roadmap-tests-terrain-forge-v3.md`  
   Roadmap indépendante détaillée en phases et tickets, avec objectif court par ticket.

3. `03-modele-ticket-ft-verrouille.md`  
   Structure obligatoire d’un ticket terrain Forge exploitable.

4. `04-modele-retour-experience-testeur.md`  
   Modèle de retour à remplir par les testeurs.

5. `05-grille-triage-decision-stabilisation.md`  
   Grille de triage des retours et critères de décision bêta/stable.

## Correction v3.1

Cette version ajoute le principe suivant :

```text
Ticket FT rédigé
→ test terrain
→ retour terrain
→ correction éventuelle
→ ticket validé
→ conversion en tutoriel
→ ajout au menu Tutoriels
```

Un ticket FT reste un outil de validation interne.  
Un tutoriel Forge est sa version nettoyée, publiée seulement après validation terrain.

## Emplacement conseillé dans le dépôt Forge

```text
docs/testing/field-test-charter.md
docs/testing/feedback-template.md
docs/testing/ticket-template.md
docs/testing/triage-and-stabilization.md
docs/roadmap/forge-field-test-roadmap.md
```

## Principe central

Cette roadmap ne sert pas à développer Forge.  
Elle sert à vérifier que Forge peut être installé, compris, utilisé, maintenu et déployé par des utilisateurs réels.

Un ticket terrain `FT-*` ne corrige pas le framework.  
Il produit un retour reproductible, des preuves, un verdict et, si nécessaire, une proposition de ticket correctif séparé.


## Correction v3.2

Cette version ajoute une règle explicite :

```text
La documentation officielle fait partie de ce qui est testé.
Si elle est fausse, incomplète ou contradictoire, le testeur ne corrige pas directement.
Il documente l’écart, fournit les preuves, classe la gravité et met le statut adapté.
```

Statuts concernés :

```text
BLOQUÉ PAR DOCUMENTATION
VALIDÉ AVEC FRICTION
```

Le référent Forge transforme ensuite le retour en ticket documentaire séparé, par exemple :

```text
DOC-FT-XX-NOM-DU-TICKET-001
```
