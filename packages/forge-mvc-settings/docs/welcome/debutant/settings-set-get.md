# Écrire et lire

Objectif : maîtriser `set_setting` et `get_setting`, valeur par défaut comprise.

**Ce que vous allez apprendre :** `set_setting` enregistre ou met à jour une
valeur (un upsert).
`get_setting` la relit, et accepte une valeur par défaut quand le paramètre
n'existe pas encore.
C'est la base de tout réglage applicatif persistant.

Deuxième palier du **niveau débutant** de la progression Settings.

## Ce que ce starter montre

- mettre à jour un paramètre existant avec `set_setting` ;
- lire un paramètre absent en fournissant une valeur par défaut.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `set_setting(key, value)` | Crée ou met à jour (upsert) un paramètre. | Opt-ins |
| `get_setting(key, default)` | Lit la valeur, ou `default` si absente. | Opt-ins |

## 1. Mettre à jour une valeur

```python
from forge_mvc_settings import set_setting, get_setting

set_setting("etablissement.nom", "Collège Victor Hugo")
set_setting("etablissement.nom", "Lycée Jean Moulin")   # remplace l'ancienne

print(get_setting("etablissement.nom"))   # Lycée Jean Moulin
```

### Comprendre ce code

- Le deuxième appel à `set_setting` ne crée pas un doublon : il met à jour la valeur.
- C'est un upsert : crée si absent, met à jour si présent.
- La dernière valeur écrite est celle que `get_setting` renvoie.

## 2. Lire avec une valeur par défaut

```python
from forge_mvc_settings import get_setting

theme = get_setting("affichage.theme", "clair")
print(theme)   # clair, car le paramètre n'existe pas encore
```

### Comprendre ce code

- Si `affichage.theme` n'a jamais été écrit, `get_setting` renvoie la valeur par défaut.
- Sans valeur par défaut, un paramètre absent renvoie `None`.
- La valeur par défaut n'est pas enregistrée : elle sert seulement de repli à la lecture.

## À retenir

- `set_setting` est un upsert : il crée ou met à jour.
- `get_setting(clé, défaut)` renvoie `défaut` si la clé n'existe pas.
- Sans valeur par défaut, une clé absente renvoie `None`.

## Après ce starter

Vous savez écrire, mettre à jour et lire un paramètre.
Faisons le point sur ce niveau débutant.

[Bilan](bilan.md)
