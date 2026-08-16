# pyright: strict
"""MAIL-SEPARATEURS-LIGNE-001 : tout séparateur de ligne est refusé, pas seulement CR et LF.

`_check_no_injection` ne cherchait que `[\\r\\n]`. Or Python coupe une ligne sur
huit autres caractères, que `str.splitlines()` énumère : tabulation verticale,
saut de page, les trois séparateurs de fichier, groupe et enregistrement, la
nouvelle ligne de la norme NEL, et les deux séparateurs Unicode de ligne et de
paragraphe.

Mesuré avant correctif : les huit passaient le constructeur, puis
`as_email_message` levait un `ValueError` **de la bibliothèque standard**, au
message anglais et sans rapport avec le vocabulaire de l'opt-in.

Il n'y avait pas de faille : la bibliothèque standard refuse ces valeurs, donc
aucune en-tête forgée ne partait. Le défaut est un **contrat rompu**. Une
application qui attrape `MailValidationError` pour rendre un message propre
recevait une exception d'un autre type, et donc une erreur cinq cents là où elle
avait prévu un refus de formulaire.

Le refus vise volontairement `str.splitlines()` plutôt qu'une liste tenue à la
main : c'est la définition que la bibliothèque standard applique elle-même en
écrivant les en-têtes, et une liste écrite à la main dériverait d'elle en
silence à la première version de Python qui l'étendrait.
"""
from __future__ import annotations

import pytest

# ADR-040 : le paquet peut ne pas être installé dans l'environnement qui collecte
# la suite du cœur ; le garde-fou `test_optin_tests_importorskip_001` l'impose.
pytest.importorskip("forge_mvc_mail")

from forge_mvc_mail.exceptions import MailValidationError  # noqa: E402
from forge_mvc_mail.message import MailMessage  # noqa: E402


#: Les huit séparateurs que `_NEWLINE_RE` laissait passer, plus les deux qu'il
#: attrapait déjà. Tous coupent une ligne au sens de `str.splitlines()`.
#:
#: Écrits en **échappement** et jamais littéralement : un U+2028 posé tel quel
#: dans le source fait alerter les éditeurs, qui proposent de le supprimer, ce
#: qui viderait ce test de son objet sans que rien ne le signale.
SEPARATEURS = [
    "\n", "\r", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029",
]


def test_les_separateurs_testes_coupent_vraiment_une_ligne() -> None:
    """Garde du garde : sans lui, la liste pourrait tester des caractères inertes.

    Si un caractère cessait d'être un séparateur, l'exiger deviendrait une
    contrainte arbitraire plutôt qu'une protection.
    """
    for separateur in SEPARATEURS:
        assert len(f"a{separateur}b".splitlines()) > 1, ascii(separateur)


@pytest.mark.parametrize("separateur", SEPARATEURS, ids=ascii)
def test_le_sujet_refuse_tout_separateur(separateur: str) -> None:
    with pytest.raises(MailValidationError):
        MailMessage(
            subject=f"Bonjour{separateur}Bcc: pirate@evil.tld",
            to="a@b.c",
            body_text="x",
        )


@pytest.mark.parametrize("separateur", SEPARATEURS, ids=ascii)
def test_l_expediteur_refuse_tout_separateur(separateur: str) -> None:
    with pytest.raises(MailValidationError):
        MailMessage(
            subject="Bonjour",
            to="a@b.c",
            body_text="x",
            from_email=f"exp@forge.tld{separateur}Bcc: pirate@evil.tld",
        )


@pytest.mark.parametrize("champ", ["to", "cc", "bcc", "reply_to"])
def test_les_champs_d_adresses_refusent_tout_separateur(champ: str) -> None:
    """Les quatre champs d'adresses passent par le même contrôle, et doivent le montrer."""
    for separateur in SEPARATEURS:
        arguments: dict[str, object] = {
            "subject": "Bonjour",
            "to": "a@b.c",
            "body_text": "x",
        }
        arguments[champ] = f"a@b.c{separateur}Bcc: pirate@evil.tld"
        with pytest.raises(MailValidationError):
            MailMessage(**arguments)  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("separateur", SEPARATEURS, ids=ascii)
def test_le_refus_precede_le_rendu(separateur: str) -> None:
    """Le refus vient de l'opt-in, jamais de la bibliothèque standard.

    C'est la distinction qui compte : les deux empêchent l'en-tête forgée, mais
    une seule des deux est le contrat annoncé par `forge-mvc-mail`.
    """
    with pytest.raises(MailValidationError):
        message = MailMessage(
            subject=f"Bonjour{separateur}Bcc: pirate@evil.tld",
            to="a@b.c",
            body_text="x",
        )
        message.as_email_message("exp@forge.tld")


def test_un_sujet_ordinaire_reste_accepte() -> None:
    """Contrôle négatif du correctif : il ne doit rien refuser d'autre.

    Espaces, accents et ponctuation ne coupent pas de ligne et doivent passer,
    sans quoi le durcissement casserait des envois légitimes.
    """
    message = MailMessage(
        subject="Votre reçu n° 42 : « merci ! »",
        to="a@b.c",
        body_text="x",
    )
    assert "reçu" in message.as_email_message("exp@forge.tld")["Subject"]
