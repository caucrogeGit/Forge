"""`MAIL-QUEUE-ATTACHMENTS-REFUSED-001` — une pièce jointe ne se perd plus en file.

`MAIL-ATTACHMENTS-001` a livré les pièces jointes. `MAIL-QUEUE-VIA-JOBS-001` a
livré la mise en file. Les deux ont été livrés séparément, et **ne composaient
pas**.

`message_to_payload` recopie huit champs nommés, et `attachments` n'en fait pas
partie. Mesuré : un message avec une pièce jointe passait la sérialisation sans
erreur, et ressortait de l'aller-retour **sans elle**.

L'email partait, le journal inscrivait `sent`, et le destinataire recevait un
corps annonçant un document absent. C'est le pire mode de panne du cycle : tout
paraît réussi.

La composition est pourtant celle que la documentation recommande, « la file est
le point de passage de tout ce qui ne doit pas faire attendre une requête » :
envoyer une facture en PDF est exactement ce qu'on met en file.

## Pourquoi refuser plutôt que sérialiser

La charge utile est du JSON rangé dans la colonne `payload` de la table `jobs`,
de type `text`. Sur MariaDB, un `TEXT` tient soixante-cinq mille octets ; une
pièce jointe de dix mégaoctets, plafond du paquet, en ferait quatorze millions
une fois encodée. **Deux cent treize fois la capacité de la colonne.**

Élargir la colonne ferait de la file une réserve de fichiers, ce qu'elle n'est
pas.

## Pourquoi le refus est uniforme

Accepter les petites pièces jointes ferait dépendre le comportement du poids du
fichier : cela marcherait en développement avec un PDF d'essai, et échouerait en
production sur un vrai document, par une erreur de base opaque. Une
fonctionnalité qui marche parfois est la plus difficile à diagnostiquer.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("forge_mvc_mail")

from forge_mvc_mail import (  # noqa: E402
    MailMessage,
    MailPayloadError,
    message_from_payload,
    message_to_payload,
)


def _message() -> MailMessage:
    return MailMessage(
        subject="Votre facture", to="client@exemple.test",
        body_text="Vous trouverez votre facture ci-jointe.")


def _avec_piece() -> MailMessage:
    return _message().with_attachment(
        "facture.pdf", b"%PDF-1.4 contenu", mime_type="application/pdf")


class TestRefus:

    def test_une_piece_jointe_est_refusee(self) -> None:
        """Le cas qui passait, et perdait le document."""
        with pytest.raises(MailPayloadError):
            message_to_payload(_avec_piece())

    def test_le_refus_nomme_le_fichier(self) -> None:
        """« Pièce jointe non supportée » ferait chercher laquelle sur un
        message qui en porte plusieurs."""
        with pytest.raises(MailPayloadError) as leve:
            message_to_payload(_avec_piece())

        assert "facture.pdf" in str(leve.value)

    def test_le_refus_dit_quoi_faire_a_la_place(self) -> None:
        """Un refus sans issue fait contourner, et le contournement est pire."""
        with pytest.raises(MailPayloadError) as leve:
            message_to_payload(_avec_piece())
        motif = str(leve.value)

        assert "référence" in motif
        assert "with_attachment" in motif

    def test_le_refus_est_uniforme(self) -> None:
        """Une petite pièce jointe est refusée comme une grande : le
        comportement ne dépend pas du poids du fichier."""
        petit = _message().with_attachment("note.txt", b"ok", mime_type="text/plain")

        with pytest.raises(MailPayloadError):
            message_to_payload(petit)

    def test_plusieurs_pieces_sont_toutes_nommees(self) -> None:
        message = _avec_piece().with_attachment(
            "cgv.pdf", b"%PDF", mime_type="application/pdf")

        with pytest.raises(MailPayloadError) as leve:
            message_to_payload(message)

        assert "facture.pdf" in str(leve.value)
        assert "cgv.pdf" in str(leve.value)


class TestAucuneRegression:

    def test_un_message_ordinaire_passe(self) -> None:
        charge = message_to_payload(_message())

        assert json.dumps(charge)
        assert message_from_payload(charge).subject == "Votre facture"

    def test_l_aller_retour_preserve_les_champs(self) -> None:
        """Comparé à la construction directe, et non à une forme écrite à la
        main : c'est le message d'origine que l'aller-retour doit rendre."""
        origine = _message()
        charge = message_to_payload(
            origine, message_type="facture",
            related_entity="Commande", related_id=12)
        refait = message_from_payload(charge)

        assert refait.to_addresses == origine.to_addresses
        assert refait.body_text == origine.body_text
        assert refait.subject == origine.subject
        assert charge["related_id"] == 12

    def test_l_envoi_direct_garde_ses_pieces_jointes(self) -> None:
        """Le refus ne vaut que pour la file : l'envoi immédiat les porte."""
        assert len(_avec_piece().attachments) == 1


class TestLeDefautNePeutPasRevenir:

    def test_aucun_champ_du_message_n_est_perdu_en_silence(self) -> None:
        """La cause était une liste de champs recopiés, muette sur ce qu'elle
        laissait derrière.

        Tout champ de `MailMessage` doit être soit recopié, soit **refusé
        explicitement**, soit dérivé d'un autre. Un champ ajouté demain qui
        n'entrerait dans aucune de ces cases repartirait dans le silence.
        """
        from forge_mvc_mail.queueing import _CHAMPS

        portes = set(_CHAMPS)
        # `attachments` est refusé, les `*_addresses` sont les formes normalisées
        # des champs déjà portés, et le message les recalcule à la construction.
        refuses = {"attachments"}
        derives = {
            "to_addresses", "cc_addresses", "bcc_addresses", "reply_to_addresses"}

        tous = set(MailMessage.__dataclass_fields__)
        oublies = tous - portes - refuses - derives

        assert not oublies, (
            f"ces champs ne sont ni recopiés, ni refusés, ni dérivés : "
            f"{', '.join(sorted(oublies))}. Un champ oublié se perd en silence "
            f"au passage par la file, comme les pièces jointes le faisaient.")
