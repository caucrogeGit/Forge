# pyright: strict
"""Envoi d'email différé par une file de tâches (MAIL-QUEUE-VIA-JOBS-001).

Envoyer un email pendant une requête HTTP la fait attendre le serveur SMTP.
Une seconde de latence est courante, dix le sont aussi quand le relais est
lent, et une panne du relais devient une panne du formulaire : l'utilisateur
voit une erreur alors que son inscription est enregistrée.

Ce module fournit de quoi confier l'envoi à `forge-mvc-jobs`, sans que les
deux opt-ins se connaissent.

## Aucune dépendance croisée

`forge-mvc-mail` n'importe **jamais** `forge_mvc_jobs`, et l'inverse est vrai
aussi. Ce module ne fait que deux choses : traduire un message en charge utile
JSON, et rendre un gestionnaire que la file appellera. C'est l'application qui
met les deux en présence, et elle seule décide d'installer les deux paquets.

## Le motif officiel

Côté requête, on met en file au lieu d'envoyer.

    from forge_mvc_jobs import enqueue
    from forge_mvc_mail import MAIL_JOB_TASK, message_to_payload

    enqueue(MAIL_JOB_TASK, message_to_payload(message))

Côté ouvrier, on enregistre le gestionnaire.

    from forge_mvc_jobs import run_worker
    from forge_mvc_mail import MAIL_JOB_TASK, make_mail_job_handler

    run_worker({MAIL_JOB_TASK: make_mail_job_handler()})
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, cast

from forge_mvc_mail.exceptions import MailError
from forge_mvc_mail.message import MailMessage

__all__ = [
    "MAIL_JOB_TASK",
    "MailPayloadError",
    "message_to_payload",
    "message_from_payload",
    "make_mail_job_handler",
]

#: Nom de tâche du motif officiel.
#:
#: Nommé ici pour que la mise en file et le gestionnaire désignent la même,
#: plutôt que de recopier une chaîne de part et d'autre.
MAIL_JOB_TASK = "mail.send"

#: Champs transportés. Les adresses dérivées (`to_addresses` et les autres) sont
#: recalculées à la reconstruction : les transporter ferait deux sources pour la
#: même information, et la validation les reconstruit de toute façon.
_CHAMPS = (
    "subject", "to", "body_text", "body_html",
    "from_email", "cc", "bcc", "reply_to",
)


class MailPayloadError(MailError):
    """Charge utile inexploitable : champ manquant, ou message invalide."""


def message_to_payload(
    message: MailMessage,
    *,
    message_type: str = "",
    related_entity: str = "",
    related_id: "int | None" = None,
) -> "dict[str, Any]":
    """Traduit un message en charge utile JSON, prête pour `enqueue`.

    Les trois paramètres de journalisation suivent le message : sans eux, une
    file d'envoi perdrait la trace que `mailer.send` sait écrire, et le journal
    des envois deviendrait muet dès qu'on diffère.

    Le message est **validé à la construction** : le mettre en file ne peut
    donc pas différer une erreur de saisie jusqu'à l'ouvrier, où plus personne
    ne la verrait.

    Raises:
        MailPayloadError: le message porte une pièce jointe. Voir ci dessous.

    ## Une pièce jointe ne passe pas par la file, et le dire vaut mieux

    La charge utile est du JSON, rangé dans la colonne `payload` de la table
    `jobs`, de type `text`. Sur MariaDB, un `TEXT` tient soixante-cinq mille
    octets ; une pièce jointe de dix mégaoctets, plafond du paquet, en ferait
    quatorze millions une fois encodée en base64. Deux cent treize fois la
    capacité de la colonne.

    Les deux fonctionnalités ont été livrées séparément et ne composaient pas.
    `message_to_payload` ne recopiait que huit champs, et les pièces jointes
    **disparaissaient en silence** : l'email partait sans elles, le journal
    inscrivait `sent`, et le destinataire recevait un corps annonçant un
    document absent (`MAIL-QUEUE-ATTACHMENTS-REFUSED-001`).

    Le refus est **uniforme**, et non conditionné à la taille. Accepter les
    petites ferait dépendre le comportement du poids du fichier, et une
    fonctionnalité qui marche parfois est la plus difficile à diagnostiquer.

    Ce qu'il faut faire à la place : ranger le fichier, mettre en file sa
    **référence**, et l'attacher dans le gestionnaire, au moment de l'envoi.
    """
    if message.attachments:
        noms = ", ".join(piece.filename for piece in message.attachments)
        raise MailPayloadError(
            f"Ce message porte {len(message.attachments)} pièce(s) jointe(s) "
            f"({noms}) et ne peut pas être mis en file : la charge utile est du "
            f"JSON rangé dans une colonne texte, qu'une pièce jointe encodée "
            f"dépasserait. Rangez le fichier, mettez en file sa référence, et "
            f"attachez le dans le gestionnaire avec "
            f"`message.with_attachment(...)` au moment de l'envoi."
        )

    charge: dict[str, Any] = {
        champ: _serialisable(getattr(message, champ)) for champ in _CHAMPS
    }
    if message_type:
        charge["message_type"] = message_type
    if related_entity:
        charge["related_entity"] = related_entity
    if related_id is not None:
        charge["related_id"] = related_id
    return charge


def _serialisable(valeur: Any) -> Any:
    """Ramène une valeur à ce que JSON accepte, sans rien inventer."""
    if valeur is None or isinstance(valeur, (str, int, float, bool)):
        return valeur
    if isinstance(valeur, (list, tuple, set)):
        elements = cast("Iterable[Any]", valeur)
        return [str(element) for element in elements]
    return str(valeur)


def message_from_payload(payload: "dict[str, Any]") -> MailMessage:
    """Reconstruit un message depuis une charge utile.

    Raises:
        MailPayloadError: la charge n'est pas exploitable. L'erreur d'origine
            est chaînée : une charge écrite par une version antérieure doit
            dire pourquoi elle est refusée, pas disparaître dans un `failed`
            sans motif.
    """
    if not isinstance(payload, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise MailPayloadError(f"charge utile invalide : {type(payload).__name__}.")
    try:
        return MailMessage(**{
            champ: payload[champ] for champ in _CHAMPS if champ in payload
        })
    except (TypeError, ValueError, MailError) as exc:
        # `MailValidationError` descend de `MailError`, pas de `ValueError` :
        # sans elle dans la liste, un message invalide remonterait tel quel et
        # l'appelant ne saurait pas que la charge est en cause.
        raise MailPayloadError(f"charge utile inexploitable : {exc}") from exc


def make_mail_job_handler(
    mailer: Any = None,
) -> Callable[["dict[str, Any]"], None]:
    """Rend le gestionnaire de tâche à enregistrer auprès de la file.

    `mailer` permet d'injecter un envoyeur, ce dont les tests ont besoin. À
    défaut, il est construit depuis la configuration au **premier appel**, et
    non à la création : un ouvrier qui démarre avant que la configuration soit
    lue ne doit pas échouer à l'enregistrement de ses gestionnaires.

    Le gestionnaire **lève** quand l'envoi échoue. C'est ce qui déclenche le
    réessai de la file : rendre `None` en silence ferait marquer la tâche comme
    réussie, et l'email ne partirait jamais.
    """
    def handler(payload: "dict[str, Any]") -> None:
        envoyeur = mailer
        if envoyeur is None:
            from forge_mvc_mail.mailer import Mailer

            envoyeur = Mailer.from_config()

        message = message_from_payload(payload)
        resultat = envoyeur.send(
            message,
            message_type=str(payload.get("message_type", "")),
            related_entity=str(payload.get("related_entity", "")),
            related_id=payload.get("related_id"),
        )
        # `skipped` n'est pas un échec : `NullTransport` rend un succès sauté
        # pour désactiver le mail, et faire échouer la tâche ferait réessayer
        # sans fin un envoi que personne ne veut.
        if not resultat.success:
            raise MailError(
                f"envoi refusé par le transport {resultat.transport} : "
                f"{resultat.detail or 'sans motif'}"
            )

    return handler
