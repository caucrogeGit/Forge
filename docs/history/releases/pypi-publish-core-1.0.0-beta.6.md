# Publication PyPI — forge-mvc 1.0.0-beta.6

**Date** : 2026-05-21
**Ticket** : PYPI-PUBLISH-CORE-001-PUBLISH-FORGE-MVC-1.0.0B6

---

## 1. Résumé

Publication du package core `forge-mvc==1.0.0b6` sur PyPI.
Les packages opt-ins ne sont pas publiés dans ce ticket.

---

## 2. Version publiée

| Élément | Valeur |
|---|---|
| Package | forge-mvc |
| Version PEP 440 | `1.0.0b6` |
| Version publique | `1.0.0-beta.6` |
| URL PyPI | https://pypi.org/project/forge-mvc/1.0.0b6/ |
| PyPI | **publié** |

---

## 3. État Git

| Élément | Valeur |
|---|---|
| Branche | `main` |
| Commit HEAD | `c8ce8c03a0ceaabbbb287d0d2259260fe5c34295` |
| Tag | `v1.0.0-beta.6` |
| Tag pointe sur | `c8ce8c03a0ceaabbbb287d0d2259260fe5c34295` ✓ |
| Copie de travail | propre (rien à valider) |

---

## 4. Vérification préalable PyPI

- `forge-mvc==1.0.0b6` existait déjà : **NON**
- Commande : `python -m pip index versions forge-mvc`
- Résultat : aucune distribution trouvée pour `forge-mvc` (première publication)

---

## 5. Build local

| Commande | Résultat |
|---|---|
| Nettoyage dist (b4, b5) | OK — fichiers b4/b5 supprimés |
| `python -m build` | `forge_mvc-1.0.0b6.tar.gz` et `forge_mvc-1.0.0b6-py3-none-any.whl` |

---

## 6. twine check

| Archive | Résultat |
|---|---|
| `forge_mvc-1.0.0b6-py3-none-any.whl` | PASSED |
| `forge_mvc-1.0.0b6.tar.gz` | PASSED |

---

## 7. Upload PyPI

- Commande : `python -m twine upload dist/forge_mvc-1.0.0b6*`
- Résultat : **succès**
- URL confirmée : https://pypi.org/project/forge-mvc/1.0.0b6/
- HTTP 429 rencontré : **NON**
- Nombre de tentatives upload : **1**

---

## 8. Vérification installation

- Commande : `pip install --pre forge-mvc==1.0.0b6`
- Environnement : venv isolé `/tmp/forge-pypi-check`
- `forge --version` → `Forge 1.0.0b6` ✓
- `core.__version__` → `1.0.0b6` ✓

*(Délai de propagation PyPI ~60s observé après upload — vérification réussie après attente.)*

---

## 9. Opt-ins

| Package | Statut |
|---|---|
| forge-mvc-rbac | **NON publié** — PYPI-OPTINS-001 |
| forge-mvc-workflow | **NON publié** — PYPI-OPTINS-001 |
| forge-mvc-stats | **NON publié** — PYPI-OPTINS-001 |
| forge-mvc-media | **NON publié** — PYPI-OPTINS-001 |
| forge-mvc-mfa | **NON publié** — PYPI-OPTINS-001 |

---

## 10. Incidents éventuels

- Délai de propagation PyPI : la version n'était pas immédiatement disponible après upload (~60s). Normal.
- Aucun autre incident.

---

## 11. Conclusion

`forge-mvc==1.0.0b6` est publié sur PyPI.

- Aucun tag créé dans ce ticket (tag `v1.0.0-beta.6` existait déjà).
- Aucune modification de version.
- Aucune boucle d'upload.
- Opt-ins non publiés — traités dans PYPI-OPTINS-001.
