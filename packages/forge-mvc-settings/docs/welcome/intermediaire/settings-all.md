# Lister et supprimer

Objectif : lister tous les paramètres et en supprimer un.

**Ce que vous allez apprendre :** `get_all_settings` renvoie tous les paramètres dans un dictionnaire, triés par clé et recoercés dans leur type.
`delete_setting` retire un paramètre et indique s'il existait.
Vous disposez ainsi d'une vue d'ensemble et d'un moyen de nettoyage.

Deuxième palier du **niveau intermédiaire** de la progression Settings.

## Ce que ce starter montre

- récupérer tous les paramètres avec `get_all_settings` ;
- supprimer un paramètre avec `delete_setting` et lire le retour.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `get_all_settings()` | Renvoie tous les paramètres, triés par clé. | Opt-ins |
| `delete_setting(key)` | Supprime un paramètre, renvoie `True` s'il existait. | Opt-ins |

## 1. Lister tous les paramètres

```python
from forge_mvc_settings import set_setting, get_all_settings

set_setting("etablissement.nom", "Collège Victor Hugo")
set_setting("qcm.session_duration", 30)
set_setting("maintenance", False)

for cle, valeur in get_all_settings().items():
    print(cle, "=", valeur)
```

### Comprendre ce code

- `get_all_settings()` renvoie un dictionnaire `clé -> valeur`.
- Les paramètres sont triés par clé, ce qui rend l'affichage stable.
- Chaque valeur est déjà recoercée dans son type d'origine.

## 2. Supprimer un paramètre

```python
from forge_mvc_settings import delete_setting

existait = delete_setting("maintenance")
print(existait)   # True : le paramètre était présent

encore = delete_setting("maintenance")
print(encore)     # False : il n'existe plus
```

### Comprendre ce code

- `delete_setting` retire le paramètre et renvoie `True` s'il existait.
- Un deuxième appel sur la même clé renvoie `False`.
- Le booléen de retour permet de savoir si une suppression a réellement eu lieu.

## À retenir

- `get_all_settings()` renvoie tous les paramètres, triés par clé et typés.
- `delete_setting(clé)` supprime un paramètre.
- Son retour vaut `True` si le paramètre existait, `False` sinon.

## Après ce starter

Vous savez lister et supprimer des paramètres.
Faisons le point sur ce niveau intermédiaire.

[Bilan](bilan.md)
