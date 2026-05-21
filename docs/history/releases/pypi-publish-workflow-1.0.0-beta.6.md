# Publication PyPI — forge-mvc-workflow 1.0.0-beta.6

**Date** : 2026-05-21
**Ticket** : PYPI-OPTINS-002-PUBLISH-FORGE-MVC-WORKFLOW-1.0.0B6
**Statut** : **LIVRÉ**

---

## 1. Résumé

Publication de `forge-mvc-workflow==1.0.0b6` sur PyPI réalisée avec succès.
Upload effectué en une seule tentative, sans erreur HTTP 403 ni HTTP 429.
Installation vérifiée depuis un venv isolé neutre (`/tmp`).

---

## 2. Contexte

| Élément | Valeur |
|---|---|
| Déjà publié | `forge-mvc==1.0.0b6` (PYPI-PUBLISH-CORE-001) |
| Déjà publié | `forge-mvc-rbac==1.0.0b6` (PYPI-OPTINS-001-RETRY) |
| Token PyPI | account-scoped « Tous les projets » (PYPI-TOKEN-001) |

---

## 3. État Git

| Élément | Valeur |
|---|---|
| Branche | `main` |
| Commit HEAD avant publication | `bd754a0` — docs: enregistrer la publication PyPI forge-mvc-rbac 1.0.0-beta.6 |
| Tag | `v1.0.0-beta.6` ✓ |
| Copie de travail | propre (rien à valider) |

---

## 4. Vérification préalable PyPI

- `forge-mvc-workflow==1.0.0b6` existait déjà : **NON**
- Commande : `python -m pip index versions forge-mvc-workflow`
- Résultat : `ERROR: No matching distribution found for forge-mvc-workflow`
- Décision : upload autorisé

---

## 5. Build local

| Commande | Résultat |
|---|---|
| Nettoyage dist/build/egg-info | OK (shutil.rmtree) |
| `python -m build` | `Successfully built forge_mvc_workflow-1.0.0b6.tar.gz and forge_mvc_workflow-1.0.0b6-py3-none-any.whl` |
| `python -m twine check dist/*` | **PASSED** (whl + tar.gz) |

---

## 6. twine check

| Archive | Résultat |
|---|---|
| `forge_mvc_workflow-1.0.0b6-py3-none-any.whl` | **PASSED** |
| `forge_mvc_workflow-1.0.0b6.tar.gz` | **PASSED** |

---

## 7. Upload PyPI

- Commande : `python -m twine upload dist/*`
- Résultat : **succès**
- URL : https://pypi.org/project/forge-mvc-workflow/1.0.0b6/
- HTTP 403 rencontré : **NON**
- HTTP 429 rencontré : **NON**
- Nombre de tentatives upload : **1**

---

## 8. Vérification installation

Venv isolé depuis `/tmp` (répertoire neutre, sans package local sur le `sys.path`) :
`/tmp/forge-workflow-pypi-check2`

| Commande | Résultat |
|---|---|
| `pip install --pre forge-mvc==1.0.0b6` | OK |
| `pip install --pre forge-mvc-workflow==1.0.0b6` | `Successfully installed forge-mvc-workflow-1.0.0b6` |
| `import forge_mvc_workflow` | `forge_mvc_workflow import OK` |

Note : une première tentative (venv `/tmp/forge-workflow-pypi-check`) avait échoué
sur le `pip install` car PyPI n'avait pas encore indexé le package (délai de propagation
post-upload de quelques secondes à quelques minutes). L'import avait alors résolu
vers le package local (working directory = `packages/forge-mvc-workflow/`).
La seconde tentative depuis `/tmp` a confirmé l'installation réelle depuis PyPI.

---

## 9. Autres opt-ins

| Package | Statut |
|---|---|
| forge-mvc-stats | **NON publié** |
| forge-mvc-media | **NON publié** |
| forge-mvc-mfa | **NON publié** |

Aucun autre opt-in n'était dans le périmètre de ce ticket.

---

## 10. Incidents

Délai d'indexation PyPI : la première vérification d'installation a échoué car
PyPI n'avait pas encore propagé le package quelques secondes après l'upload.
La seconde vérification (depuis `/tmp`) a confirmé le succès. Pas d'impact sur
la publication elle-même.

---

## 11. Conclusion

- `forge-mvc-workflow==1.0.0b6` : **publié** sur PyPI
- `forge-mvc==1.0.0b6` : déjà publié (PYPI-PUBLISH-CORE-001)
- `forge-mvc-rbac==1.0.0b6` : déjà publié (PYPI-OPTINS-001-RETRY)
- stats / media / mfa : non publiés (hors périmètre)
- Aucun tag créé
- Aucune modification de version
- Aucune boucle d'upload (1 seule tentative)
- HTTP 429 : NON — HTTP 403 : NON

Prochain ticket recommandé : **PYPI-OPTINS-003** — Publier `forge-mvc-stats==1.0.0b6`
