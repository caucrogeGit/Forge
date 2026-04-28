# Génération PDF

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Forge propose une commande optionnelle pour générer un PDF de sa documentation.
Cette fonctionnalité repose sur [Quarkdown](https://quarkdown.com/), un outil externe indépendant du cœur du framework.

---

## Objectif V1

Produire un PDF de la documentation Forge à partir des fichiers Markdown existants, sans modifier le moteur applicatif ni les starters.

---

## Documentation PDF vs PDF applicatif

| | Documentation PDF | PDF applicatif (V2) |
|---|---|---|
| **Source** | Fichiers `docs/*.md` | Templates Jinja2 applicatifs |
| **Déclencheur** | Commande CLI `forge docs:pdf` | Requête HTTP dans un contrôleur |
| **Destinataire** | Développeur du framework | Utilisateur final de l'application |
| **Exemples** | Guide, référence, roadmap | Facture, devis, fiche élève |
| **Disponibilité** | V1 (optionnel) | V2 (pas encore implémenté) |

---

## Prérequis — Quarkdown

Quarkdown est un système de typesetting moderne basé sur Markdown. Il requiert **Java 17+**.

### Installation

```bash
# Linux / macOS
curl -fsSL https://raw.githubusercontent.com/quarkdown-labs/get-quarkdown/refs/heads/main/install.sh \
  | sudo env "PATH=$PATH" bash

# Homebrew
brew install quarkdown
```

Vérifier l'installation :

```bash
quarkdown --version
```

Quarkdown n'est **pas** une dépendance de Forge. Le framework fonctionne entièrement sans lui.

---

## Utilisation

Depuis la racine du dépôt Forge :

```bash
forge docs:pdf
```

La commande :

1. vérifie que Quarkdown est installé ;
2. lit le fichier source `docs/quarkdown/forge-documentation.qd` ;
3. génère `build/docs/forge-documentation.pdf`.

---

## Structure des fichiers

```
docs/
  quarkdown/
    forge-documentation.qd   ← fichier source Quarkdown (agrégation)
build/
  docs/
    forge-documentation.pdf  ← PDF généré (ignoré par git)
```

Le fichier `.qd` est versionné. Le PDF généré ne l'est pas.

---

## Personnaliser le contenu du PDF

Éditer `docs/quarkdown/forge-documentation.qd` pour inclure ou exclure des pages :

```
.include {../guide.md}
.include {../installation.md}
```

Les commentaires Quarkdown utilisent la syntaxe `{{ texte commenté }}`.

---

## Limites V1

- Les extensions MkDocs Material (admonitions `!!! note`, onglets `=== "Tab"`, blocs `<details>`) ne sont pas rendues par Quarkdown — elles apparaissent comme texte brut dans le PDF.
- Les pages avec beaucoup de ces extensions (reference.md, starter-app-*.md) sont désactivées par défaut dans `forge-documentation.qd`.
- Le rendu graphique dépend du thème Quarkdown configuré.
- L'emplacement exact du fichier PDF généré peut varier selon la version de Quarkdown.

---

## PDF applicatif — V2

La génération de PDF depuis une application Forge (factures, fiches, rapports) est prévue en V2, indépendamment de cette fonctionnalité :

- module `core/pdf/` dédié ;
- templates Jinja2 adaptés au rendu imprimable ;
- fonction `render_pdf()` ;
- réponse HTTP avec `Content-Type: application/pdf`.

Cette V2 ne fait pas partie de Forge 1.0.x.
