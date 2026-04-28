# Changelog

## [1.0.1] - Stabilisation

### Corrigé
- Alignement de la version Forge en 1.0.1.
- Inclusion complète des fichiers starters dans le package Python.
- Correction de la gestion des fichiers statiques pour éviter une erreur 500 sur `/static/`.
- Sécurisation de `forge new` : un échec du commit Git initial ne supprime plus le projet généré.
- Nettoyage de l'incohérence entre le layout Jinja réel et la documentation.

### Documentation
- Clarification de l'usage du layout Jinja.
- Mise à jour des références de version.

## 1.0.0

Version initiale stable de Forge.

Fonctionnalités principales :
- framework Python MVC minimal
- routeur HTTP
- contrôleurs / vues / modèles
- entités JSON canoniques
- génération SQL visible
- génération de CRUD
- sessions
- CSRF
- erreurs HTTP propres
- upload local sécurisé
- déploiement minimal guidé
- starter-apps
- documentation MkDocs avec recherche
