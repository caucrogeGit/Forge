"""CORE-WSGI-MEDIA-PARITY-001 — `/media/` servi par les deux serveurs.

`/media/` est un préfixe, pas une route : il est intercepté avant le routage.
Cette interception vivait dans le seul `RequestHandler` du squelette, si bien
qu'une application déployée servait ses pages et rendait **404 sur tous ses
médias**. Mesuré sur un projet engendré, le même fichier des deux côtés :

    serveur de développement : 200
    chemin WSGI (Gunicorn)   : 404

C'est le défaut de `CORE-WSGI-HEALTH-PARITY-001` à l'identique, et il appelle le
même remède : la réponse est définie une fois, dans `core.http.media`, et les
deux serveurs la servent.

Le contournement évident, un `location /media/` dans Nginx, est celui qu'il ne
faut pas prendre : il rend public tout `UPLOAD_ROOT` et retire à l'application
le droit de décider qui lit quoi.

Deux exigences gouvernent ces tests.

**Le cœur ne nomme aucun opt-in.** Le fournisseur est découvert par entry point
(ADR-054, ADR-059), sur ce qui est INSTALLÉ et non sur ce qui a été importé :
un registre alimenté à l'import ferait dépendre les médias de l'ordre des
imports du projet.

**Ce chemin est atteint par n'importe quel visiteur, avant le routage.** Toute
absence et toute erreur y donnent 404, jamais une trace d'exception.
"""
from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import pytest

from core.app.wsgi import _format_status, create_wsgi_app
from core.http.media import (
    MEDIA_PREFIX,
    is_media_request,
    media_response,
    media_server,
    reset_media_server_cache,
)
from core.http.response import Response

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _cache_neuf():
    """Le fournisseur est mémorisé : sans ça, un test contaminerait le suivant."""
    reset_media_server_cache()
    yield
    reset_media_server_cache()


@pytest.fixture
def fournisseur(monkeypatch):
    """Injecte un fournisseur de médias et enregistre ses appels."""
    appels: list[tuple[str, object]] = []

    def _poser(reponse: "Response | Exception" = Response(200, b"media")):
        def _servir(relative_path: str, *, request=None):
            appels.append((relative_path, request))
            if isinstance(reponse, Exception):
                raise reponse
            return reponse
        monkeypatch.setattr("core.http.media._decouvrir", lambda: _servir)
        reset_media_server_cache()
        return appels

    return _poser


# ── Le chemin visé ───────────────────────────────────────────────────────────

class TestIsMediaRequest:

    @pytest.mark.parametrize("chemin", [
        "/media/note.txt",
        "/media/documents/2026/rapport.pdf",
        "/media/",
    ])
    def test_reconnait_le_prefixe(self, chemin: str) -> None:
        assert is_media_request(chemin)

    @pytest.mark.parametrize("chemin", [
        "/", "/health", "/mediatheque", "/media", "/static/media/x.png",
    ])
    def test_ignore_le_reste(self, chemin: str) -> None:
        """`/mediatheque` est une route applicative légitime, pas un média."""
        assert not is_media_request(chemin)


# ── La réponse, source unique ────────────────────────────────────────────────

class TestMediaResponse:

    def test_delegue_le_chemin_sans_le_prefixe(self, fournisseur) -> None:
        appels = fournisseur()

        media_response("/media/documents/note.txt")

        assert appels[0][0] == "documents/note.txt"

    def test_propage_la_requete_pour_le_range(self, fournisseur) -> None:
        """Sans `request`, le fichier part en entier : plus de HTTP Range."""
        appels = fournisseur()
        sentinelle = object()

        media_response("/media/film.mp4", sentinelle)

        assert appels[0][1] is sentinelle

    def test_rend_la_reponse_du_fournisseur(self, fournisseur) -> None:
        fournisseur(Response(206, b"tranche", "video/mp4"))

        reponse = media_response("/media/film.mp4")

        assert reponse.status == 206
        assert reponse.body == b"tranche"

    def test_sans_fournisseur_installe_404(self, monkeypatch) -> None:
        """Le cœur reste utilisable sans l'opt-in, comme avant."""
        monkeypatch.setattr("core.http.media._decouvrir", lambda: None)
        reset_media_server_cache()

        reponse = media_response("/media/note.txt")

        assert reponse.status == 404

    def test_un_fournisseur_qui_leve_donne_404(self, fournisseur, caplog) -> None:
        """Avant le routage, une trace d'exception n'a rien à faire."""
        fournisseur(RuntimeError("disque en panne"))

        with caplog.at_level(logging.ERROR):
            reponse = media_response("/media/note.txt")

        assert reponse.status == 404
        assert reponse.body == b"Not found"
        assert "note.txt" in caplog.text, "l'échec doit rester au journal du serveur"

    def test_le_404_ne_dit_pas_ce_qui_manque(self, monkeypatch) -> None:
        """Fichier absent ou opt-in absent : même réponse, exprès."""
        monkeypatch.setattr("core.http.media._decouvrir", lambda: None)
        reset_media_server_cache()

        sans_optin = media_response("/media/note.txt")

        assert sans_optin.body == b"Not found"
        assert b"forge" not in sans_optin.body.lower()


# ── La découverte du fournisseur ─────────────────────────────────────────────

class TestDecouverte:

    def test_le_coeur_ne_nomme_aucun_opt_in(self) -> None:
        """La règle qui a dicté la conception : elle vaut d'être figée."""
        source = (PROJECT_ROOT / "core" / "http" / "media.py").read_text(encoding="utf-8")

        code = "\n".join(
            ligne for ligne in source.splitlines()
            if not ligne.strip().startswith("#")
        )
        # Le nom peut figurer dans la docstring d'explication, jamais dans un import.
        assert "import forge_mvc_files" not in code
        assert "from forge_mvc_files" not in code

    def test_le_fournisseur_est_memorise(self, monkeypatch) -> None:
        """Résoudre des entry points à chaque requête coûterait cher."""
        compteur = {"n": 0}

        def _compter():
            compteur["n"] += 1
            return lambda p, *, request=None: Response(200, b"ok")

        monkeypatch.setattr("core.http.media._decouvrir", _compter)
        reset_media_server_cache()

        for _ in range(5):
            media_response("/media/note.txt")

        assert compteur["n"] == 1

    def test_l_opt_in_declare_l_entry_point_dans_sa_source(self) -> None:
        """Sur la SOURCE versionnée, jamais sur l'installation.

        Un test qui interroge `entry_points()` ne peut que se taire quand
        l'environnement est mal installé, et un skip ne prouve rien : il
        masquerait tout aussi bien un entry point retiré du paquet.

        Le piège est réel et il a été rencontré ici : `conftest.py` place chaque
        `packages/*` en tête de `sys.path`, si bien que `importlib.metadata` lit
        d'abord les `*.egg-info` du dépôt. Ces artefacts de build, ignorés par
        git, survivent aux modifications du `pyproject.toml` : l'entry point
        était déclaré, installé, visible du shell, et invisible sous pytest.
        """
        import tomllib

        pyproject = PROJECT_ROOT / "packages" / "forge-mvc-files" / "pyproject.toml"
        declares = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        groupe = declares["project"]["entry-points"]["forge_mvc.media_server"]

        assert groupe, "aucun fournisseur de médias déclaré par forge-mvc-files"
        assert "forge_mvc_files:serve_media_file" in groupe.values()

    def test_le_fournisseur_declare_existe_vraiment(self) -> None:
        """Le nom pointé est vérifié, pas seulement écrit."""
        module = pytest.importorskip("forge_mvc_files")

        assert callable(getattr(module, "serve_media_file", None))

    def test_le_coeur_resout_le_fournisseur_installe(self) -> None:
        """Bout en bout, quand l'environnement est installé comme la CI le fait."""
        pytest.importorskip("forge_mvc_files")
        from importlib.metadata import entry_points

        if not list(entry_points(group="forge_mvc.media_server")):
            pytest.skip(
                "environnement local sans l'entry point : egg-info du dépôt "
                "périmé, réinstaller forge-mvc-files. La déclaration elle-même "
                "est couverte sur la source, sans skip possible.")

        assert media_server() is not None


# ── Le chemin WSGI ───────────────────────────────────────────────────────────

def _environ(chemin: str, entetes: "dict[str, str] | None" = None) -> dict:
    env = {
        "REQUEST_METHOD": "GET", "PATH_INFO": chemin, "QUERY_STRING": "",
        "SERVER_NAME": "t", "SERVER_PORT": "80", "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1", "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(), "wsgi.url_scheme": "http",
    }
    env.update(entetes or {})
    return env


class _ApplicationQui404:
    """Application dont le routeur ne connaît aucun média."""

    def __init__(self) -> None:
        self.vue: list[str] = []

    def dispatch(self, request):
        self.vue.append(request.path)
        return Response(404, b"route inconnue", "text/plain; charset=utf-8")


class TestCheminWsgi:

    def _appeler(self, chemin: str, application, entetes=None):
        callable_wsgi = create_wsgi_app(application, emit_prod_warnings=False)
        vu = {}

        def start_response(status, headers, exc_info=None):
            vu["status"] = status
            vu["headers"] = dict(headers)
            return lambda c: None

        corps = b"".join(callable_wsgi(_environ(chemin, entetes), start_response))
        return vu, corps

    def test_le_media_est_servi(self, fournisseur) -> None:
        """LE test du ticket : ce chemin rendait 404."""
        fournisseur(Response(200, b"contenu", "text/plain; charset=utf-8"))
        application = _ApplicationQui404()

        vu, corps = self._appeler("/media/note.txt", application)

        assert vu["status"] == "200 OK"
        assert corps == b"contenu"

    def test_l_interception_precede_le_routage(self, fournisseur) -> None:
        """Sinon un routeur sans route /media/ répondrait 404 avant tout le monde."""
        fournisseur()
        application = _ApplicationQui404()

        self._appeler("/media/note.txt", application)

        assert application.vue == [], "la requête a été routée au lieu d'être servie"

    def test_les_autres_chemins_sont_routes(self, fournisseur) -> None:
        fournisseur()
        application = _ApplicationQui404()

        self._appeler("/mediatheque", application)

        assert application.vue == ["/mediatheque"]

    def test_une_tranche_garde_son_statut_complet(self, fournisseur) -> None:
        """206 sortait sans phrase de raison, ce que la PEP 3333 refuse."""
        reponse = Response(206, b"tranche", "video/mp4")
        reponse.headers["Content-Range"] = "bytes 0-6/25"
        fournisseur(reponse)

        vu, _ = self._appeler("/media/film.mp4", _ApplicationQui404(),
                              {"HTTP_RANGE": "bytes=0-6"})

        assert vu["status"] == "206 Partial Content"
        assert vu["headers"]["Content-Range"] == "bytes 0-6/25"


# ── Le formatage des statuts ─────────────────────────────────────────────────

class TestFormatStatus:
    """La table du module ne portait ni 206, ni 416, ni 503."""

    @pytest.mark.parametrize(("code", "attendu"), [
        (206, "206 Partial Content"),
        (416, "416 Requested Range Not Satisfiable"),
        (503, "503 Service Unavailable"),
    ])
    def test_les_codes_absents_de_la_table_ont_leur_raison(
        self, code: int, attendu: str,
    ) -> None:
        assert _format_status(code) == attendu

    def test_503_est_rendu_par_le_coeur_lui_meme(self) -> None:
        """Ce n'est pas un cas d'école : `_service_unavailable` le renvoie."""
        source = (PROJECT_ROOT / "core" / "app" / "application.py").read_text(encoding="utf-8")

        assert "503" in source

    @pytest.mark.parametrize(("code", "attendu"), [
        (200, "200 OK"),
        (404, "404 Not Found"),
        (413, "413 Payload Too Large"),
    ])
    def test_les_formulations_de_forge_priment(self, code: int, attendu: str) -> None:
        """413 vaut « Payload Too Large » chez Forge, pas la phrase de la stdlib."""
        assert _format_status(code) == attendu

    def test_un_code_inconnu_ne_leve_pas(self) -> None:
        assert _format_status(799) == "799"


# ── La parité, vérifiée sur le squelette ─────────────────────────────────────

class TestParite:

    def test_le_squelette_delegue_a_la_source_unique(self) -> None:
        """Il portait sa propre copie du service : c'est ainsi qu'on diverge."""
        source = (PROJECT_ROOT / "skeleton" / "data" / "app.py").read_text(encoding="utf-8")

        assert "from core.http.media import media_response" in source
        assert "self._send_response(media_response(path, request))" in source

    def test_le_squelette_n_a_plus_sa_copie(self) -> None:
        source = (PROJECT_ROOT / "skeleton" / "data" / "app.py").read_text(encoding="utf-8")

        assert "from forge_mvc_files import serve_media_file" not in source
        assert 'path.removeprefix("/media/")' not in source

    def test_le_prefixe_est_le_meme_des_deux_cotes(self) -> None:
        source = (PROJECT_ROOT / "skeleton" / "data" / "app.py").read_text(encoding="utf-8")

        assert f'request.path.startswith("{MEDIA_PREFIX.rstrip("/")}")' in source or \
               f'startswith("{MEDIA_PREFIX}")' in source
