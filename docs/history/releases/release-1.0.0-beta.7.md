# Release — Forge 1.0.0-beta.7

**Version** : `1.0.0b7` (PEP 440) / `1.0.0-beta.7` (SemVer)
**Tag** : `v1.0.0-beta.7`
**Date** : 2026-05-22

---

## Résumé

Forge 1.0.0-beta.7 est une release axée sur la documentation pédagogique.
Le starter Welcome est entièrement refondu pour accompagner les nouveaux
utilisateurs pas à pas : diagrammes visuels des cycles MVC, code visible
par défaut, logo agrandi dans la navigation MkDocs.

Aucune rupture d'API publique. Aucune modification du runtime Forge.

---

## Nouveautés principales

### Documentation pédagogique — starter Welcome

- Refonte complète de `docs/starters/welcome/index.md` :
  - diagrammes ASCII de structure du projet ;
  - table route → méthode → template → URL ;
  - cycles MVC HTML et JSON illustrés avec Mermaid ;
  - admonitions `!!! success` et `!!! info` pour les deux cycles ;
  - ordre de lecture suggéré, limites du starter documentées.
- Vues du starter visibles par défaut (`<details open>`) : le code
  des 6 templates est affiché sans clic supplémentaire.
- Phrase de transition corrigée ("Après ces repères..." plutôt que "Avant").
- Reformulation neutre de la comparaison Symfony/Django.
- URLs neutralisées (`localhost:8000/` sans schéma http) dans le texte
  pédagogique.

### Logo MkDocs

- CSS dédié `docs/stylesheets/extra.css` : logo agrandi à 8 rem, hauteur
  du header adaptée, texte "Forge" masqué (redondant avec le logo).

---

## Tickets livrés

| Ticket | Description |
|---|---|
| DOC-PREMIER-PAS-PEDAGOGY-001 | Refonte pédagogique du starter Welcome |
| DOCS-NAV-LOGO-SIZE-001 | Agrandissement logo MkDocs |
| DOC-PREMIER-PAS-CODE-VISIBLE-001 | Vues visibles par défaut |
| DOC-PREMIER-PAS-CYCLES-TABS-VISUAL-001 | Cycles Mermaid dans les onglets |
| DOC-PREMIER-PAS-FINAL-CLEANUP-001 | Nettoyage final documentation |

---

## Non publié dans cette release

- `forge-mvc-media` — encore source-only
- `forge-mvc-mfa` — encore Pre-Alpha (SEC-MFA-SECRET-ENCRYPTION-001)
- `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats` — publication
  prévue dans PYPI-OPTINS-001
