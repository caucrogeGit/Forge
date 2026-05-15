## Trajectoire post-consolidation Forge 2.x

Ces phases s’appliquent après la consolidation Forge 2.2.  
Elles ne remplacent pas la roadmap actuelle. Elles prolongent Forge vers une meilleure expérience développeur, une validation plus réelle, une documentation avancée et une API JSON légère.

### Phase 5 — Expérience développeur

| Ticket | Objectif |
|---|---|
| DX-DOCTOR-001 | étendre `forge doctor` aux migrations, i18n, templates et modules |
| DX-PROJECT-CHECK-001 | ajouter `forge project:check` |
| DX-ERRORS-001 | standardiser les messages d'erreur CLI |
| DX-HELP-001 | harmoniser les aides |
| DX-RECOVERY-001 | ajouter des conseils de correction dans les erreurs fréquentes |
| DX-PROJECT-AUDIT-001 | ajouter `forge project:audit` |

### Phase 6 — Tests d’intégration réels

| Ticket | Objectif |
|---|---|
| E2E-CLI-001 | cycle complet `forge new` → entité → migration → CRUD |
| E2E-NON-OVERWRITE-001 | vérifier la préservation du code utilisateur |
| E2E-STARTER-001 | génération et exécution des starters |
| E2E-MODULE-001 | installation et suppression de module dans projet généré |
| E2E-MARIADB-001 | migrations sur MariaDB réelle |
| QUALITY-COVERAGE-001 | identifier les zones non couvertes |

### Phase 7 — Sécurité approfondie

| Ticket | Objectif |
|---|---|
| SECURITY-AUDIT-001 | audit sécurité complet post-consolidation |
| SECURITY-CSRF-AUDIT-001 | vérifier CSRF sur les formulaires sensibles |
| SECURITY-COOKIES-001 | auditer les cookies de session |
| SECURITY-HEADERS-001 | auditer les pourheaders HTTP de sécurité |
| SECURITY-UPLOADS-AUDIT-001 | réauditer uploads et médias |
| SECURITY-RBAC-AUDIT-001 | vérifier cohérence RBAC / routes / templates |
| DEPLOY-PROD-SECURITY-DOC-001 | renforcer la documentation de production sécurisée |

### Phase 8 — Release et compatibilité

| Ticket | Objectif |
|---|---|
| RELEASE-POLICY-001 | définir la politique de versionnement |
| RELEASE-DEPRECATION-001 | définir la politique de dépréciation |
| RELEASE-COMPAT-001 | documenter compatibilité Python / MariaDB / Node |
| RELEASE-MIGRATION-GUIDE-001 | créer un guide de migration entre versions |
| RELEASE-LTS-001 | évaluer l’intérêt d’une version LTS |

### Phase 9 — Documentation avancée

| Ticket | Objectif |
|---|---|
| DOC-STRUCTURE-001 | organiser la documentation par parcours |
| DOC-15MIN-001 | créer un tutoriel “15 minutes avec Forge” |
| DOC-APP-COMPLETE-001 | créer un tutoriel application complète |
| DOC-MODULE-AUTHOR-001 | documenter la création d’un module |
| DOC-STARTER-AUTHOR-001 | documenter la création d’un starter |
| DOC-DEPLOY-ADVANCED-001 | documenter un déploiement propre avancé |
| DOC-CONTRIBUTE-001 | créer un guide contributeur |

### Phase 10 — API JSON légère

| Ticket | Objectif |
|---|---|
| API-JSON-001 | réponses JSON simples |
| API-CONTROLLER-001 | conventions de contrôleurs JSON |
| API-ROUTES-001 | routes API séparées |
| API-AUTH-001 | auth API minimale |
| API-DOC-001 | documentation API légère |