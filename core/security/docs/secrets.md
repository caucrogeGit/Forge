# La reconnaissance des secrets dans Forge

Ce document décrit comment Forge reconnaît un secret laissé à sa valeur d'amorçage.

Un mot de passe ou un jeton recopié d'un exemple et jamais changé est une faille qui ne se voit pas.
La configuration paraît complète, et rien ne signale que le secret n'en est pas un.
Le fichier de code correspondant est `core/security/secrets.py`.

## 1. Rôle

`forge-mvc-mfa` refusait déjà les valeurs évidentes pour sa clé de chiffrement, et il était le seul.

Le pré-vol de déploiement en avait besoin pour les mots de passe de base et les jetons d'API.
Un opt-in ne pouvant pas dépendre d'un autre, la liste a remonté ici plutôt que d'être recopiée.

Ce module ne décide de rien et n'accède à rien.
Il répond à une question, et l'appelant décide s'il refuse, avertit ou passe.

## 2. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Module Python | `core.security.secrets` |
| Couche | Sécurité |
| Rôle | reconnaître une valeur d'amorçage et un nom de variable sensible |
| Dépend de | rien, pas même la bibliothèque standard |
| API publique | `looks_like_placeholder`, `is_sensitive_name` |
| Constantes publiques | `PLACEHOLDER_VALUES`, `SENSITIVE_NAME_MARKERS`, `NON_SECRET_NAME_SUFFIXES` |
| Effet de bord | aucun |
| Employé par | `forge deploy:check`, `forge-mvc-mfa` |

## 3. Reconnaître une valeur d'amorçage

`looks_like_placeholder(value)` compare la valeur, en minuscules et sans blancs de bord, à une liste de chaînes évidentes.

| Valeur | Placeholder |
|---|---|
| `"change-me"` | oui |
| `"CHANGE-ME"` | oui |
| `"  default  "` | oui |
| `"secret"` | oui |
| `""` | oui |
| absente | oui |
| `"xK9mP2vL7qR4nT8"` | non |

Une valeur absente ou vide compte comme un placeholder.
Dans les deux cas, aucun secret n'a été posé, et c'est bien ce que l'appelant veut savoir.

!!! warning "Forge ne juge pas de la force d'un secret"
    Le module refuse l'évidence, jamais la faiblesse.

    Mesurer l'entropie d'une chaîne demanderait des règles arbitraires, sur la longueur ou la variété des caractères, que Forge n'impose pas.
    Un mot de passe court mais non évident passe donc le contrôle, et le choix reste celui de l'exploitant.

## 4. Reconnaître un nom sensible

`is_sensitive_name(name)` repère les variables d'environnement qui portent un secret.

Le repérage porte sur le nom et non sur une liste figée de variables.
Un opt-in ajouté demain est donc couvert sans que ce module change.

| Nom | Sensible | Pourquoi |
|---|---|---|
| `DB_APP_PWD` | oui | contient `PWD` |
| `FORGE_MFA_SECRET_KEY` | oui | contient `SECRET` |
| `MAIL_PASSWORD` | oui | contient `PASSWORD` |
| `FORGE_IOT_API_TOKEN` | oui | contient `TOKEN` |
| `SSL_KEYFILE` | non | se termine par `_FILE`, c'est un chemin |
| `DB_NAME` | non | se termine par `_NAME` |
| `APP_CSP_NONCE_ENABLED` | non | se termine par `_ENABLED`, c'est un drapeau |

!!! info "Pourquoi les exclusions comptent autant que les marqueurs"
    `SSL_KEYFILE` nomme un fichier, pas une clé, et sa valeur usuelle est `key.pem`.

    Sans l'exclusion, le pré-vol crierait sur une configuration correcte.
    Un contrôle qui crie à tort finit désactivé, et il ne protège alors plus de rien.

## 5. Employer le module

```python
from core.security.secrets import is_sensitive_name, looks_like_placeholder

fautives = [
    nom for nom, valeur in configuration.items()
    if is_sensitive_name(nom) and looks_like_placeholder(valeur)
]
```

!!! danger "Ne jamais afficher la valeur"
    Un rapport de diagnostic est collé dans un ticket ou un journal.

    Nommer la variable suffit à corriger, et rendre sa valeur y ferait fuir un secret réel.
    `forge deploy:check` suit cette règle.

## 6. Ce que le module ne fait pas

Il ne lit aucun fichier et aucune variable d'environnement.
L'appelant fournit ce qu'il a lu, ce qui rend les deux fonctions testables sans toucher au processus.

Il ne chiffre ni ne génère aucun secret.
La génération d'une clé de chiffrement appartient à l'opt-in qui l'exige, `forge-mvc-mfa` documentant la sienne.
