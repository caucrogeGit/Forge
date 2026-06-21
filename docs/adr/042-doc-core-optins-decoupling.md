# ADR-042 : Découpler la documentation du cœur et celle des opt-ins

## Statut

Accepté.

## Contexte

Depuis l'ADR-038, la documentation des 12 opt-ins est embarquée dans chaque
paquet (`packages/<pkg>/docs/`) et agrégée au build dans le site unique
`forgemvc.com` par le plugin `mkdocs-monorepo`.
L'ADR-039 a réorganisé l'arborescence du cœur.

Dans cet état, le cœur et les opt-ins partageaient une seule navigation et
étaient fortement couplés par des liens transversaux dans les deux sens :

- liens cœur vers opt-in (ex. `docs/features/auth.md` vers la référence MFA) ;
- liens opt-in vers cœur (ex. un welcome opt-in vers le guide d'installation).

Ce couplage brouille la frontière entre le framework (cœur) et les briques
optionnelles, à rebours du principe 8 (noyau minimal, briques opt-in) et du
principe 1 (séparer framework et application).

## Décision

1. **Deux navigations distinctes dans un site unique.**
   La navigation se scinde en deux onglets de premier niveau
   (`navigation.tabs`, déjà actif) :

   - **Cœur de Forge** : installation, concepts, modèle de données, guides,
     référence, parcours cœur, déploiement, release, philosophie, tests
     terrain, projet ;
   - **Opt-ins officiels** : les 12 paquets, chacun avec sa propre
     progression et sa référence par-module.

   Le site reste **un seul build** et une seule URL ; le découplage est de
   navigation et de contenu, pas d'infrastructure.

2. **Aucun lien transversal entre les deux espaces.**
   Aucune page du cœur ne lie une page d'opt-in, et réciproquement.
   Les renvois transversaux existants sont **neutralisés** : le texte est
   conservé, le lien est retiré.
   Les liens **internes à un espace** restent autorisés :
   cœur vers cœur, et opt-in vers opt-in (les opt-ins partagent le même
   onglet).

3. **Les mentions restent permises, pas les liens.**
   Une page du cœur peut **mentionner** qu'un opt-in existe (ex. « le module
   `forge-mvc-mfa` fournit le MFA »), mais sans lien hypertexte vers sa
   documentation.

## Conséquences

- La navigation reflète la frontière framework / briques optionnelles.
- Un lecteur du cœur n'est jamais détourné vers la doc d'un opt-in, et
  inversement.
- Les parcours d'installation des opt-ins ne renvoient plus par lien vers le
  guide d'installation du cœur : l'utilisateur installe Forge d'abord, puis
  consulte l'espace opt-ins.
- Deux garde-fous qui exigeaient un lien transversal
  (`test_docs_reference_split_001`, `test_pivot_advanced_usage_docs_008`) sont
  réécrits pour interdire ces liens au lieu de les exiger.
- Un garde-fou nouveau vérifie l'absence de lien transversal dans les deux
  sens.

## Alternatives écartées

- **Deux sites mkdocs séparés** (deux builds, deux URLs) : découplage plus
  fort mais surcoût de CI et de déploiement non justifié ; un seul site avec
  deux onglets suffit à séparer les navigations.
- **Découpler la navigation seulement** (garder les liens de contenu utiles) :
  écarté, le couplage par liens de contenu subsistait.
