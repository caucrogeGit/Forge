# Avancé 4 : Le registre d'importeurs

Objectif : lancer un import depuis une file de tâches, sans que la file connaisse vos entités.

## Le problème d'un import long

Un import de dix mille lignes tenu dans la requête fait une page qui expire.
Le mettre en file demande que le worker sache quoi importer : il ne peut pas recevoir une fonction, seulement du JSON.

Le registre fait le lien par un **nom**.

```python
from forge_mvc_import_export import FieldSpec, register_importer


def enregistrer_un_eleve(nom: str) -> None:
    """Votre écriture en base, telle que vous l'écrivez déjà."""


register_importer(
    "eleves",
    specs=[FieldSpec(name="nom", required=True)],
    insert=lambda ligne: enregistrer_un_eleve(ligne["nom"]),
    partial=True,
)
```

```python
chemin = "/srv/imports/eleves-2026.csv"

charge = {"importer": "eleves", "source": chemin}
```

Cette charge part dans la file, par exemple avec `forge_mvc_jobs.enqueue("import.csv", charge)`.
Le worker y lit le nom, retrouve la fonction, et lit le fichier.

Le worker retrouve la fonction par son nom, et l'appelle.

!!! danger "Un nom inconnu lève, il n'est pas ignoré"
    `ImporterNotFound` dit lequel manquait et lesquels sont enregistrés.

    Ignorer une tâche dont l'importeur est inconnu la ferait disparaître en silence : l'utilisateur attendrait un import qui n'a jamais eu lieu.

!!! warning "Enregistrez au câblage, pas à l'import d'un module"
    Le registre vit dans le processus, et le **worker** est un autre processus que le serveur web.

    Un importeur enregistré depuis un contrôleur n'existe pas côté worker : `bootstrap.py` est lu par les deux.

!!! info "La source est une référence, jamais un contenu"
    La charge utile d'une tâche est du JSON stocké en base.

    Y mettre le CSV entier ferait grossir la table à chaque import ; on y met un chemin, et le worker lit le fichier.

## Le rapport d'erreurs

```python
from forge_mvc_import_export import errors_to_rows, errors_to_csv
```

Un import partiel produit des lignes en erreur, avec leur numéro et leur motif.
Rendues en CSV, elles se corrigent dans un tableur et se réimportent.

!!! info "Les cellules du rapport sont neutralisées"
    Une valeur commençant par `=` redeviendrait une formule vive à l'ouverture.

    Le rapport passe par le même échappement que tout export CSV de Forge.

## À retenir

- Le registre relie un nom à une fonction, ce qu'une file peut transporter.
- L'enregistrement va dans `bootstrap.py`, lu par le serveur comme par le worker.
- Le rapport d'erreurs se relit dans un tableur, sans redevenir des formules.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
