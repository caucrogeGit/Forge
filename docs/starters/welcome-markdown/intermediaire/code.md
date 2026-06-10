# Montrer du code

**Objectif** : ajouter à la page les commandes d'installation et un exemple de contrôleur, dans des blocs de code colorés.

**Ce que vous allez apprendre :** les blocs de code (extensions `pymdownx.highlight` et `pymdownx.superfences`), avec langage, numéros de ligne, titre et surlignage.

Votre page explique les prérequis et le dépannage.

Nous ajoutons une vraie section « Installation » avec des commandes, puis un aperçu de code.

## Un bloc de code

Une clôture de trois accents graves, suivie du nom du langage, ouvre un bloc coloré.

````md
```bash
pip install forge-mvc
forge new mon-projet
```
````

Rendu :

```bash
pip install forge-mvc
forge new mon-projet
```

!!! tip "Afficher des accents graves dans un bloc"
    Pour montrer un bloc de trois accents graves, **entourez-le d'une clôture plus longue** (quatre accents graves).
    La clôture la plus longue gagne ; le bloc intérieur s'affiche littéralement.

## Numéros de ligne, titre et surlignage

Les options `linenums`, `title` et `hl_lines` enrichissent le bloc.

````md
```python title="welcome_controller.py" linenums="1" hl_lines="3"
class WelcomeController(BaseController):
    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge")
```
````

Rendu :

```python title="welcome_controller.py" linenums="1" hl_lines="3"
class WelcomeController(BaseController):
    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge")
```

## Ajoutez à votre page

Ajoutez une section « Installation » à `prise-en-main.md` :

~~~md
## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install forge-mvc
forge new mon-projet
```
~~~

## À retenir

- Un bloc de code s'ouvre par trois accents graves suivis du langage.
- `linenums="1"`, `hl_lines="2 3"`, `title="…"` enrichissent le bloc.
- Pour montrer trois accents graves, on entoure d'une clôture de quatre.

[Voir le bilan du niveau intermédiaire](bilan.md)
