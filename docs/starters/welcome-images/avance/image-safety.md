# Garde de sécurité à l'upload

Objectif : comprendre **comment Forge refuse une image piégée** — un fichier
déguisé en image, ou une image-bombe conçue pour saturer le serveur.

**Ce que vous allez apprendre :** avant toute écriture, `verify_image_content`
ouvre réellement le fichier pour confirmer que c'est une image d'un format
autorisé, et rejette les images dont la surface dépasse `upload_max_image_pixels`
(défense anti-bombe de décompression). Ce palier met la garde en scène **sans
rien écrire** ni base de données.

Troisième palier du **niveau avancé** de la progression images.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation »).
    Comme images est une brique **bibliothèque** (pas de CLI `images:doctor`),
    ce palier joue le rôle de diagnostic de sécurité.

## Ce que ce starter montre

- la politique de sécurité affichée (formats acceptés, surface maximale) ;
- `verify_image_content` appliqué à un fichier reçu, **sans l'enregistrer** ;
- un verdict clair : image acceptée, ou rejetée avec la raison ;
- la même politique en JSON (`GET /image-safety/inspect`).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.verify_image_content` | Vérifier qu'un contenu est une vraie image autorisée. | [Médias](../../../features/media.md) |
| `core.forge.get` | Lire `upload_max_image_pixels` (budget anti-bombe). | [Configuration](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-safety`, envoyez une vraie image (acceptée),
puis un fichier texte renommé en `.jpg` (rejeté) : la garde fait la différence
sur le **contenu**, pas sur l'extension.

## Le contrôleur

```python
# mvc/controllers/image_safety_controller.py
from core.forge import get as get_config
from forge_mvc_files import UploadError
from forge_mvc_images import ALLOWED_IMAGE_EXTENSIONS, verify_image_content


class ImageSafetyController(BaseController):

    @staticmethod
    def check(request: Request) -> Response:
        uploaded = request.file("image")
        try:
            verify_image_content(uploaded.content)
        except UploadError as exc:
            # rejeté : contenu non-image, format interdit, ou image trop grande
            ...
        # accepté : c'est bien une image valide, rien n'a été écrit
```

### Comprendre ce code

- La garde décide sur le **contenu binaire**, pas sur l'extension ni le
  `Content-Type` (tous deux falsifiables).
- Le budget `upload_max_image_pixels` (24 Mpx par défaut) rejette une image
  démesurée **avant** tout décodage coûteux — c'est la défense anti-bombe.
- On ne fait que vérifier : aucun fichier n'est écrit. Idéal pour un diagnostic.

## À retenir

- `verify_image_content` valide le **contenu** avant toute écriture disque.
- L'anti-bombe rejette les images démesurées (`upload_max_image_pixels`).
- C'est cette garde que `save_image_upload` applique en interne à chaque upload.

## Après ce starter

Vous avez fait le tour du niveau avancé : couverture, suppression propre,
sécurité.

[Bilan du niveau avancé](bilan.md)
