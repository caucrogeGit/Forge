# Les transactions dans Forge

Ce document décrit les transactions SQL explicites.

Le fichier de code correspondant est `core/database/transaction.py`.

## 1. À quoi sert ce module ?

Quand plusieurs écritures doivent réussir **ensemble** (ou échouer ensemble), on les groupe dans une transaction.
Ce module fournit un bloc `with transaction()` explicite : à la sortie sans erreur Forge committe, sur exception Forge annule (rollback).

## 2. L'API

```python
from core.database.db import insert, execute
from core.database.transaction import transaction

with transaction() as tx:
    insert("INSERT INTO article (title, category_id) VALUES (?, ?)", (title, cat), tx=tx)
    execute("UPDATE categories SET article_count = article_count + 1 WHERE id = ?", (cat,), tx=tx)
```

| Élément | Rôle |
|---|---|
| `transaction()` | gestionnaire de contexte ouvrant une transaction explicite |
| `Transaction(connection)` | l'objet transaction porté par le bloc (passé en `tx=` aux helpers) |

## 3. Le contrat

- Les helpers DB reçoivent `tx=tx` et **ne committent jamais seuls** : c'est le bloc qui décide.
- Sortie sans erreur → **commit** ; exception traversant le bloc → **rollback** (aucune écriture partielle).

## 4. Contextes d'utilisation

- **Écritures liées** : créer une entité + mettre à jour un compteur, etc.
- **Tout ou rien** : garantir l'atomicité d'une opération métier.

## 5. Voir aussi

- [Les helpers SQL](db.md) : `insert` / `execute` avec `tx=`.
