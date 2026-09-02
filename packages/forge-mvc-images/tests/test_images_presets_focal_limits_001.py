"""Les cinq tickets images du cycle rc8.

`IMAGES-PRESETS-DECLARATIFS-001`, `IMAGES-FOCAL-CROP-001`,
`IMAGES-ORPHAN-VARIANTS-001`, `IMAGES-ENTITY-FIELD-001` et
`IMAGES-LIMITS-CONFIG-001`.

Les deux variantes du paquet vivaient dans une constante de module accordée à
la main avec deux dictionnaires littéraux. L'ADR-018 avait relevé la
conséquence sans la corriger : « non extensible sans éditer le code ».

Rendre les préréglages déclarables ouvre trois questions que la constante
fermait d'elle même : un nom devient un dossier sur le disque, retirer un
préréglage laisse des fichiers derrière lui, et une entité doit pouvoir dire
lesquels il lui faut.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from core.forms.upload_exceptions import UploadStorageError  # noqa: E402
from forge_mvc_images.focal import CENTER, FocalPoint, crop_box, crop_to_focal  # noqa: E402
from forge_mvc_images.limits import (  # noqa: E402
    DEFAULT_MAX_PIXELS,
    ImageLimits,
    ImageLimitsError,
    check_dimensions,
    check_weight,
    image_limits,
)
from forge_mvc_images.presets import (  # noqa: E402
    DEFAULT_PRESETS,
    MODE_CROP,
    MODE_FIT,
    RESERVED_PRESET_NAMES,
    ImagePresetError,
    parse_presets,
    preset_by_name,
    preset_names,
    variant_presets,
)
from forge_mvc_images.processing import (  # noqa: E402
    _selected_presets,
    generate_image_variants,
    image_variant_relative_paths,
)
from forge_mvc_images.variants_cleanup import (  # noqa: E402
    find_orphan_variants,
    purge_orphan_variants,
)


@pytest.fixture(autouse=True)
def _env_propre(monkeypatch: pytest.MonkeyPatch):
    for nom in ("IMAGE_VARIANTS", "IMAGE_MAX_WIDTH", "IMAGE_MAX_HEIGHT",
                "IMAGE_MAX_BYTES", "UPLOAD_MAX_IMAGE_PIXELS"):
        monkeypatch.delenv(nom, raising=False)
    yield


# ------------------------------------------------- IMAGES-PRESETS-DECLARATIFS


class TestDeclaration:

    def test_sans_declaration_le_comportement_ne_change_pas(self) -> None:
        """Un projet existant ne doit rien voir changer."""
        assert variant_presets() == DEFAULT_PRESETS
        assert preset_names() == ("medium", "thumbnail")

    def test_une_declaration_remplace_les_defauts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("IMAGE_VARIANTS", "carre:400x400,hero:1920x1080:crop")

        assert preset_names() == ("carre", "hero")

    def test_les_prereglages_sont_lus_et_non_figes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Le défaut corrigé.

        La constante précédente était un instantané pris au chargement du
        module, aveugle à toute configuration posée ensuite.
        """
        premier = preset_names()
        monkeypatch.setenv("IMAGE_VARIANTS", "carre:400x400")

        assert preset_names() != premier
        assert preset_names() == ("carre",)

    def test_l_ordre_declare_est_conserve(self) -> None:
        presets = parse_presets("c:1x1,a:2x2,b:3x3")

        assert [p.name for p in presets] == ["c", "a", "b"]

    def test_le_mode_par_defaut_ajuste(self) -> None:
        assert parse_presets("a:10x10")[0].mode == MODE_FIT

    def test_le_mode_rogne_se_declare(self) -> None:
        preset = parse_presets("a:10x10:crop")[0]

        assert preset.mode == MODE_CROP
        assert preset.crops is True

    def test_on_retrouve_un_prereglage_par_son_nom(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("IMAGE_VARIANTS", "carre:400x400")

        trouve = preset_by_name("CARRE")
        assert trouve is not None and trouve.size == (400, 400)
        assert preset_by_name("absent") is None


class TestDeclarationRefusee:

    def test_le_nom_original_est_reserve(self) -> None:
        """Il désigne le fichier source : une variante l'écraserait."""
        assert "original" in RESERVED_PRESET_NAMES

        with pytest.raises(ImagePresetError, match="réservé"):
            parse_presets("original:100x100")

    @pytest.mark.parametrize("nom", ["../evil", "a/b", "a b", "", "-a", "A B"])
    def test_un_nom_qui_n_est_pas_un_segment_de_chemin_est_refuse(
        self, nom: str
    ) -> None:
        """Le nom devient un dossier sur le disque."""
        with pytest.raises(ImagePresetError):
            parse_presets(f"{nom}:100x100")

    @pytest.mark.parametrize("declaration", ["a:0x10", "a:10x0", "a:-5x10"])
    def test_une_dimension_nulle_ou_negative_est_refusee(
        self, declaration: str
    ) -> None:
        with pytest.raises(ImagePresetError):
            parse_presets(declaration)

    def test_une_dimension_demesuree_est_refusee(self) -> None:
        """Au delà, la variante pèserait plus que l'original."""
        with pytest.raises(ImagePresetError, match="démesurée"):
            parse_presets("a:99999x10")

    def test_un_doublon_est_refuse(self) -> None:
        """Garder la dernière en silence produirait une taille que personne n'a lue."""
        with pytest.raises(ImagePresetError, match="deux fois"):
            parse_presets("a:10x10,a:20x20")

    @pytest.mark.parametrize("declaration", ["a:10", "a", "a:10x10x10", "a:axb"])
    def test_une_entree_mal_formee_est_refusee(self, declaration: str) -> None:
        with pytest.raises(ImagePresetError):
            parse_presets(declaration)

    def test_un_mode_inconnu_est_refuse(self) -> None:
        with pytest.raises(ImagePresetError, match="Mode inconnu"):
            parse_presets("a:10x10:zoom")

    def test_le_message_dit_la_forme_attendue(self) -> None:
        with pytest.raises(ImagePresetError, match="LARGEURxHAUTEUR"):
            parse_presets("a:10")


class TestCheminsDerives:

    def test_les_chemins_suivent_la_declaration(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Trois endroits devaient s'accorder à la main, et rien ne le vérifiait."""
        monkeypatch.setenv("IMAGE_VARIANTS", "carre:400x400,hero:1920x1080")

        chemins = image_variant_relative_paths("images/photo.jpg")

        assert set(chemins) == {"original", "carre", "hero"}
        assert chemins["carre"] == "images/carre/photo.jpg"

    def test_l_original_figure_toujours(self) -> None:
        assert "original" in image_variant_relative_paths("images/photo.jpg")


# ------------------------------------------------------- IMAGES-FOCAL-CROP


class TestFenetreDeRognage:

    def test_le_centre_est_le_defaut(self) -> None:
        assert crop_box((800, 1200), (1920, 1080)) == crop_box(
            (800, 1200), (1920, 1080), CENTER
        )

    def test_le_point_deplace_la_fenetre(self) -> None:
        """Une bannière taillée au centre d'un portrait coupe la tête."""
        haut = crop_box((800, 1200), (1920, 1080), FocalPoint(0.5, 0.1))
        centre = crop_box((800, 1200), (1920, 1080))

        assert haut[1] < centre[1]

    def test_la_fenetre_garde_le_rapport_de_la_cible(self) -> None:
        gauche, haut, droite, bas = crop_box((800, 1200), (1920, 1080))

        assert round((droite - gauche) / (bas - haut), 2) == round(1920 / 1080, 2)

    def test_la_fenetre_ne_deborde_jamais_de_la_source(self) -> None:
        """Sans recalage, Pillow comblerait le vide par du noir."""
        for point in (FocalPoint(0, 0), FocalPoint(1, 1), FocalPoint(0, 1)):
            gauche, haut, droite, bas = crop_box((800, 1200), (1920, 1080), point)

            assert gauche >= 0 and haut >= 0
            assert droite <= 800 and bas <= 1200

    def test_la_fenetre_est_la_plus_grande_possible(self) -> None:
        gauche, haut, droite, bas = crop_box((800, 1200), (400, 400))

        assert (droite - gauche, bas - haut) == (800, 800)

    @pytest.mark.parametrize("source", [(0, 100), (100, 0), (-1, 10)])
    def test_une_source_invalide_leve(self, source: Any) -> None:
        with pytest.raises(ValueError):
            crop_box(source, (10, 10))


class TestPointDInteret:

    @pytest.mark.parametrize(
        "brut,attendu", [(1.7, 1.0), (-3.0, 0.0), (0.5, 0.5), (1.0001, 1.0)]
    )
    def test_une_valeur_hors_intervalle_est_ramenee(
        self, brut: float, attendu: float
    ) -> None:
        """Un clic au bord d'une interface donne facilement 1.0001.

        Refuser ferait échouer un téléversement pour un arrondi.
        """
        assert FocalPoint(brut, brut).x == attendu

    def test_le_point_par_defaut_est_le_centre(self) -> None:
        assert FocalPoint() == CENTER


class TestRognageEffectif:

    def test_le_rognage_remplit_exactement_la_boite(self) -> None:
        image = Image.new("RGB", (2000, 2000), "navy")

        assert crop_to_focal(image, (400, 200)).size == (400, 200)

    def test_forge_n_invente_pas_de_pixels(self) -> None:
        """Agrandir donnerait une image floue se faisant passer pour la taille demandée."""
        image = Image.new("RGB", (800, 1200), "navy")

        rognee = crop_to_focal(image, (1920, 1080))

        assert rognee.size == (800, 450)
        assert round(800 / 450, 2) == round(1920 / 1080, 2)


# -------------------------------------------------------- IMAGES-ENTITY-FIELD


class TestPrereglagesNommes:

    def test_sans_liste_tous_sont_retenus(self) -> None:
        assert _selected_presets(None) == DEFAULT_PRESETS

    def test_une_liste_restreint(self) -> None:
        assert [p.name for p in _selected_presets(["thumbnail"])] == ["thumbnail"]

    def test_un_doublon_ne_genere_qu_une_fois(self) -> None:
        assert len(_selected_presets(["medium", "medium"])) == 1

    def test_la_casse_et_les_espaces_sont_tolerees(self) -> None:
        assert [p.name for p in _selected_presets([" MEDIUM "])] == ["medium"]

    def test_un_nom_inconnu_leve(self) -> None:
        """Le point qui compte.

        L'ignorer laisserait une entité réclamer une déclinaison inexistante,
        et la page finirait avec une image cassée sans signal.
        """
        with pytest.raises(UploadStorageError, match="inconnu"):
            _selected_presets(["hero"])

    def test_le_message_liste_les_declares(self) -> None:
        with pytest.raises(UploadStorageError, match="medium"):
            _selected_presets(["hero"])

    def test_le_contrat_d_entite_accepte_une_liste(self) -> None:
        from forge_mvc_entities.crud.controller_builder import _media_upload_call

        rendu = _media_upload_call("image", "_f", ["thumbnail", "hero"])

        assert "variants=['thumbnail', 'hero']" in rendu

    def test_le_contrat_d_entite_accepte_toujours_un_booleen(self) -> None:
        from forge_mvc_entities.crud.controller_builder import _media_upload_call

        assert "variants=True" in _media_upload_call("image", "_f", True)


# --------------------------------------------------------- IMAGES-LIMITS-CONFIG


class TestLimitesDeclarees:

    def test_sans_declaration_seule_la_surface_borne(self) -> None:
        bornes = image_limits()

        assert bornes.max_width is None
        assert bornes.max_height is None
        assert bornes.max_bytes is None
        assert bornes.max_pixels == DEFAULT_MAX_PIXELS

    def test_la_largeur_se_borne(self) -> None:
        """La seule surface laissait passer une image de 12000 sur 2000."""
        check_dimensions(12000, 2000)

        with pytest.raises(UploadStorageError, match="trop large"):
            check_dimensions(12000, 2000, limits=ImageLimits(max_width=4000))

    def test_la_hauteur_se_borne(self) -> None:
        with pytest.raises(UploadStorageError, match="trop haute"):
            check_dimensions(100, 9000, limits=ImageLimits(max_height=4000))

    def test_la_surface_borne_toujours(self) -> None:
        """La garde anti bombe protégeait contre autre chose, elle reste."""
        with pytest.raises(UploadStorageError, match="trop volumineuse"):
            check_dimensions(9000, 9000, limits=ImageLimits(max_pixels=1000))

    def test_le_poids_se_borne_a_part_de_upload_max_size(self) -> None:
        """Une application peut accepter un PDF de 20 Mo et refuser une photo de 5."""
        check_weight(9999, limits=ImageLimits())

        with pytest.raises(UploadStorageError, match="trop lourde"):
            check_weight(9999, limits=ImageLimits(max_bytes=1000))

    @pytest.mark.parametrize("valeur", ["abc", "5MB", "1.5", "0", "-1"])
    def test_une_valeur_illisible_leve(
        self, monkeypatch: pytest.MonkeyPatch, valeur: str
    ) -> None:
        """Même leçon que le quota de files : le silence irait dans le mauvais sens."""
        monkeypatch.setenv("IMAGE_MAX_WIDTH", valeur)

        with pytest.raises(ImageLimitsError):
            image_limits()

    def test_le_message_dit_comment_ne_pas_borner(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("IMAGE_MAX_WIDTH", "0")

        with pytest.raises(ImageLimitsError, match="retirer la variable"):
            image_limits()

    def test_les_limites_sont_lues_a_chaque_appel(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert image_limits().max_width is None
        monkeypatch.setenv("IMAGE_MAX_WIDTH", "500")

        assert image_limits().max_width == 500


# ------------------------------------------------------ IMAGES-ORPHAN-VARIANTS


@pytest.fixture
def arbre(tmp_path: Path) -> Path:
    """Racine d'upload avec un original, ses variantes, et un intrus."""
    images = tmp_path / "images"
    images.mkdir()
    Image.new("RGB", (10, 10), "navy").save(images / "photo.jpg")
    for variante in ("medium", "thumbnail", "hero"):
        (images / variante).mkdir()
        Image.new("RGB", (5, 5), "navy").save(images / variante / "photo.jpg")
        Image.new("RGB", (5, 5), "navy").save(images / variante / "disparue.jpg")
    return tmp_path


class TestRapprochementDesVariantes:

    def test_une_variante_sans_original_est_reperee(self, arbre: Path) -> None:
        rapport = find_orphan_variants(root=arbre)

        assert "images/medium/disparue.jpg" in rapport.without_original

    def test_une_variante_d_un_prereglage_retire_est_reperee(
        self, arbre: Path
    ) -> None:
        """La situation créée par les préréglages déclarables.

        `hero` n'est plus déclaré, et son dossier garde tout ce qu'il a produit.
        """
        rapport = find_orphan_variants(root=arbre)

        assert rapport.from_removed_presets == ("images/hero/photo.jpg",)

    def test_une_variante_vivante_n_est_pas_touchee(self, arbre: Path) -> None:
        rapport = find_orphan_variants(root=arbre)

        assert "images/medium/photo.jpg" not in rapport.without_original
        assert "images/medium/photo.jpg" not in rapport.from_removed_presets

    def test_un_orphelin_n_apparait_que_dans_une_categorie(
        self, arbre: Path
    ) -> None:
        """`hero/disparue.jpg` cumule les deux motifs, le plus grave l'emporte."""
        rapport = find_orphan_variants(root=arbre)

        assert "images/hero/disparue.jpg" in rapport.without_original
        assert "images/hero/disparue.jpg" not in rapport.from_removed_presets

    def test_le_rapport_nomme_les_prereglages_en_vigueur(self, arbre: Path) -> None:
        """Sans eux, « préréglage retiré » ne se vérifie pas."""
        rapport = find_orphan_variants(root=arbre)

        assert rapport.declared_presets == ("medium", "thumbnail")

    def test_aucune_base_n_est_consultee(self, arbre: Path) -> None:
        """Contrairement à files:orphans, le disque suffit."""
        import forge_mvc_images.variants_cleanup as module
        from pathlib import Path as _P

        source = _P(module.__file__).read_text(encoding="utf-8")

        assert "fetch_all" not in source
        assert "core.database" not in source

    def test_un_dossier_ordinaire_n_est_pas_balaye(self, tmp_path: Path) -> None:
        """Un dossier applicatif ne doit pas passer pour un dossier de variantes."""
        (tmp_path / "factures").mkdir()
        (tmp_path / "factures" / "a.pdf").write_bytes(b"x")

        rapport = find_orphan_variants(root=tmp_path)

        assert rapport.is_empty

    def test_une_racine_absente_ne_leve_pas(self, tmp_path: Path) -> None:
        rapport = find_orphan_variants(root=tmp_path / "jamais_creee")

        assert rapport.is_empty


class TestPurgeDesVariantes:

    def test_elle_supprime_les_deux_categories(self, arbre: Path) -> None:
        rapport = find_orphan_variants(root=arbre)

        supprimes, echecs = purge_orphan_variants(rapport, root=arbre)

        assert echecs == ()
        assert len(supprimes) == 4
        assert (arbre / "images" / "medium" / "photo.jpg").exists()
        assert not (arbre / "images" / "hero" / "photo.jpg").exists()

    def test_on_peut_ne_purger_qu_une_categorie(self, arbre: Path) -> None:
        """Retirer un préréglage est parfois temporaire."""
        rapport = find_orphan_variants(root=arbre)

        purge_orphan_variants(
            rapport, root=arbre, remove_from_removed_presets=False
        )

        assert (arbre / "images" / "hero" / "photo.jpg").exists()
        assert not (arbre / "images" / "medium" / "disparue.jpg").exists()

    def test_un_chemin_hors_racine_est_refuse(self, arbre: Path) -> None:
        """Le rapport peut avoir été construit par l'appelant."""
        from forge_mvc_images.variants_cleanup import VariantOrphanReport

        rapport = VariantOrphanReport(
            without_original=("../../etc/passwd",),
            from_removed_presets=(),
            scanned_variants=1,
            declared_presets=("medium",),
        )

        supprimes, echecs = purge_orphan_variants(rapport, root=arbre)

        assert supprimes == ()
        assert len(echecs) == 1


class TestGenerationBoutEnBout:

    def test_seules_les_variantes_produites_sont_rendues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Rendre le chemin d'une variante non générée ferait stocker une
        adresse qui ne répond pas."""
        monkeypatch.setenv("IMAGE_VARIANTS", "thumbnail:300x300,hero:1920x1080:crop")
        images = tmp_path / "images"
        images.mkdir()
        Image.new("RGB", (800, 1200), "navy").save(images / "p.jpg")

        rendus = generate_image_variants(
            "images/p.jpg", root=tmp_path, presets=["thumbnail"]
        )

        assert set(rendus) == {"original", "thumbnail"}
        assert not (images / "hero" / "p.jpg").exists()

    def test_le_mode_rogne_produit_le_rapport_demande(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("IMAGE_VARIANTS", "banniere:1920x1080:crop")
        images = tmp_path / "images"
        images.mkdir()
        Image.new("RGB", (800, 1200), "navy").save(images / "p.jpg")

        generate_image_variants("images/p.jpg", root=tmp_path)

        with Image.open(images / "banniere" / "p.jpg") as produite:
            assert produite.size == (800, 450)

    def test_le_mode_ajuste_conserve_le_rapport_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("IMAGE_VARIANTS", "carre:300x300")
        images = tmp_path / "images"
        images.mkdir()
        Image.new("RGB", (800, 1200), "navy").save(images / "p.jpg")

        generate_image_variants("images/p.jpg", root=tmp_path)

        with Image.open(images / "carre" / "p.jpg") as produite:
            assert produite.size == (200, 300)


class TestCommandeCli:

    def test_elle_affiche_sans_supprimer_par_defaut(self) -> None:
        from forge_mvc_images.cli.orphans import parse_options

        assert parse_options([]).delete is False

    def test_une_option_inconnue_est_une_erreur(self) -> None:
        from forge_mvc_images.cli.orphans import parse_options

        assert parse_options(["--dlete"]).error is not None

    def test_une_valeur_only_inconnue_est_une_erreur(self) -> None:
        from forge_mvc_images.cli.orphans import parse_options

        assert parse_options(["--only", "tout"]).error is not None

    @pytest.mark.parametrize(
        "argv", [["--only", "sans-original"], ["--only=sans-original"]]
    )
    def test_les_deux_ecritures_d_option_sont_lues(self, argv: list[str]) -> None:
        from forge_mvc_images.cli.orphans import parse_options

        assert parse_options(argv).only == "sans-original"

    def test_le_rapport_nomme_les_prereglages(self, arbre: Path) -> None:
        from forge_mvc_images.cli.orphans import render_report

        texte = render_report(find_orphan_variants(root=arbre))

        assert "medium, thumbnail" in texte

    def test_la_commande_affiche_et_ne_supprime_pas(
        self, arbre: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from forge_mvc_images.cli.orphans import main

        code = main(["--root", str(arbre)])

        assert code == 0
        assert "Rien n'a été supprimé" in capsys.readouterr().out
        assert (arbre / "images" / "hero" / "photo.jpg").exists()

    def test_avec_delete_elle_supprime(
        self, arbre: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from forge_mvc_images.cli.orphans import main

        code = main(["--root", str(arbre), "--delete"])

        assert code == 0
        assert not (arbre / "images" / "hero" / "photo.jpg").exists()
        assert (arbre / "images" / "medium" / "photo.jpg").exists()
