# Publication PyPI — forge-mvc-rbac 1.0.0-beta.6

**Date** : 2026-05-21
**Ticket** : PYPI-OPTINS-001-RETRY-PUBLISH-FORGE-MVC-RBAC-1.0.0B6
**Statut** : **LIVRÉ**

---

## 1. Résumé

Publication de `forge-mvc-rbac==1.0.0b6` sur PyPI réalisée avec succès.
Upload effectué en une seule tentative, sans erreur HTTP 403 ni HTTP 429.

Contexte : la tentative précédente (PYPI-OPTINS-001) avait échoué sur HTTP 403
car le token PyPI était limité au projet `forge-mvc`. Un nouveau token
« Tous les projets » a été créé et configuré dans `~/.pypirc` (PYPI-TOKEN-001).

---

## 2. Contexte

| Élément | Valeur |
|---|---|
| Ticket précédent | PYPI-OPTINS-001 — arrêt HTTP 403 |
| Correction appliquée | PYPI-TOKEN-001 — nouveau token account-scoped |
| Core déjà publié | `forge-mvc==1.0.0b6` (PYPI-PUBLISH-CORE-001) |

---

## 3. État Git

| Élément | Valeur |
|---|---|
| Branche | `main` |
| Commit HEAD avant publication | `c701150` — docs: record PyPI token setup for opt-ins |
| Tag | `v1.0.0-beta.6` ✓ |
| Copie de travail | propre (rien à valider) |

---

## 4. Vérification préalable PyPI

- `forge-mvc-rbac==1.0.0b6` existait déjà : **NON**
- Commande : `python -m pip index versions forge-mvc-rbac`
- Résultat : `ERROR: No matching distribution found for forge-mvc-rbac`
- Décision : upload autorisé

---

## 5. Build local

| Commande | Résultat |
|---|---|
| Nettoyage dist/build/egg-info | OK (shutil.rmtree) |
| `python -m build` | `Successfully built forge_mvc_rbac-1.0.0b6.tar.gz and forge_mvc_rbac-1.0.0b6-py3-none-any.whl` |
| `python -m twine check dist/*` | **PASSED** (whl + tar.gz) |

---

## 6. twine check

| Archive | Résultat |
|---|---|
| `forge_mvc_rbac-1.0.0b6-py3-none-any.whl` | **PASSED** |
| `forge_mvc_rbac-1.0.0b6.tar.gz` | **PASSED** |

---

## 7. Upload PyPI

- Commande : `python -m twine upload dist/*`
- Résultat : **succès**
- URL : https://pypi.org/project/forge-mvc-rbac/1.0.0b6/
- HTTP 403 rencontré : **NON**
- HTTP 429 rencontré : **NON**
- Nombre de tentatives upload : **1**

---

## 8. Vérification installation

Venv isolé : `/tmp/forge-rbac-pypi-check`

| Commande | Résultat |
|---|---|
| `pip install --pre forge-mvc==1.0.0b6` | OK |
| `pip install --pre forge-mvc-rbac==1.0.0b6` | OK |
| `import forge_mvc_rbac` | `forge_mvc_rbac import OK` |
| `from forge_mvc_rbac import has_permission, require_permission` | `RBAC public imports OK` |

---

## 9. Autres opt-ins

| Package | Statut |
|---|---|
| forge-mvc-workflow | **NON publié** |
| forge-mvc-stats | **NON publié** |
| forge-mvc-media | **NON publié** |
| forge-mvc-mfa | **NON publié** |

Aucun autre opt-in n'était dans le périmètre de ce ticket.

---

## 10. Incidents

Aucun incident. Le token « Tous les projets » (PYPI-TOKEN-001) a fonctionné
correctement dès la première tentative.

---

## 11. Prochain ticket recommandé

**PYPI-OPTINS-002** — Publier `forge-mvc-workflow==1.0.0b6`

---

## 12. Conclusion

Ticket considéré comme terminé parce que :

- `forge-mvc-rbac==1.0.0b6` est publié sur PyPI
- L'installation depuis PyPI est vérifiée dans un venv isolé
- Les imports publics (`has_permission`, `require_permission`) fonctionnent
- Aucun tag créé
- Aucune modification de version
- Aucune boucle d'upload (1 seule tentative)
- HTTP 429 : NON — HTTP 403 : NON
- `forge-mvc` core : déjà publié (PYPI-PUBLISH-CORE-001)
- opt-ins workflow/stats/media/mfa : non tentés (hors périmètre)
