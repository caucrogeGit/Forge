# L'échange CSV dans Forge (forge-mvc-import-export)

Ce document explique ce que fait l'opt-in `forge-mvc-import-export`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-import-export` offre deux briques explicites : **importer** un CSV (lire, valider par champ, rapporter les erreurs, insérer les lignes valides) et **exporter** des lignes en CSV (`to_csv`).

Le cœur ne sait pas échanger du CSV : ce paquet fournit l'outillage, l'application fournit la fonction d'insertion et le SQL.

??? note "1. Rôle du module"

    Importer un fichier suppose de le lire, de valider chaque ligne, de signaler clairement les lignes fautives, et de n'insérer que les bonnes.

    L'opt-in décompose ce flux : `parse_csv` lit, `import_rows` valide selon des `FieldSpec` et insère via une fonction fournie, `ImportReport` résume le résultat (importées + erreurs).

    Pour l'export, `to_csv` rend des lignes en texte CSV, l'inverse de `parse_csv`, pour un script ou un rapport.

??? note "2. Installation"

    !!! warning "Prérequis : activez le venv du projet"

        Quelle que soit la source, installez **dans le venv du projet** :

        ```bash
        source .venv/bin/activate
        ```

        Lancé hors d'un venv, `pip` vise le Python **système** (Debian 12+, Ubuntu 23.04+),
        protégé par PEP 668. Il refuse alors d'installer, pour ne pas écraser les paquets
        gérés par `apt`, et affiche `externally-managed-environment`.
        Le venv de projet créé par `forge new` n'a pas ce verrou.

    #### Installer le paquet

    <div class="canal">

    #### A. Depuis PyPI (stable)

    La dernière version publiée :

    ```bash
    pip install --pre forge-mvc-import-export
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-import-export"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-import-export`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-import-export==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable import-export --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    Rien à faire : cet opt-in n'apporte aucune table.

    #### 4. Le brancher là où il agit

    Il s'importe dans le code qui s'en sert. Il n'y a ni route à monter ni middleware
    à poser.

    #### 5. Le prouver

    ```bash
    make check
    forge doctor
    ```

    Puis un premier usage réel.
    Un opt-in installé, inscrit et provisionné qu'aucun code n'appelle n'est pas
    opérationnel : il est seulement présent.


??? note "4. Désinstallation"

    ```bash
    forge opt-in:disable import-export
    pip uninstall forge-mvc-import-export
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove import-export` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    Cet opt-in n'expose aucune commande CLI : il s'utilise **par import** dans le code applicatif (voir l'API publique ci-dessous).

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-import-export` |
    | Module | `forge_mvc_import_export` |
    | Catégorie | Données et modélisation (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` |
    | API publique | `parse_csv`, `to_csv`, `import_rows`, `FieldSpec`, `ImportReport`, `RowError`, `coerce_int`, `coerce_float`, `coerce_bool`, `register_importer`, `make_import_job_handler` |
    | Objets | `FieldSpec` (validation), `ImportReport`, `RowError` |
    | Insertion | fonction fournie par l'application (le SQL vit dans le modèle) |
    | Exception | `CsvImportError` |
    | Installation | `pip install --pre forge-mvc-import-export` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre les fonctions, les specs et le rapport.

    Le diagramme de séquence montre un import validé ligne par ligne.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que `import_rows` valide selon des `FieldSpec`, insère via une fonction **fournie**, et renvoie un `ImportReport`.

    ```mermaid
    classDiagram
        direction LR

        class csv {
            <<module>>
            +parse_csv(text, delimiter) list
            +to_csv(rows, columns, delimiter) str
            +import_rows(rows, specs, insert, partial) ImportReport
            +coerce_int / coerce_float / coerce_bool
        }

        class FieldSpec {
            <<dataclass>>
            +str name
            +bool required
            +coerce
        }

        class ImportReport {
            <<dataclass>>
            +int imported
            +list errors
        }

        class RowError {
            <<dataclass>>
            +int row
            +str field
            +str message
        }

        class insert {
            <<callable>>
            +insert(row) object
        }

        csv --> FieldSpec : valide selon
        csv --> ImportReport : renvoie
        ImportReport --> RowError : contient 0..*
        csv --> insert : appelle (fournie)

    ```

    À retenir :

    - `import_rows` valide chaque ligne selon les `FieldSpec` ;
    - les lignes valides sont insérées via la fonction `insert` fournie ;
    - les lignes fautives deviennent des `RowError` (numéro, champ, message) ;
    - le résultat est un `ImportReport` (importées + erreurs).

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un import CSV de bout en bout.

    ```mermaid
    sequenceDiagram
        participant App as Code applicatif
        participant IO as forge_mvc_import_export
        participant Insert as insert (fournie)

        App->>IO: parse_csv(texte)
        IO-->>App: lignes (dict en-tête -> valeur)
        App->>IO: import_rows(lignes, specs, insert)
        loop par ligne
            IO->>IO: valide / coerce selon FieldSpec
            alt ligne valide
                IO->>Insert: insert(ligne typée)
            else ligne invalide
                IO->>IO: ajoute un RowError
            end
        end
        IO-->>App: ImportReport (imported, errors)

    ```

    À retenir :

    - la validation est **par champ** (requis, coercition de type) ;
    - une erreur sur une ligne n'interrompt pas l'import (elle est rapportée) ;
    - l'insertion réelle est déléguée à l'application (le SQL lui appartient) ;
    - `partial=True` permet d'insérer les valides même s'il y a des erreurs.

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `parse_csv` | `parse_csv(text, *, delimiter=",") -> list[dict[str, str]]` | lit un CSV en lignes (dict) |
    | `to_csv` | `to_csv(rows, columns, delimiter=",") -> str` | rend des lignes en CSV |
    | `import_rows` | `import_rows(rows, specs, insert, partial=False) -> ImportReport` | valide et insère |
    | `FieldSpec` | dataclass | `name`, `required`, `coerce` |
    | `ImportReport` | dataclass | `imported`, `errors` |
    | `RowError` | dataclass | `row`, `field`, `message` |
    | `coerce_int` / `coerce_float` / `coerce_bool` | fonctions | coercition de valeurs |
    | `CsvImportError` | exception | CSV illisible |

    `insert` est une fonction `dict -> object` fournie par l'application (elle exécute le SQL d'insertion de votre modèle).

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Lire un CSV | `parse_csv(text)` |
    | Valider par champ | `FieldSpec(name, required, coerce)` |
    | Importer avec rapport | `import_rows(rows, specs, insert)` |
    | Insérer malgré des erreurs | `partial=True` |
    | Exporter des données | `to_csv(rows, columns)` |
    | Coercer des valeurs | `coerce_int`, `coerce_float`, `coerce_bool` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Importer un CSV

    ```python
    from forge_mvc_import_export import parse_csv, import_rows, FieldSpec, coerce_int

    specs = [
        FieldSpec("nom", required=True),
        FieldSpec("age", required=True, coerce=coerce_int),

    ]

    def insert(row: dict) -> object:
        return db.execute("INSERT INTO eleve (nom, age) VALUES (?, ?)", (row["nom"], row["age"]))

    rows = parse_csv(csv_text)
    report = import_rows(rows, specs, insert)
    print(report.imported, "lignes importées,", len(report.errors), "erreurs")
    ```

    Le SQL d'insertion vit dans votre code ; l'opt-in valide et orchestre.

    ### 8.2 Exporter en CSV

    ```python
    from forge_mvc_import_export import to_csv

    csv_text = to_csv(rows, columns=["nom", "age"])
    ```

    !!! tip "Aide-mémoire"
        Deux sens, des contrats clairs :

        - import : `parse_csv` puis `import_rows(specs, insert)` -> `ImportReport` ;
        - export : `to_csv(rows, columns)`.

??? note "11. Validation, rapport et frontière"

    La validation est par champ (`FieldSpec`) : champ requis manquant ou coercition impossible produit un `RowError` précis (numéro de ligne, champ, message).

    Par défaut, l'import est tout-ou-rien sur les lignes valides rapportées ; `partial=True` insère les valides et liste les fautives.

    !!! note "Le SQL appartient à l'application"
        `import_rows` n'écrit pas en base lui-même : il appelle votre fonction `insert`.

        Le SQL d'insertion vit dans le modèle de l'application (SQL visible, principe 5).

    !!! note "Frontière avec l'export web"
        Pour télécharger une entité depuis une page, la **route d'export générée par le CRUD du cœur** reste la voie officielle (principe 11).

        `to_csv` sert l'export **programmatique** (script, rapport, données hors entité CRUD).

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-import-export` : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Lecture CSV (csv_reader.py)](references/csv.md) : `parse_csv`.
- [Moteur d'import (engine.py)](references/engine.md) : `import_rows`, `FieldSpec`, `ImportReport`.
- [Export programmatique (csv_writer.py)](references/export.md) : `to_csv`.
- [Erreurs (errors.py)](references/errors.md) : `CsvImportError`.
- [Welcome-Import/Export](welcome/debutant/import-welcome.md) : parcours d'apprentissage.

## Importer un gros fichier par la file de tâches

Importer pendant une requête HTTP la fait attendre autant qu'il y a de lignes.

Dix mille lignes, dix mille insertions, et le navigateur abandonne avant la fin.
L'utilisateur relance, l'import repart de zéro, et parfois double les lignes déjà écrites (`IMPEXP-ASYNC-JOBS-001`).

### Pourquoi la charge utile ne porte pas le travail

Le moteur prend des `FieldSpec` avec leurs fonctions de conversion, et une fonction d'insertion.
Rien de tout cela ne se sérialise en JSON, contrairement à un message d'email.

La tâche transporte donc un **nom d'importeur** et un **chemin de fichier**, et l'application enregistre ses importeurs des deux côtés.

```python
# Au démarrage, des deux côtés : celui qui met en file et l'ouvrier.
from forge_mvc_import_export import FieldSpec, coerce_int, register_importer

register_importer(
    "personnes",
    specs=[FieldSpec("nom"), FieldSpec("age", coerce=coerce_int)],
    insert=enregistrer_personne,
    on_report=prevenir_le_deposant,
)
```

```python
# Côté requête, après le dépôt du fichier.
from forge_mvc_import_export import IMPORT_JOB_TASK, import_payload
from forge_mvc_jobs import enqueue

enqueue(IMPORT_JOB_TASK, import_payload("personnes", chemin, auteur=utilisateur.id))
```

```python
# Côté ouvrier.
from forge_mvc_import_export import IMPORT_JOB_TASK, make_import_job_handler
from forge_mvc_jobs import run_worker

run_worker({IMPORT_JOB_TASK: make_import_job_handler(root="storage/imports")})
```

!!! danger "Bornez la racine des chemins"
    `root` refuse tout fichier hors de l'arborescence indiquée.

    Le chemin vient d'une charge utile, donc d'une file que plusieurs processus écrivent.
    Sans racine, un `../../etc/passwd` serait lu et importé ligne à ligne dans la base.

!!! warning "Un fichier mal rempli n'est pas une panne"
    Le gestionnaire ne lève **pas** pour des lignes invalides.

    Réessayer ne corrigerait pas un CSV, et faire échouer la tâche la ferait rejouer jusqu'à épuisement de ses tentatives.
    Il lève en revanche sur un importeur inconnu ou un fichier illisible : une configuration à corriger, ou un dépôt qu'un réessai peut résoudre.

!!! info "Le rapport revient à l'application"
    `on_report` reçoit le rapport et le contexte de la tâche.

    Sans lui, un import différé serait muet : celui qui a déposé le fichier n'apprendrait jamais combien de lignes sont passées, ni lesquelles ont été refusées.
    Le contexte porte ce qu'il faut pour lui répondre, son identifiant par exemple.

!!! info "Un nom déjà pris est refusé"
    Écraser un importeur en silence ferait traiter un fichier par le mauvais, et écrire dans la mauvaise table.
