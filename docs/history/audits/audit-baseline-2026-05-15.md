# Baseline d'audit — Forge 1.0.0-beta.1

**Ticket** : `AUDIT-BASELINE-LOCK-001`  
**Date de baseline** : 2026-05-15  
**Version de départ** : `1.0.0-beta.1`  
**Branche de départ** : `main`  
**Commit de départ** : `d611636ae6addebcfa7cb075c3c75714e7aae3a2`  
**Tag non-release attendu** : `baseline/audit-2026-05-15`

---

## Rôle de cette baseline

Ce document fige le point de référence officiel avant toute correction
post-audits sur Forge 1.0.0-beta.1.

Il permet de :

- identifier sans ambiguïté l'état Git de départ ;
- lister les audits qui servent de base aux constats à solder ;
- tracer la frontière entre l'état pré-correction et les tickets de
  consolidation à venir.

**Ce document ne corrige aucun constat.** Les corrections commencent
uniquement après la Phase 0 — Baseline d'audit.

---

## Audits de référence

Les deux audits suivants servent de base aux constats à solder :

### 1. Audit complet Forge MVC 2.0.0 — `audit-claude.md`

| Champ | Valeur |
|---|---|
| Auditeur | Claude (Sonnet 4.5 / Opus 4.7) |
| Date | 2026-05-09 |
| Version auditée | Forge 2.0.0 (branche `main`, commit `435ffa9`) |
| Périmètre | Architecture, sécurité, tests, CLI, documentation |
| Fichier | [`docs/history/audits/audit-claude.md`](audit-claude.md) |

**Constats principaux identifiés** :

- coexistence de deux piles d'authentification (`core/security/` legacy et `core/auth/` moderne) ;
- paramètre de hachage PBKDF2 sous-dimensionné par rapport à OWASP ;
- incohérence entre starters et application par défaut (authentifications silencieusement incorrectes) ;
- génération CRUD potentiellement vulnérable à l'injection SQL dans le mécanisme de filtres.

### 2. Audit renforcé Forge 3.0.2 — `audit-renforce-3.0.2-001.md`

| Champ | Valeur |
|---|---|
| Date | 2026-05-13 |
| Version auditée | Forge 3.0.2 (tag `v3.0.2`) |
| Périmètre | Environnement core-only, API docs, versions, angles morts, CLI, packaging |
| Suite de tests | 9 651 passés, 2 skippés |
| Fichier | [`docs/history/audits/audit-renforce-3.0.2-001.md`](audit-renforce-3.0.2-001.md) |

**Constats principaux identifiés** :

- `pytest` en environnement core-only (`requirements.txt` seul) produit 30 erreurs de collecte (exit 2) — les tests opt-in importent sans garde `pytest.importorskip` ;
- plusieurs imports documentés dans l'API reference retournent `ImportError` ;
- anomalies de cohérence de versioning entre `pyproject.toml`, `__version__` et les starters générés.

---

## État du dépôt au point de baseline

```
Branche  : main
Commit   : d611636ae6addebcfa7cb075c3c75714e7aae3a2
Message  : docs: update PyPI installation after beta publication
Version  : 1.0.0b1 (pyproject.toml)
Tag PyPI : v1.0.0-beta.1
```

Dernière validation connue (PYPI-PUBLISH-CORE-3.0.5-001) :

- `pytest` : **9 693 passed**
- `python -m compileall -q .` : **OK**
- `mkdocs build --strict` : **OK**
- `git diff --check` : **OK**

---

## Règle de stabilité

Aucune correction de constat d'audit ne sera appliquée avant que :

1. ce document soit commité sur `main` ;
2. le tag non-release `baseline/audit-2026-05-15` soit créé et poussé ;
3. le tracker détaillé des constats (ticket `AUDIT-FINDINGS-TRACKER-001`) soit établi.

Cette règle est conforme à la politique Forge : *ne pas mélanger audit,
correction, refonte et publication*.

---

## Tag non-release

Le tag associé à cette baseline est :

```
baseline/audit-2026-05-15
```

Il est créé avec :

```bash
git tag -a baseline/audit-2026-05-15 -m "Audit baseline before post-audit consolidation"
git push origin baseline/audit-2026-05-15
```

Ce tag n'est pas une version de release. Il sert uniquement de point de repère
pour la Phase 0 de consolidation post-audits.

---

## Limites de ce document

- Ce document ne crée pas encore le tracker détaillé des constats
  (ticket suivant : `AUDIT-FINDINGS-TRACKER-001`).
- Ce document ne corrige aucun constat d'audit.
- Les corrections commencent uniquement après validation complète de la Phase 0.
