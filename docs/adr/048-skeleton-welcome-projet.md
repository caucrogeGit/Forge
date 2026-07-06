# ADR-048 : Parcours d'accueil « welcome-projet » dans le squelette

## Statut

**Annulé** (consolidation bêta 1.0).
Initialement accepté en bêta publique 1.0 (`1.0.0-beta.x`), mis en œuvre par les tickets `WELCOME-PROJET-*`.

### Révision : retrait du parcours welcome-projet

Retour terrain : le parcours `docs/welcome/` embarqué faisait double emploi avec la documentation officielle (forgemvc.com), que le squelette référence déjà.
La promesse « court, anti-duplication » de la décision n'a pas tenu à l'usage : maintenir un fil conducteur local aligné avec le CLI revenait à dupliquer la doc en ligne.

Conséquences du retrait :

- suppression de `skeleton/data/docs/welcome/` (le dossier `docs/` du squelette source disparaît ; un projet généré peut toujours obtenir un `docs/` via la guidance agent ADR-047, mais plus de `docs/welcome/`) ;
- suppression du garde-fou de navigation `WELCOME-PROJET-NAV-001` (`tests/test_skeleton_welcome_projet_nav_001.py`) ;
- bascule des garde-fous du squelette en tests d'absence (`test_skeleton_tree_001`, `test_new_core_dep_001`).

L'onboarding humain repose désormais entièrement sur la documentation officielle.
Les couches ADR-024 (projet nu) et ADR-047 (guidance agent) restent en place.

---

## Date

2026-06-24

---

## Contexte

`forge new` produit un projet nu (ADR-024), accompagné d'une page d'accueil web (`mvc/views/home/index.html`) et, depuis l'ADR-047, d'une couche de guidance pour les agents IA (`CLAUDE.md`, `AGENTS.md`, ADR-001).

Il manque un **onboarding pédagogique humain, local au projet** : un fil conducteur qui guide les premiers gestes *dans ce projet précis*.
Le tutoriel `welcome-forge` (publié sur forgemvc.com) enseigne le framework, mais il est exhaustif et en ligne, pas un point de départ local et court.

## Décision

`forge new` embarque un parcours d'accueil `docs/welcome/` dans le projet généré.

1. **Local et orienté « ton projet »** : le parcours fait faire les premiers gestes dans l'application qu'on vient de créer (première entité, CRUD, page, opt-in, validation), pas un cours abstrait.
2. **Court, anti-duplication** : chaque page reste brève et renvoie à forgemvc.com pour approfondir, plutôt que de recopier la documentation exhaustive.
   On évite de dupliquer `welcome-forge`.
3. **Multi-paliers** : `installation.md`, puis trois niveaux (débutant, intermédiaire, avancé) de deux étapes chacun, chaînés par un `bilan.md`, et un `recapitulatif.md`.
4. **Source** : contenu statique sous `skeleton/data/docs/welcome/`, copié tel quel par `forge new` (couvert par le package-data `skeleton/data/**`).
5. **Propriété du projet** : le développeur peut adapter ou supprimer ce parcours.

## Conséquences

Positives :

- un développeur dispose d'un fil conducteur local dès la création du projet ;
- le parcours utilise les commandes réelles du projet, pas des exemples hors sol.

Coûts et limites :

- déviation assumée d'ADR-024 : le projet généré gagne un onboarding (comme la config VS Code, les schémas JSON et la couche agent) ;
- contenu à maintenir distillé et aligné avec le CLI ;
- pas de version de Forge codée en dur dans les pages (pour ne pas dater le squelette ni déclencher les garde-fous de version).

## Relation avec ADR-024 et ADR-047

Trois couches « expérience » accompagnent désormais un projet nu, sans générer de code métier :

- ADR-024 : le projet reste nu côté code applicatif ;
- ADR-047 : guidance pour les agents IA (`CLAUDE.md`, `AGENTS.md`, ADR-001) ;
- ADR-048 : onboarding humain (`docs/welcome/`).

## Alternatives écartées

- Un simple `README` d'onboarding : utile mais moins guidé qu'un parcours ; pourra coexister, mais ne remplace pas le fil conducteur multi-paliers.
- Dupliquer intégralement `welcome-forge` dans le projet : redondant et lourd à maintenir.
- Ne rien fournir : le développeur démarre sans fil conducteur local.

## Mise en œuvre (tickets `WELCOME-PROJET-*`)

- `WELCOME-PROJET-CONTENT-001` : rédiger le parcours dans `skeleton/data/docs/welcome/` (installation + 3 niveaux + bilans + récapitulatif), court et renvoyant à forgemvc.com.
- `WELCOME-PROJET-NAV-001` : garde-fou de chaînage du parcours.

## Liens

- Projet nu : [ADR-024](024-skeleton-bootstrap.md).
- Guidance agent : [ADR-047](047-app-agent-guidance-layer.md).
