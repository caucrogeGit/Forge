# FT-01-INSTALL-VERSION-CHECK-001 — Vérifier la version Forge installée

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

---

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Phase | FT-01 — Installation de Forge |
| Ticket | FT-01-INSTALL-VERSION-CHECK-001 |
| Niveau de guidage | G0 — Guidé complètement |
| Profil testeur visé | débutant Forge / développeur Python |
| Durée indicative | courte (20 à 40 minutes) |
| Environnement cible | tout environnement où Forge est installé |
| Dépend de | FT-01-INSTALL-PIPX-001 |
| Peut être testé sans base ? | oui |
| Peut être testé sans navigateur ? | oui |

---

## 2. Objectif du ticket

Vérifier que la version de Forge affichée par la CLI est lisible, cohérente avec la documentation et facilement interprétable par un testeur débutant.

---

## 3. Ce que ce ticket permet de tester dans Forge

Ce ticket vérifie que :

- la commande `forge --version` produit une sortie claire et non ambiguë ;
- la version affichée correspond à la version documentée dans `docs/install/poste-linux.md` ou `docs/compatibility.md` ;
- un testeur débutant peut confirmer qu'il utilise la bonne version sans ambiguïté ;
- le format de version affiché est cohérent (PEP 440 ou SemVer selon la documentation).

---

## 4. Périmètre

### Inclus

- exécution de la commande de version ;
- lecture de la version affichée ;
- comparaison avec la version documentée ;
- vérification de cohérence entre méthodes d'installation si plusieurs sont disponibles.

### Exclu

- modification de Forge ;
- création d'un projet ;
- installation de Forge (ticket précédent) ;
- tests de fonctionnalités.

---

## 5. Contexte utile avant de commencer

Forge utilise un format de version PEP 440 en interne (ex : `{{ forge_version }}`) et une notation SemVer dans certaines communications (ex : `1.0.0-beta.3`). Ces deux formats désignent la même version.

La cohérence entre ce que la CLI affiche et ce que la documentation présente est importante pour éviter la confusion chez les testeurs débutants.

```text
Format PEP 440 :  {{ forge_version }}
Format SemVer  :  1.0.0-beta.3  (exemple — vérifier la documentation)
Ces deux notations désignent la même version.
```

---

## 6. Documentation Forge à consulter

```text
docs/install/index.md
docs/install/poste-linux.md
docs/compatibility.md
docs/release-and-compatibility.md
```

Le retour testeur devra indiquer quelles pages ont réellement été lues et si elles permettaient de connaître la version attendue.

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

- Forge installé (FT-01-INSTALL-PIPX-001 complété) ;
- `forge` accessible depuis le terminal ;
- accès à la documentation Forge.

---

## 8. Fichiers, classes ou commandes concernés

### `forge --version`

- **Rôle :** affiche la version installée de Forge.
- **Nature :** commande CLI.
- **Utilisation dans ce ticket :** exécuter et copier la sortie.
- **Action autorisée :** exécuter la commande, noter la sortie.
- **À ne pas faire :** modifier les fichiers internes de Forge pour changer la version affichée.
- **Erreurs fréquentes :**
  - commande non reconnue si Forge n'est pas dans le PATH ;
  - version affichée différente de la version documentée.

### `pip show forge-mvc` (optionnel selon installation)

- **Rôle :** affiche des informations sur le paquet installé.
- **Nature :** commande `pip` / `pipx`.
- **Utilisation dans ce ticket :** vérification complémentaire si utile.
- **Action autorisée :** exécuter dans l'environnement Forge.

### `pipx list` (optionnel si installation via pipx)

- **Rôle :** liste les applications installées via pipx avec leur version.
- **Nature :** commande `pipx`.
- **Utilisation dans ce ticket :** vérification complémentaire si utile.
- **Action autorisée :** exécuter et copier la sortie pertinente.

---

## 9. Exemple indicatif décorrélé

L'exemple suivant montre la forme d'une sortie de version pour une autre CLI Python :

```bash
ma-cli-python --version
# ma-cli-python 2.4.1
```

```bash
pip show ma-cli-python
# Name: ma-cli-python
# Version: 2.4.1
# ...
```

Pour ce ticket, transposer avec la commande Forge et comparer avec la version attendue selon la documentation.

---

## 10. Procédure de test

1. Ouvrir un terminal.
2. Vérifier que `forge` est accessible.
3. Exécuter la commande de version Forge.
4. Copier la sortie exacte.
5. Ouvrir la documentation d'installation et identifier la version attendue.
6. Comparer la version affichée avec la version documentée.
7. Si l'installation était via `pipx`, exécuter `pipx list` pour vérifier la version.
8. Si disponible, exécuter `pip show forge-mvc` dans l'environnement actif.
9. Noter les cohérences et incohérences éventuelles.
10. Remplir le retour d'expérience.

---

## 11. Résultat attendu

- `forge --version` affiche une version lisible ;
- la version affichée correspond à la version mentionnée dans la documentation ;
- le format de version est interprétable sans ambiguïté (même si PEP 440 et SemVer sont tous les deux utilisés, la documentation l'explique) ;
- aucune erreur n'est levée par la commande.

---

## 12. Erreurs ou cas à observer

- version affichée non documentée : noter l'écart, gravité S2 ;
- format de version ambigu sans explication dans la documentation : gravité S3 ;
- `forge --version` déclenche une erreur : copier la sortie complète, gravité S1 ;
- documentation muette sur la version attendue : gravité S2 ou S3 selon l'impact ;
- deux sources documentaires donnant des versions différentes : gravité S2.

---

## 13. Critères de validation du ticket

Le ticket est validé si :

- `forge --version` produit une sortie sans erreur ;
- la version affichée est identifiable dans la documentation ;
- le testeur peut confirmer qu'il utilise la bonne version ;
- les sorties terminal sont copiées dans le retour ;
- le retour d'expérience est rempli avec verdict, gravité et niveau d'aide.

---

## 14. Preuves à fournir

```bash
forge --version
pipx list
```

Fournir la sortie complète de chaque commande.

Ajouter si utile :

- sortie de `pip show forge-mvc` ;
- extrait de la documentation indiquant la version attendue ;
- comparaison version affichée / version documentée.

---

## 15. Retour d'expérience attendu

Le testeur doit répondre au [modèle de retour testeur](../field-test-feedback-template.md).

Points obligatoires :

- méthode d'installation utilisée ;
- version affichée par `forge --version` ;
- version attendue selon la documentation ;
- cohérence ou écart constaté ;
- documentation lue pour trouver la version attendue ;
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
| Ce ticket peut-il devenir un tutoriel ? | partiellement — la section "vérifier sa version" peut enrichir le tutoriel d'installation |
| Nom proposé de la page tutoriel | fusionner avec `docs/tutorials/installer-forge-pipx.md` |
| Menu proposé | Tutoriels > Installation > Installer Forge avec pipx |
| Ticket FT validé par un testeur externe ? | à renseigner |
| Conversion autorisée maintenant ? | non |

### Contenu à conserver pour le tutoriel

- commandes de vérification de version ;
- explication du format PEP 440 / SemVer si nécessaire ;
- résultat attendu de `forge --version`.

### Contenu à retirer du tutoriel

- preuves obligatoires ;
- retour d'expérience ;
- gravité ;
- niveau d'aide ;
- statut interne ;
- notes du référent.

### Règle

Le tutoriel ne doit pas être publié tant que ce ticket FT n'a pas été validé au moins une fois par un testeur externe ou non expert Forge.

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
