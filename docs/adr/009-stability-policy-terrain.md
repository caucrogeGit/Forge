# ADR-009 — Politique de stabilité : audits, bêta consolidée, tests terrain et stable

## Statut

Acceptée — Forge 1.0.0-beta.1 (ticket `ADR-009-STABILITY-POLICY-TERRAIN-001`).

---

## Date

2026-05-15

---

## Contexte

Forge 1.0.0-beta.1 est publié sur PyPI. La baseline d'audit a été figée
(`baseline/audit-2026-05-15`, commit `baba2f4`, tag `baseline/audit-2026-05-15`).
Le tracker officiel des constats d'audit existe et recense 18 constats OUVERT
et 1 constat REPORTÉ.

La question est : **à quelles conditions Forge passe-t-il en version stable ?**

Sans politique explicite, le risque est double :

1. Passer trop tôt en stable alors que des constats d'audit restent ouverts et
   qu'aucun test terrain réel n'a eu lieu.
2. Rester en bêta indéfiniment faute de critères objectifs de sortie.

Les deux situations nuisent à la crédibilité du framework. Cette ADR tranche.

---

## Décision

**Forge ne passe pas en version `1.0.0` stable uniquement parce que les audits
sont corrigés.**

La correction des constats d'audit est une condition nécessaire mais pas
suffisante. Forge 1.0.0 stable exige en plus des tests terrain réels sur une
durée minimale, une bêta consolidée, et une release candidate qui tient sans
nouveau bloquant.

---

## Trajectoire officielle

```
1.0.0-beta.1  ← point de départ (baseline/audit-2026-05-15)
1.0.0-beta.2  ← corrections post-audit (Phase 1)
1.0.0-beta.3  ← corrections post-audit (Phase 2)
1.0.0-beta.4  ← corrections post-audit (Phase 3)
1.0.0-beta.5  ← corrections post-audit (Phase 4)
1.0.0-beta.6  ← bêta consolidée = T0 tests terrain
→ tests terrain : 2 mois minimum
→ 1.0.0-beta.7, beta.8… si corrections terrain nécessaires
→ 1.0.0-rc1  ← release candidate
→ 1.0.0      ← stable
```

**`1.0.0-beta.6` marque le T0 officiel des tests terrain.** C'est la version
qui est proposée à une équipe réelle pour utilisation sur une durée minimale
de deux mois.

---

## Critères de passage en version stable

Forge 1.0.0 stable est autorisé si et seulement si **tous** les critères
suivants sont satisfaits :

1. **Tracker fermé** : tous les constats du tracker officiel
   (`docs/history/audits/findings-tracker.md`) sont en statut FERMÉ ou
   HORS PÉRIMÈTRE. Aucun constat ne reste OUVERT.

2. **Bêta consolidée publiée** : `1.0.0-beta.6` est publiée sur PyPI et
   installable proprement.

3. **Tests terrain effectués** : au moins une équipe a utilisé Forge sur un
   projet réel pendant au moins **deux mois** à partir du T0.

4. **Retours terrain traités** : tous les retours terrain identifiés comme
   bloquants ont été corrigés et documentés.

5. **Release candidate stable** : `1.0.0-rc1` a tenu **au moins deux semaines**
   sans qu'un nouveau bloquant soit identifié.

---

## Gestion des corrections terrain

Les retours terrain peuvent produire des versions supplémentaires :
`1.0.0-beta.7`, `1.0.0-beta.8`, etc.

**Si une correction terrain modifie le périmètre ou les fondamentaux de
Forge de façon significative, le T0 peut être réinitialisé** : le compteur
de deux mois repart de zéro. Cette décision est prise explicitement, en
rédigeant un complément à cette ADR.

Une correction mineure (documentation, cas limite, ergonomie) ne réinitialise
pas le T0.

---

## Ce que cette ADR interdit

- Passer en `1.0.0-rc1` tant que le tracker contient des constats OUVERT.
- Passer en `1.0.0` stable sans tests terrain d'au moins deux mois.
- Passer en `1.0.0` stable si des retours terrain bloquants ne sont pas corrigés.
- Passer en `1.0.0` stable si la RC n'a pas tenu au moins deux semaines.
- Déclarer la bêta "prête" sur la base des corrections d'audit seules,
  sans passage par `1.0.0-beta.6`.

---

## Conséquences

- Les phases de correction post-audit (Phase 1 et suivantes) produisent des
  versions `1.0.0-beta.2` à `1.0.0-beta.5`.
- `1.0.0-beta.6` est la cible de publication consolidée qui déclenche les
  tests terrain officiels.
- La progression est tracée dans `docs/roadmap/forge-roadmap.md`.
- Chaque version bêta est publiée sur PyPI avant de passer à la suivante.
- Les tests terrain et leurs retours seront documentés dans `docs/history/`.

---

## Références

- Tracker officiel des constats d'audit :
  [`docs/history/audits/findings-tracker.md`](../history/audits/findings-tracker.md)
- Baseline d'audit :
  [`docs/history/audits/audit-baseline-2026-05-15.md`](../history/audits/audit-baseline-2026-05-15.md)
- Charte philosophique v2 (principe 6 — tester avant d'élargir) :
  `CHARTE_DOC.md` à la racine du dépôt
- ADR-005 Packaging :
  [`docs/adr/005-packaging.md`](005-packaging.md)
