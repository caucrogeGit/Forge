# Audit — PUBLICATION-2.0-VERSION-001 : Verrouillage version Forge 2.0.0

**Date :** 2026-05-09  
**Ticket :** PUBLICATION-2.0-VERSION-001  
**Statut :** VALIDÉ

---

## Objectif

Mettre à jour tous les numéros de version actifs `1.5.0` → `2.0.0` dans les fichiers sources,
documentaires et de packaging — sans écraser les mentions historiques.

---

## Fichiers mis à jour

| Fichier | Champ / Ligne | Avant | Après |
|---|---|---|---|
| `pyproject.toml` | `version` | `1.5.0` | `2.0.0` |
| `pyproject.toml` | `Development Status` | `3 - Alpha` | `4 - Beta` |
| `core/__init__.py` | `__version__` | `1.5.0` | `2.0.0` |
| `forge.py` | `_FORGE_VERSION` | `1.5.0` | `2.0.0` |
| `forge.py` | `_FORGE_DEFAULT_REF` | `v1.5.0` | `v2.0.0` |
| `package.json` | `version` | `1.5.0` | `2.0.0` |
| `README.md` | titre, git clone tag, message init | `1.5.0` | `2.0.0` |
| `docs/index.html` | badge version, titre workflow, bloc État actuel | `1.5.0` | `2.0.0` |
| `docs/reference.md` | intro, tableau CLI, ref par défaut | `1.5.0` | `2.0.0` |
| `docs/installation.md` | phrase version stable | `1.5.0` | `2.0.0` |
| `docs/guide.md` | git clone tag | `v1.5.0` | `v2.0.0` |
| `docs/installation-github.md` | git clone tag, message init | `1.5.0` / `v1.5.0` | `2.0.0` / `v2.0.0` |
| `docs/release-local.md` | nom wheel, résultat attendu, tableau récap | `1.5.0` | `2.0.0` |
| `docs/profiles.md` | exemple `--ref` | `v1.5.0` | `v2.0.0` |
| `CHANGELOG.md` | ajout section `## 2.0.0` | — | ajouté |
| `tests/test_package_metadata.py` | constante `_VERSION` | `1.5.0` | `2.0.0` |
| `tests/test_project_profiles.py` | valeurs `ref` et assertion | `v1.5.0` | `v2.0.0` |

---

## Fichiers préservés (mentions historiques)

| Fichier | Raison de la préservation |
|---|---|
| `docs/forge-roadmap.md` | Descriptions de phases, jalons `v1.5.0` tagué |
| `CHANGELOG.md` | Section `## 1.5.0` existante conservée intacte |
| `docs/relations.md` | Documentation de l'API V1, référence historique |
| `docs/audits/*.md` | Documents d'audit figés, contexte historique |

---

## Cohérence vérifiée

- `pyproject.toml`, `core/__init__.py`, `forge.py`, `package.json` : tous à `2.0.0` ✅
- `_FORGE_DEFAULT_REF` → `v2.0.0` ✅
- `tests/test_package_metadata.py::test_versions_actives_sont_alignees` valide l'alignement de ces 4 sources ✅
- `CHANGELOG.md` : section `2.0.0` présente, section `1.5.0` intacte ✅
- Classifier PyPI : `4 - Beta` ✅

---

## Verdict

**VALIDÉ.** Tous les numéros de version actifs sont verrouillés à 2.0.0.
La distinction mentions courantes / mentions historiques a été respectée.
