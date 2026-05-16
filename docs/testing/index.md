# Tests terrain Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette section regroupe les documents de pilotage de la campagne de tests terrain progressive de Forge.

La campagne ne cherche pas à ajouter de nouvelles fonctionnalités. Elle cherche à répondre à une question simple :

> Un développeur qui ne connaît pas Forge peut-il l'installer, le comprendre, l'utiliser, diagnostiquer ses erreurs, construire une application et la maintenir ?

---

## Principe central

Cette campagne ne sert pas à développer Forge. Elle sert à vérifier que Forge peut être installé, compris, utilisé, maintenu et déployé par des utilisateurs réels.

Un ticket terrain `FT-*` ne corrige pas le framework. Il produit un retour reproductible, des preuves, un verdict et, si nécessaire, une proposition de ticket correctif séparé.

```text
ticket FT rédigé
→ test terrain
→ retour terrain
→ correction éventuelle
→ ticket validé
→ conversion en tutoriel
→ ajout au menu Tutoriels
```

Un ticket FT reste un outil de validation interne. Un tutoriel Forge est sa version nettoyée, publiée seulement après validation terrain.

---

## Documentation officielle erronée pendant un ticket

La documentation officielle fait partie de ce qui est testé. Si elle est fausse, incomplète ou contradictoire, le testeur ne corrige pas directement. Il documente l'écart, fournit les preuves, classe la gravité et met le statut adapté.

```text
BLOQUÉ PAR DOCUMENTATION
VALIDÉ AVEC FRICTION
```

Le référent Forge transforme ensuite le retour en ticket documentaire séparé (`DOC-FT-XX-...`).

---

!!! tip "Envoyer un retour de test terrain"
    Après avoir exécuté un ticket FT, utilisez le formulaire GitHub Issue pour transmettre un retour structuré.

    [Soumettre un retour de test terrain →](https://github.com/caucrogeGit/Forge/issues/new?template=field-test-feedback.yml)

---

## Documents de la campagne

| Document | Rôle |
|---|---|
| [État des parcours](field-test-status.md) | Matrice de suivi : quels parcours sont prêts, en test, validés |
| [Roadmap des tests terrain](../roadmap/forge-field-test-roadmap.md) | Phases et tickets FT-* progressifs (vue complète) |
| [Charte de campagne](field-test-charter.md) | Règles, niveaux de guidage, gravité, statuts, gestion des écarts |
| [Modèle de ticket FT](field-test-ticket-template.md) | Structure obligatoire d'un ticket terrain exploitable |
| [Modèle de retour testeur](field-test-feedback-template.md) | Formulaire à remplir après chaque ticket FT-* |
| [Formulaire GitHub Issue](https://github.com/caucrogeGit/Forge/issues/new?template=field-test-feedback.yml) | Soumettre un retour directement sur GitHub (recommandé) |
| [Triage et stabilisation](field-test-triage.md) | Grille de décision bêta / stable |
| [Conversion en tutoriel](field-test-to-tutorial.md) | Règles de transformation d'un ticket FT validé en tutoriel |
