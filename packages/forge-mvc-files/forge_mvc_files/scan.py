# pyright: strict
"""Analyse d'un fichier déposé avant écriture (`FILES-SCAN-HOOK-001`).

Forge valide l'extension, le type MIME, la taille et les premiers octets d'un
envoi. Aucun de ces contrôles ne dit si le contenu est malveillant : un PDF
porteur d'une charge active a l'extension, le type et la signature d'un PDF.

Le paquet ne fournit **aucune analyse**, et n'en fournira pas.

Un moteur antivirus est un service à installer, à tenir à jour et à surveiller,
avec son cycle de vie propre. L'embarquer ferait de `forge-mvc-files` une usine
métier, que le principe 8 refuse, et donnerait au projet une base de signatures
périmée le jour de sa publication.

Ce module fournit la **prise** : l'application branche son analyseur, Forge
l'appelle au bon moment.

## Deux règles qui font tout l'intérêt de la prise

**L'analyse précède l'écriture.** Un fichier analysé après avoir touché le
disque y est déjà, et l'y laisser quelques millisecondes suffit à ce qu'une
sauvegarde ou un indexeur le voie.

**Une analyse qui échoue refuse le dépôt.** Un analyseur qui lève, qui expire
ou qui rend n'importe quoi ne dit **pas** que le fichier est sain, il ne dit
rien. Traiter ce silence comme un feu vert est la faute classique de ce genre
de branchement : le jour où le service antivirus tombe, tout passe, et rien ne
le signale.

## Ce que le paquet ne fait pas non plus

Il n'impose pas de délai d'attente. L'analyseur est appelé pendant la requête,
et une analyse qui traîne la retient : borner cette durée appartient à
l'implémentation, qui seule sait parler à son moteur.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from core.forms.upload_exceptions import UploadError

__all__ = [
    "ScanVerdict",
    "FileScanner",
    "UploadRejectedByScanError",
    "ScannerUnavailableError",
    "register_file_scanner",
    "unregister_file_scanner",
    "registered_scanners",
    "clear_file_scanners",
    "scan_upload",
]


@dataclass(frozen=True)
class ScanVerdict:
    """Ce qu'un analyseur répond.

    Immuable : le verdict traverse le code qui décide d'écrire ou non, et un
    verdict modifiable après coup ne serait plus un verdict.
    """

    is_clean: bool
    detail: str = ""

    @classmethod
    def clean(cls) -> "ScanVerdict":
        return cls(True)

    @classmethod
    def infected(cls, detail: str) -> "ScanVerdict":
        """Refus motivé. Le motif est journalisé, jamais rendu au déposant.

        Le nom d'une signature renseigne sur ce qui est détecté, donc sur ce
        qui ne l'est pas.
        """
        return cls(False, detail)


#: Un analyseur reçoit le contenu et le nom d'origine, et rend un verdict.
FileScanner = Callable[[bytes, str], ScanVerdict]


class UploadRejectedByScanError(UploadError):
    """Un analyseur a refusé le contenu.

    Descend d'`UploadError`, donc traitée par les gestionnaires déjà en place.
    À distinguer de `ScannerUnavailableError` : ici le dispositif fonctionne et
    a rendu un avis, rien n'est à réparer.
    """


class ScannerUnavailableError(UploadError):
    """Un analyseur n'a pas pu rendre d'avis.

    Le dépôt est refusé, mais la cause est une **panne** et non un fichier
    douteux : c'est l'exploitant qu'il faut prévenir, pas le déposant. Le type
    distinct existe pour que les deux cas ne se confondent pas dans les
    journaux, où « refusé » sans nuance ferait chercher un problème de fichier.
    """


_scanners: list[FileScanner] = []


def register_file_scanner(scanner: FileScanner) -> None:
    """Branche un analyseur, appelé par `save_upload` avant l'écriture.

    L'enregistrement est explicite, et c'est là toute la déclaration : une fois
    branché, l'analyseur tourne à chaque dépôt, comme un middleware inscrit
    tourne à chaque requête. Sans enregistrement, rien ne change.

    Plusieurs analyseurs peuvent cohabiter, consultés dans l'ordre
    d'enregistrement. Le premier refus arrête la série : ce qui suit ne
    changerait pas la décision.

    Un même analyseur enregistré deux fois n'est branché qu'une fois, un
    module importé deux fois ne devant pas doubler le travail.
    """
    if not callable(scanner):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"Un analyseur doit être appelable. Reçu : {scanner!r}.")
    if scanner not in _scanners:
        _scanners.append(scanner)


def unregister_file_scanner(scanner: FileScanner) -> bool:
    """Débranche un analyseur. Vrai s'il était branché."""
    if scanner in _scanners:
        _scanners.remove(scanner)
        return True
    return False


def registered_scanners() -> "tuple[FileScanner, ...]":
    """Analyseurs branchés, dans l'ordre d'appel.

    Rend une copie figée : la liste interne ne se modifie que par les fonctions
    d'enregistrement, sans quoi un appelant pourrait la vider sans le vouloir.
    """
    return tuple(_scanners)


def clear_file_scanners() -> None:
    """Débranche tout. Utile aux tests, et à un redémarrage à chaud."""
    _scanners.clear()


def scan_upload(data: bytes, original_name: str) -> None:
    """Soumet un contenu aux analyseurs branchés. Ne rend rien s'il passe.

    Sans analyseur branché, ne fait rien et ne coûte rien.

    Raises:
        UploadRejectedByScanError: un analyseur a rendu un verdict négatif.
        ScannerUnavailableError: un analyseur a levé, ou rendu autre chose
            qu'un `ScanVerdict`. Le dépôt est refusé faute d'avis, jamais
            accepté par défaut.
    """
    if not _scanners:
        return

    for scanner in _scanners:
        try:
            verdict = scanner(data, original_name)
        except Exception as exc:
            raise ScannerUnavailableError(
                "L'analyse du fichier a échoué, le dépôt est refusé par "
                f"précaution : {exc}"
            ) from exc

        if not isinstance(verdict, ScanVerdict):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ScannerUnavailableError(
                "Un analyseur doit rendre un ScanVerdict, le dépôt est refusé "
                f"par précaution. Reçu : {verdict!r}."
            )

        if not verdict.is_clean:
            raise UploadRejectedByScanError(
                "Le fichier déposé a été refusé par l'analyse de sécurité."
            )
