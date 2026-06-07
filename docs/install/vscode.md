# Configurer VS Code pour l'auto-import des classes Forge

Ce guide configure VS Code et Pylance pour qu'ils **résolvent** et **proposent
automatiquement** (`Ctrl + .`, puis « Ajouter l'import ») les classes du
framework Forge (paquet `core`, fourni par `forge-mvc`) dans un projet Forge nu.

!!! info "Pourquoi cette configuration est nécessaire"
    Le code du framework (`core.mvc.controller.BaseController`, etc.) n'est
    **pas** présent dans le dépôt du projet. Il est installé dans le `.venv`
    via le paquet `forge-mvc`. Sans réglage, Pylance ne sait ni où le chercher,
    ni à quelle profondeur l'indexer, donc l'auto-import ne fonctionne pas.

Cette aide est optionnelle : Forge ne dépend pas de VS Code. Elle améliore
seulement le confort d'écriture des contrôleurs et des classes applicatives.

---

## Prérequis

- Le projet dispose d'un environnement virtuel avec `forge-mvc` installé :

  ```bash
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt   # contient forge-mvc==…
  ```

- Les extensions VS Code **Python** (`ms-python.python`) et **Pylance**
  (`ms-python.vscode-pylance`) sont installées.

Vérifier d'abord que l'import fonctionne côté interpréteur. Si cette commande
échoue, le problème vient de l'installation, pas de VS Code :

```bash
.venv/bin/python -c "from core.mvc.controller import BaseController; print('OK')"
```

---

## Configuration

Créer (ou compléter) le fichier **`.vscode/settings.json`** à la racine du
projet :

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.indexing": true,
  "python.analysis.packageIndexDepths": [
    { "name": "core", "depth": 4, "includeAllSymbols": true }
  ]
}
```

### Rôle de chaque clé

| Clé | Rôle |
|-----|------|
| `python.defaultInterpreterPath` | Pointe Pylance vers le Python du `.venv`, là où `core` est installé. |
| `python.analysis.autoImportCompletions` | Active les suggestions d'import dans l'autocomplétion. |
| `python.analysis.indexing` | Active l'indexation des paquets installés, nécessaire à l'auto-import. |
| `python.analysis.packageIndexDepths` | Au pluriel. Force Pylance à indexer le paquet `core` en profondeur. |

### Pourquoi `depth: 4` ?

Par défaut, Pylance n'indexe les paquets installés qu'au niveau 1 (le
`__init__.py` racine). Or les classes Forge sont imbriquées plus profondément,
par exemple :

```text
core / mvc / controller / base_controller.py   →  niveau 3
```

`depth: 4` couvre largement l'arborescence de `core`. `includeAllSymbols: true`
indexe tous les symboles, pas seulement ceux listés dans `__all__`.

!!! warning "Piège fréquent : le pluriel"
    Le paramètre s'écrit **`packageIndexDepths`** (avec un `s`). Écrit au
    singulier (`packageIndexDepth`), il est **silencieusement ignoré** et
    l'auto-import ne fonctionne pas.

---

## Activation (étapes obligatoires)

Les réglages ne sont pris en compte qu'après ces deux actions :

1. **Sélectionner l'interpréteur** : `Ctrl + Shift + P`, puis
   **Python: Select Interpreter**, et choisir `./.venv/bin/python`.
   La barre d'état (en bas) doit afficher `.venv (3.x.x)`.

2. **Recharger la fenêtre** (indispensable après toute modification de
   `settings.json`) : `Ctrl + Shift + P`, puis **Developer: Reload Window**.

Patienter une quinzaine de secondes : Pylance ré-indexe `core` en arrière-plan.

---

## Vérification

1. Dans un contrôleur, écrire une classe qui hérite d'une classe Forge **sans
   l'importer** :

   ```python
   class WelcomeController(BaseController):

       @staticmethod
       def index(request):
           return Response.text("Bonjour Forge")
   ```

2. `BaseController` est souligné (signalé comme non défini).
3. Placer le curseur sur `BaseController`, puis `Ctrl + .` : la correction
   rapide **« Ajouter l'import "BaseController" depuis core.mvc.controller »**
   doit apparaître. La sélectionner insère l'import en haut du fichier.

---

## Dépannage

L'auto-import n'apparaît toujours pas ? Vérifier dans l'ordre :

1. **L'interpréteur** : la barre d'état doit afficher `.venv`, pas un
   « Python 3.x » système. Sinon, relancer **Python: Select Interpreter**, puis
   recharger la fenêtre.

2. **Pylance a-t-il relu la configuration ?** Ouvrir
   **Affichage → Sortie**, canal **Pylance** (ou « Serveur de langage Python »).
   Après un rechargement, une ligne `Indexing … indexed N files` doit
   apparaître. Si `N` reste très bas (proche du seul nombre de fichiers du
   projet), l'indexation de `core` n'a pas eu lieu : recharger à nouveau la
   fenêtre.

3. **Configuration réellement appliquée ?** Le `settings.json` doit avoir été
   enregistré **avant** le dernier rechargement. Toute édition postérieure exige
   un nouveau **Developer: Reload Window**.

4. **Repli si l'interpréteur reste mal détecté** : ajouter explicitement le
   chemin des paquets (adapter la version de Python) :

   ```json
   "python.analysis.extraPaths": ["${workspaceFolder}/.venv/lib/python3.12/site-packages"]
   ```

5. **Vérifier que `core` est bien installé** dans le `.venv` (voir la commande
   des prérequis).

---

## Suivi de version

`.vscode/settings.json` peut être versionné : il documente la configuration
attendue et profite à toute l'équipe. En revanche, `.venv/` doit rester dans le
`.gitignore`.
