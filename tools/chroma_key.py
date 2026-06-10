"""Outil de détourage par fond uni (chroma key) pour les illustrations de la doc.

Transforme une image à fond vert (ou magenta) uni en PNG **RGBA transparent**,
avec suppression du liseré (despill). Conçu pour le flux : on exporte une
illustration sur un fond vif que l'on incruste ensuite proprement.

Usage :
    python tools/chroma_key.py docs/reference/http/imgs/requete.png
    python tools/chroma_key.py img1.png img2.png            # plusieurs images, en place
    python tools/chroma_key.py source.png -o sortie.png     # une image, vers un autre fichier
    python tools/chroma_key.py logo.png --color magenta     # fond magenta

Par défaut, l'image est réécrite **en place** (le fichier source à fond vert est
remplacé par sa version transparente). Garde une copie du fond vert si tu veux
pouvoir réajuster les seuils.

Repères de seuils (sur la composante de « clé » = dominance de la couleur de fond) :
  - keyness >= --high  -> pixel de fond  -> transparent (alpha 0)
  - keyness <= --low   -> contenu        -> opaque (alpha 255)
  - entre les deux      -> bord anti-crénelé -> alpha progressif + despill

Dépend uniquement de Pillow (déjà présent dans l'environnement doc).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops


def _keyness_and_despill(im: Image.Image, color: str) -> tuple[Image.Image, Image.Image]:
    """Renvoie (image RGB despillée, image L de « keyness » 0..255)."""
    r, g, b, _a = im.split()
    if color == "green":
        other_max = ImageChops.lighter(r, b)          # max(R, B)
        keyness = ImageChops.subtract(g, other_max)   # G - max(R, B), borné à 0
        g = ImageChops.darker(g, other_max)           # despill : ramène le vert
    else:  # magenta : R et B hauts, G bas
        keyness = ImageChops.subtract(ImageChops.darker(r, b), g)  # min(R, B) - G
        r = ImageChops.darker(r, ImageChops.lighter(g, b))         # despill R
        b = ImageChops.darker(b, ImageChops.lighter(g, r))         # despill B
    return Image.merge("RGB", (r, g, b)), keyness


def chroma_key(
    src: Path,
    *,
    color: str = "green",
    high: int = 80,
    low: int = 20,
    output: Path | None = None,
) -> Path:
    """Détoure le fond `color` de `src` et écrit un PNG RGBA. Renvoie le chemin écrit."""
    im = Image.open(src).convert("RGBA")
    original_alpha = im.getchannel("A")
    rgb, keyness = _keyness_and_despill(im, color)
    span = max(1, high - low)

    def alpha_map(v: int) -> int:
        if v >= high:
            return 0
        if v <= low:
            return 255
        return round(255 * (high - v) / span)

    new_alpha = keyness.point(alpha_map)
    # Ne jamais rendre un pixel plus opaque que dans la source.
    new_alpha = ImageChops.darker(new_alpha, original_alpha)

    out_im = Image.merge("RGBA", (*rgb.split(), new_alpha))
    target = output or src
    out_im.save(target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Détoure un fond vert/magenta uni en PNG transparent (despill inclus).",
    )
    parser.add_argument("images", nargs="+", type=Path, help="image(s) à détourer")
    parser.add_argument(
        "--color", choices=("green", "magenta"), default="green",
        help="couleur du fond à retirer (défaut : green)",
    )
    parser.add_argument("--high", type=int, default=80, help="seuil fond (défaut : 80)")
    parser.add_argument("--low", type=int, default=20, help="seuil contenu (défaut : 20)")
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="fichier de sortie (une seule image) ; sinon réécriture en place",
    )
    args = parser.parse_args(argv)

    if args.output is not None and len(args.images) != 1:
        parser.error("--output ne s'utilise qu'avec une seule image.")

    for src in args.images:
        if not src.exists():
            print(f"[ignoré] introuvable : {src}", file=sys.stderr)
            continue
        target = chroma_key(
            src, color=args.color, high=args.high, low=args.low, output=args.output,
        )
        res = Image.open(target).convert("RGBA")
        hist = res.getchannel("A").histogram()
        total = res.size[0] * res.size[1]
        transp = 100 * hist[0] / total
        print(f"[ok] {target}  (fond {args.color} retiré : {transp:.0f}% transparent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
