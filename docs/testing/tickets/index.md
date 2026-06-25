# Tests terrain : Tickets détaillés

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette section regroupe les premiers tickets détaillés de la campagne de tests terrain Forge.

Ces tickets ne sont pas des tutoriels publics. Ce sont des outils de validation interne : ils guident un testeur à travers une action précise, demandent des preuves observables et un retour d'expérience structuré.

Un ticket FT validé par un testeur externe pourra ensuite être converti en tutoriel. Voir [Conversion des tickets FT en tutoriels](../field-test-to-tutorial.md).

Les retours doivent utiliser le [modèle de retour testeur](../field-test-feedback-template.md) ou le [formulaire GitHub Issue](https://github.com/caucrogeGit/Forge/issues/new?template=field-test-feedback.yml).

!!! tip "Après chaque ticket"
    Une fois un ticket FT exécuté, remplissez le formulaire de retour :

    [Soumettre un retour de test terrain →](https://github.com/caucrogeGit/Forge/issues/new?template=field-test-feedback.yml)

---

## Tickets disponibles

| Ticket | Objectif | Phase |
|---|---|---|
| [FT-00-TEST-CHARTER-001](ft-00-test-charter-001.md) | Lire et comprendre la charte de campagne | FT-00 |
| [FT-00-FEEDBACK-TEMPLATE-001](ft-00-feedback-template-001.md) | Remplir un retour d'expérience de test à blanc | FT-00 |
| [FT-00-DOC-ERROR-PROTOCOL-001](ft-00-doc-error-protocol-001.md) | Appliquer la procédure documentation officielle erronée | FT-00 |
| [FT-00-DEBUG-TOOLS-INTRO-001](ft-00-debug-tools-intro-001.md) | Découvrir les outils de diagnostic Forge | FT-00 |
| [FT-01-INSTALL-PIPX-001](ft-01-install-pipx-001.md) | Installer Forge via pipx | FT-01 |
| [FT-01-INSTALL-VERSION-CHECK-001](ft-01-install-version-check-001.md) | Vérifier la version Forge installée | FT-01 |

---

!!! tip "En cas d'échec d'un ticket"
    Avant de remplir le retour, consultez la page [Outils de diagnostic](../field-test-debug-tools.md) pour savoir quelle commande lancer et quelles preuves collecter.

---

## Envoyer un retour après un ticket

Deux options disponibles :

| Option | Lien |
|---|---|
| Formulaire GitHub Issue (recommandé) | [Soumettre un retour →](https://github.com/caucrogeGit/Forge/issues/new?template=field-test-feedback.yml) |
| Modèle Markdown à copier-coller | [Modèle de retour testeur](../field-test-feedback-template.md) |

---

## Rappel

Ces tickets font partie de la campagne de tests terrain dont la roadmap complète est dans [Roadmap, Tests terrain Forge](../../roadmap/forge-field-test-roadmap.md).

Chaque retour de ticket doit respecter la [charte de campagne](../field-test-charter.md).
