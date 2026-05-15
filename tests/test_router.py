import pytest
from core.http.router import Router


def _ha(req): pass
def _hb(req): pass


@pytest.fixture
def router():
    r = Router()
    r.add("GET",  "/",             _ha, name="home")
    r.add("GET",  "/clients/{id}", _hb, name="client_show")
    r.add("POST", "/clients",      _hb, name="client_create")
    with r.group("", public=True) as pub:
        pub.add("GET",  "/login",  _ha, name="login")
        pub.add("POST", "/login",  _ha)
        pub.add("GET",  "/logout", _ha, name="logout")
    return r


class TestResolve:
    def test_route_statique(self, router):
        handler, params = router.resolve("GET", "/")
        assert handler is _ha
        assert params == {}

    def test_route_dynamique(self, router):
        handler, params = router.resolve("GET", "/clients/42")
        assert handler is _hb
        assert params == {"id": "42"}

    def test_chemin_inconnu_retourne_none(self, router):
        assert router.resolve("GET", "/inexistant") is None

    def test_mauvaise_methode_retourne_none(self, router):
        assert router.resolve("DELETE", "/") is None

    def test_methode_insensible_casse(self, router):
        assert router.resolve("get", "/") is not None

    def test_route_post(self, router):
        handler, params = router.resolve("POST", "/clients")
        assert handler is _hb
        assert params == {}

    def test_match_retourne_metadata_route(self, router):
        entry, params = router.match("POST", "/clients")
        assert entry.name == "client_create"
        assert entry.csrf is True
        assert entry.api is False
        assert entry.requires_csrf("POST") is True
        assert params == {}

    def test_parametre_avec_slash_ne_matche_pas(self, router):
        assert router.resolve("GET", "/clients/42/extra") is None


class TestIsPublic:
    def test_login_est_public(self, router):
        assert router.is_public("/login") is True

    def test_logout_est_public(self, router):
        assert router.is_public("/logout") is True

    def test_home_est_prive(self, router):
        assert router.is_public("/") is False

    def test_client_est_prive(self, router):
        assert router.is_public("/clients/42") is False


class TestUrlFor:
    def test_route_statique(self, router):
        assert router.url_for("home") == "/"

    def test_route_dynamique(self, router):
        assert router.url_for("client_show", id=42) == "/clients/42"

    def test_route_inconnue_leve_keyerror(self, router):
        with pytest.raises(KeyError):
            router.url_for("inexistant")

    def test_parametre_manquant_leve_keyerror(self, router):
        with pytest.raises(KeyError):
            router.url_for("client_show")

    def test_nom_duplique_leve_valueerror(self):
        r = Router()
        r.add("GET", "/a", _ha, name="dup")
        with pytest.raises(ValueError):
            r.add("GET", "/b", _hb, name="dup")


class TestRouteMetadata:
    def test_group_herite_csrf_api_public(self):
        r = Router()
        with r.group("/api", public=True, csrf=False, api=True) as api:
            api.add("POST", "/webhook", _ha, name="webhook")

        entry, _params = r.match("POST", "/api/webhook")
        assert entry.public is True
        assert entry.csrf is False
        assert entry.api is True
        assert entry.requires_csrf("POST") is False

    def test_get_ne_requiert_pas_csrf(self):
        r = Router()
        r.add("GET", "/contacts", _ha)
        entry, _params = r.match("GET", "/contacts")
        assert entry.requires_csrf("GET") is False

    def test_iter_routes_garde_ordre_de_declaration(self):
        r = Router()
        r.add("GET", "/a", _ha)
        r.add("POST", "/b", _hb)
        assert [entry.pattern for entry in r.iter_routes()] == ["/a", "/b"]
