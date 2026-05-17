# Audit — OPTIN-PYPI-NAMES-CHECK-001

**Date** : 2026-05-17  
**Ticket** : OPTIN-PYPI-NAMES-CHECK-001  
**Phase** : 12 — Sécurité, résilience et préparation PyPI opt-ins

---

## Objectif

Vérifier et documenter l'état des noms PyPI prévus pour les packages opt-in Forge
avant toute préparation de publication. Aucune publication n'est effectuée dans ce ticket.

---

## Méthode

### Vérification PyPI

API JSON PyPI : `https://pypi.org/pypi/<package>/json`

- HTTP 404 = nom non publié (disponible)
- HTTP 200 = nom occupé (publié)

Note : l'URL web `https://pypi.org/project/<package>/` retourne HTTP 200 même pour
les packages non publiés (page de recherche PyPI). Seul l'endpoint JSON est fiable.

```bash
for pkg in forge-mvc-rbac forge-mvc-workflow forge-mvc-stats forge-mvc-media forge-mvc-mfa; do
  curl -s -o /dev/null -w "HTTP_CODE: %{http_code}\n" "https://pypi.org/pypi/$pkg/json"
done
```

```bash
python -m pip index versions <package>
# → ERROR: No matching distribution found = non publié
```

### Vérification TestPyPI

```bash
for pkg in forge-mvc-rbac forge-mvc-workflow forge-mvc-stats forge-mvc-media forge-mvc-mfa; do
  curl -s -o /dev/null -w "HTTP_CODE: %{http_code}\n" "https://test.pypi.org/pypi/$pkg/json"
done
```

---

## Packages vérifiés

| Package | Nom cible PyPI |
|---|---|
| forge-mvc-rbac | `forge-mvc-rbac` |
| forge-mvc-workflow | `forge-mvc-workflow` |
| forge-mvc-stats | `forge-mvc-stats` |
| forge-mvc-media | `forge-mvc-media` |
| forge-mvc-mfa | `forge-mvc-mfa` |

---

## Résultats PyPI

| Package | PyPI JSON API | pip index versions | Statut |
|---|---|---|---|
| `forge-mvc-rbac` | HTTP 404 | No matching distribution | **NOM_DISPONIBLE** |
| `forge-mvc-workflow` | HTTP 404 | No matching distribution | **NOM_DISPONIBLE** |
| `forge-mvc-stats` | HTTP 404 | No matching distribution | **NOM_DISPONIBLE** |
| `forge-mvc-media` | HTTP 404 | No matching distribution | **NOM_DISPONIBLE** |
| `forge-mvc-mfa` | HTTP 404 | No matching distribution | **NOM_DISPONIBLE** |

Référence : `forge-mvc` (core) → HTTP 200, version 1.0.0b4 publié (Roger Lequette).

---

## Résultats TestPyPI

| Package | TestPyPI JSON API | Statut |
|---|---|---|
| `forge-mvc-rbac` | HTTP 404 | **NOM_DISPONIBLE** |
| `forge-mvc-workflow` | HTTP 404 | **NOM_DISPONIBLE** |
| `forge-mvc-stats` | HTTP 404 | **NOM_DISPONIBLE** |
| `forge-mvc-media` | HTTP 404 | **NOM_DISPONIBLE** |
| `forge-mvc-mfa` | HTTP 404 | **NOM_DISPONIBLE** |

---

## Cohérence des métadonnées locales

| Package | Version | Development Status | Private :: Do Not Upload | Dépend de | Cohérence |
|---|---|---|---|---|---|
| `forge-mvc-rbac` | 1.0.0b4 | 4 - Beta | ✅ | forge-mvc==1.0.0b4 | ✅ OK |
| `forge-mvc-workflow` | 1.0.0b4 | 4 - Beta | ✅ | forge-mvc==1.0.0b4 | ✅ OK |
| `forge-mvc-stats` | 1.0.0b4 | 4 - Beta | ✅ | forge-mvc==1.0.0b4 | ✅ OK |
| `forge-mvc-media` | 1.0.0b4 | 2 - Pre-Alpha | ✅ | forge-mvc==1.0.0b4 | ✅ OK |
| `forge-mvc-mfa` | 1.0.0b4 | 2 - Pre-Alpha | ✅ | forge-mvc==1.0.0b4 | ✅ OK |

Tous les packages portent le classifier `Private :: Do Not Upload` — aucun ne peut
être publié accidentellement par `twine upload`.

---

## Décision par package

| Package | PyPI | TestPyPI | Décision | Motivation |
|---|---|---|---|---|
| `forge-mvc-rbac` | Disponible | Disponible | À_RÉSERVER_PLUS_TARD | Candidat beta.5 — API stable, attente publication coordonnée |
| `forge-mvc-workflow` | Disponible | Disponible | À_RÉSERVER_PLUS_TARD | Candidat beta.5 — API stable, attente publication coordonnée |
| `forge-mvc-stats` | Disponible | Disponible | À_RÉSERVER_PLUS_TARD | Candidat beta.5 — API stable, attente publication coordonnée |
| `forge-mvc-media` | Disponible | Disponible | NE_PAS_PUBLIER | Source-only, Phase 11 stabilisation récente, Pre-Alpha |
| `forge-mvc-mfa` | Disponible | Disponible | NE_PAS_PUBLIER | Pre-Alpha, SEC-MFA-SECRET-ENCRYPTION-001 requis avant publication |

---

## Risques

- Les noms sont actuellement disponibles. Aucune garantie qu'ils le restent.
- PyPI ne permet pas de réservation de noms sans publication effective.
- Une publication factice (version 0.0.1 vide) pour réserver le nom est possible
  mais non recommandée — elle crée des attentes et des dépendances indésirables.
- La dépendance `forge-mvc==1.0.0b4` dans les opt-ins devra être relaxée lors de
  la publication (ex : `forge-mvc>=1.0.0b4,<2`).

---

## Recommandations

1. **rbac / workflow / stats** : préparer la publication coordonnée dans `OPTIN-PYPI-PUBLISH-PREPARE-001`.
   Retirer `Private :: Do Not Upload` et mettre à jour les dépendances juste avant publication.

2. **forge-mvc-mfa** : ne pas publier tant que `SEC-MFA-SECRET-ENCRYPTION-001` n'est pas livré.
   Le stockage du secret TOTP en clair constitue un risque de sécurité inacceptable pour une
   distribution publique.

3. **forge-mvc-media** : ne pas publier. Phase 11 récente (2026-05-17), stabilisation nécessaire.
   Réévaluer après une période d'usage interne.

4. Tous les packages portent déjà `Private :: Do Not Upload` — le risque de publication
   accidentelle est mitigé.

---

## Tickets futurs suggérés

- `OPTIN-PYPI-PUBLISH-PREPARE-001` : préparer la publication de rbac/workflow/stats.
- `SEC-MFA-SECRET-ENCRYPTION-001` : durcir le stockage des secrets MFA avant publication.
- `OPTIN-PYPI-MFA-PUBLICATION-001` : publication forge-mvc-mfa après durcissement.
- `OPTIN-PYPI-MEDIA-EVALUATION-001` : réévaluer forge-mvc-media après stabilisation.

---

## Conclusion

Tous les 5 noms PyPI ciblés (`forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`,
`forge-mvc-media`, `forge-mvc-mfa`) sont disponibles sur PyPI et TestPyPI au 2026-05-17.

Aucune publication n'est effectuée dans ce ticket. Les décisions par package sont
documentées et reflétées dans la roadmap. Le ticket OPTIN-PYPI-NAMES-CHECK-001 est livré.
