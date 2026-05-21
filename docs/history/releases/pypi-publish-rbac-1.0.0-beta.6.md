# Publication PyPI — forge-mvc-rbac 1.0.0-beta.6

**Date** : 2026-05-21
**Ticket** : PYPI-OPTINS-001-PUBLISH-FORGE-MVC-RBAC-1.0.0B6
**Statut** : **ARRÊT CONTRÔLÉ — TOKEN INSUFFISANT**

---

## 1. Résumé

Tentative de publication de `forge-mvc-rbac==1.0.0b6` sur PyPI.
Upload bloqué par HTTP 403 : le token API configuré est scopé au seul projet
`forge-mvc` et ne dispose pas des droits pour `forge-mvc-rbac`.

**Aucune publication effective. Aucune boucle d'upload. Aucune autre opt-in tentée.**

---

## 2. Version publiée

| Élément | Valeur |
|---|---|
| Package | forge-mvc-rbac |
| Version PEP 440 | `1.0.0b6` |
| Version publique | `1.0.0-beta.6` |
| PyPI | **NON publié** — arrêt sur 403 |

---

## 3. État Git

| Élément | Valeur |
|---|---|
| Branche | `main` |
| Commit HEAD | `ea663fe` |
| Tag | `v1.0.0-beta.6` ✓ |
| Copie de travail | propre (rien à valider) |

---

## 4. Vérification préalable PyPI

- `forge-mvc-rbac==1.0.0b6` existait déjà : **NON**
- Commande : `python -m pip install --no-cache-dir --pre forge-mvc-rbac==1.0.0b6 --dry-run`
- Résultat : `Could not find a version that satisfies the requirement forge-mvc-rbac==1.0.0b6 (from versions: none)`

---

## 5. Build local

| Commande | Résultat |
|---|---|
| Nettoyage dist (b4, b5) | OK |
| `python -m build` | `forge_mvc_rbac-1.0.0b6.tar.gz` + `.whl` ✓ |

---

## 6. twine check

| Archive | Résultat |
|---|---|
| `forge_mvc_rbac-1.0.0b6-py3-none-any.whl` | **PASSED** |
| `forge_mvc_rbac-1.0.0b6.tar.gz` | **PASSED** |

---

## 7. Upload PyPI

- Commande : `python -m twine upload forge_mvc_rbac-1.0.0b6-py3-none-any.whl forge_mvc_rbac-1.0.0b6.tar.gz`
- Résultat : **ÉCHEC — HTTP 403 Forbidden**
- HTTP 429 rencontré : **NON**
- Nombre de tentatives upload : **1** (arrêt immédiat après l'échec)

**Erreur exacte (extrait verbose) :**

```
403 Invalid API Token: project-scoped token is not valid for project:
'forge-mvc-rbac', project-scoped token is not valid for project: 'forge-mvc-rbac'
```

**Cause** : le token API dans `~/.pypirc` est scopé au projet `forge-mvc` uniquement.
Il n'a pas les droits pour publier un nouveau projet `forge-mvc-rbac`.

**Action requise** : créer sur PyPI un nouveau token API avec l'un des scopes suivants :

- **Option A (recommandée)** : token **account-scoped** (`Entire account`) couvrant
  tous les projets `forge-mvc-*` à publier.
- **Option B** : token project-scoped pour `forge-mvc-rbac` — mais il faut d'abord
  que le projet existe sur PyPI (premier upload depuis l'interface ou avec un token
  account-scoped).

Procédure : https://pypi.org/manage/account/token/

---

## 8. Vérification installation

Non effectuée — upload échoué.

---

## 9. Autres opt-ins

Aucun opt-in tenté dans ce ticket, conformément à la règle d'arrêt.

| Package | Statut |
|---|---|
| forge-mvc-workflow | **NON publié** |
| forge-mvc-stats | **NON publié** |
| forge-mvc-media | **NON publié** |
| forge-mvc-mfa | **NON publié** |

---

## 10. Incidents éventuels

**HTTP 403 — Token project-scoped insuffisant**

Le token configuré dans `~/.pypirc` a été créé avec le scope `forge-mvc`
(projet unique). PyPI refuse l'upload pour tout autre nom de projet, même
appartenant au même compte.

Ce blocage est attendu et documenté. Il n'y a pas de bug dans le package.

---

## 11. Prochain ticket recommandé

**PYPI-TOKEN-OPTINS-001** — Créer un token PyPI account-scoped (ou des tokens
project-scoped par opt-in) et relancer la publication des opt-ins.

Après résolution du token, reprendre avec :
- PYPI-OPTINS-001 (rbac) — à relancer
- PYPI-OPTINS-002 (workflow)
- PYPI-OPTINS-003 (stats)

---

## 12. Conclusion

Ticket arrêté proprement après HTTP 403 conformément à la règle d'arrêt.

- `forge-mvc-rbac` : **non publié** — token insuffisant
- `forge-mvc` core : déjà publié (ticket PYPI-PUBLISH-CORE-001)
- Aucun tag créé
- Aucune modification de version
- Aucune boucle d'upload (1 seule tentative)
- opt-ins workflow/stats/media/mfa : non tentés
