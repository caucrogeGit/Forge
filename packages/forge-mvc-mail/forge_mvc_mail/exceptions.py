# pyright: strict
class MailError(Exception):
    """Erreur de base pour le service mail Forge."""


class MailConfigurationError(MailError):
    """La configuration SMTP est incomplète ou incohérente."""


class MailValidationError(MailConfigurationError):
    """Le message mail lui-même est invalide (champ manquant ou injection détectée)."""


class MailTemplateError(MailConfigurationError):
    """Un template mail est absent, illisible ou produit une erreur de rendu."""


class MailSendError(MailError):
    """L'envoi SMTP a échoué."""
