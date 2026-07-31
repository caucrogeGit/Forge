# Nettoyer les sessions expirées

Objectif : supprimer périodiquement les sessions expirées avec `cleanup_expired()`.

**Ce que vous allez apprendre :** une session expirée reste physiquement en base tant qu'on ne la supprime pas.
`get()` ignore les sessions expirées, mais la ligne demeure et la table grossit.
`cleanup_expired()` supprime en une passe toutes les lignes expirées, à lancer depuis un cron applicatif.

Deuxième palier du **niveau intermédiaire** de la progression Sessions BDD.

## Ce que ce starter montre

- pourquoi les sessions expirées s'accumulent en base ;
- supprimer les sessions expirées avec `cleanup_expired()` ;
- déclencher ce nettoyage depuis un cron applicatif.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `cleanup_expired()` | Supprime les sessions expirées et renvoie le nombre de lignes supprimées. | Opt-ins |

## 1. Pourquoi nettoyer

```text
create(ttl=3600)  : la session expire dans une heure.
Une heure passe   : get() renvoie None, mais la ligne existe toujours.
Sans nettoyage    : la table forge_sessions grossit indéfiniment.
```

### Comprendre ce code

- `get()` filtre à la lecture : une session expirée est traitée comme absente.
- La ligne correspondante n'est pas supprimée automatiquement à l'expiration.
- Sans nettoyage régulier, la table conserve toutes les sessions jamais créées.

## 2. Supprimer les sessions expirées

```python
from forge_mvc_sessions_db import DbSessionStore

store = DbSessionStore(ttl=3600)

supprimees = store.cleanup_expired()
print(f"{supprimees} sessions expirées supprimées")
```

### Comprendre ce code

- `cleanup_expired()` supprime en une seule requête toutes les lignes dont l'expiration est passée.
- Elle renvoie le nombre de lignes supprimées, pratique pour un journal.
- Les sessions encore valides ne sont jamais touchées.

## 3. Déclencher depuis un cron applicatif

Forge ne planifie rien tout seul : le nettoyage relève de l'application.
Exposez un point d'entrée que votre planificateur appelle, par exemple chaque nuit.

```python
# scripts/cleanup_sessions.py
from forge_mvc_sessions_db import DbSessionStore

if __name__ == "__main__":
    store = DbSessionStore()
    n = store.cleanup_expired()
    print(f"{n} sessions expirées supprimées")
```

```text
# crontab de l'application : tous les jours à 3 h du matin
0 3 * * * /chemin/vers/venv/bin/python /chemin/vers/scripts/cleanup_sessions.py
```

Cette ligne se pose dans une crontab, avec `crontab -e` ; ce n'est pas une commande à taper dans un terminal.

### Comprendre ce code

- Le script construit un store et appelle `cleanup_expired()`, rien de plus.
- Le cron du système déclenche ce script à intervalle régulier.
- La fréquence dépend de votre trafic : une fois par jour convient à la plupart des applications.

## À retenir

- Une session expirée reste en base tant qu'on ne la supprime pas.
- `cleanup_expired()` supprime les sessions expirées et renvoie leur nombre.
- Le déclenchement relève de l'application : un cron appelle un petit script dédié.

## Après ce starter

Vous savez maintenir la table propre dans le temps.
Faisons le point sur ce niveau intermédiaire.

[Bilan](bilan.md)
