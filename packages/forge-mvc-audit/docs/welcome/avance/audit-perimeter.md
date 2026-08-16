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

## Ce que le module n'efface pas tout seul

`audit_log` grossit à chaque action tracée, et rien ne la borne d'elle-même.
Sur une application active, la table finit par peser sur les lectures, sans qu'un signal ne prévienne.

La rétention est une **décision applicative**, comme la décision de tracer : Forge ne choisit pas à votre place ce que vous détruisez.

```bash
forge db:config          # amorce la connexion dans env/ (une seule fois)
forge db:init            # provisionne la base
forge audit:init         # copie la migration de l'opt-in
forge migration:apply    # l'applique en base
forge audit:gc --days 90          # affiche le nombre d'entrées visées
forge audit:gc --days 90 --run    # supprime
```

La commande affiche par défaut et n'efface qu'avec `--run`, une entrée d'audit étant un enregistrement délibéré.
Forge ne fournit pas d'ordonnanceur : branchez-la sur cron ou un minuteur systemd.

Aucune archive n'est produite avant suppression.
Si vous devez conserver vos journaux, exportez-les en amont.

## À retenir

- L'audit est **applicatif** : il consigne des événements métier.
- Ce n'est pas un outil de cybersécurité ni un SIEM.
- Forge fournit la table et le helper ; tracer reste une décision de l'application (ADR-008).
- La table ne se purge pas toute seule : `forge audit:gc --days N --run`, à brancher sur un ordonnanceur.

## Après ce starter

Vous savez ce que le module trace.
Voyons comment il reste indépendant du cœur.

[Indépendance du cœur](audit-independance.md)
