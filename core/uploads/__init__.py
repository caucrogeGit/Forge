from core.uploads.exceptions import (
    UploadError,
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadStorageError,
    UploadTooLargeError,
)
# IMAGES-MOVE-PROCESSING-001 (ADR-018) : le traitement d'image (save_image,
# variantes, verify_image_content, constantes ALLOWED_IMAGE_*, MediaRecord) a
# quitté le core pour l'opt-in forge-mvc-images. Le core n'en réexporte plus
# rien ; importer depuis `forge_mvc_images`. save_upload reste générique et
# délègue le chemin image-aware à l'opt-in (manager._require_image_processing).
from core.uploads.manager import (
    SavedUpload,
    delete_media_file,
    delete_upload,
    get_upload_path,
    save_upload,
    serve_media_file,
)
from core.uploads.storage import (
    is_safe_media_path,
    media_path_to_storage_path,
    normalize_media_path,
)

# Re-exports opt-in — fonctions applicatives médias. Détenues par
# forge-mvc-images depuis IMAGES-MOVE-APPLICATIVE-001 (ADR-018). Disponibles si
# l'opt-in est installé, silencieux sinon (le core ne dépend pas de l'opt-in).
try:
    from forge_mvc_images import (  # noqa: F401
        attach_media_to_entity,
        create_media_record,
        delete_media,
        delete_media_record,
        get_cover_media,
        get_media_gallery,
        get_media_record,
        list_media_for_entity,
        media_url,
        update_media_alt_text,
        update_media_position,
    )
except ImportError:
    pass

__all__ = [
    "SavedUpload",
    "UploadError",
    "UploadInvalidExtensionError",
    "UploadInvalidMimeTypeError",
    "UploadStorageError",
    "UploadTooLargeError",
    "delete_media_file",
    "delete_upload",
    "get_upload_path",
    "is_safe_media_path",
    "media_path_to_storage_path",
    "normalize_media_path",
    "save_upload",
    "serve_media_file",
]
