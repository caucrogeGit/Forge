# Tests terrain : État des parcours

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page donne une vue synthétique de l'avancement de la campagne de tests terrain Forge. Elle ne remplace pas la [roadmap complète](../roadmap/forge-field-test-roadmap.md) ni le [détail des tickets disponibles](tickets/index.md).

---

## Distinction importante

| Terme | Définition |
|---|---|
| **Ticket technique validé** | Une brique Forge a été développée, testée et documentée par les auteurs du framework |
| **Ticket FT rédigé** | Un ticket de test terrain existe dans `docs/testing/tickets/` et peut être donné à un testeur |
| **Ticket FT validé** | Un testeur a exécuté le ticket et fourni un retour exploitable |
| **Tutoriel publié** | Le contenu d'un ticket FT validé a été nettoyé et publié dans la documentation utilisateur |
| **Tutoriel testé** | Le tutoriel publié a lui-même été vérifié par un lecteur externe |
| **Parcours validé terrain** | Plusieurs tickets FT d'un même thème sont validés avec retour exploitable |

---

## Légende des statuts de parcours

| Statut | Signification |
|---|---|
| **À préparer** | les tickets détaillés ne sont pas encore rédigés |
| **Prêt à tester** | au moins les tickets clés du parcours sont rédigés et disponibles |
| **En test** | au moins un testeur exécute le parcours |
| **Validé terrain** | le parcours a été exécuté avec retour exploitable et sans bloquant |
| **À corriger** | un retour terrain impose une correction ou une clarification |
| **Converti en tutoriel** | le parcours validé a été transformé en page tutoriel publiée |
| **Bloqué** | le parcours ne peut pas être poursuivi sans correction préalable |

## Légende documentaire

| Statut documentaire | Signification |
|---|---|
| **Non rédigé** | aucun ticket détaillé n'existe encore |
| **Ticket FT disponible** | le ticket est rédigé mais pas encore validé terrain |
| **Validé terrain** | le ticket a été exécuté et validé par retour testeur |
| **Tutoriel publié** | le contenu a été converti en page tutoriel |
| **Tutoriel testé** | le tutoriel publié a lui-même été vérifié |

---

## Matrice synthétique des parcours

| Parcours | Phases | Statut | Tickets rédigés | Tutoriel | Notes |
|---|---|---|---|---|---|
| Cadre de campagne | FT-00 | Prêt à tester | 4 / 10 | Non publié | Tickets essentiels disponibles |
| Installation avec pipx | FT-01 | Prêt à tester | 2 / 9 | Non publié | pipx + vérification version |
| Configuration environnement | FT-02 | À préparer | 0 / 10 | Non publié | |
| MariaDB système | FT-03 | À préparer | 0 / 10 | Non publié | Inclure utilisateur non-root |
| Connexion Forge à MariaDB | FT-04 | À préparer | 0 / 9 | Non publié | |
| Premier projet | FT-05 | À préparer | 0 / 8 | Non publié | Après configuration DB |
| Architecture du projet | FT-06 | À préparer | 0 / 9 | Non publié | |
| Routes et contrôleurs | FT-07 + FT-08 | À préparer | 0 / 16 | Non publié | Parcours web minimal |
| Templates Jinja | FT-09 + FT-10 | À préparer | 0 / 17 | Non publié | Avant Tailwind |
| Layout public | FT-11 | À préparer | 0 / 8 | Non publié | |
| Tailwind | FT-12 | À préparer | 0 / 9 | Non publié | Front visuel |
| Formulaires et CSRF | FT-13 + FT-14 | À préparer | 0 / 15 | Non publié | |
| HTMX progressif | FT-15 | À préparer | 0 / 8 | Non publié | HTML partiel |
| Alpine.js | FT-16 | À préparer | 0 / 7 | Non publié | Optionnel |
| Mail développement | FT-17 | À préparer | 0 / 7 | Non publié | |
| CLI et diagnostics | FT-18 + FT-19 + FT-20 | À préparer | 0 / 20 | Non publié | |
| Entités, SQL, migrations | FT-21 + FT-22 + FT-23 + FT-24 | À préparer | 0 / 31 | Non publié | Modèle de données |
| CRUD | FT-25 + FT-26 + FT-27 + FT-28 + FT-29 | À préparer | 0 / 38 | Non publié | Génération et usage |
| Relations | FT-30 + FT-31 | À préparer | 0 / 15 | Non publié | Simples et avancées |
| Médias et uploads | FT-32 + FT-33 | À préparer | 0 / 16 | Non publié | Inclure sécurité uploads |
| Authentification | FT-34 + FT-35 | À préparer | 0 / 16 | Non publié | Login / logout / session |
| RBAC | FT-36 | À préparer | 0 / 8 | Non publié | Autorisations |
| Diagnostics applicatifs | FT-37 | À préparer | 0 / 8 | Non publié | |
| Déploiement | FT-38 + FT-39 | À préparer | 0 / 16 | Non publié | VM Debian |
| Maintenance | FT-40 | À préparer | 0 / 7 | Non publié | Évolution projet |
| Mini-projet guidé | FT-41 | À préparer | 0 / 11 | Non publié | Parcours complet |
| Projet autonome | FT-42 | À préparer | 0 / 8 | Non publié | Autonomie testeur |
| Consolidation des retours | FT-43 | À préparer | 0 / 9 | Non publié | |
| Conversion en tutoriels | FT-44 | À préparer | 0 / 13 | Non publié | |
| Décision bêta ou stable | FT-45 | À préparer | 0 / 7 | Non publié | |

---

## Détail des parcours disponibles

### Parcours : Cadre de campagne (FT-00)

**Statut :** Prêt à tester (4 tickets rédigés sur 10)

**Objectif :** vérifier que le testeur comprend la campagne, le modèle de retour, la procédure documentation officielle erronée et les outils de diagnostic disponibles.

**Tickets FT rédigés :**

- [FT-00-TEST-CHARTER-001](tickets/ft-00-test-charter-001.md), lire et valider la charte de campagne
- [FT-00-FEEDBACK-TEMPLATE-001](tickets/ft-00-feedback-template-001.md), remplir un retour d'expérience à blanc
- [FT-00-DOC-ERROR-PROTOCOL-001](tickets/ft-00-doc-error-protocol-001.md), appliquer la procédure documentation erronée
- [FT-00-DEBUG-TOOLS-INTRO-001](tickets/ft-00-debug-tools-intro-001.md), découvrir les outils de diagnostic Forge

**Tickets FT restant à rédiger :** FT-00-SEVERITY-SCALE-001, FT-00-GUIDANCE-LEVELS-001, FT-00-HELP-LEVELS-001, FT-00-TICKET-FORMAT-001, FT-00-TRIAGE-RULES-001, FT-00-ENV-MATRIX-001

**Tutoriel :** aucun publié.

**Blocages connus :** aucun.

---

### Parcours : Installation avec pipx (FT-01)

**Statut :** Prêt à tester (2 tickets rédigés sur 9)

**Objectif :** tester l'installation de Forge via `pipx` et vérifier la cohérence de la version affichée.

**Tickets FT rédigés :**

- [FT-01-INSTALL-PIPX-001](tickets/ft-01-install-pipx-001.md), installer Forge via pipx
- [FT-01-INSTALL-VERSION-CHECK-001](tickets/ft-01-install-version-check-001.md), vérifier la version installée

**Tickets FT restant à rédiger :** FT-01-INSTALL-VENV-001, FT-01-INSTALL-GITHUB-001, FT-01-INSTALL-DEV-EDITABLE-001, FT-01-INSTALL-WINDOWS-WSL-001, FT-01-INSTALL-DEBIAN-VM-001, FT-01-INSTALL-UNINSTALL-001, FT-01-PHASE-REVIEW-001

**Tutoriel :** aucun publié.

**Blocages connus :** aucun.

---

### Parcours : Configuration environnement (FT-02)

**Statut :** À préparer

**Objectif :** tester la configuration de l'environnement Forge (`.env`, variables, mode dev/prod, secrets).

**Tickets FT rédigés :** aucun.

**Tutoriel :** aucun publié.

---

### Parcours : MariaDB (FT-03)

**Statut :** À préparer

**Objectif :** tester l'installation et la configuration de MariaDB, incluant la création d'un utilisateur non-root.

**Tickets FT rédigés :** aucun.

**Tutoriel :** aucun publié.

---

### Parcours : Premier projet (FT-04 à FT-06)

**Statut :** À préparer

**Objectif :** tester la connexion Forge à MariaDB, la création d'un premier projet et la compréhension de l'architecture.

**Tickets FT rédigés :** aucun.

**Tutoriel :** aucun publié.

---

### Parcours : Routes et contrôleurs (FT-07 + FT-08)

**Statut :** À préparer

**Objectif :** tester le routage applicatif et les contrôleurs Forge.

**Tickets FT rédigés :** aucun.

**Tutoriel :** aucun publié.

---

### Parcours : Templates Jinja (FT-09 + FT-10 + FT-11)

**Statut :** À préparer

**Objectif :** tester les templates Jinja2 et le layout public Forge.

**Tickets FT rédigés :** aucun.

**Tutoriel :** aucun publié.

---

### Parcours : CRUD (FT-25 à FT-29)

**Statut :** À préparer

**Objectif :** tester la génération et l'utilisation du CRUD Forge (38 tickets).

**Tickets FT rédigés :** aucun.

**Tutoriel :** aucun publié.

---

### Parcours : Déploiement (FT-38 + FT-39)

**Statut :** À préparer

**Objectif :** tester le déploiement Forge sur VM Debian.

**Tickets FT rédigés :** aucun.

**Tutoriel :** aucun publié.

---

### Parcours : Mini-projet guidé et autonomie (FT-41 + FT-42)

**Statut :** À préparer

**Objectif :** tester la capacité du testeur à construire un projet complet puis un projet autonome.

**Tickets FT rédigés :** aucun.

**Tutoriel :** aucun publié.

---

## Règle de mise à jour

Cette page doit être mise à jour :

- après chaque lot de tickets FT détaillés rédigés ;
- après chaque retour terrain significatif ;
- après chaque conversion d'un ticket FT validé en tutoriel.

**Règles de statut :**

- un parcours ne passe pas en **Validé terrain** sans retour testeur exploitable ;
- un parcours ne passe pas en **Converti en tutoriel** sans page tutoriel publiée dans la documentation ;
- un tutoriel n'est pas déclaré **Tutoriel testé** sans validation explicite par un lecteur externe.
