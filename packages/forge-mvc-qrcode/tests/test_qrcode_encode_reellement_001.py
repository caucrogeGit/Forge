"""QRCODE-ENCODE-REEL-001 — le PNG rendu porte vraiment le texte demandé.

Les contrôles existants vérifiaient que la sortie **ressemble** à une image :
`png.startswith(_PNG_MAGIC)` et `"<svg" in svg`. Un PNG blanc aux bons octets
d'en-tête les passait tous, et un générateur qui aurait ignoré son argument
aussi.

C'est la signature poursuivie par tout ce pré-mortem, transposée hors base de
données : on vérifie la **construction** et jamais l'**effet**.

## Ce que ce fichier vérifie, et ce qu'il ne peut pas

Aucun décodeur de QR Code n'est disponible ici, et en ajouter un ferait entrer
une dépendance système (`libzbar`) dans la suite pour un seul opt-in. Ce
fichier ne prouve donc **pas** qu'un téléphone lira le code.

Il prouve trois choses plus fortes que « ça ressemble à un PNG » :

- la matrice change avec le texte, donc le contenu est bien encodé ;
- les pixels du PNG **correspondent à cette matrice**, donc l'image la
  représente fidèlement, à la bonne échelle et avec la bonne marge ;
- les motifs de repérage sont aux trois coins, sans quoi aucun lecteur ne
  trouverait le code.
"""
from __future__ import annotations

import io

import pytest

from forge_mvc_qrcode.generator import QrCode

Image = pytest.importorskip("PIL.Image", reason="Pillow absent")


def _matrice(code: QrCode) -> list[list[int]]:
    """La matrice de modules, telle que segno la calcule."""
    return [list(ligne) for ligne in code._qr.matrix]  # pyright: ignore[reportPrivateUsage]


def _pixels_du_png(png: bytes, *, scale: int, border: int) -> list[list[int]]:
    """Relit le PNG et rend la matrice de modules qu'il représente.

    Un module est lu en son centre, ce qui rend le contrôle insensible à un
    éventuel lissage des bords.
    """
    image = Image.open(io.BytesIO(png)).convert("1")
    largeur, _hauteur = image.size
    modules = largeur // scale - 2 * border
    pixels = image.load()
    assert pixels is not None

    lues: list[list[int]] = []
    for ligne in range(modules):
        courante: list[int] = []
        for colonne in range(modules):
            x = (border + colonne) * scale + scale // 2
            y = (border + ligne) * scale + scale // 2
            # `1` en mode « 1 » vaut blanc ; la matrice de segno vaut 1 pour
            # un module SOMBRE. On inverse pour comparer.
            courante.append(0 if pixels[x, y] else 1)
        lues.append(courante)
    return lues


# ── Le contenu est réellement encodé ─────────────────────────────────────────


def test_deux_textes_differents_donnent_deux_codes_differents() -> None:
    """LE test : un générateur qui ignorerait son argument passait tout le reste.

    C'est le contrôle minimal qu'aucune assertion de forme ne remplace.
    """
    premier = _matrice(QrCode.from_text("https://exemple.fr"))
    second = _matrice(QrCode.from_text("https://autre.fr"))

    assert premier != second, (
        "deux textes distincts produisent la même matrice : le contenu n'est "
        "pas encodé"
    )


def test_le_meme_texte_donne_le_meme_code() -> None:
    """La contrepartie : un générateur aléatoire passerait le test précédent."""
    assert _matrice(QrCode.from_text("stable")) == _matrice(QrCode.from_text("stable"))


def test_un_texte_plus_long_exige_une_matrice_plus_grande() -> None:
    """La taille suit la charge : un code tronqué serait plus petit qu'il ne doit.

    C'est ce que verrait un lecteur avant tout : une donnée coupée rend un code
    valide mais faux, et rien dans les octets du fichier ne le dirait.
    """
    court = _matrice(QrCode.from_text("a"))
    long = _matrice(QrCode.from_text("a" * 400))

    assert len(long) > len(court)


def test_un_texte_accentue_est_encode_sans_erreur() -> None:
    """L'UTF-8 est le cas où un encodage approximatif se voit en production.

    Un nom de rue français dans une URL de QR Code n'a rien d'exotique.
    """
    code = QrCode.from_text("https://exemple.fr/café-crème?nom=Noël")

    assert _matrice(code)
    assert code.to_png()


# ── L'image représente fidèlement la matrice ─────────────────────────────────


@pytest.mark.parametrize(("scale", "border"), [(1, 0), (4, 4), (8, 2)])
def test_les_pixels_du_png_correspondent_a_la_matrice(scale: int, border: int) -> None:
    """L'aller-retour qui manquait : rendre, relire, comparer.

    Il ferme d'un coup plusieurs défauts qu'aucun contrôle de forme ne voit :
    une image blanche, une image tronquée, une échelle qui ne s'applique pas,
    une marge absente qui collerait le code au bord.
    """
    code = QrCode.from_text("https://exemple.fr/page")

    attendue = _matrice(code)
    lue = _pixels_du_png(code.to_png(scale=scale, border=border), scale=scale, border=border)

    assert lue == attendue, (
        f"les pixels du PNG ne représentent pas la matrice (scale={scale}, "
        f"border={border})"
    )


def test_la_marge_est_reellement_blanche() -> None:
    """La zone de silence est exigée par la norme : sans elle, un lecteur cale.

    Elle est invisible dans les octets du fichier, et le contrôle de forme la
    laissait donc passer quelle que soit sa valeur.
    """
    png = QrCode.from_text("https://exemple.fr").to_png(scale=4, border=4)
    image = Image.open(io.BytesIO(png)).convert("1")
    pixels = image.load()
    assert pixels is not None
    largeur, hauteur = image.size

    for x in range(largeur):
        for y in list(range(4 * 4)) + list(range(hauteur - 4 * 4, hauteur)):
            assert pixels[x, y], f"pixel sombre dans la marge en ({x}, {y})"


def test_les_trois_motifs_de_reperage_sont_presents() -> None:
    """Sans eux, aucun lecteur ne trouve le code, quel que soit son contenu.

    Un motif de repérage est un carré sombre de 7 modules, bordé de clair,
    avec un noyau sombre de 3 modules. On contrôle ses angles, ce qui suffit à
    distinguer un vrai motif d'une zone uniformément sombre.
    """
    matrice = _matrice(QrCode.from_text("https://exemple.fr"))
    taille = len(matrice)

    coins = {
        "haut gauche": (0, 0),
        "haut droit": (0, taille - 7),
        "bas gauche": (taille - 7, 0),
    }
    for nom, (ligne, colonne) in coins.items():
        bloc = [rangee[colonne:colonne + 7] for rangee in matrice[ligne:ligne + 7]]

        assert all(bloc[0]), f"bord supérieur du motif « {nom} » incomplet"
        assert all(rangee[0] for rangee in bloc), f"bord gauche du motif « {nom} » incomplet"
        # L'anneau clair qui sépare le bord du noyau : c'est lui qui distingue
        # un motif de repérage d'un carré plein.
        assert not bloc[1][1], f"anneau clair du motif « {nom} » absent"
        assert bloc[3][3], f"noyau sombre du motif « {nom} » absent"
