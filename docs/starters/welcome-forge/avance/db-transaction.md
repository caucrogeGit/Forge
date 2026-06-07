# Écritures transactionnelles

Objectif : regrouper plusieurs écritures pour qu'elles soient **atomiques** :
soit tout réussit, soit rien.

**Ce que vous allez apprendre :** le bloc `with transaction() as tx:`. Il ouvre
une transaction explicite et passe `tx` aux helpers DB, qui réutilisent la
connexion **sans jamais committer eux-mêmes**. À la sortie du bloc, Forge
committe ; si une exception traverse le bloc, Forge **annule** (rollback). C'est
indispensable dès que deux écritures doivent rester cohérentes.

Dernier palier du **niveau avancé** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [API JSON protégée](json-api.md).

## Ce que ce starter montre

- une transaction explicite `with transaction() as tx:` ;
- deux `insert(..., tx=tx)` dans le même bloc ;
- un **rollback** : si le second message manque, une erreur est levée **après**
  la première insertion → tout est annulé, rien n'est écrit ;
- le motif POST-Redirect-GET en cas de succès.

Table neutre `first_sql_messages`.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `core.database.transaction.transaction` | Ouvrir une transaction explicite (commit / rollback). | [Base de données](../../../reference/api.md#coredatabase) |
| `core.database.db.insert` | Insérer une ligne **dans** la transaction (`tx=tx`). | [Base de données](../../../reference/api.md#coredatabase) |
| `BaseController.csrf_token` / `redirect` | Protéger le POST, rediriger après succès (PRG). | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/db-transaction`. Saisissez les **deux** messages
et validez : les deux apparaissent. Laissez le **second vide** et validez : une
erreur s'affiche et **aucun** des deux n'est enregistré : le premier `insert` a
été annulé par le rollback.

## Le contrôleur

```python
# mvc/controllers/db_transaction_controller.py
from core.database.db import fetch_all, insert
from core.database.transaction import transaction


INSERT_MESSAGE = "INSERT INTO first_sql_messages (content) VALUES (?)"


class DbTransactionController(BaseController):

    @staticmethod
    def store(request: Request) -> Response:
        first = (request.form("message_a") or "").strip()
        second = (request.form("message_b") or "").strip()
        try:
            with transaction() as tx:
                insert(INSERT_MESSAGE, (first,), tx=tx)
                if not second:
                    # Erreur APRÈS la première insertion : le rollback l'annule.
                    raise ValueError("Le second message est obligatoire : tout est annulé.")
                insert(INSERT_MESSAGE, (second,), tx=tx)
        except ValueError as exc:
            return DbTransactionController._page(request, error=str(exc))
        return BaseController.redirect("/db-transaction")
```

### Comprendre ce code

- `with transaction() as tx:` ouvre la transaction. Chaque `insert(..., tx=tx)`
  écrit **dans** cette transaction, mais **ne committe pas**.
- Si tout le bloc se termine sans erreur, Forge **committe** : les deux lignes
  sont enregistrées.
- Si une exception (ici `ValueError`) traverse le bloc, Forge **annule** : même
  le premier `insert`, déjà exécuté, est défait. C'est l'atomicité : **tout ou
  rien**.
- En cas de succès, on **redirige** (POST-Redirect-GET).

## À retenir

- `with transaction() as tx:` rend un groupe d'écritures **atomique**.
- Les helpers DB reçoivent `tx` et ne committent jamais seuls : c'est le bloc qui
  décide.
- Une exception dans le bloc = **rollback** : aucune écriture partielle ne
  subsiste.

## Après ce starter

Vous avez terminé le **niveau avancé** : relations, fichiers, emails, API JSON et
transactions. Faites le point dans le bilan du niveau.

[Bilan du niveau avancé](bilan.md)
