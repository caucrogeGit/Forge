# Modèle verrouillé — Ticket terrain Forge

> Ce modèle doit être utilisé pour produire chaque ticket `FT-*`.

---

# FT-XX-NOM-DU-TICKET-001 — Titre du ticket

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Phase | FT-XX — Nom de la phase |
| Ticket | FT-XX-NOM-DU-TICKET-001 |
| Niveau de guidage | G0 / G1 / G2 / G3 |
| Profil testeur visé | débutant Forge / développeur Python / développeur web / exploitation |
| Durée indicative | courte / moyenne / longue |
| Environnement cible | WSL / Debian / venv / pipx / GitHub / VM / autre |
| Dépend de | tickets précédents nécessaires |
| Peut être testé sans base ? | oui / non |
| Peut être testé sans navigateur ? | oui / non |

---

## 2. Objectif du ticket

Décrire précisément ce que le testeur doit réaliser.

Exemple :

> Créer une route publique `/hello-forge` qui affiche une réponse simple dans le navigateur.

---

## 3. Ce que ce ticket permet de tester dans Forge

Expliquer ce qu’on cherche à valider.

Exemple :

> Ce ticket vérifie que le routage applicatif Forge permet d’associer une URL à une méthode de contrôleur sans modifier le cœur du framework.

---

## 4. Périmètre

### Inclus

- action principale testée ;
- fichiers à manipuler ;
- commandes à lancer ;
- comportement attendu.

### Exclu

- corrections du framework ;
- fonctionnalités non liées ;
- refonte ;
- optimisation ;
- modification du core.

---

## 5. Contexte utile avant de commencer

Donner les notions minimales nécessaires.

Le texte doit être opérationnel, pas scolaire.

Exemple :

> Dans Forge, une route relie une méthode HTTP et une URL à une méthode de contrôleur.  
> Le fichier des routes applicatives est `mvc/routes.py`.  
> Le contrôleur appartient à l’application et se trouve dans `mvc/controllers/`.

---

## 6. Documentation Forge à consulter

Lister uniquement les pages utiles.

```text
docs/getting-started.md
docs/reference/routes.md
docs/reference/controllers.md
```

Le retour testeur devra indiquer quelles pages ont réellement été lues.

### Verrou — documentation erronée

Si une documentation indiquée dans ce ticket est fausse, incomplète ou contradictoire :

1. ne pas corriger directement la documentation pendant ce ticket ;
2. noter la page concernée ;
3. noter le passage erroné ou ambigu ;
4. noter l’étape du ticket concernée ;
5. expliquer ce que la documentation dit ;
6. expliquer ce que Forge fait réellement ;
7. fournir les preuves ;
8. indiquer le contournement éventuel ;
9. choisir le statut `BLOQUÉ PAR DOCUMENTATION` ou `VALIDÉ AVEC FRICTION` ;
10. proposer la gravité S1, S2, S3 ou S4 selon l’impact.

Le référent Forge décidera ensuite si un ticket documentaire séparé doit être créé.

---

## 7. Pré-requis

Exemple :

- Forge installé ;
- projet Forge créé ;
- environnement virtuel activé ;
- serveur local fonctionnel ;
- MariaDB configuré si nécessaire ;
- aucun fichier `core/` modifié ;
- `git status` connu avant de commencer.

---

## 8. Fichiers, classes ou commandes concernés

Présenter chaque élément utile.

### `mvc/routes.py`

- **Rôle :** déclarer les routes de l’application.
- **Nature :** fichier applicatif.
- **Utilisation dans ce ticket :** ajouter ou vérifier une route.
- **Action autorisée :** modifier ce fichier dans le cadre du ticket.
- **À ne pas faire :** modifier `core/http/router.py`.
- **Erreurs fréquentes :**
  - oublier l’import du contrôleur ;
  - donner une méthode qui n’existe pas ;
  - créer une route dupliquée.

### `mvc/controllers/`

- **Rôle :** contenir les méthodes appelées par les routes.
- **Nature :** code applicatif.
- **Utilisation dans ce ticket :** créer ou modifier un contrôleur.
- **Action autorisée :** créer un contrôleur applicatif.
- **À ne pas faire :** transformer le contrôleur en fichier métier trop large.

### Commande éventuelle

```bash
forge routes:list
```

- **Rôle :** vérifier les routes disponibles.
- **Action autorisée :** exécuter et copier la sortie.

---

## 9. Exemple indicatif décorrélé

L’exemple montre seulement la forme générale.  
Il ne doit pas être recopié tel quel pour valider le ticket.

### Exemple de forme

Si le ticket demande de créer `/hello-forge`, l’exemple doit utiliser un autre cas :

```python
# Exemple décorrélé : route de démonstration
router.add("GET", "/demo", DemoController.index, name="demo")
```

```python
# Exemple décorrélé : contrôleur de démonstration
class DemoController:
    @staticmethod
    def index(request):
        return "Page de démonstration"
```

Le testeur doit transposer l’idée au ticket demandé.

---

## 10. Procédure de test

Décrire les étapes.

1. Ouvrir le projet Forge.
2. Vérifier l’état initial.
3. Lire la documentation indiquée.
4. Modifier uniquement les fichiers autorisés.
5. Lancer les commandes demandées.
6. Tester dans le navigateur si nécessaire.
7. Collecter les preuves.
8. Remplir le retour d’expérience.

---

## 11. Résultat attendu

Décrire le résultat observable.

Exemple :

- la route répond ;
- le navigateur affiche le contenu attendu ;
- aucune erreur serveur ;
- aucun fichier `core/` n’a été modifié ;
- le diagnostic éventuel reste vert.

---

## 12. Erreurs ou cas à observer

Uniquement si utile pour le ticket.

Exemple :

- route absente ;
- contrôleur mal importé ;
- méthode inexistante ;
- template absent ;
- mauvaise variable d’environnement ;
- erreur SQL ;
- erreur CSRF ;
- documentation officielle fausse, incomplète ou contradictoire.

---

## 13. Critères de validation du ticket

Le ticket est validé si :

- l’objectif principal est réalisé ;
- le résultat attendu est observable ;
- les preuves minimales sont fournies ;
- les fichiers modifiés sont conformes au périmètre ;
- le retour d’expérience est rempli ;
- la gravité éventuelle est indiquée ;
- le statut final est donné.

---

## 14. Preuves à fournir

Selon le ticket :

```bash
forge --version
python --version
git status
git diff --check
```

Ajouter si utile :

- sortie terminal complète ;
- capture navigateur ;
- extrait de log ;
- fichiers créés ou modifiés ;
- configuration masquée sans secrets ;
- capture de l’erreur ;
- version MariaDB ;
- navigateur utilisé.

---

## 15. Retour d’expérience attendu

Le testeur doit répondre au modèle de retour.

Points obligatoires :

- documentation utilisée ;
- étape bloquante ou non ;
- ambiguïtés ;
- résultat obtenu ;
- aide extérieure ;
- verdict ;
- gravité ;
- suggestion éventuelle.

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

## 18. Niveau d’aide utilisé

```text
A0 — aucune aide
A1 — documentation Forge uniquement
A2 — recherche personnelle ou documentation externe
A3 — aide d’un autre testeur
A4 — aide du référent Forge
A5 — impossible malgré aide
```

---

## 19. Conversion documentation

À remplir après validation terrain.

| Question | Réponse |
|---|---|
| Ce ticket peut-il devenir un tutoriel ? | oui / non / partiellement |
| Nom proposé de la page tutoriel | `docs/tutorials/...` |
| Menu proposé | Tutoriels > ... |
| Ticket FT validé par un testeur externe ou non expert ? | oui / non |
| Conversion autorisée maintenant ? | oui / non |

### Contenu à conserver pour le tutoriel

- objectif ;
- contexte utile ;
- documentation liée ;
- fichiers/classes/commandes concernés ;
- exemple indicatif décorrélé ;
- procédure ;
- résultat attendu ;
- erreurs fréquentes ;
- vérifications.

### Contenu à retirer du tutoriel

- preuves obligatoires ;
- retour d’expérience ;
- gravité ;
- niveau d’aide ;
- statut interne ;
- notes du référent ;
- triage ;
- décisions correctives.

### Règle

Le tutoriel ne doit pas être publié comme parcours recommandé tant que le ticket FT correspondant n’a pas été validé au moins une fois par un testeur externe ou non expert Forge.

---

## 20. Notes pour le référent Forge

À remplir après analyse du retour.

- Problème reproductible : oui / non
- Problème framework : oui / non / probable
- Problème documentation : oui / non / probable
- Problème ergonomie : oui / non / probable
- Hors périmètre : oui / non
- Ticket correctif à créer : oui / non
- Type de ticket correctif :
  - bug ;
  - documentation ;
  - documentation officielle erronée pendant test ;
  - ergonomie CLI ;
  - sécurité ;
  - générateur ;
  - exemple ;
  - backlog.
- Priorité proposée :
  - immédiate ;
  - avant stable ;
  - avant RC ;
  - backlog ;
  - refusé.
