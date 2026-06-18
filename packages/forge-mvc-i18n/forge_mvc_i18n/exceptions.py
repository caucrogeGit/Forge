# pyright: strict
class I18nError(Exception):
    """Erreur de base pour l'internationalisation Forge."""


class TranslationCatalogError(I18nError):
    """Un catalogue de traductions est absent, illisible ou invalide."""
