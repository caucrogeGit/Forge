# FT-00-FEEDBACK-TEMPLATE-001 — Remplir un retour d'expérience de test à blanc

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

---

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Phase | FT-00 — Cadre de la campagne terrain |
| Ticket | FT-00-FEEDBACK-TEMPLATE-001 |
| Niveau de guidage | G0 — Guidé complètement |
| Profil testeur visé | tout profil |
| Durée indicative | courte (30 à 45 minutes) |
| Environnement cible | tout environnement |
| Dépend de | FT-00-TEST-CHARTER-001 (recommandé) |
| Peut être testé sans base ? | oui |
| Peut être testé sans navigateur ? | oui |

---

## 2. Objectif du ticket

Produire un retour d'expérience fictif complet en utilisant le modèle officiel, afin de vérifier que le testeur sait remplir un retour exploitable avant les tickets techniques.

---

## 3. Ce que ce ticket permet de tester dans Forge

Ce ticket ne teste pas le framework. Il vérifie que le testeur :

- connaît la structure du modèle de retour ;
- sait identifier et remplir tous les champs obligatoires ;
- sait choisir un statut et une gravité cohérents ;
- produit un retour exploitable par le référent Forge.

---

## 4. Périmètre

### Inclus

- lecture du modèle de retour d'expérience ;
- production d'un retour fictif complet pour un scénario imaginé ;
- vérification des champs obligatoires.

### Exclu

- test de fonctionnalités Forge ;
- modification de fichiers du projet ;
- installation de Forge.

---

## 5. Contexte utile avant de commencer

Un retour d'expérience exploitable contient :

- les données d'identification du testeur et de l'environnement ;
- la documentation utilisée pendant le test ;
- le résultat attendu et le résultat obtenu ;
- des preuves (sortie terminal, capture, log) ;
- un verdict parmi les statuts officiels ;
- une gravité éventuelle.

Un retour sans preuve est faible. Un retour sans verdict est inexploitable.

---

## 6. Documentation Forge à consulter

```text
docs/testing/field-test-feedback-template.md
docs/testing/field-test-charter.md
```

Le retour testeur devra indiquer quelles pages ont réellement été lues.

### Verrou — documentation erronée

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

- avoir lu ou parcouru FT-00-TEST-CHARTER-001 ;
- accès à la documentation Forge ;
- aucun pré-requis technique.

---

## 8. Fichiers, classes ou commandes concernés

### `docs/testing/field-test-feedback-template.md`

- **Rôle :** modèle officiel de retour d'expérience terrain.
- **Nature :** document de référence.
- **Utilisation dans ce ticket :** lire et reproduire la structure pour un retour fictif.
- **Action autorisée :** copier la structure, remplir avec des données fictives.
- **À ne pas faire :** modifier le modèle lui-même.

---

## 9. Exemple indicatif décorrélé

L'exemple suivant montre la forme d'un retour pour un ticket différent :

```text
Ticket testé : FT-99-DEMO-001
Testeur : Alice D.
Statut : VALIDÉ AVEC FRICTION
Gravité : S3
Aide : A1 — documentation Forge uniquement

Résultat attendu : la commande affiche un message de bienvenue.
Résultat obtenu : la commande affiche le message, mais avec une faute de frappe.
Preuve : sortie terminal copiée ci-dessous.
Suggestion : corriger la typo dans le message de bienvenue.
```

Pour ce ticket, inventer un scénario différent (un autre numéro de ticket fictif, un autre objectif).

---

## 10. Procédure de test

1. Ouvrir le [modèle de retour testeur](../field-test-feedback-template.md).
2. Lire intégralement le modèle.
3. Identifier tous les champs obligatoires.
4. Inventer un scénario fictif simple (un ticket imaginaire, par exemple `FT-99-DEMO-001`).
5. Remplir le modèle de retour pour ce scénario fictif.
6. Vérifier que tous les champs obligatoires sont remplis.
7. Vérifier que le verdict et la gravité sont cohérents.
8. Produire le retour pour ce ticket réel (FT-00-FEEDBACK-TEMPLATE-001).

---

## 11. Résultat attendu

Le testeur produit un retour fictif complet contenant :

- identification (testeur, date, profil, environnement) ;
- documentation utilisée ;
- résultat attendu et résultat obtenu (fictifs) ;
- une preuve illustrative (texte libre ou extrait fictif) ;
- un verdict parmi les statuts officiels ;
- une gravité ;
- un niveau d'aide.

---

## 12. Erreurs ou cas à observer

- retour fictif vide ou incomplet : noter les champs manquants ;
- statut incohérent avec la situation décrite : noter l'ambiguïté ;
- modèle de retour peu clair sur un point : gravité S3 ou S2 selon l'impact.

---

## 13. Critères de validation du ticket

Le ticket est validé si :

- le testeur a lu intégralement le modèle de retour ;
- un retour fictif complet est produit ;
- tous les champs obligatoires sont remplis ;
- le statut et la gravité sont choisis et justifiés ;
- le retour pour ce ticket est produit séparément.

---

## 14. Preuves à fournir

- retour fictif produit (complet) ;
- retour d'expérience pour ce ticket FT-00-FEEDBACK-TEMPLATE-001 lui-même.

---

## 15. Retour d'expérience attendu

Le testeur doit répondre au [modèle de retour testeur](../field-test-feedback-template.md).

Points obligatoires :

- documentation lue ;
- clarté du modèle de retour (oui / partiellement / non) ;
- champs ambigus relevés ;
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
| Ce ticket peut-il devenir un tutoriel ? | non — ticket d'amorçage interne |
| Nom proposé de la page tutoriel | — |
| Menu proposé | — |
| Ticket FT validé par un testeur externe ? | à renseigner |
| Conversion autorisée maintenant ? | non |

### Règle

Le tutoriel ne doit pas être publié tant que le ticket FT correspondant n'a pas été validé au moins une fois par un testeur externe ou non expert Forge.

---

## 20. Notes pour le référent Forge

À remplir après analyse du retour.

- Problème reproductible : —
- Problème framework : —
- Problème documentation : —
- Problème ergonomie : —
- Hors périmètre : —
- Ticket correctif à créer : —
- Priorité proposée : —
