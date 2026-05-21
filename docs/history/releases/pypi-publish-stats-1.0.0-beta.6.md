# Publication PyPI — forge-mvc-stats 1.0.0-beta.6

**Date** : 2026-05-21
**Ticket** : PYPI-OPTINS-003-PUBLISH-FORGE-MVC-STATS-1.0.0B6
**Statut** : **ARRÊT CONTRÔLÉ — HTTP 429 TOO MANY REQUESTS**

---

## 1. Résumé

Tentative de publication de `forge-mvc-stats==1.0.0b6` sur PyPI.
Upload bloqué par HTTP 429 Too Many Requests.

Arrêt immédiat conformément à la règle d'arrêt. Aucune relance. Aucun autre
opt-in tenté.

Le package est correctement buildé et twine check est PASSED. La publication
peut être relancée dans un ticket dédié, après un délai suffisant.

---

## 2. Contexte

| Élément | Valeur |
|---|---|
| Déjà publié | `forge-mvc==1.0.0b6` (PYPI-PUBLISH-CORE-001) |
| Déjà publié | `forge-mvc-rbac==1.0.0b6` (PYPI-OPTINS-001-RETRY) |
| Déjà publié | `forge-mvc-workflow==1.0.0b6` (PYPI-OPTINS-002) |
| Cause probable du 429 | Trop de publications rapprochées sur le même compte PyPI |

---

## 3. État Git

| Élément | Valeur |
|---|---|
| Branche | `main` |
| Commit HEAD | `22316b6` — docs: enregistrer la publication PyPI forge-mvc-workflow 1.0.0-beta.6 |
| Tag | `v1.0.0-beta.6` ✓ |
| Copie de travail | propre (rien à valider) |

---

## 4. Vérification préalable PyPI

- `forge-mvc-stats==1.0.0b6` existait déjà : **NON**
- Commande : `python -m pip index versions forge-mvc-stats`
- Résultat : `ERROR: No matching distribution found for forge-mvc-stats`
- Décision : upload autorisé

---

## 5. Build local

| Commande | Résultat |
|---|---|
| Nettoyage dist/build/egg-info | OK (shutil.rmtree) |
| `python -m build` | `Successfully built forge_mvc_stats-1.0.0b6.tar.gz and forge_mvc_stats-1.0.0b6-py3-none-any.whl` |
| `python -m twine check dist/*` | **PASSED** (whl + tar.gz) |

---

## 6. twine check

| Archive | Résultat |
|---|---|
| `forge_mvc_stats-1.0.0b6-py3-none-any.whl` | **PASSED** |
| `forge_mvc_stats-1.0.0b6.tar.gz` | **PASSED** |

---

## 7. Upload PyPI

- Commande : `python -m twine upload dist/*`
- Résultat : **ÉCHEC — HTTP 429 Too Many Requests**
- HTTP 403 rencontré : **NON**
- HTTP 429 rencontré : **OUI**
- Nombre de tentatives upload : **1** (arrêt immédiat, aucune relance)

**Erreur exacte :**

```
ERROR HTTPError: 429 Too Many Requests from https://upload.pypi.org/legacy/
Too Many Requests
```

**Cause probable** : PyPI applique un rate-limit sur les uploads rapprochés.
Trois publications ont été effectuées dans la même session (forge-mvc-rbac,
forge-mvc-workflow, forge-mvc-stats), ce qui a déclenché le throttling.

**Action requise** : attendre un délai suffisant (quelques heures) avant de
relancer la publication de `forge-mvc-stats==1.0.0b6` dans un ticket dédié.

---

## 8. Vérification installation

Non effectuée — upload échoué.

---

## 9. Autres opt-ins

| Package | Statut |
|---|---|
| forge-mvc-media | **NON publié** |
| forge-mvc-mfa | **NON publié** |

Aucun autre opt-in tenté dans ce ticket, conformément à la règle d'arrêt.

---

## 10. Incidents

**HTTP 429 — Rate limit PyPI**

PyPI a retourné 429 Too Many Requests lors de l'upload de `forge-mvc-stats`.
Arrêt immédiat, aucune relance. Les artefacts buildés (`dist/`) sont conservés
pour le prochain ticket — ils n'ont pas besoin d'être rebuildés si aucune
modification de code n'intervient d'ici là.

---

## 11. Conclusion

- `forge-mvc-stats==1.0.0b6` : **non publié** — HTTP 429 rate limit
- `forge-mvc==1.0.0b6` : déjà publié (PYPI-PUBLISH-CORE-001)
- `forge-mvc-rbac==1.0.0b6` : déjà publié (PYPI-OPTINS-001-RETRY)
- `forge-mvc-workflow==1.0.0b6` : déjà publié (PYPI-OPTINS-002)
- media / mfa : non tentés (hors périmètre)
- Aucun tag créé
- Aucune modification de version
- Aucune boucle d'upload (1 seule tentative)
- HTTP 403 : NON — HTTP 429 : **OUI**

Prochain ticket recommandé : **PYPI-OPTINS-003-RETRY** — Relancer la publication
de `forge-mvc-stats==1.0.0b6` après un délai suffisant (recommandé : plusieurs
heures ou le lendemain).
