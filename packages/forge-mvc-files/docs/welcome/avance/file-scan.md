# Avancé 4 : Le crochet d'analyse

Objectif : refuser un dépôt qu'un antivirus signale, sans que Forge embarque un antivirus.

## Forge ne scanne rien, et branche ce qui scanne

```python
from forge_mvc_files import ScanVerdict, register_file_scanner


def analyser(data, original_name):
    if antivirus.est_infecte(data):
        return ScanVerdict(False, "Fichier signalé par l'analyse.")
    return ScanVerdict(True)


register_file_scanner(analyser)
```

Chaque dépôt passe par les analyseurs enregistrés, avant d'être écrit.

| Retour | Effet |
|---|---|
| `ScanVerdict(True)` | le dépôt continue |
| `ScanVerdict(False, motif)` | `UploadRejectedByScanError`, le fichier n'est pas écrit |
| autre chose, ou une exception | `ScannerUnavailableError`, le dépôt est refusé |

!!! danger "Un analyseur en panne refuse le dépôt"
    C'est délibéré, et c'est l'inverse du confort.

    Le jour où l'antivirus tombe, laisser passer les dépôts est exactement le moment où il ne faut pas : une analyse qu'on ne peut pas faire n'est pas une analyse réussie.

!!! warning "Rendez un `ScanVerdict`, jamais une chaîne"
    Un retour d'un autre type est traité comme une panne d'analyseur, et refuse le dépôt.

    Le voisin `forge-mvc-workflow` emploie la convention opposée pour ses conditions, qui rendent un motif ou `None` : les deux paquets ne se ressemblent pas sur ce point, et il vaut mieux le savoir que le supposer.

!!! info "Deux erreurs, deux causes, deux messages"
    `UploadRejectedByScanError` dit que le fichier est refusé ; `ScannerUnavailableError` dit qu'on n'a pas pu le savoir.

    Les confondre ferait dire à un utilisateur que son fichier est infecté alors que le service est simplement tombé.

## À retenir

- Forge branche un analyseur, il n'en fournit aucun.
- Une panne d'analyse refuse le dépôt, elle ne l'autorise pas.
- Le refus et l'indisponibilité sont deux erreurs distinctes.

## Étape suivante

[Suivant : le registre et les orphelins](file-registre.md)
