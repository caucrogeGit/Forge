# Tests terrain, Conversion des tickets FT en tutoriels

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

## 1. Objectif

Ce document définit comment transformer un ticket de test terrain validé en page de tutoriel Forge.

Le principe est :

```text
ticket FT validé
→ extraction du contenu opératoire
→ retrait des éléments internes de test
→ rédaction tutoriel
→ ajout dans docs/tutorials/
→ ajout au menu MkDocs
→ validation mkdocs build --strict
```

## 2. Ne pas publier le ticket tel quel

Un ticket FT contient des éléments internes :

- preuves à fournir ;
- gravité ;
- niveau d’aide ;
- statut ;
- notes du référent ;
- triage ;
- retour testeur.

Ces éléments ne doivent pas apparaître dans la documentation utilisateur.

## 3. Contenu à conserver

Un tutoriel peut reprendre :

- objectif ;
- contexte utile ;
- prérequis ;
- documentation liée ;
- présentation des fichiers, classes et commandes ;
- exemples indicatifs décorrélés ;
- procédure ;
- résultat attendu ;
- erreurs fréquentes ;
- vérifications.

## 4. Contenu à retirer

Retirer :

- modèle de retour d’expérience ;
- preuves obligatoires ;
- statut du ticket ;
- gravité S0 à S5 ;
- niveau d’aide A0 à A5 ;
- notes référent ;
- décisions de triage ;
- mentions de campagne terrain.

## 5. Structure conseillée d’un tutoriel

```md
# Titre du tutoriel

## Objectif

## Pré-requis

## Ce que tu vas utiliser

## Fichiers, classes ou commandes concernés

## Exemple indicatif décorrélé

## Étapes

## Vérification

## Erreurs fréquentes

## Étape suivante
```

## 6. Emplacement conseillé

```text
docs/tutorials/
```

## 7. Menu conseillé

```yaml
nav:
  - Tutoriels:
      - Vue d’ensemble: tutorials/index.md
      - Installer Forge: tutorials/01-installer-forge.md
      - Configurer l’environnement: tutorials/02-configurer-environnement.md
      - Configurer MariaDB: tutorials/03-configurer-mariadb.md
      - Créer un premier projet: tutorials/04-creer-premier-projet.md
      - Créer une première route: tutorials/05-creer-premiere-route.md
      - Utiliser Jinja: tutorials/06-utiliser-jinja.md
      - Utiliser Tailwind: tutorials/07-utiliser-tailwind.md
      - Utiliser HTMX: tutorials/08-utiliser-htmx.md
      - Utiliser Alpine.js: tutorials/09-utiliser-alpine.md
      - Créer une entité: tutorials/10-creer-entite.md
      - SQL et migrations: tutorials/11-sql-et-migrations.md
      - Générer un CRUD: tutorials/12-generer-crud.md
      - Déployer: tutorials/13-deployer.md
```

## 8. Verrou avant conversion : documentation officielle erronée

Un ticket FT ne doit pas être converti en tutoriel tant qu’une erreur de documentation officielle liée à ce ticket reste ouverte.

Avant conversion, vérifier :

- aucun retour `BLOQUÉ PAR DOCUMENTATION` non traité ;
- aucune contradiction connue entre la page tutoriel et le comportement réel ;
- les contournements temporaires ne sont pas présentés comme comportement normal ;
- les corrections documentaires issues du ticket ont été appliquées ;
- `mkdocs build --strict` passe.

Si une erreur documentaire existe encore, créer ou rattacher le ticket :

```text
DOC-FT-XX-NOM-DU-TICKET-001
```

## 9. Validation

Avant publication :

```bash
mkdocs build --strict
git diff --check
```

Si le tutoriel modifie ou ajoute des exemples exécutables, lancer aussi les validations adaptées au projet.
