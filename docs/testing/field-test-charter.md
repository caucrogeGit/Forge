# Tests terrain : Charte de campagne

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

## 1. But du document

Ce document définit les règles de la campagne indépendante de tests terrain Forge.

Cette campagne commence après la consolidation fonctionnelle du framework.
Elle ne cherche pas à ajouter de nouvelles fonctionnalités.
Elle cherche à répondre à une question simple :

> Un développeur qui ne connaît pas Forge peut-il l’installer, le comprendre, l’utiliser, diagnostiquer ses erreurs, construire une application et la maintenir ?

La campagne teste donc à la fois :

- le framework ;
- la CLI ;
- la documentation ;
- les messages d’erreur ;
- les générateurs ;
- l’architecture projet ;
- la maintenabilité ;
- la sécurité de base ;
- le déploiement.

## 2. Périmètre

La campagne couvre :

- installation : pipx, venv, GitHub, editable, WSL, Debian ;
- environnement : `.env`, secrets, dev/prod ;
- MariaDB ;
- premier projet ;
- architecture `core/`, `mvc/`, `cli/`, `docs/`, `tests/` ;
- routes, contrôleurs, templates ;
- Jinja ;
- Tailwind ;
- HTMX ;
- Alpine.js ;
- formulaires ;
- CSRF ;
- mail en mode développement ;
- CLI et diagnostics ;
- entités JSON ;
- modèles générés et fichiers manuels ;
- SQL visible ;
- migrations ;
- CRUD ;
- relations ;
- médias/uploads ;
- auth ;
- RBAC ;
- sécurité ;
- erreurs ;
- déploiement ;
- maintenance ;
- mini-projet guidé ;
- projet autonome ;
- consolidation des retours ;
- décision bêta ou stable.

## 3. Ce qu’un ticket terrain ne doit pas faire

Un ticket terrain `FT-*` ne doit pas :

- demander de corriger Forge ;
- modifier le cœur du framework sauf si le ticket porte explicitement sur l’observation du core ;
- mélanger plusieurs responsabilités ;
- transformer un test en activité scolaire ;
- demander au testeur de deviner les fichiers à utiliser ;
- fournir une solution prête à copier-coller ;
- produire un ticket de développement directement dans la même étape ;
- ajouter une fonctionnalité non prévue ;
- transformer une demande de test en refonte.

Un ticket terrain doit observer, reproduire, documenter, mesurer et conclure.

## 4. Principe de progression

La roadmap suit le parcours naturel d’un utilisateur qui découvre Forge :

1. installer ;
2. configurer ;
3. préparer la base ;
4. créer un projet ;
5. comprendre l’architecture ;
6. afficher une page ;
7. utiliser les templates ;
8. utiliser le front HTML-first ;
9. manipuler les formulaires ;
10. découvrir la CLI ;
11. créer des entités ;
12. générer SQL, modèles, migrations ;
13. générer et utiliser du CRUD ;
14. utiliser relations, médias, auth, RBAC ;
15. diagnostiquer ;
16. déployer ;
17. maintenir ;
18. construire un mini-projet ;
19. construire un projet autonome ;
20. consolider les retours ;
21. décider stable ou bêta prolongée.

## 5. Niveaux de guidage

Chaque ticket doit indiquer son niveau de guidage.

| Niveau | Nom | Signification |
|---|---|---|
| G0 | Guidé complètement | Procédure très détaillée, utilisée pour les premières étapes ou les environnements sensibles |
| G1 | Guidé avec transposition | Exemples décorrélés, le testeur transpose dans le cas demandé |
| G2 | Semi-guidé | Objectif clair, procédure moins détaillée, documentation indiquée |
| G3 | Autonome | Objectif applicatif donné sans procédure complète |

La progression doit aller de G0 vers G3.

## 6. Niveaux d’aide extérieure

Le retour testeur doit indiquer l’aide utilisée.

| Niveau | Signification |
|---|---|
| A0 | aucune aide |
| A1 | documentation Forge uniquement |
| A2 | recherche personnelle ou documentation externe |
| A3 | aide d’un autre testeur |
| A4 | aide du référent Forge |
| A5 | impossible malgré aide |

Un ticket réussi en A4 ou A5 signale un problème de documentation, d’ergonomie ou de framework.

## 7. Gravité des retours

| Niveau | Nom | Définition | Traitement |
|---|---|---|---|
| S0 | Bloquant critique | installation impossible, perte de données, faille évidente, projet inutilisable | correction immédiate |
| S1 | Bloquant fonctionnel | une étape documentée ne peut pas être terminée | correction prioritaire |
| S2 | Friction forte | ça fonctionne, mais c’est confus, fragile ou mal documenté | correction ou documentation obligatoire |
| S3 | Friction mineure | gêne réelle mais non bloquante | backlog possible |
| S4 | Suggestion | amélioration utile mais facultative | backlog post-stable |
| S5 | Hors périmètre | remarque intéressante mais extérieure au ticket ou à Forge core | classer hors campagne |

## 8. Statuts finaux d’un ticket terrain

Chaque ticket doit finir avec un statut.

```text
VALIDÉ
VALIDÉ AVEC FRICTION
ÉCHOUÉ
BLOQUÉ PAR BUG FORGE
BLOQUÉ PAR DOCUMENTATION
HORS PÉRIMÈTRE
NON TESTÉ
```

## 9. Preuves minimales obligatoires

Un retour sans preuve est faible.

Selon le ticket, demander :

- commandes exécutées ;
- sortie terminal complète ;
- capture navigateur ;
- fichiers créés ou modifiés ;
- `git status` avant/après ;
- extrait `git diff` si utile ;
- logs complets en cas d’erreur ;
- version Python ;
- version Forge ;
- OS ;
- méthode d’installation ;
- base de données utilisée ;
- navigateur utilisé.

## 10. Règle sur les exemples

Les exemples sont autorisés et recommandés, mais ils doivent être décorrélés du livrable demandé.

Règle :

> L’exemple montre une forme, une syntaxe ou une logique.
> Il ne doit pas être copiable tel quel pour valider le ticket.

Exemple de verrou :

- si le ticket demande `/hello`, l’exemple montre `/demo` ;
- si le ticket demande `BookController`, l’exemple montre `DemoController` ;
- si le ticket demande une page `about.html`, l’exemple montre une page `sample.html`.

## 11. Présentation obligatoire des fichiers, classes ou commandes

Chaque ticket doit présenter les éléments utilisés.

Pour chaque élément :

- rôle ;
- nature ;
- pourquoi il intervient ;
- usage correct ;
- action autorisée ;
- action interdite ;
- erreurs fréquentes.

Exemple de classification :

| Élément | Nature | Action autorisée |
|---|---|---|
| `mvc/routes.py` | applicatif | modifiable |
| `mvc/controllers/` | applicatif | modifiable |
| `mvc/views/` | applicatif | modifiable |
| `mvc/entities/` | applicatif canonique | modifiable selon procédure |
| `mvc/models/*_base.py` | généré | ne pas modifier directement |
| `mvc/models/*.py` | manuel applicatif | modifiable |
| `core/` | framework | ne pas modifier dans un ticket FT |
| `cli/` | CLI framework | consulter uniquement sauf ticket spécifique |
| `storage/` | données/logs/uploads | observer selon ticket |
| `static/` | assets applicatifs | modifiable selon ticket |

## 12. Git minimal

Pour les tickets qui modifient un projet, demander au minimum :

```bash
git status
```

avant et après.

Pour les tickets avancés :

```bash
git diff --check
```

Si le ticket touche un projet de test, il peut demander un commit local de preuve, mais ce n’est pas obligatoire.


## 13. Verrou : Documentation officielle erronée pendant un test

La documentation officielle fait partie de ce qui est testé.

Si une page de documentation Forge est fausse, incomplète, contradictoire ou ne correspond pas au comportement réel observé, le testeur ne doit pas improviser silencieusement et ne doit pas corriger directement la documentation pendant le ticket.

### Règle

```text
Une documentation erronée est un résultat de test.
Elle doit être signalée, prouvée, classée et triée.
```

### Procédure testeur

Si la documentation est erronée pendant un ticket :

1. s’arrêter au point d’écart ou continuer uniquement si un contournement évident existe ;
2. noter la page consultée ;
3. citer ou résumer le passage concerné ;
4. noter l’étape exacte du ticket concernée ;
5. indiquer ce que la documentation annonce ;
6. indiquer ce que Forge fait réellement ;
7. fournir les commandes, logs, captures ou fichiers observés ;
8. indiquer si un contournement a été trouvé ;
9. classer la gravité ;
10. choisir le statut adapté.

### Statuts adaptés

```text
BLOQUÉ PAR DOCUMENTATION
```

si le ticket ne peut pas être terminé à cause de la documentation.

```text
VALIDÉ AVEC FRICTION
```

si le ticket est terminé, mais avec contournement ou effort non prévu.

### Gravité recommandée

| Gravité | Cas |
|---|---|
| S1 | la documentation bloque la réalisation du ticket |
| S2 | la documentation est fausse mais contournable avec forte friction |
| S3 | la documentation est ambiguë mais le test reste simple |
| S4 | amélioration de clarté ou exemple utile à ajouter |
| S5 | remarque documentaire hors périmètre du ticket |

### Ce que le testeur ne doit pas faire

- corriger directement la documentation pendant le ticket ;
- modifier Forge pour contourner une documentation fausse ;
- masquer l’écart dans son retour ;
- présenter un contournement comme vérité officielle.

### Rôle du référent Forge

Le référent analyse le retour et crée si nécessaire un ticket documentaire séparé.

Nom conseillé :

```text
DOC-FT-XX-NOM-DU-TICKET-001
```

Exemple :

```text
DOC-FT-04-FORGE-DB-CONFIG-001
```

Objectif du ticket documentaire :

```text
Corriger la documentation suite au retour terrain du ticket FT concerné.
```

## 14. Transformation des retours en tickets correctifs

Après triage :

- retour S0/S1 reproductible : ticket correctif Forge obligatoire ;
- retour S2 : ticket correctif ou documentation obligatoire ;
- retour S3 : backlog ;
- retour S4 : backlog post-stable ;
- retour S5 : hors périmètre ;
- retour non reproductible : demander compléments ou classer à surveiller.

## 15. Capitalisation documentaire : ticket FT validé vers tutoriel

La campagne de test doit aussi servir à produire une documentation tutorielle fiable.

Règle :

> Tout ticket FT validé sans bloquant doit être évalué pour conversion en tutoriel Forge.

Le cycle attendu est :

```text
ticket FT rédigé
→ testeur l’exécute
→ retour terrain
→ correction éventuelle
→ ticket validé
→ conversion en tutoriel documentation
→ ajout au menu Tutoriels
```

Un ticket FT ne doit pas être publié tel quel dans la documentation utilisateur.

### Ce qui peut être conservé dans le tutoriel

- objectif ;
- contexte utile ;
- documentation liée ;
- présentation des fichiers, classes et commandes ;
- exemples indicatifs décorrélés ;
- procédure opératoire ;
- résultat attendu ;
- erreurs fréquentes ;
- vérifications.

### Ce qui doit être retiré du tutoriel

- preuves obligatoires ;
- retour d’expérience testeur ;
- gravité S0 à S5 ;
- niveau d’aide A0 à A5 ;
- statut de ticket ;
- notes du référent Forge ;
- triage interne ;
- décisions correctives.

### Règle de publication

Un tutoriel Forge ne doit pas être publié comme parcours recommandé tant que le ticket FT correspondant n’a pas été validé au moins une fois par un testeur externe ou non expert Forge.

### Emplacement conseillé

```text
docs/tutorials/
```

### Menu conseillé

```text
Tutoriels
├── Installer Forge
├── Configurer l’environnement
├── Configurer MariaDB
├── Créer un premier projet
├── Comprendre l’architecture
├── Créer une première route
├── Créer un contrôleur
├── Utiliser les templates Jinja
├── Utiliser Tailwind
├── Utiliser HTMX
├── Utiliser Alpine.js
├── Créer une entité
├── SQL et migrations
├── Générer un CRUD
├── Relations
├── Médias et uploads
├── Authentification
├── RBAC
├── Déploiement
└── Mini-projet complet
```

## 16. Phase review

Certaines phases doivent se terminer par un ticket de revue de phase.

Ce ticket sert à décider si la phase suivante peut commencer.

Le ticket de revue doit synthétiser :

- tickets validés ;
- tickets bloqués ;
- retours S0/S1 ;
- problèmes documentaires ;
- corrections à prévoir ;
- décision : continuer, corriger avant suite, ou suspendre la campagne.

## 17. Critère de réussite global

Forge ne doit pas être déclaré stable uniquement parce que ses tests automatisés passent.

Forge peut être considéré prêt pour stable si :

- les installations principales sont reproductibles ;
- la documentation permet de commencer sans aide du créateur ;
- MariaDB est configuré sans compte root applicatif ;
- un projet minimal fonctionne ;
- un mini-projet guidé est construit ;
- un projet autonome est construit ;
- les erreurs courantes sont diagnostiquables ;
- aucun S0/S1 n’est ouvert ;
- les S2 sont corrigés ou documentés ;
- les limites restantes sont assumées.
