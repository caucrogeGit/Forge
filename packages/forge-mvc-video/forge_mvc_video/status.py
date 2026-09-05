# pyright: strict
"""État de traitement, restituable dans une interface (`VIDEO-STATUS-UI-001`).

Une vidéo passe par quatre états, `uploaded`, `processing`, `ready` et
`failed`. Le paquet les enregistrait sans jamais donner de quoi les montrer :
après l'envoi, la page ne savait pas dire où en était le transcodage, et chaque
application réécrivait sa table de correspondance vers un libellé français.

## Le point qui n'est pas cosmétique

`error_message` porte la sortie d'erreur de ffmpeg, qui contient les **chemins
absolus** des fichiers d'entrée et de sortie. Le rendre à un visiteur publierait
l'arborescence du serveur, et un gabarit qui affiche « la raison de l'échec »
le fait sans y penser.

`VideoStatusView` sépare donc deux champs :

- `public_message`, destiné à l'écran, qui ne dit que ce que le visiteur peut
  faire ;
- `technical_detail`, destiné au journal et à l'exploitant, jamais rendu.

La séparation est portée par le type, non par une consigne de documentation :
un gabarit ne peut pas afficher par accident un champ qui n'est pas là.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forge_mvc_video.storage.repository import (
    STATUS_FAILED,
    STATUS_PROCESSING,
    STATUS_READY,
    STATUS_UPLOADED,
    VALID_STATUSES,
)

__all__ = [
    "STATUS_LABELS",
    "PENDING_STATUSES",
    "FINAL_STATUSES",
    "UNKNOWN_LABEL",
    "VideoStatusView",
    "describe_video_status",
]

#: Libellé destiné à l'écran, par état.
STATUS_LABELS: "dict[str, str]" = {
    STATUS_UPLOADED: "En attente de traitement",
    STATUS_PROCESSING: "Transcodage en cours",
    STATUS_READY: "Prête à la lecture",
    STATUS_FAILED: "Traitement en échec",
}

#: Libellé d'un état que le paquet ne connaît pas.
UNKNOWN_LABEL = "État inconnu"

#: États où le traitement n'a pas encore rendu son verdict.
PENDING_STATUSES = frozenset({STATUS_UPLOADED, STATUS_PROCESSING})

#: États où plus rien ne bougera sans une action.
FINAL_STATUSES = frozenset({STATUS_READY, STATUS_FAILED})

_PUBLIC_MESSAGES: "dict[str, str]" = {
    STATUS_UPLOADED: "La vidéo est reçue, son traitement va commencer.",
    STATUS_PROCESSING: "La vidéo est en cours de traitement, revenez dans un instant.",
    STATUS_READY: "La vidéo est disponible.",
    STATUS_FAILED: "Le traitement de cette vidéo a échoué. Essayez un autre fichier, "
                   "ou signalez le problème à un administrateur.",
}


@dataclass(frozen=True)
class VideoStatusView:
    """Ce qu'une interface peut montrer d'un état de traitement.

    Immuable : la vue traverse le rendu, et un état modifié en route
    afficherait autre chose que ce qui a été lu.
    """

    status: str
    label: str
    public_message: str
    technical_detail: "str | None" = None
    #: Métadonnées sondées au transcodage. Elles étaient inscrites en base et
    #: jamais rendues (`VIDEO-POSTER-ROUTE-001`).
    duration_seconds: "int | None" = None
    width: "int | None" = None
    height: "int | None" = None
    #: Une vignette existe. Son chemin de stockage n'est pas rendu, la route
    #: `/videos/<uuid>/poster` la sert.
    has_poster: bool = False

    @property
    def is_known(self) -> bool:
        return self.status in VALID_STATUSES

    @property
    def is_ready(self) -> bool:
        return self.status == STATUS_READY

    @property
    def is_failed(self) -> bool:
        return self.status == STATUS_FAILED

    @property
    def is_pending(self) -> bool:
        """Vrai tant que le traitement n'a pas rendu son verdict.

        C'est la question que pose une page qui se rafraîchit : faut il
        redemander l'état ?
        """
        return self.status in PENDING_STATUSES

    @property
    def is_final(self) -> bool:
        return self.status in FINAL_STATUSES

    def as_public_dict(self) -> "dict[str, Any]":
        """Représentation **sûre**, destinée à une réponse HTTP.

        `technical_detail` en est absent par construction : la sortie d'erreur
        de ffmpeg porte les chemins absolus du serveur.

        Les métadonnées accompagnent l'état (`VIDEO-POSTER-ROUTE-001`). Elles
        étaient sondées au transcodage et inscrites en base, et cette réponse ne
        les rendait pas : une interface qui sonde l'état pour savoir quand
        afficher n'avait ni la durée, ni les dimensions, ni la vignette, et
        devait interroger la base par un chemin qu'elle n'a pas.

        `poster_path` n'est **pas** rendu : c'est un chemin de stockage, pas une
        URL. Le rendre publierait l'arborescence du serveur, ce que le reste de
        cette classe évite. Un booléen dit qu'une vignette existe, et la route
        `/videos/<uuid>/poster` la sert.
        """
        rendu: "dict[str, Any]" = {
            "status": self.status,
            "label": self.label,
            "message": self.public_message,
            "ready": self.is_ready,
            "failed": self.is_failed,
            "pending": self.is_pending,
            "has_poster": self.has_poster,
        }
        if self.duration_seconds is not None:
            rendu["duration_seconds"] = self.duration_seconds
        if self.width is not None and self.height is not None:
            rendu["width"] = self.width
            rendu["height"] = self.height
        return rendu


def _entier(row: "dict[str, Any] | None", cle: str) -> "int | None":
    """Entier d'une colonne, ou `None`.

    Une ligne peut porter `None`, une chaîne venue d'un pilote, ou rien du tout.
    Lever ici remplacerait une page par une erreur, alors que le contrat de
    cette fonction est justement de toujours pouvoir afficher quelque chose.
    """
    if not row:
        return None
    valeur = row.get(cle)
    if valeur is None or isinstance(valeur, bool):
        return None
    try:
        return int(valeur)  # pyright: ignore[reportArgumentType]
    except (TypeError, ValueError):
        return None


def describe_video_status(row: "dict[str, Any] | None") -> VideoStatusView:
    """Vue d'état pour une ligne de la table `videos`.

    Une ligne absente ou un état inconnu ne lèvent pas : une interface doit
    pouvoir afficher quelque chose, et une exception ici remplacerait une page
    dégradée par une page d'erreur.
    """
    brut = "" if not row else str(row.get("status") or "").strip()
    connu = brut in VALID_STATUSES

    detail: "str | None" = None
    if row and brut == STATUS_FAILED:
        message = row.get("error_message")
        detail = str(message) if message else None

    return VideoStatusView(
        status=brut,
        label=STATUS_LABELS.get(brut, UNKNOWN_LABEL),
        public_message=_PUBLIC_MESSAGES.get(
            brut,
            "L'état de cette vidéo n'a pas pu être déterminé."
            if not connu
            else "",
        ),
        technical_detail=detail,
        duration_seconds=_entier(row, "duration_seconds"),
        width=_entier(row, "width"),
        height=_entier(row, "height"),
        has_poster=bool(row and row.get("poster_path")),
    )
