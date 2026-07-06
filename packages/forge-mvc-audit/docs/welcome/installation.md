# Installation de forge-mvc-audit

Objectif : installer l'opt-in journal d'audit et préparer sa table.

Le parcours qui suit montre, en trois niveaux, comment enregistrer une action, relire le journal, enrichir et filtrer les traces, puis comprendre le périmètre borné du module.

## Installer le paquet

```bash
pip install --pre forge-mvc-audit
```

En développement, depuis le dépôt, vous pouvez installer le paquet en mode éditable :

```bash
pip install -e packages/forge-mvc-audit
```

Le paquet dépend du cœur `forge-mvc`.
Il enregistre les actions dans une table MariaDB nommée `audit_log`.

## Créer la table d'audit

La table n'est pas créée automatiquement.
Forge copie la migration fournie par le paquet dans votre projet, puis vous l'appliquez :

```bash
forge audit:init
forge migration:apply
```

`forge audit:init` dépose la migration dans `mvc/migrations/`.
`forge migration:apply` exécute la migration et crée la table `audit_log`.

## Vérifier l'installation

```python
from forge_mvc_audit import TABLE_NAME, MAX_LIMIT

print(TABLE_NAME, MAX_LIMIT)
```

Si ce script affiche `audit_log 1000`, l'import de l'opt-in fonctionne.

## Après cette étape

Place au niveau débutant : enregistrer votre première action d'audit.

[Niveau débutant : Première action d'audit](debutant/audit-welcome.md)
