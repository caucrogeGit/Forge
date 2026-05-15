# Roadmap Forge Design

Forge Design est un projet compagnon de Forge.

Il ne fait pas partie du cœur Forge 2.0. Il doit être construit après stabilisation du framework Forge.

---

## Vision

Forge Design est un outil graphique destiné à produire des interfaces Forge propres.

Il doit permettre de construire visuellement :

- des pages publiques ;
- des templates Jinja ;
- des fragments HTML ;
- des composants Tailwind ;
- des formulaires simples ;
- des comportements HTMX ;
- des comportements Alpine.js simples ;
- des fichiers JSON de description exportables vers un projet Forge.

Forge Design ne doit pas devenir :

- un éditeur React ;
- un éditeur Vue ;
- un clone de Webflow ;
- une SPA lourde obligatoire ;
- une dépendance obligatoire de Forge ;
- un générateur opaque.

Règle centrale :

```text
Forge Design produit du code Forge lisible.
```

---

## Condition d’entrée

Forge Design ne doit pas démarrer fortement tant que Forge n’a pas atteint une version publiable et exploitable.

Condition minimale :

- Forge 2.0 publié ou quasi publié ;
- CLI stable ;
- conventions templates stabilisées ;
- composants Jinja stabilisés ;
- profils de projet définis ;
- starter démonstrateur disponible ;
- documentation Forge cohérente ;
- tests principaux verts.

---

## Phase FD-0 — Cadrage de Forge Design

**État : à venir.**

Objectif : définir précisément ce que Forge Design est, et surtout ce qu’il n’est pas.

| Ticket | Objectif |
|---|---|
| FD-CADRAGE-001 | Définir la philosophie de Forge Design |
| FD-CADRAGE-002 | Définir les limites : pas de React/Vue obligatoire, pas de Webflow bis |
| FD-CADRAGE-003 | Définir les fichiers produits |
| FD-CADRAGE-004 | Définir le lien avec Forge MVC |
| FD-CADRAGE-DOC-001 | Document de cadrage officiel |

Décision attendue :

```text
Forge Design est un outil de production de templates Forge, pas un framework concurrent.
```

---

## Phase FD-1 — Modèle de page Forge Design

**État : à venir.**

Objectif : définir une représentation JSON d’une page ou d’un fragment.

| Ticket | Objectif |
|---|---|
| FD-MODEL-001 | Définir le modèle JSON d’une page |
| FD-MODEL-002 | Définir les blocs HTML supportés |
| FD-MODEL-003 | Définir les composants Forge réutilisables |
| FD-MODEL-004 | Définir les zones Jinja |
| FD-MODEL-005 | Définir les métadonnées d’export |
| FD-MODEL-VALIDATION-001 | Valider le modèle JSON |
| FD-MODEL-DOC-001 | Documenter le modèle JSON |

Exemple de structure visée :

```json
{
  "type": "page",
  "name": "accueil",
  "layout": "public.html",
  "blocks": []
}
```

---

## Phase FD-2 — Lecture d’un projet Forge

**État : à venir.**

Objectif : permettre à Forge Design de comprendre un projet Forge existant.

| Ticket | Objectif |
|---|---|
| FD-FORGE-READ-001 | Lire la structure d’un projet Forge |
| FD-FORGE-READ-002 | Détecter les layouts disponibles |
| FD-FORGE-READ-003 | Détecter les composants Jinja |
| FD-FORGE-READ-004 | Détecter les vues existantes |
| FD-FORGE-READ-005 | Détecter les entités disponibles |
| FD-FORGE-READ-006 | Détecter les routes publiques |
| FD-FORGE-READ-DOC-001 | Documenter la lecture d’un projet Forge |

Interdiction : ne pas modifier le projet pendant cette phase.

---

## Phase FD-3 — Éditeur visuel de structure

**État : à venir.**

Objectif : créer une interface graphique permettant de construire la structure HTML d’une page.

| Ticket | Objectif |
|---|---|
| FD-EDITOR-001 | Éditeur de page minimal |
| FD-EDITOR-002 | Ajout de sections |
| FD-EDITOR-003 | Ajout de colonnes |
| FD-EDITOR-004 | Ajout de blocs texte |
| FD-EDITOR-005 | Ajout d’images |
| FD-EDITOR-006 | Ajout de boutons |
| FD-EDITOR-007 | Réorganisation simple des blocs |
| FD-EDITOR-008 | Suppression de blocs |
| FD-EDITOR-DOC-001 | Documentation de l’éditeur de structure |

Règle : l’éditeur manipule une structure Forge Design, pas directement un fichier HTML brut au départ.

---

## Phase FD-4 — Génération HTML/Jinja

**État : à venir.**

Objectif : transformer le modèle Forge Design en fichiers HTML/Jinja lisibles.

| Ticket | Objectif |
|---|---|
| FD-JINJA-001 | Générer du HTML simple |
| FD-JINJA-002 | Générer des blocs Jinja |
| FD-JINJA-003 | Utiliser un layout Forge |
| FD-JINJA-004 | Générer des includes composants |
| FD-JINJA-005 | Préserver les zones modifiables |
| FD-JINJA-VALIDATION-001 | Valider le HTML/Jinja produit |
| FD-JINJA-DOC-001 | Documenter la génération Jinja |

Interdiction : ne pas générer du code opaque ou minifié.

---

## Phase FD-5 — Tailwind et design visuel

**État : à venir.**

Objectif : permettre l’habillage Tailwind sans transformer Forge Design en usine à classes incompréhensible.

| Ticket | Objectif |
|---|---|
| FD-TAILWIND-001 | Définir les classes autorisées de base |
| FD-TAILWIND-002 | Gérer espacements |
| FD-TAILWIND-003 | Gérer couleurs |
| FD-TAILWIND-004 | Gérer typographie |
| FD-TAILWIND-005 | Gérer bordures et arrondis |
| FD-TAILWIND-006 | Gérer grilles simples |
| FD-TAILWIND-007 | Présets visuels simples |
| FD-TAILWIND-DOC-001 | Documentation Tailwind dans Forge Design |

Règle : Tailwind reste lisible. Forge Design ne doit pas produire des chaînes de classes incontrôlables.

---

## Phase FD-6 — Données Jinja et variables de vue

**État : à venir.**

Objectif : permettre à Forge Design d’utiliser les données envoyées par les contrôleurs Forge.

| Ticket | Objectif |
|---|---|
| FD-DATA-001 | Définir les variables attendues par une vue |
| FD-DATA-002 | Détecter les variables Jinja utilisées |
| FD-DATA-003 | Signaler les variables manquantes |
| FD-DATA-004 | Afficher des données de prévisualisation |
| FD-DATA-005 | Lier une liste à une collection |
| FD-DATA-006 | Lier une fiche à un objet |
| FD-DATA-DOC-001 | Documenter les données de vue |

Exemple :

```jinja
{{ hebergement.nom }}
{{ hebergement.description }}
```

Forge Design doit signaler clairement si `hebergement` n’est pas fourni.

---

## Phase FD-7 — Formulaires Forge

**État : à venir.**

Objectif : construire visuellement des formulaires compatibles avec Forge.

| Ticket | Objectif |
|---|---|
| FD-FORM-001 | Représentation JSON d’un formulaire |
| FD-FORM-002 | Champs texte |
| FD-FORM-003 | Champs email/téléphone/url |
| FD-FORM-004 | Textarea |
| FD-FORM-005 | Select |
| FD-FORM-006 | Upload fichier/image |
| FD-FORM-007 | Affichage des erreurs |
| FD-FORM-008 | CSRF |
| FD-FORM-DOC-001 | Documentation formulaires |

Règle : Forge Design ne doit pas contourner la validation serveur Forge.

---

## Phase FD-8 — HTMX et interactions simples

**État : à venir.**

Objectif : ajouter des comportements dynamiques simples compatibles Forge.

| Ticket | Objectif |
|---|---|
| FD-HTMX-001 | Définir les actions HTMX supportées |
| FD-HTMX-002 | Configurer `hx-get` |
| FD-HTMX-003 | Configurer `hx-post` |
| FD-HTMX-004 | Configurer `hx-target` |
| FD-HTMX-005 | Configurer `hx-swap` |
| FD-HTMX-006 | Prévisualiser une zone HTMX |
| FD-HTMX-DOC-001 | Documentation HTMX |

Interdiction : ne pas transformer Forge Design en SPA.

---

## Phase FD-9 — Alpine.js et petits états locaux

**État : à venir.**

Objectif : gérer de petits comportements locaux.

| Ticket | Objectif |
|---|---|
| FD-ALPINE-001 | Définir les comportements Alpine supportés |
| FD-ALPINE-002 | Afficher/masquer |
| FD-ALPINE-003 | Menus déroulants |
| FD-ALPINE-004 | États ouverts/fermés |
| FD-ALPINE-005 | Petites interactions locales |
| FD-ALPINE-DOC-001 | Documentation Alpine |

Règle : Alpine complète le HTML serveur. Il ne remplace pas l’état applicatif côté serveur.

---

## Phase FD-10 — Export vers projet Forge

**État : à venir.**

Objectif : exporter proprement les fichiers produits dans un projet Forge.

| Ticket | Objectif |
|---|---|
| FD-EXPORT-001 | Export HTML/Jinja |
| FD-EXPORT-002 | Export fragments/components |
| FD-EXPORT-003 | Export JSON Forge Design |
| FD-EXPORT-004 | Vérification non-écrasement |
| FD-EXPORT-005 | Mode dry-run |
| FD-EXPORT-006 | Rapport d’export |
| FD-EXPORT-DOC-001 | Documentation export |

Règle : aucun fichier utilisateur ne doit être écrasé silencieusement.

---

## Phase FD-11 — Prévisualisation

**État : à venir.**

Objectif : permettre de visualiser le rendu avant export.

| Ticket | Objectif |
|---|---|
| FD-PREVIEW-001 | Prévisualisation statique |
| FD-PREVIEW-002 | Prévisualisation avec données fictives |
| FD-PREVIEW-003 | Prévisualisation responsive |
| FD-PREVIEW-004 | Prévisualisation composants |
| FD-PREVIEW-005 | Prévisualisation erreurs formulaire |
| FD-PREVIEW-DOC-001 | Documentation prévisualisation |

---

## Phase FD-12 — Intégration avec profils Forge

**État : à venir.**

Objectif : aligner Forge Design avec les profils de projet Forge.

| Ticket | Objectif |
|---|---|
| FD-PROFILE-001 | Support profil minimal |
| FD-PROFILE-002 | Support profil standard |
| FD-PROFILE-003 | Support profil dynamic |
| FD-PROFILE-004 | Support profil multilingual |
| FD-PROFILE-DOC-001 | Documentation profils |

Forge Design doit s’adapter au profil du projet, pas imposer un profil unique.

---

## Phase FD-13 — Stabilisation Forge Design 1.0

**État : à venir.**

Objectif : rendre Forge Design exploitable comme outil compagnon.

| Ticket | Objectif |
|---|---|
| FD-STABILIZE-001 | Audit architecture Forge Design |
| FD-STABILIZE-002 | Audit qualité export |
| FD-STABILIZE-003 | Audit non-écrasement |
| FD-STABILIZE-004 | Audit documentation |
| FD-STABILIZE-005 | Tests bout en bout |
| FD-STABILIZE-006 | Préparer Forge Design 1.0 |

Critères de sortie :

- export fiable ;
- code généré lisible ;
- non-écrasement garanti ;
- documentation claire ;
- compatibilité avec Forge 2.0 ;
- pas de dépendance obligatoire de Forge vers Forge Design.

---

## Limites assumées

Forge Design ne fournit pas au départ :

- éditeur React ;
- éditeur Vue ;
- éditeur Svelte ;
- marketplace de composants ;
- IA générative intégrée ;
- design system complexe ;
- collaboration temps réel ;
- hébergement ;
- déploiement ;
- paiement ;
- réservation ;
- logique métier ;
- base de données propre ;
- moteur CMS complet.

---

## Conclusion

Forge Design doit être construit seulement après stabilisation de Forge.

Objectif :

```text
Créer un outil graphique qui aide à produire des vues Forge propres, sans rendre Forge opaque.
```

Règle finale :

```text
Forge Design sert Forge.
Forge ne dépend pas de Forge Design.
```

---

## Règle de mise à jour

Les tickets Forge Design mettent à jour `docs/roadmap/forge-design-roadmap.md`.

Les tickets Forge classiques ne doivent pas modifier cette roadmap, sauf s'ils changent explicitement la relation entre Forge et Forge Design.

Exemple de section attendue dans les tickets Forge Design :

```text
## Roadmap à mettre à jour
Mettre à jour uniquement : docs/roadmap/forge-design-roadmap.md
Ne pas modifier : docs/roadmap/forge-roadmap.md
```