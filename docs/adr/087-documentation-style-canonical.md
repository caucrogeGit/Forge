# ADR-087 : Style rédactionnel canonique de la documentation Forge

## Statut

Acceptée.
Décision de gouvernance documentaire ; relève du mainteneur.
Source de l'ADR de style que l'ADR-082 fait poser dans les projets.

## Date

2026-07-28

## Contexte

Forge impose un style rédactionnel à sa documentation depuis longtemps : français, une phrase par ligne, pas de tiret cadratin, ponctuation française.
Ces règles vivent dans `CLAUDE.md`, section 2.1, sous forme de directive adressée aux agents.

L'ADR-082, lui, fait poser dans chaque projet un `docs/adr/002-style-documentation.md`, écrit depuis un gabarit de `cli/agents/seed_adr.py`, qui énonce **six règles**.
Forge prescrit donc à ses utilisateurs un ADR, daté et motivé, pour une règle qu'il s'applique à lui-même sans ADR.

Trois conséquences, constatées.

D'abord, les deux énoncés ne coïncident pas.
Le gabarit projet exige la vérification des liens internes au build strict ; `CLAUDE.md` ne la mentionne pas.
`CLAUDE.md` détaille la portée (guides, pages MkDocs, README, tickets) ; le gabarit reste général.
Rien ne garantit qu'ils restent alignés, puisque rien ne déclare qu'ils devraient l'être.

Ensuite, le statut diffère.
`CLAUDE.md` est un briefing, refondu à chaque version majeure, et son en-tête l'annonce.
Une règle de style n'a pas vocation à disparaître au prochain tag majeur : elle mérite le format qui la date et la motive, celui-là même que Forge recommande à ses utilisateurs.

Enfin, une application réelle a montré la valeur du format.
RéférenCiel Manager, banc d'essai au sens de l'ADR-009, a reçu l'ADR de style posé par `forge new`, puis l'a **étendu** de cinq règles propres à son domaine, chacune datée et motivée par un constat de terrain.
Le mécanisme d'amorçage fonctionne ; c'est sa source qui manque.

## Décision

Le présent ADR devient la **source unique** du style rédactionnel de la documentation Forge.

Toute documentation du dépôt respecte les règles suivantes.

1. **Langue** : rédiger en français, sauf les noms de commandes, symboles de code et termes techniques indispensables.
2. **Une phrase par ligne** dans la source Markdown : après le point final, la phrase suivante commence sur une nouvelle ligne.
   Cela garde les diffs lisibles, et l'extension `nl2br` étant active, le rendu suit ligne à ligne.
3. **Pas de tiret cadratin** (le caractère long, U+2014).
   Préférer la virgule, le point-virgule, les deux-points, ou le trait d'union court selon le sens.
4. **Ponctuation française** : espaces insécables avant les signes doubles (deux-points, point-virgule, point d'interrogation, point d'exclamation) et guillemets français.
5. **Au plus un deux-points par phrase**, réservé à l'énumération, à la citation ou à la conséquence annoncée.
   Sinon, une virgule pour l'incise, ou un point et une phrase nouvelle.
   Cette règle attrape un travers d'écriture fréquent, l'empilement de propositions dans une phrase à rallonge.
6. **Liens internes** vers le fichier `.md` cible, vérifiés au build strict de la documentation.
7. **Éviter les anglicismes** inutiles et les tournures calquées sur l'anglais.

Portée : tous les fichiers de documentation, les guides, les pages MkDocs, les README, la documentation embarquée des paquets, et toute proposition d'édition produite par un agent.

Cette décision porte sur la rédaction, pas sur le fond.
Elle s'applique aux corrections comme aux nouveaux documents, et n'impose aucune campagne de réécriture du fonds existant.

### Articulation avec les documents voisins

- **`CLAUDE.md` §2.1 renvoie ici** et cesse d'énoncer les règles en double.
  Le briefing reste le point d'entrée d'un agent ; la règle, elle, vit dans un document daté.
- **Le gabarit de `cli/agents/seed_adr.py` dérive du présent ADR.**
  Les règles posées dans un projet sont celles-ci ; le gabarit le déclare, pour qu'une divergence se voie.
- **L'ADR-003 n'est pas révisé.**
  L'API publique de Forge reste en anglais ; le français vise la **documentation**, pas les identifiants.
  Une application peut décider d'écrire son code métier en français, comme l'a fait le banc d'essai : c'est sa décision, pas celle de Forge.

### Ce qui est vérifiable, et ce qui ne l'est pas

Deux règles se contrôlent mécaniquement, et un garde-fou les fige : l'absence de tiret cadratin (règle 3) et l'unicité du deux-points par phrase (règle 5).

Les autres relèvent du jugement.
La qualité d'une tournure française ne se mesure pas par une expression rationnelle, et un contrôle approximatif produirait des faux positifs qui feraient désactiver l'ensemble.
Forge préfère un garde-fou étroit et respecté à un garde-fou large et contourné.

Le fonds existant est **gelé en l'état** par un cliquet : le compte de fichiers non conformes ne peut que décroître.
Cela interdit toute nouvelle infraction sans imposer de campagne de réécriture, sur le modèle du garde-fou de portabilité du DDL.

## Conséquences

- La règle de style a un lieu unique, daté et motivé, au lieu de deux énoncés partiels dont l'alignement n'était garanti par rien.
- Ce que Forge demande à ses utilisateurs, il se l'applique dans la même forme.
- Un écart de style devient un correctif simple, pas une négociation.
- Les deux règles mécanisables cessent de reposer sur la seule relecture.
- Le fonds documentaire n'est pas réécrit : il est gelé, et se conforme au fil des retouches.
- Une évolution du style se fait ici, et se répercute au gabarit projet par une décision explicite, jamais par dérive.

## Alternatives écartées

**Laisser la règle dans `CLAUDE.md` seul.**
Rejeté : le briefing est refondu à chaque version majeure, et il ne porte ni date ni motivation.
Forge recommanderait par ailleurs à ses utilisateurs un format qu'il refuserait pour lui-même.

**Un garde-fou couvrant les sept règles.**
Rejeté : la langue et les tournures ne se contrôlent pas mécaniquement sans faux positifs.
Un garde-fou bruyant est désactivé, donc inutile.

**Réécrire tout le fonds documentaire pour le rendre conforme.**
Rejeté : le volume est considérable et le bénéfice faible, l'existant restant lisible.
Le cliquet obtient le même résultat dans le temps, sans campagne ni risque de régression.

**Aligner l'ADR-003 pour autoriser le français dans le code.**
Rejeté : l'API publique d'un framework est un contrat, et l'anglais y reste la convention.
La question du code métier d'une application ne relève pas de Forge.
