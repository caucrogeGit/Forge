# Audit : portabilité du DDL livré par les opt-ins

**Ticket** : `OPTIN-DDL-DIALECT-AUDIT-001`
**Date** : 2026-07-27
**Auteur** : Forge (audit pré-implémentation, mesure sur serveurs réels)
**Périmètre** : tous les fichiers `.sql` livrés par `packages/`, plus les constantes `CREATE TABLE` en Python

---

## 1. Résumé

L'ADR-084 déclare les quatre backends BDD au niveau plein.
Le contrat est effectivement tenu par la couche d'accès aux données : les quatre backends implémentent **28 méthodes de dialecte sur 28** et **4 méthodes de backend sur 4**, chacune définie par eux-mêmes, aucune manquante.
Le cœur ne contient plus aucun SQL spécifique à un SGBD.

Mais **dix opt-ins contournent entièrement le dialecte** en livrant du SQL MariaDB écrit à la main.

Mesuré en exécution contre quatre serveurs réels : **douze fichiers SQL audités, zéro portable sur les quatre moteurs.**

| Moteur | Fichiers acceptés |
|---|---|
| MariaDB 10.x | 11 sur 12 |
| SQLite | **0 sur 12** |
| PostgreSQL 17.10 | **0 sur 12** |
| SQL Server 2022 | **0 sur 12** |

Ces dix opt-ins ne sont donc installables que sur MariaDB, ce que ni leur documentation ni leurs classifieurs PyPI n'indiquent.

Aucun correctif n'est appliqué dans ce ticket.

---

## 2. Méthode

Chaque fichier `.sql` livré sous `packages/` est découpé par `split_sql_statements` (le découpeur canonique du cœur, ADR-079), puis exécuté instruction par instruction contre les quatre moteurs, dans une base jetable créée et supprimée pour chaque fichier.

Une table `users(id)` est créée au préalable dans chaque base jetable : `forge-mvc-mfa` et `forge-mvc-rbac` y font référence par clé étrangère, et sans elle l'échec mesurerait l'absence du prérequis plutôt que la portabilité du dialecte.

Deux défauts de la sonde ont été corrigés avant de retenir les résultats.
D'abord, pyodbc met les connexions en pool : `close()` ne libère pas la base et le `DROP DATABASE` suivant échouait, si bien que SQL Server n'était pas mesuré du tout.
Ensuite, l'absence de la table `users` produisait des échecs MariaDB trompeurs sur `mfa` et `rbac`.

---

## 3. Résultats détaillés

| Opt-in | Fichier | MariaDB | SQLite | PostgreSQL | SQL Server |
|---|---|---|---|---|---|
| `forge-mvc-audit` | `create_audit_log.sql` | OK | échec | échec | échec |
| `forge-mvc-images` | `create_media.sql` | OK | échec | échec | échec |
| `forge-mvc-iot` | `create_iot_events.sql` | OK | échec | échec | échec |
| `forge-mvc-jobs` | `create_jobs.sql` | OK | échec | échec | échec |
| `forge-mvc-mfa` | `auth_mfa_factors.sql` | OK | échec | échec | échec |
| `forge-mvc-mfa` | `auth_mfa_recovery_codes.sql` | OK | échec | échec | échec |
| `forge-mvc-notifications` | `create_notifications.sql` | OK | échec | échec | échec |
| `forge-mvc-rbac` | `rbac.sql` | OK | échec | échec | échec |
| `forge-mvc-rbac` | `user_roles.sql` | échec | échec | échec | échec |
| `forge-mvc-sessions-db` | `create_forge_sessions.sql` | OK | échec | échec | échec |
| `forge-mvc-settings` | `create_app_settings.sql` | OK | échec | échec | échec |
| `forge-mvc-video` | `create_videos.sql` | OK | échec | échec | échec |

L'unique échec MariaDB, `user_roles.sql`, n'est pas un défaut de dialecte : le fichier référence la table `roles` créée par `rbac.sql`, donc il dépend d'un ordre d'application entre fichiers du même paquet.
Ce point mérite d'être noté séparément, il concerne l'ordonnancement des migrations et non la portabilité.

---

## 4. Causes, par famille

Quatre constructions MariaDB expliquent la totalité des échecs.

| Construction | Alternative portable | Fichiers touchés |
|---|---|---|
| `AUTO_INCREMENT` | `Dialect.identity_type()` | 10 |
| `BIGINT UNSIGNED` | `Dialect.identity_type()` / `identity_storage_type()` | 3 |
| `ENGINE=InnoDB DEFAULT CHARSET=... COLLATE=...` | `Dialect.table_suffix()` / `collated_table_suffix()` | 2 |
| `INDEX (...)` dans le `CREATE TABLE` | `Dialect.inline_indexes()` puis `create_index_sql()` | 2 |
| `ON UPDATE CURRENT_TIMESTAMP` | `Dialect.timestamp_default_clause(on_update=True)` | 1 |

Le point important : **le contrat `Dialect` couvre déjà les cinq cas**.
Rien ne manque au contrat, ces fichiers ne l'appellent simplement pas.

---

## 5. Défaut aggravant : le DDL est écrit deux fois

Quatre opt-ins définissent la même table à deux endroits, dans leur migration `.sql` et dans une constante Python.

| Opt-in | Migration | Constante |
|---|---|---|
| `forge-mvc-jobs` | `create_jobs.sql` | `queue.py` → `CREATE_TABLE_SQL` |
| `forge-mvc-audit` | `create_audit_log.sql` | `store.py` |
| `forge-mvc-settings` | `create_app_settings.sql` | `store.py` |
| `forge-mvc-notifications` | `create_notifications.sql` | `store.py` |

Deux sources pour la même définition, ce que le principe 11 proscrit : rien ne garantit qu'elles restent d'accord.
Toute correction devra traiter les deux, ou mieux, supprimer la duplication.

---

## 6. Portée réelle du défaut

Le défaut est **franc et immédiat**, pas silencieux : l'installation échoue sur une erreur de syntaxe SQL claire, dès `forge migration:apply`.
C'est préférable aux deux bugs corrigés la veille (clés étrangères, doublons), qui produisaient des comportements faux sans rien signaler.

Il reste que la promesse « quatre backends au niveau plein » n'est tenue que pour le cœur et la génération d'entités.
Dès qu'une application installe l'un de ces dix opt-ins, elle est de fait restreinte à MariaDB.

---

## 7. Recommandation

Deux voies, exclusives, à trancher par le mainteneur.

**Voie A, rendre le DDL dialectal.**
Les opt-ins produisent leur DDL via le contrat `Dialect`, comme le fait déjà le moteur d'entités.
Cohérent avec l'ADR-054 et l'ADR-084, mais représente dix paquets à reprendre, plus la suppression des quatre duplications.

**Voie B, assumer la restriction.**
Ces opt-ins déclarent ne supporter que MariaDB, dans leur documentation, leur README et leurs classifieurs PyPI, et `<opt-in>:init` refuse explicitement un backend non supporté au lieu d'échouer sur une erreur SQL.
Beaucoup moins coûteux, honnête, mais affaiblit la portée de l'ADR-084.

Une voie mixte est envisageable : traiter d'abord les opt-ins d'infrastructure dont la portabilité conditionne l'usage du framework (`sessions-db`, `rbac`, `mfa`), et assumer la restriction pour les opt-ins applicatifs.

Le choix n'appartient pas à cet audit.
Quelle que soit la voie retenue, un garde-fou automatisé devrait figer le résultat : sans lui, la dérive recommencera au prochain opt-in livré.

---

## 8. Reproduire la mesure

Les quatre moteurs sont disponibles sur la station de développement : MariaDB et PostgreSQL 17 en natif, SQL Server 2022 en conteneur Podman (`podman start forge-mssql`).
La sonde n'écrit rien dans le dépôt et supprime ses bases jetables en sortie.
