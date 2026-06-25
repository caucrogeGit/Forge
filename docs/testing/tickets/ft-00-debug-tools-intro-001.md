# FT-00-DEBUG-TOOLS-INTRO-001 : Découvrir les outils de diagnostic Forge

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

---

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Phase | FT-00, Cadre de la campagne terrain |
| Ticket | FT-00-DEBUG-TOOLS-INTRO-001 |
| Niveau de guidage | G0, Guidé complètement |
| Profil testeur visé | débutant Forge / développeur Python |
| Durée indicative | courte (20 à 40 minutes) |
| Environnement cible | tout environnement avec Forge installé |
| Dépend de | FT-00-TEST-CHARTER-001 (recommandé) |
| Peut être testé sans base ? | oui, plusieurs commandes ne nécessitent pas MariaDB |
| Peut être testé sans navigateur ? | oui |

---

## 2. Objectif du ticket

Faire découvrir aux testeurs les outils de diagnostic disponibles dans Forge et leur apprendre quelles preuves collecter et fournir dans un retour terrain.

---

## 3. Ce que ce ticket permet de tester dans Forge

Ce ticket vérifie que :

- le testeur sait quelle commande lancer selon la situation rencontrée ;
- le testeur sait copier une sortie de commande utile ;
- le testeur comprend la différence entre observer et corriger ;
- le testeur sait où trouver les logs Forge en mode développement ;
- le testeur sait quoi ne pas publier dans un retour (secrets, mots de passe).

---

## 4. Périmètre

### Inclus

- lecture de la page [Outils de diagnostic](../field-test-debug-tools.md) ;
- exécution de `forge doctor` ;
- exécution de `forge project:check` ;
- exécution de `forge routes:list` (si un projet Forge est disponible) ;
- exécution de `git status` et `git diff --check` ;
- localisation des fichiers de logs Forge ;
- identification de ce qu'il ne faut pas publier dans un retour.

### Exclu

- correction d'erreurs signalées par les outils ;
- modification de `core/` ;
- modification du comportement de `forge doctor` ;
- exécution de `pytest` (hors périmètre de ce ticket) ;
- déploiement ;
- MariaDB.

---

## 5. Contexte utile avant de commencer

Les outils de diagnostic Forge sont des commandes en lecture seule. Leur rôle est d'observer l'état du projet, pas de le modifier.

Trois niveaux de diagnostic sont disponibles :

```text
forge doctor         — diagnostic large et tolérant (recommandé en premier)
forge project:check  — contrôle strict CI-ready
forge project:audit  — rapport d'audit détaillé
```

Ces trois commandes ne modifient rien dans le projet. Elles peuvent être lancées à tout moment pendant un ticket, sans risque.

---

## 6. Documentation Forge à consulter

```text
docs/testing/field-test-debug-tools.md
docs/testing/field-test-feedback-template.md
docs/testing/field-test-charter.md
```

Le retour testeur devra indiquer quelles pages ont réellement été lues et si elles permettaient de comprendre quoi lancer selon la situation.

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

---

## 7. Pré-requis

- Forge installé et accessible depuis le terminal (`forge --version`) ;
- un projet Forge existant pour les commandes qui le nécessitent (`forge project:check`, `forge routes:list`) ;
- accès à la documentation Forge.

Note : si aucun projet Forge n'est disponible, `forge doctor` peut être exécuté depuis n'importe quel répertoire. Les autres commandes nécessitent un projet Forge valide.

---

## 8. Fichiers, classes ou commandes concernés

### `forge doctor`

- **Rôle :** diagnostic large et tolérant de l'environnement Forge.
- **Nature :** commande CLI, lecture seule.
- **Utilisation dans ce ticket :** exécuter et copier la sortie complète.
- **Action autorisée :** exécuter, lire, copier la sortie.
- **À ne pas faire :** modifier Forge pour corriger ce que doctor signale.

### `forge project:check`

- **Rôle :** contrôle strict des conventions du projet.
- **Nature :** commande CLI, lecture seule.
- **Utilisation dans ce ticket :** exécuter depuis la racine d'un projet Forge.
- **Action autorisée :** exécuter, copier la sortie.
- **À ne pas faire :** corriger les anomalies signalées sans les documenter d'abord.

### `forge routes:list`

- **Rôle :** liste les routes déclarées dans le projet.
- **Nature :** commande CLI, lecture seule.
- **Utilisation dans ce ticket :** vérifier que les routes s'affichent sans erreur.
- **Action autorisée :** exécuter et copier la sortie.
- **Erreurs fréquentes :** erreur si `mvc/routes.py` est absent ou malformé.

### `git status` et `git diff --check`

- **Rôle :** observer l'état du dépôt et détecter les problèmes de whitespace.
- **Nature :** commandes `git`, lecture seule.
- **Utilisation dans ce ticket :** exécuter et copier la sortie.

### Logs Forge

- **Rôle :** journal des erreurs runtime en mode développement.
- **Nature :** fichiers dans `storage/logs/`.
- **Utilisation dans ce ticket :** localiser les fichiers, identifier leur contenu.
- **Action autorisée :** lire, copier les lignes pertinentes.
- **À ne pas faire :** publier des lignes contenant des secrets ou des mots de passe.

---

## 9. Exemple indicatif décorrélé

L'exemple suivant montre la forme d'une sortie de `forge doctor` pour un projet sain :

```text
[OK]  Python 3.12.x — version supportée
[OK]  forge-mvc installé
[OK]  env/dev présent
[OK]  mvc/routes.py présent
```

Pour ce ticket, transposer avec la sortie réelle obtenue sur l'environnement de test.

---

## 10. Procédure de test

1. Lire la page [Outils de diagnostic](../field-test-debug-tools.md) en entier.
2. Ouvrir un terminal dans le répertoire d'un projet Forge (ou n'importe quel répertoire pour `forge doctor`).
3. Exécuter `forge doctor`. Copier la sortie complète.
4. Depuis la racine d'un projet Forge, exécuter `forge project:check`. Copier la sortie.
5. Exécuter `forge routes:list`. Copier la sortie.
6. Exécuter `git status`. Copier la sortie.
7. Exécuter `git diff --check`. Copier la sortie (vide = OK).
8. Localiser le fichier `storage/logs/errors.dev.md`. Identifier ce qu'il contient.
9. Identifier une ligne de log qui ne devrait pas être publiée dans un retour public.
10. Remplir le retour d'expérience.

Note : si certaines commandes (`forge project:check`, `forge routes:list`) nécessitent un projet Forge et qu'aucun n'est disponible, noter la situation dans le retour avec le statut `HORS PÉRIMÈTRE` ou `VALIDÉ AVEC FRICTION` selon le cas.

---

## 11. Résultat attendu

- `forge doctor` produit une sortie lisible sans erreur Python ;
- `forge project:check` produit une sortie structurée (`[OK]`, `[WARN]`, `[ERREUR]`) ;
- `forge routes:list` liste les routes du projet sans erreur ;
- `git status` et `git diff --check` produisent une sortie interprétable ;
- `storage/logs/errors.dev.md` est localisé et son contenu est compris ;
- le testeur sait identifier une ligne de log qui ne doit pas être publiée.

---

## 12. Erreurs ou cas à observer

- commande non reconnue (`forge doctor` : erreur si Forge n'est pas dans le PATH) : gravité S1 ;
- sortie illisible ou tronquée : gravité S3 ;
- `forge project:check` signale une anomalie inattendue : noter et documenter, gravité S2 ;
- `storage/logs/` absent : noter, gravité S3 ;
- log contenant visiblement un secret (mot de passe, token) : noter le format sans exposer la valeur, gravité S2.

---

## 13. Critères de validation du ticket

Le ticket est validé si :

- les commandes listées ont été exécutées et leurs sorties copiées ;
- le testeur a localisé les logs Forge ;
- le testeur peut identifier ce qu'il ne faut pas publier dans un retour ;
- le retour d'expérience est rempli avec verdict, gravité et niveau d'aide.

---

## 14. Preuves à fournir

```bash
forge doctor
forge project:check
forge routes:list
git status
git diff --check
```

Fournir la sortie complète de chaque commande exécutée.

Ajouter si utile :

- sortie de `forge project:audit` ;
- chemin et premières lignes de `storage/logs/errors.dev.md` (sans secret) ;
- toute erreur inattendue rencontrée.

---

## 15. Retour d'expérience attendu

Le testeur doit répondre au [modèle de retour testeur](../field-test-feedback-template.md).

Points obligatoires :

- commandes exécutées et sorties obtenues ;
- localisation des logs réussie ou non ;
- exemple de ligne de log identifiée comme potentiellement sensible ;
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
| Ce ticket peut-il devenir un tutoriel ? | partiellement, la section "quels outils utiliser" peut enrichir un tutoriel de prise en main |
| Nom proposé de la page tutoriel | `docs/tutorials/diagnostiquer-un-projet-forge.md` |
| Menu proposé | Tutoriels > Diagnostic > Diagnostiquer un projet Forge |
| Ticket FT validé par un testeur externe ? | à renseigner |
| Conversion autorisée maintenant ? | non |

### Contenu à conserver pour le tutoriel

- tableau "Quel outil utiliser ?" ;
- commandes de base avec leur objectif ;
- règle sur les secrets dans les logs.

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

- Problème reproductible : -
- Problème framework : -
- Problème documentation : -
- Problème ergonomie : -
- Hors périmètre : -
- Ticket correctif à créer : -
- Priorité proposée : -
