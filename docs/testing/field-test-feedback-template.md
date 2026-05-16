# Tests terrain — Modèle de retour testeur

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

> À remplir par le testeur après chaque ticket `FT-*`.

---

## Retour via GitHub Issue (recommandé)

Un formulaire structuré est disponible directement sur GitHub :

**[Soumettre un retour de test terrain →](https://github.com/caucrogeGit/Forge/issues/new?template=field-test-feedback.yml)**

Le formulaire reprend tous les champs du modèle ci-dessous. Il permet de soumettre un retour sans copier-coller le modèle Markdown manuellement.

---

## Retour au format Markdown (alternative)

---

# Retour terrain — [CODE DU TICKET]

## 1. Identification

| Champ | Réponse |
|---|---|
| Ticket testé |  |
| Testeur |  |
| Date |  |
| Profil | débutant Forge / développeur Python / développeur web / exploitation |
| Niveau Forge avant test | aucun / faible / moyen / confirmé |
| Niveau d’aide utilisé | A0 / A1 / A2 / A3 / A4 / A5 |

---

## 2. Environnement

| Élément | Valeur |
|---|---|
| OS |  |
| Shell | Bash / PowerShell / autre |
| Python |  |
| pip / pipx |  |
| Forge |  |
| Installation | pipx / venv / GitHub / editable / autre |
| Base de données | MariaDB / aucune / autre |
| MariaDB version |  |
| Navigateur |  |
| Éditeur | VS Code / autre |

---

## 3. Documentation réellement utilisée

| Page | Utilisée ? | Commentaire |
|---|---:|---|
| page 1 | oui/non |  |
| page 2 | oui/non |  |
| page 3 | oui/non |  |

### Passage utile

Indiquer le passage qui a aidé.

### Passage confus

Indiquer le passage ambigu ou incomplet.

### Passage manquant

Indiquer ce qui aurait dû être documenté.

---

## 4. Problème documentaire éventuel

À remplir si la documentation officielle est fausse, incomplète, contradictoire ou ne correspond pas au comportement réel.

| Champ | Réponse |
|---|---|
| Page concernée |  |
| Passage erroné ou ambigu |  |
| Étape du ticket concernée |  |
| Ce que la documentation dit |  |
| Ce que Forge fait réellement |  |
| Impact sur le ticket | bloquant / contournable / mineur |
| Contournement trouvé | oui / non |
| Statut proposé | BLOQUÉ PAR DOCUMENTATION / VALIDÉ AVEC FRICTION |
| Gravité proposée | S1 / S2 / S3 / S4 / S5 |

### Preuve de l’écart documentaire

Ajouter commande, log, capture, extrait de fichier ou observation.

```text

```

---

## 5. Objectif compris

Décrire en une phrase ce que le ticket demandait de faire.

---

## 6. Étapes réellement suivies

Lister les étapes exécutées.

1.
2.
3.
4.

---

## 7. Commandes exécutées

```bash

```

---

## 8. Résultat attendu

Décrire ce qui devait se produire.

---

## 9. Résultat obtenu

Décrire ce qui s’est réellement produit.

---

## 10. Preuves

Ajouter selon le cas :

- sortie terminal ;
- capture navigateur ;
- logs ;
- `git status` ;
- fichiers modifiés ;
- message d’erreur complet ;
- configuration sans secrets ;
- capture de documentation.

### Sortie terminal ou log

```text

```

### `git status`

```text

```

---

## 11. Fichiers modifiés ou créés

| Fichier | Type d’action | Attendu ? |
|---|---|---:|
|  | créé/modifié/supprimé | oui/non |

---

## 12. Problème rencontré

Remplir si nécessaire.

### Description courte

### Étapes pour reproduire

1.
2.
3.

### Le problème est-il reproductible ?

oui / non / non testé

### Contournement trouvé ?

oui / non

Si oui, expliquer.

---

## 13. Évaluation du ticket

| Question | Réponse |
|---|---|
| La procédure était-elle suffisante ? | oui/non |
| Le contexte fourni était-il utile ? | oui/non |
| Les fichiers/classes étaient-ils assez expliqués ? | oui/non |
| L’exemple décorrélé était-il utile ? | oui/non |
| L’exemple était-il trop proche de la solution ? | oui/non |
| La documentation était-elle suffisante ? | oui/non |
| La documentation contenait-elle une erreur officielle ? | oui/non |
| Cette erreur a-t-elle bloqué le ticket ? | oui/non |
| Les erreurs étaient-elles compréhensibles ? | oui/non |
| As-tu dû modifier un fichier non prévu ? | oui/non |
| As-tu modifié `core/` ? | oui/non |

---

## 14. Verdict

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

## 15. Gravité proposée

```text
S0 — Bloquant critique
S1 — Bloquant fonctionnel
S2 — Friction forte
S3 — Friction mineure
S4 — Suggestion
S5 — Hors périmètre
```

Justification :

---

## 16. Commentaire libre

Indiquer ce qui a été :

- clair ;
- confus ;
- inutile ;
- manquant ;
- dangereux ;
- surprenant ;
- bien conçu.
