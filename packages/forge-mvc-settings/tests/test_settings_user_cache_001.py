"""SETTINGS-PER-USER-001 et SETTINGS-CACHE-001 : préférences et lectures répétées.

Un paramètre par utilisateur n'avait pas de place : la clé primaire porte la
seule clé du paramètre. Le ranger sous une clé composée marchait, mais rien
n'empêchait la collision : une clé globale `user.42.theme` et la préférence de
l'utilisateur 42 auraient désigné la même ligne, et l'une aurait écrasé
l'autre en silence.

Un paramètre est par ailleurs lu à chaque requête et change une fois par mois,
et chaque lecture faisait un aller-retour vers la base.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_settings")

from forge_mvc_settings import (  # noqa: E402
    USER_SCOPE_PREFIX,
    SettingsError,
    clear_settings_cache,
    delete_user_setting,
    disable_settings_cache,
    enable_settings_cache,
    get_all_settings,
    get_setting,
    get_user_setting,
    get_user_settings,
    set_setting,
    set_user_setting,
    settings_cache_enabled,
    user_setting_key,
)


class _FauxDb:
    def __init__(self) -> None:
        self.lignes: dict[str, tuple[str, str]] = {}
        self.lectures: list[str] = []

    def execute(self, sql: str, params: Any) -> int:
        if "UPDATE" in sql:
            if params[3] in self.lignes:
                self.lignes[params[3]] = (params[0], params[1])
                return 1
            return 0
        if "INSERT" in sql:
            self.lignes[params[0]] = (params[1], params[2])
            return 1
        if "DELETE" in sql:
            return 1 if self.lignes.pop(params[0], None) is not None else 0
        return 0

    def fetch_one(self, sql: str, params: Any) -> "dict[str, Any] | None":
        self.lectures.append(params[0])
        valeur = self.lignes.get(params[0])
        if valeur is None:
            return None
        return {"setting_value": valeur[0], "value_type": valeur[1]}

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        return [
            {"setting_key": k, "setting_value": v[0], "value_type": v[1]}
            for k, v in sorted(self.lignes.items())
        ]


@pytest.fixture(autouse=True)
def _sans_cache():
    disable_settings_cache()
    yield
    disable_settings_cache()


@pytest.fixture
def db() -> _FauxDb:
    return _FauxDb()


class TestCollisionFermee:
    """Le point qui justifie un préfixe réservé plutôt qu'une convention."""

    def test_une_cle_globale_dans_l_espace_utilisateur_est_refusee(
        self, db: _FauxDb
    ) -> None:
        with pytest.raises(SettingsError, match="réservée"):
            set_setting("user.42.theme", "x", db=db)

    def test_le_refus_indique_la_bonne_porte(self, db: _FauxDb) -> None:
        with pytest.raises(SettingsError, match="set_user_setting"):
            set_setting("user.autre", "x", db=db)

    def test_une_cle_globale_ordinaire_reste_permise(self, db: _FauxDb) -> None:
        set_setting("users_max", 10, db=db)
        assert get_setting("users_max", db=db) == 10


class TestCleComposee:
    def test_la_cle_porte_l_espace_de_noms(self) -> None:
        assert user_setting_key(42, "theme") == f"{USER_SCOPE_PREFIX}42.theme"

    def test_un_identifiant_avec_un_point_est_refuse(self) -> None:
        """Deux utilisateurs pourraient sinon viser la même clé."""
        with pytest.raises(SettingsError, match="point"):
            user_setting_key("4.2", "theme")

    @pytest.mark.parametrize("vide", [None, "", "   "])
    def test_un_identifiant_vide_est_refuse(self, vide: Any) -> None:
        with pytest.raises(SettingsError, match="ne peut pas être vide"):
            user_setting_key(vide, "theme")

    def test_une_cle_composee_trop_longue_est_refusee(self) -> None:
        """Une clé tronquée en silence viserait une autre ligne."""
        with pytest.raises(SettingsError):
            user_setting_key("x" * 150, "y" * 100)


class TestSeparationDesEspaces:
    def test_un_reglage_personnel_n_apparait_pas_dans_les_globaux(
        self, db: _FauxDb
    ) -> None:
        """Sinon la configuration grossirait au rythme des comptes."""
        set_setting("theme", "clair", db=db)
        set_user_setting(42, "theme", "sombre", db=db)

        assert get_all_settings(db=db) == {"theme": "clair"}

    def test_deux_utilisateurs_ne_se_marchent_pas_dessus(self, db: _FauxDb) -> None:
        set_user_setting(42, "theme", "sombre", db=db)
        set_user_setting(7, "theme", "contraste", db=db)

        assert get_user_setting(42, "theme", db=db) == "sombre"
        assert get_user_setting(7, "theme", db=db) == "contraste"

    def test_les_reglages_d_un_utilisateur_sortent_sans_prefixe(
        self, db: _FauxDb
    ) -> None:
        """L'appelant a fourni l'utilisateur : le lui rendre serait redondant."""
        set_user_setting(42, "theme", "sombre", db=db)
        set_user_setting(42, "langue", "fr", db=db)

        assert get_user_settings(42, db=db) == {"theme": "sombre", "langue": "fr"}

    def test_un_reglage_absent_ne_retombe_pas_sur_le_global(self, db: _FauxDb) -> None:
        """Sinon « pas de préférence » et « préférence identique au défaut » se confondent."""
        set_setting("theme", "clair", db=db)

        assert get_user_setting(42, "theme", db=db) is None
        assert get_user_setting(42, "theme", "sombre", db=db) == "sombre"

    def test_la_suppression_ne_touche_que_l_utilisateur_vise(
        self, db: _FauxDb
    ) -> None:
        set_setting("theme", "clair", db=db)
        set_user_setting(42, "theme", "sombre", db=db)

        assert delete_user_setting(42, "theme", db=db) is True
        assert get_setting("theme", db=db) == "clair"


class TestCache:
    def test_il_est_eteint_par_defaut(self) -> None:
        """Un cache change ce qu'une lecture garantit : l'application l'active."""
        assert settings_cache_enabled() is False

    def test_sans_cache_chaque_lecture_va_en_base(self, db: _FauxDb) -> None:
        set_setting("theme", "clair", db=db)
        db.lectures.clear()

        get_setting("theme", db=db)
        get_setting("theme", db=db)

        assert len(db.lectures) == 2

    def test_avec_cache_une_seule_lecture_suffit(self, db: _FauxDb) -> None:
        set_setting("theme", "clair", db=db)
        enable_settings_cache()
        db.lectures.clear()

        get_setting("theme", db=db)
        get_setting("theme", db=db)
        get_setting("theme", db=db)

        assert len(db.lectures) == 1

    def test_une_ecriture_invalide_l_entree(self, db: _FauxDb) -> None:
        set_setting("theme", "clair", db=db)
        enable_settings_cache()
        get_setting("theme", db=db)

        set_setting("theme", "sombre", db=db)

        assert get_setting("theme", db=db) == "sombre"

    def test_une_suppression_invalide_l_entree(self, db: _FauxDb) -> None:
        set_setting("theme", "clair", db=db)
        enable_settings_cache()
        get_setting("theme", db=db)

        delete_user_setting(42, "absent", db=db)
        set_setting("theme", "autre", db=db)

        assert get_setting("theme", db=db) == "autre"

    def test_une_absence_est_mise_en_cache(self, db: _FauxDb) -> None:
        """Sinon un paramètre absent serait relu à chaque fois."""
        enable_settings_cache()

        get_setting("jamais_pose", db=db)
        get_setting("jamais_pose", db=db)

        assert len(db.lectures) == 1

    def test_le_defaut_est_rendu_meme_depuis_le_cache(self, db: _FauxDb) -> None:
        enable_settings_cache()
        get_setting("jamais_pose", db=db)

        assert get_setting("jamais_pose", "repli", db=db) == "repli"

    def test_l_invalidation_manuelle_force_une_relecture(self, db: _FauxDb) -> None:
        """Pour une écriture faite hors du paquet, par une migration."""
        set_setting("theme", "clair", db=db)
        enable_settings_cache()
        get_setting("theme", db=db)
        db.lignes["theme"] = ("sombre", "str")

        clear_settings_cache("theme")

        assert get_setting("theme", db=db) == "sombre"

    def test_l_activation_vide_le_cache(self, db: _FauxDb) -> None:
        """Son contenu pourrait dater d'avant des écritures faites entre temps."""
        set_setting("theme", "clair", db=db)
        enable_settings_cache()
        get_setting("theme", db=db)
        disable_settings_cache()
        db.lignes["theme"] = ("sombre", "str")

        enable_settings_cache()

        assert get_setting("theme", db=db) == "sombre"
