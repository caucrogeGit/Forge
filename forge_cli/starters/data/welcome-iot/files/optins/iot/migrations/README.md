# Migrations de l'opt-in Forge IoT

La migration `iot_events` est **packagée** dans `forge-mvc-iot` et copiée
dans `mvc/migrations/` par la commande dédiée :

```bash
forge iot:init          # copie *_create_iot_events.sql vers mvc/migrations/
forge migration:apply   # applique la migration (crée la table iot_events)
```

Ce dossier sert de **repère** : il documente quelle migration l'opt-in
IoT utilise. Le SQL réel reste appliqué via `mvc/migrations/` — SQL
visible, appliqué **explicitement**. Rien n'est appliqué automatiquement.
