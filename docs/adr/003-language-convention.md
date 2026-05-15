# ADR-003 — Convention de langue pour l'API publique

## Statut

Acceptée

---

## Contexte

Forge a été développé en français dès ses origines : noms de fonctions
(`authentifier_session`, `hacher_mot_de_passe`, `creer_session`), noms de
variables de session (`utilisateur`, `authentifie`), noms de routes et de
colonnes de base de données.

Ce choix avait du sens pour un projet pédagogique francophone. Mais au fil
des phases, Forge a accumulé deux couches parallèles :

- `core/security/` avec une API nommée en français (API legacy)
- `core/auth/` avec une API partiellement nommée en anglais (API officielle)

La coexistence crée plusieurs problèmes :

1. **Incohérence** : deux API pour la même chose, avec des noms de langues
   différentes.
2. **Friction pour les contributeurs** : un développeur non francophone ne
   peut pas lire le code sans traduction.
3. **Tension avec les standards** : PyPI, les outils Python et la communauté
   open source utilisent l'anglais comme langue standard du code.
4. **Contradiction avec le Principe 11** (une seule façon officielle) : avoir
   `verifier_mot_de_passe` et `verify_password` pour la même opération n'est
   pas tenable à long terme.

Le choix doit être acté avant la phase 14.3 pour guider les renommages.

---

## Décision

**L'API publique de Forge 3.0 sera nommée en anglais.**

Concrètement :

1. Toutes les fonctions, classes et constantes exportées depuis les packages
   `core.*` doivent avoir des noms en anglais dans Forge 3.0.

2. Les noms de variables internes, les commentaires et la documentation
   (docs Markdown) restent en français — langue de travail de l'équipe et
   des apprenants visés par Forge.

3. Les noms de colonnes SQL générés par Forge (dans les entités applicatives)
   restent sous le contrôle du développeur. Forge ne force pas de convention
   de langue pour les colonnes SQL applicatives.

4. Les noms de clés de session (`authentifie`, `utilisateur`) sont des
   détails d'implémentation internes — leur migration fera l'objet d'un
   ticket séparé.

5. La migration effective des noms est planifiée dans `LANG-MIGRATION-001`
   (ticket #29 de la phase 14.3). Cette ADR grave la décision ; la migration
   n'est pas faite ici.

---

## Conséquences

- `LANG-MIGRATION-001` renommera les symboles publics français vers l'anglais
  dans `core/auth/`, `core/security/` et les modules concernés.
- Les aliases dépréciés (renvoyant un `DeprecationWarning`) seront maintenus
  pendant la période de transition selon la règle C de la charte.
- Les starters et la documentation seront mis à jour en parallèle.
- Les développeurs ayant du code Forge 2.x appelant les APIs françaises devront
  migrer — le guide de migration `MIGRATION-GUIDE-3.0-001` les documentera.

---

## Alternatives considérées

**Garder le français.** Abandonné : crée une friction inutile avec
l'écosystème Python standard et rend Forge non-contributable sans traduction.

**Bilingue (alias permanents).** Abandonné : viole le Principe 11 de la charte
(une seule façon officielle). Les aliases temporaires dépréciés sont acceptables
pendant la transition, mais pas comme état final.
