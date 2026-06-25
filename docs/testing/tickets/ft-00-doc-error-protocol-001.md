# FT-00-DOC-ERROR-PROTOCOL-001 : Appliquer la procédure documentation officielle erronée

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

---

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Phase | FT-00, Cadre de la campagne terrain |
| Ticket | FT-00-DOC-ERROR-PROTOCOL-001 |
| Niveau de guidage | G0, Guidé complètement |
| Profil testeur visé | tout profil |
| Durée indicative | courte (30 à 45 minutes) |
| Environnement cible | tout environnement |
| Dépend de | FT-00-TEST-CHARTER-001 |
| Peut être testé sans base ? | oui |
| Peut être testé sans navigateur ? | oui |

---

## 2. Objectif du ticket

Comprendre et appliquer la procédure à suivre lorsque la documentation officielle Forge est fausse, incomplète ou contradictoire pendant un ticket de test terrain.

---

## 3. Ce que ce ticket permet de tester dans Forge

Ce ticket ne teste pas le framework. Il vérifie que le testeur :

- sait que la documentation fait partie de ce qui est testé ;
- sait qu'il ne doit pas corriger lui-même la documentation ;
- sait documenter un écart entre documentation et réalité ;
- sait choisir le bon statut (`BLOQUÉ PAR DOCUMENTATION` ou `VALIDÉ AVEC FRICTION`) ;
- sait que le référent Forge crée le ticket correctif si nécessaire.

---

## 4. Périmètre

### Inclus

- lecture de la procédure documentation erronée dans la charte ;
- simulation d'un scénario fictif de documentation erronée ;
- production d'un retour classé selon la procédure.

### Exclu

- correction effective de la documentation Forge ;
- modification de fichiers du projet ;
- installation de Forge.

---

## 5. Contexte utile avant de commencer

La documentation officielle Forge fait partie de ce qui est testé dans la campagne terrain. Si elle est fausse, incomplète ou contradictoire, le testeur ne la corrige pas directement.

La procédure à respecter est la suivante :

```text
1. S'arrêter ou continuer avec un contournement.
2. Noter la page concernée (chemin dans docs/).
3. Noter le passage erroné ou ambigu (copier le texte exact).
4. Noter l'étape du ticket affectée.
5. Expliquer ce que la documentation dit.
6. Expliquer ce que Forge fait réellement (ou ce qui est bloquant).
7. Fournir des preuves (sortie terminal, capture, log).
8. Indiquer le contournement utilisé si le test a pu continuer.
9. Choisir le statut : BLOQUÉ PAR DOCUMENTATION ou VALIDÉ AVEC FRICTION.
10. Proposer la gravité S1, S2, S3 ou S4 selon l'impact.
```

Le référent Forge transforme ensuite le retour en ticket correctif séparé, par exemple `DOC-FT-XX-NOM-001`.

---

## 6. Documentation Forge à consulter

```text
docs/testing/field-test-charter.md       (section 8 : statuts finaux)
docs/testing/field-test-feedback-template.md
docs/testing/field-test-triage.md
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

- avoir complété FT-00-TEST-CHARTER-001 ;
- accès à la documentation Forge ;
- aucun pré-requis technique.

---

## 8. Fichiers, classes ou commandes concernés

### `docs/testing/field-test-charter.md`

- **Rôle :** définit la procédure complète pour les retours terrain.
- **Utilisation dans ce ticket :** lire la section sur les statuts finaux et la procédure documentation erronée.
- **Action autorisée :** lire, prendre des notes.
- **À ne pas faire :** modifier ce fichier.

### `docs/testing/field-test-feedback-template.md`

- **Rôle :** modèle de retour officiel.
- **Utilisation dans ce ticket :** identifier les champs liés aux erreurs de documentation.
- **Action autorisée :** lire, prendre des notes.
- **À ne pas faire :** modifier ce fichier.

---

## 9. Exemple indicatif décorrélé

L'exemple suivant montre comment documenter un écart entre documentation et réalité dans un ticket différent :

```text
Page concernée : docs/installation-demo.md
Passage erroné : "La commande forge init crée le projet dans le répertoire courant."
Réalité observée : la commande crée un sous-répertoire supplémentaire.
Étape concernée : étape 3 — initialiser le projet.
Contournement : se déplacer dans le sous-répertoire créé.
Statut retenu : VALIDÉ AVEC FRICTION
Gravité : S3 — Friction mineure
```

Pour ce ticket, le testeur devra produire un exemple similaire basé sur un scénario fictif différent.

---

## 10. Procédure de test

1. Ouvrir la [charte de campagne](../field-test-charter.md).
2. Lire la section consacrée aux statuts finaux.
3. Lire la section consacrée aux preuves minimales obligatoires.
4. Ouvrir le [modèle de retour testeur](../field-test-feedback-template.md).
5. Identifier les champs utilisés pour documenter une erreur de documentation.
6. Inventer un scénario fictif : une page imaginaire contient une information inexacte.
7. Remplir le modèle de retour pour ce scénario fictif en appliquant la procédure documentation erronée.
8. Choisir le statut (`BLOQUÉ PAR DOCUMENTATION` ou `VALIDÉ AVEC FRICTION`) et justifier.
9. Produire le retour pour ce ticket réel (FT-00-DOC-ERROR-PROTOCOL-001).

---

## 11. Résultat attendu

Le testeur produit :

- un scénario fictif de documentation erronée documenté selon la procédure ;
- un statut choisi et justifié ;
- une gravité proposée et justifiée ;
- un retour pour ce ticket lui-même.

---

## 12. Erreurs ou cas à observer

- procédure peu claire : noter le passage ambigu, gravité S2 ou S3 ;
- statuts `BLOQUÉ PAR DOCUMENTATION` et `VALIDÉ AVEC FRICTION` difficiles à distinguer : noter l'ambiguïté ;
- absence de la procédure documentation erronée dans la charte : statut `BLOQUÉ PAR DOCUMENTATION`, gravité S1.

---

## 13. Critères de validation du ticket

Le ticket est validé si :

- le testeur a lu la section sur la procédure documentation erronée ;
- un scénario fictif documenté selon la procédure est produit ;
- le statut est choisi parmi les deux statuts corrects ;
- la gravité est indiquée et justifiée ;
- le retour pour ce ticket est rempli.

---

## 14. Preuves à fournir

- scénario fictif documenté (copier-coller dans le retour) ;
- retour d'expérience pour ce ticket FT-00-DOC-ERROR-PROTOCOL-001.

---

## 15. Retour d'expérience attendu

Le testeur doit répondre au [modèle de retour testeur](../field-test-feedback-template.md).

Points obligatoires :

- documentation lue ;
- clarté de la procédure documentation erronée (oui / partiellement / non) ;
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
S0 — Bloquant critique
S1 — Bloquant fonctionnel
S2 — Friction forte
S3 — Friction mineure
S4 — Suggestion
S5 — Hors périmètre
```

---

## 18. Niveau d'aide utilisé

```text
A0 — aucune aide
A1 — documentation Forge uniquement
A2 — recherche personnelle ou documentation externe
A3 — aide d'un autre testeur
A4 — aide du référent Forge
A5 — impossible malgré aide
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
