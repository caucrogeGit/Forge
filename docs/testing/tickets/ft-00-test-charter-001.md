# FT-00-TEST-CHARTER-001 : Lire et comprendre la charte de campagne

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

---

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Phase | FT-00, Cadre de la campagne terrain |
| Ticket | FT-00-TEST-CHARTER-001 |
| Niveau de guidage | G0, Guidé complètement |
| Profil testeur visé | tout profil |
| Durée indicative | courte (30 à 60 minutes) |
| Environnement cible | tout environnement |
| Dépend de | aucun |
| Peut être testé sans base ? | oui |
| Peut être testé sans navigateur ? | oui |

---

## 2. Objectif du ticket

Lire la charte de campagne et vérifier que le testeur comprend son rôle, ses responsabilités et les règles de la campagne de tests terrain Forge.

---

## 3. Ce que ce ticket permet de tester dans Forge

Ce ticket ne teste pas le framework. Il vérifie que le testeur est opérationnel pour la campagne :

- il sait distinguer ce qu'il doit faire et ce qu'il ne doit pas faire ;
- il connaît les niveaux de guidage G0 à G3 ;
- il connaît les niveaux d'aide A0 à A5 ;
- il connaît les gravités S0 à S5 ;
- il connaît les statuts finaux d'un ticket terrain ;
- il sait quoi faire si la documentation officielle est erronée.

---

## 4. Périmètre

### Inclus

- lecture de la charte de campagne ;
- lecture du modèle de retour d'expérience ;
- vérification de la compréhension des statuts, gravités et niveaux ;
- production d'un retour à blanc sur ce ticket.

### Exclu

- installation de Forge ;
- modification de fichiers du projet ;
- test de fonctionnalités du framework.

---

## 5. Contexte utile avant de commencer

La campagne de tests terrain Forge est indépendante du développement du framework. Elle ne cherche pas à ajouter des fonctionnalités. Elle cherche à vérifier qu'un utilisateur réel peut installer, comprendre, utiliser et déployer Forge.

Un ticket terrain `FT-*` ne corrige pas Forge. Il produit un retour reproductible, des preuves, un verdict et, si nécessaire, une proposition de ticket correctif séparé.

---

## 6. Documentation Forge à consulter

```text
docs/testing/field-test-charter.md
docs/testing/field-test-feedback-template.md
```

Le retour testeur devra indiquer quelles pages ont réellement été lues.

### Verrou : documentation erronée

Si une documentation indiquée dans ce ticket est fausse, incomplète ou contradictoire :

1. ne pas corriger directement la documentation pendant ce ticket ;
2. noter la page concernée ;
3. noter le passage erroné ou ambigu ;
4. noter l'étape du ticket concernée ;
5. expliquer ce que la documentation dit ;
6. expliquer ce que Forge fait réellement ;
7. fournir les preuves ;
8. indiquer le contournement éventuel ;
9. choisir le statut `BLOQUÉ PAR DOCUMENTATION` ou `VALIDÉ AVEC FRICTION` ;
10. proposer la gravité S1, S2, S3 ou S4 selon l'impact.

Le référent Forge décidera ensuite si un ticket documentaire séparé doit être créé.

---

## 7. Pré-requis

- accès à la documentation Forge (locale ou en ligne) ;
- aucun pré-requis technique.

---

## 8. Fichiers, classes ou commandes concernés

### `docs/testing/field-test-charter.md`

- **Rôle :** définir les règles de la campagne de tests terrain.
- **Nature :** document de référence.
- **Utilisation dans ce ticket :** lecture intégrale.
- **Action autorisée :** lire, prendre des notes.
- **À ne pas faire :** modifier ce fichier.

### `docs/testing/field-test-feedback-template.md`

- **Rôle :** modèle de retour à remplir après chaque ticket terrain.
- **Nature :** document de référence.
- **Utilisation dans ce ticket :** lecture et compréhension de la structure.
- **Action autorisée :** lire, identifier les champs obligatoires.
- **À ne pas faire :** modifier ce fichier.

---

## 9. Exemple indicatif décorrélé

Ce ticket ne demande pas de modifier du code. L'exemple ci-dessous illustre la forme d'un statut et d'une gravité dans un retour différent de ce ticket :

```text
Statut : VALIDÉ AVEC FRICTION
Gravité : S3 - Friction mineure
Commentaire : la commande a fonctionné, mais le message d'erreur était peu clair.
```

Le testeur devra produire un exemple similaire pour ce ticket après lecture.

---

## 10. Procédure de test

1. Ouvrir la [charte de campagne](../field-test-charter.md).
2. Lire intégralement le document.
3. Identifier et noter les niveaux de guidage G0 à G3.
4. Identifier et noter les niveaux d'aide A0 à A5.
5. Identifier et noter les gravités S0 à S5.
6. Identifier et noter les statuts finaux possibles.
7. Lire le [modèle de retour testeur](../field-test-feedback-template.md).
8. Identifier les champs obligatoires du retour.
9. Produire un retour à blanc pour ce ticket.

---

## 11. Résultat attendu

Le testeur est capable de répondre aux questions suivantes sans consulter la charte :

- Quelle est la différence entre S1 et S2 ?
- Que signifie A4 ?
- Quel statut choisir si Forge fonctionne mais la documentation est fausse ?
- Qui crée le ticket correctif quand la documentation est erronée ?

---

## 12. Erreurs ou cas à observer

- charte peu claire sur un point précis : noter le passage, gravité S3 ou S2 ;
- lien vers la charte cassé depuis l'index : noter la page, gravité S2 ;
- charte absente ou inaccessible : statut `BLOQUÉ PAR DOCUMENTATION`, gravité S1.

---

## 13. Critères de validation du ticket

Le ticket est validé si :

- le testeur a lu intégralement la charte ;
- le testeur peut citer correctement les statuts finaux ;
- le testeur peut citer les gravités S0 à S5 ;
- un retour à blanc est produit ;
- le retour contient verdict, gravité et niveau d'aide.

---

## 14. Preuves à fournir

- capture ou extrait de la section de la charte jugée la plus importante ;
- retour d'expérience rempli pour ce ticket.

---

## 15. Retour d'expérience attendu

Le testeur doit répondre au [modèle de retour testeur](../field-test-feedback-template.md).

Points obligatoires :

- documentation lue ;
- clarté de la charte (oui / partiellement / non) ;
- points ambigus relevés ;
- verdict ;
- gravité éventuelle ;
- niveau d'aide utilisé.

---

## 16. Verdict du testeur

Choisir un statut :

```text
VALIDÉ
VALIDÉ AVEC FRICTION
ÉCHOUÉ
BLOQUÉ PAR BUG FORGE
BLOQUÉ PAR DOCUMENTATION
HORS PÉRIMÈTRE
NON TESTÉ
```

---

## 17. Gravité du problème éventuel

```text
S0 - Bloquant critique
S1 - Bloquant fonctionnel
S2 - Friction forte
S3 - Friction mineure
S4 - Suggestion
S5 - Hors périmètre
```

---

## 18. Niveau d'aide utilisé

```text
A0 - aucune aide
A1 - documentation Forge uniquement
A2 - recherche personnelle ou documentation externe
A3 - aide d'un autre testeur
A4 - aide du référent Forge
A5 - impossible malgré aide
```

---

## 19. Conversion documentation

| Question | Réponse |
|---|---|
| Ce ticket peut-il devenir un tutoriel ? | non, ticket d'amorçage interne |
| Nom proposé de la page tutoriel |, |
| Menu proposé |, |
| Ticket FT validé par un testeur externe ? | à renseigner |
| Conversion autorisée maintenant ? | non |

### Règle

Le tutoriel ne doit pas être publié tant que le ticket FT correspondant n'a pas été validé au moins une fois par un testeur externe ou non expert Forge.

---

## 20. Notes pour le référent Forge

À remplir après analyse du retour.

- Problème reproductible : -
- Problème framework : -
- Problème documentation : -
- Problème ergonomie : -
- Hors périmètre : -
- Ticket correctif à créer : -
- Priorité proposée : -
