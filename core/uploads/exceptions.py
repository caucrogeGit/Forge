class UploadError(Exception):
    """Erreur de base pour le service d'upload Forge."""


class UploadTooLargeError(UploadError):
    """Le fichier depasse la taille maximale autorisee."""


class UploadInvalidExtensionError(UploadError):
    """L'extension du fichier n'est pas autorisee."""


class UploadInvalidMimeTypeError(UploadError):
    """Le type MIME du fichier n'est pas autorise."""


class UploadStorageError(UploadError):
    """Le fichier ne peut pas etre ecrit ou supprime proprement."""
