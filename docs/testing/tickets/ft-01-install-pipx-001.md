# FT-01-INSTALL-PIPX-001 : Installer Forge via pipx

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

---

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Phase | FT-01, Installation de Forge |
| Ticket | FT-01-INSTALL-PIPX-001 |
| Niveau de guidage | G0, Guidé complètement |
| Profil testeur visé | débutant Forge / développeur Python |
| Durée indicative | moyenne (45 à 90 minutes) |
| Environnement cible | Debian / Ubuntu / WSL / macOS avec pipx |
| Dépend de | FT-00-TEST-CHARTER-001 |
| Peut être testé sans base ? | oui |
| Peut être testé sans navigateur ? | oui |

---

## 2. Objectif du ticket

Installer Forge via `pipx` en suivant la documentation officielle, vérifier que la commande `forge` est accessible depuis le terminal et que l'aide s'affiche correctement.

---

## 3. Ce que ce ticket permet de tester dans Forge

Ce ticket vérifie que :

- la procédure d'installation via `pipx` décrite dans la documentation est complète et reproductible ;
- la commande `forge` est accessible après installation ;
- le PATH est correctement configuré ou que la documentation explique comment le corriger ;
- un débutant Forge peut terminer l'installation sans aide extérieure ou avec l'aide de la documentation uniquement.

---

## 4. Périmètre

### Inclus

- vérification de Python et de sa version ;
- vérification ou installation de `pipx` ;
- installation de Forge via `pipx` ;
- vérification que `forge` est accessible dans le terminal ;
- affichage de la version et de l'aide Forge.

### Exclu

- création d'un projet Forge (ticket suivant) ;
- configuration MariaDB ;
- modification du framework ;
- installation via `venv`, `pip` direct ou depuis GitHub (autres tickets).

---

## 5. Contexte utile avant de commencer

`pipx` est un outil qui installe des applications Python dans des environnements virtuels isolés et les rend accessibles globalement dans le terminal. Il est recommandé pour les CLI Python comme Forge.

```text
pipx installe Forge dans un environnement isolé.
La commande forge devient accessible partout sans activer un venv.
```

Si `forge` n'est pas trouvé après installation, vérifier que le répertoire `~/.local/bin` est dans le `PATH`. C'est une friction fréquente sur certains systèmes.

---

## 6. Documentation Forge à consulter

```text
docs/install/index.md
docs/install/poste-linux.md
docs/compatibility.md
docs/getting-started.md
```

Le retour testeur devra indiquer quelles pages ont réellement été lues et si elles étaient suffisantes.

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

- accès à un terminal Linux, macOS ou WSL ;
- Python 3.12 ou supérieur installé ;
- connexion internet pour installer `pipx` et Forge ;
- droits d'installation sur la machine (pas de sudo nécessaire avec `pipx` utilisateur) ;
- avoir complété FT-00-TEST-CHARTER-001.

---

## 8. Fichiers, classes ou commandes concernés

### `python` / `python3`

- **Rôle :** interpréteur Python, pré-requis de Forge.
- **Utilisation dans ce ticket :** vérifier la version disponible.
- **Action autorisée :** exécuter la commande de vérification.
- **À ne pas faire :** installer une version Python non documentée.
- **Erreurs fréquentes :**
  - `python` pointe vers Python 2 sur certains systèmes ;
  - utiliser `python3` si `python` n'est pas disponible.

### `pipx`

- **Rôle :** outil d'installation d'applications Python en environnements isolés.
- **Utilisation dans ce ticket :** installer Forge.
- **Action autorisée :** installer ou mettre à jour `pipx` selon la documentation.
- **À ne pas faire :** utiliser `sudo pipx` pour l'installation utilisateur standard.
- **Erreurs fréquentes :**
  - `pipx` absent du PATH après installation ;
  - confusion entre `pip install pipx` et `apt install pipx`.

### `forge`

- **Rôle :** CLI Forge, point d'entrée principal.
- **Utilisation dans ce ticket :** vérifier l'accessibilité après installation.
- **Action autorisée :** exécuter `forge --version` et `forge help`.
- **À ne pas faire :** modifier les fichiers internes de Forge.
- **Erreurs fréquentes :**
  - `forge: command not found` si `~/.local/bin` n'est pas dans le PATH.

---

## 9. Exemple indicatif décorrélé

L'exemple suivant montre la forme générale pour une autre CLI Python :

```bash
# Vérifier Python
python3 --version
# Python 3.12.x

# Installer pipx (si absent)
pip install --user pipx

# Installer un outil via pipx
pipx install ma-cli-python

# Vérifier l'accessibilité
ma-cli-python --version
```

Pour ce ticket, transposer avec les commandes Forge indiquées dans la documentation officielle.

---

## 10. Procédure de test

1. Ouvrir un terminal.
2. Vérifier la version de Python disponible.
3. Vérifier si `pipx` est installé.
4. Si absent, installer `pipx` selon la documentation `docs/install/poste-linux.md`.
5. Installer Forge via `pipx` selon la documentation officielle.
6. Vérifier que la commande `forge` est accessible.
7. Si `forge` n'est pas trouvé, diagnostiquer le PATH selon la documentation.
8. Afficher la version de Forge.
9. Afficher l'aide Forge.
10. Collecter les sorties terminal.
11. Remplir le retour d'expérience.

---

## 11. Résultat attendu

- `python` ou `python3` est disponible en version 3.12 ou supérieur ;
- `pipx` est installé et accessible ;
- `forge` est installé et accessible depuis le terminal sans activation de venv ;
- `forge --version` affiche la version installée ;
- `forge help` (ou commande équivalente) affiche l'aide sans erreur.

---

## 12. Erreurs ou cas à observer

- Python < 3.12 : noter la version, gravité S1 si Forge refuse de s'installer ;
- `forge: command not found` après installation : noter le contexte PATH, gravité S2 ;
- documentation d'installation incomplète sur un point : noter le passage, gravité S2 ou S3 ;
- version Forge affichée différente de la version documentée : noter l'écart, gravité S2 ;
- erreur d'installation inattendue : copier la sortie complète, gravité S0 ou S1 selon l'impact.

---

## 13. Critères de validation du ticket

Le ticket est validé si :

- `forge` est accessible depuis le terminal après installation ;
- `forge --version` affiche une version ;
- `forge help` (ou commande équivalente) affiche l'aide ;
- les sorties terminal sont copiées dans le retour ;
- le retour d'expérience est rempli avec verdict, gravité et niveau d'aide.

---

## 14. Preuves à fournir

```bash
python3 --version
pipx --version
forge --version
forge help
```

Fournir la sortie complète de chaque commande.

Ajouter si utile :

- message d'erreur complet si installation échouée ;
- contenu de `~/.local/bin` si problème de PATH ;
- OS et version du système.

---

## 15. Retour d'expérience attendu

Le testeur doit répondre au [modèle de retour testeur](../field-test-feedback-template.md).

Points obligatoires :

- système d'exploitation et version ;
- version Python disponible ;
- méthode d'installation `pipx` utilisée ;
- documentation suivie (pages lues) ;
- étapes bloquantes ou non ;
- problèmes de PATH rencontrés ;
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
| Ce ticket peut-il devenir un tutoriel ? | oui, si validé sans friction ou avec friction documentée |
| Nom proposé de la page tutoriel | `docs/tutorials/installer-forge-pipx.md` |
| Menu proposé | Tutoriels > Installation > Installer Forge avec pipx |
| Ticket FT validé par un testeur externe ? | à renseigner |
| Conversion autorisée maintenant ? | non |

### Contenu à conserver pour le tutoriel

- objectif ;
- contexte utile (description de pipx) ;
- commandes de vérification Python ;
- procédure d'installation ;
- vérification finale ;
- erreurs fréquentes.

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
