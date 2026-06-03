# Téléverser une vidéo

Objectif : **alimenter** le module en enregistrant une vidéo uploadée, sans
transcodage.

**Ce que vous allez apprendre :** `ingest_video`. Le formulaire envoie un
fichier ; la fonction le **valide** (taille, conteneur déclaré), le **stocke**
sous un UUID (jamais le nom de fichier utilisateur) et **insère** une ligne
`videos` au statut `uploaded` — **sans ffmpeg**. Le transcodage est un worker
séparé (niveau avancé) : jamais pendant une requête HTTP.

Premier palier du **niveau intermédiaire** de la progression vidéo, après le
[niveau débutant](../debutant/bilan.md).

## Ce que ce starter montre

- un formulaire `multipart/form-data` pour envoyer un fichier vidéo ;
- l'ingestion validée via `ingest_video` (stockage + insertion `videos`) ;
- le statut initial `uploaded` ;
- la liste des vidéos enregistrées, avec leur statut.

La table `videos` est créée par la migration livrée. **Aucun ffmpeg.**

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `request.file` | Récupérer le fichier vidéo reçu. | [Request](../../../reference/api.md#corehttp) |
| `forge_mvc_video.ingest.ingest_video` | Valider, stocker et enregistrer la vidéo (statut `uploaded`). | [Parcours vidéo](../../../video/parcours.md) |
| `VideoIngestError` | Upload refusé (vide, trop gros, conteneur non autorisé). | [Parcours vidéo](../../../video/parcours.md) |

## Tester

```bash
forge db:init
forge run
```

Ouvrez `https://localhost:8000/video-upload`, choisissez un fichier vidéo et
cliquez **Téléverser** : il apparaît dans la liste au statut `uploaded`. Vous
venez d'alimenter la table `videos` **sans lancer aucun transcodage**.

## Le contrôleur

```python
# mvc/controllers/video_upload_controller.py
from forge_mvc_video.ingest import VideoIngestError, ingest_video
from forge_mvc_video.storage.repository import VideoRepository


class VideoUploadController(BaseController):

    @staticmethod
    def upload(request: Request) -> Response:
        uploaded = request.file("video")
        if uploaded is None:
            return VideoUploadController._page(request, error="Aucun fichier sélectionné.")
        title = (request.form("title") or "").strip() or None
        try:
            ingest_video(uploaded.read(), uploaded.filename, title=title)
        except VideoIngestError as exc:
            return VideoUploadController._page(request, error=str(exc))
        return BaseController.redirect("/video-upload")
```

### Comprendre ce code

- `ingest_video(data, filename, title=...)` fait tout le travail sûr : validation,
  stockage sous UUID, insertion de la ligne `videos` au statut `uploaded`. Une
  `VideoIngestError` (fichier vide, trop gros, type refusé) est attrapée pour
  afficher un message clair.
- **Aucun ffmpeg n'est lancé ici** : l'upload est rapide et synchrone, le
  transcodage lourd est délégué à un worker CLI (modèle worker-CLI de Forge).
- En cas de succès, on **redirige** (POST-Redirect-GET).

## La vue

```html
<!-- mvc/views/video_upload/index.html -->
<form method="post" action="/video-upload" enctype="multipart/form-data">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <label>Titre <input type="text" name="title"></label>
  <label>Fichier vidéo <input type="file" name="video" required></label>
  <button type="submit">Téléverser</button>
</form>
```

### Comprendre ce code

- `enctype="multipart/form-data"` est **obligatoire** pour transmettre un
  fichier.
- Le formulaire reste protégé par **CSRF**, comme tout POST.

## À retenir

- `ingest_video` valide, stocke (sous UUID) et enregistre — **sans ffmpeg**.
- L'upload est synchrone ; le transcodage lourd est un **worker séparé**.
- Le statut démarre à `uploaded` ; il évoluera au niveau avancé.

## Après ce starter

Vous savez enregistrer une vidéo. La suite : la **servir** en streaming.

[Lire une vidéo](video-playback.md)
