# Export CSV : neutraliser l'injection de formule

`core.security.csv_export` fournit une primitive unique, `escape_csv_field`, qui rend une valeur de cellule inerte pour un tableur.

## Le risque

Un tableur interprète comme une **formule** toute cellule commençant par certains caractères.
Une valeur saisie par un utilisateur, par exemple `=1+1` ou `@SUM(A1)`, redevient donc du code exécutable à l'ouverture du fichier exporté.
C'est l'injection de formule CSV.

Le danger ne pèse pas sur l'application qui exporte, mais sur la personne qui ouvre le fichier : exfiltration de données vers une URL, exécution de commandes selon le tableur et sa configuration.

Le guillemetage CSV ne protège pas.
`csv.QUOTE_ALL` garantit un fichier bien formé, pas une cellule inerte : le tableur retire les guillemets avant d'interpréter le contenu.

## Utilisation

```python
import csv, io
from core.security.csv_export import escape_csv_field

output = io.StringIO()
writer = csv.writer(output, quoting=csv.QUOTE_ALL)
writer.writerow(["Nom", "Commentaire"])
for row in rows:
    writer.writerow([escape_csv_field(str(row.get(key) or "")) for key in ("nom", "commentaire")])
```

La valeur est renvoyée telle quelle quand elle ne peut pas être interprétée comme une formule, ce qui est le cas courant.
Aucun caractère n'est retiré ni remplacé : seule une apostrophe peut être ajoutée en tête, ce que les tableurs traitent comme « le contenu qui suit est du texte ».

| Entrée | Sortie | Raison |
|---|---|---|
| `Dupont` | `Dupont` | inoffensive |
| `=1+1` | `'=1+1` | ouvre une formule |
| `+33 1 23 45` | `'+33 1 23 45` | un numéro de téléphone déclenche aussi |
| `-5` | `'-5` | un nombre négatif également |
| `\t=1+1` | `'\t=1+1` | la tabulation masque la tête réelle |
| `a=1` | `a=1` | le déclencheur n'est pas en tête |

## Pourquoi la tabulation et le retour chariot

Un tableur ignore ces caractères à l'affichage.
`"\t=1+1"` s'ouvre donc comme la formule `=1+1`, alors qu'un filtre ne regardant que le premier caractère laisse passer la valeur.
La primitive franchit ces caractères invisibles avant d'examiner la tête de cellule.

## Pourquoi cette règle vit dans le cœur

Le CRUD généré par `forge make:crud` **appelle** cette primitive ; il n'en recopie pas la règle.

C'est une conséquence directe du principe 9 : Forge ne réécrit jamais le code utilisateur.
Une règle de sécurité dupliquée dans chaque contrôleur ne peut donc plus être corrigée par une montée de version, et une application comptant plusieurs dizaines de contrôleurs devrait éditer autant de fichiers à la main.
En la plaçant dans le cœur, un `pip install --upgrade` suffit.

## Limites

La primitive n'assainit **qu'une valeur de cellule**.
Elle ne fabrique pas de CSV : le formatage, le guillemetage et l'encodage restent à la charge de l'appelant, avec le module `csv` de la bibliothèque standard.

Elle ne protège pas non plus contre un contenu dangereux qui ne serait pas une formule, par exemple un lien de hameçonnage en texte clair.
