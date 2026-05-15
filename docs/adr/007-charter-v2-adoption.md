# ADR-007 — Adoption formelle de la charte philosophique v2

## Statut

Acceptée

---

## Contexte

Forge a fonctionné depuis ses origines avec un ensemble de principes implicites
et une charte documentaire (v1) qui définissait les conventions de rédaction de
la documentation.

L'audit de la phase 14 a révélé plusieurs tensions dans le code :

- Des modules avancés (`core/auth/mfa.py`, `core/workflow/`, `core/stats/`)
  hébergés dans le `core/` alors qu'ils relèvent de modules optionnels.
- Une API publique exposant du code expérimental ou partiel (OIDC).
- Deux façons parallèles de faire la même chose (API française legacy,
  API anglaise moderne) sans cadre de décision explicite.
- Des exceptions avalées silencieusement (`try: log_auth_event(...) except: pass`)
  masquant des problèmes observables.
- L'absence de règles d'évolution écrites, rendant les décisions
  architecturales implicites et non opposables.

Ces tensions ont été résolues par les tickets de la phase 14.1, mais sans
cadre philosophique formalisé pour les guider. La charte v2 fournit ce cadre.

---

## Décision

**La charte philosophique v2 est adoptée formellement comme document de
référence de Forge.**

Elle remplace la charte documentaire v1 (qui définissait les conventions de
rédaction) et étend son périmètre à l'ensemble des décisions d'architecture,
de développement et d'évolution du framework.

La charte v2 ajoute par rapport à la v1 :

- **Principe 8** — Noyau minimal, briques opt-in
- **Principe 9** — Pas d'écriture invisible dans le code utilisateur
- **Principe 10** — Une API publique est un contrat de complétude
- **Principe 11** — Une seule façon officielle de faire chaque chose
- **Règles d'évolution A-D** — cadre explicite pour gérer les changements
- **Périmètre du noyau** — définition canonique de ce qui appartient à `core/`
- **Formule de décision finale** — critère opérationnel pour évaluer toute
  proposition

La charte v2 est publiée dans `CHARTE_DOC.md` à la racine du dépôt.
La charte v1 est archivée dans `docs/history/charte-v1.md`.

Toute décision future — ticket, PR, refactoring, extraction de module — doit
pouvoir s'appuyer sur un ou plusieurs principes de la charte v2.

---

## Conséquences

- Les ADR 003 à 006 (langue, périmètre, packaging, Python) s'appuient sur
  la charte v2 pour leur justification.
- Les tickets de la phase 14.3 (reconstruction) se réfèrent explicitement
  aux principes de la charte.
- Le test garde-fou `tests/test_charter_v2_adoption_001.py` vérifie la
  présence et la cohérence des documents fondateurs.
- Les contributeurs futurs sont invités à lire la charte avant de soumettre
  une PR.

---

## Ce que cette ADR ne fait pas

- N'applique pas les décisions des autres ADR (003-006) — ce sont des tickets
  de la phase 14.3.
- Ne supprime pas la charte v1 — elle est archivée, pas effacée.
- Ne définit pas de processus d'amendement de la charte — les amendements
  futurs feront l'objet de nouvelles ADR.
