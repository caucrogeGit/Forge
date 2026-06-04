"""Hiérarchie d'exceptions de validation de fichier — reste dans le core.

FILES-VALIDATORS-KEEP-001 (ADR-019) : déplacée hors de ``core/uploads/`` (qui
part vers l'opt-in ``forge-mvc-files``). Ces exceptions restent dans le core car
``core/forms`` (``FileField``) en dépend, et le core ne peut pas dépendre d'un
opt-in (ADR-004). Ce sont de simples types d'erreur, sans I/O.

``forge-mvc-files`` réutilise ces exceptions (il dépend du core).
"""


class UploadError(Exception):
    """Erreur de base pour la validation/le service d'upload Forge."""


class UploadTooLargeError(UploadError):
    """Le fichier depasse la taille maximale autorisee."""


class UploadInvalidExtensionError(UploadError):
    """L'extension du fichier n'est pas autorisee."""


class UploadInvalidMimeTypeError(UploadError):
    """Le type MIME du fichier n'est pas autorise."""


class UploadStorageError(UploadError):
    """Le fichier ne peut pas etre ecrit ou supprime proprement."""
