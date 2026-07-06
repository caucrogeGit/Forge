# Le périmètre de l'audit

Objectif : comprendre ce que ce module trace, et ce qu'il ne trace pas.

**Ce que vous allez apprendre :** `forge-mvc-audit` est un journal d'audit **applicatif**, au périmètre volontairement borné.
Il enregistre des événements métier décidés par l'application.
Ce n'est pas un SIEM de cybersécurité.

Premier palier du **niveau avancé** de la progression Audit.

!!! note "Module opt-in"
    Si `forge-mvc-audit` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- la nature des actions à tracer (événements applicatifs) ;
- la limite assumée du module (pas de cybersécurité, pas de SIEM).

## Ce que ce module trace

Des événements métier que l'application choisit de consigner :

- un élève créé (`"eleve.cree"`) ;
- une note modifiée (`"note.modifiee"`) ;
- un QCM corrigé (`"qcm.corrige"`) ;
- une connexion utilisateur (`"utilisateur.connecte"`) ;
- un rôle changé (`"role.modifie"`) ;
- un fichier supprimé (`"fichier.supprime"`).

## Ce que ce module ne fait pas

- Il ne surveille pas le réseau ni le système : ce n'est pas un SIEM.
- Il ne détecte pas d'intrusion et ne corrèle pas d'alertes de sécurité.
- Il ne décide jamais seul quoi tracer : c'est l'application qui appelle `record_audit`.

## Cohérence avec l'ADR-008

Cette frontière suit l'ADR-008.
Forge fournit la table `audit_log` et les helpers `record_audit` et `get_audit_log`.
La décision de tracer un événement, et le choix de ce qui mérite une trace, restent applicatifs.

## À retenir

- L'audit est **applicatif** : il consigne des événements métier.
- Ce n'est pas un outil de cybersécurité ni un SIEM.
- Forge fournit la table et le helper ; tracer reste une décision de l'application (ADR-008).

## Après ce starter

Vous savez ce que le module trace.
Voyons comment il reste indépendant du cœur.

[Indépendance du cœur](audit-independance.md)
