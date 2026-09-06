# Calculateur de sous-réseau (SSR pur)

**Objectif**{ .intro-label } : construire un outil de calcul sans aucun JavaScript, selon le motif idiomatique de Forge.

**Ce que vous allez apprendre :**{ .intro-label } isoler le calcul dans un **service Python testable**, le relier par un contrôleur, et rendre le résultat par une vue Jinja, avec un POST protégé par CSRF.

L'outil prend une notation CIDR (par exemple `192.168.1.10/24`) et affiche l'adresse réseau, le masque, l'adresse de diffusion, la plage d'hôtes et le nombre d'hôtes.
Tout le calcul reste en Python : la vue ne fait qu'afficher, Jinja échappe les valeurs, aucun risque d'injection.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [Outils interactifs](../../features/outils-interactifs.md) | le motif SSR pur et ses garanties |
    | [L'objet Request](../../core-http/request.md) | l'accesseur `form(...)` pour lire un champ de POST |
    | [La protection CSRF](../../core-security/csrf.md) | pourquoi le champ caché `csrf_token` est requis |

??? note "Service"
    Le cœur de l'outil est une fonction pure, sans dépendance HTTP, donc testable en isolation.
    Créez `mvc/services/subnet.py` :

    ```python
    # mvc/services/subnet.py
    import ipaddress


    def describe_subnet(cidr: str) -> dict[str, str]:
        """Décrit un sous-réseau IPv4 à partir d'une notation CIDR (ex. 192.168.1.10/24).

        Lève ValueError si la notation est invalide (le contrôleur la rattrape).
        """
        network = ipaddress.ip_network(cidr, strict=False)
        hosts = list(network.hosts())
        return {
            "reseau": str(network.network_address),
            "masque": str(network.netmask),
            "diffusion": str(network.broadcast_address),
            "premier_hote": str(hosts[0]) if hosts else "-",
            "dernier_hote": str(hosts[-1]) if hosts else "-",
            "nb_hotes": str(network.num_addresses - 2 if network.num_addresses > 2 else 0),
        }
    ```

    La fonction ne connaît ni la requête ni la réponse : elle se teste avec un simple `assert describe_subnet("192.168.1.0/24")["nb_hotes"] == "254"`.

??? note "Contrôleur"
    Le contrôleur relie HTTP et service, et garde la validation côté serveur.
    Créez `mvc/controllers/sandbox_controller.py` :

    ```python
    # mvc/controllers/sandbox_controller.py
    from core.http.request import Request
    from core.http.response import Response
    from core.mvc.controller.base_controller import BaseController
    from core.security.cookies import set_session_cookie
    from core.security.session import get_session, get_session_id
    from core.sessions.manager import get_session_store
    from mvc.services.subnet import describe_subnet


    class SandboxController:

        @staticmethod
        def _start_session(request: Request):
            """Garantit une session active et renvoie (session_id, csrf_token).

            Le jeton CSRF vit dans la session : sans session, il serait vide.
            Ce helper reprend celui du parcours cœur (palier CSRF).
            """
            session_id = get_session_id(request)
            if session_id is None or get_session(session_id) is None:
                session_id = get_session_store().create()
            session = get_session(session_id) or {}
            return session_id, session.get("csrf_token", "")

        @staticmethod
        def subnet_form(request: Request) -> Response:
            session_id, csrf_token = SandboxController._start_session(request)
            response = BaseController.render(
                "sandbox/subnet.html",
                request=request,
                context={"csrf_token": csrf_token, "resultat": None, "erreur": None},
            )
            set_session_cookie(response, session_id)
            return response

        @staticmethod
        def subnet_compute(request: Request) -> Response:
            session_id, csrf_token = SandboxController._start_session(request)
            cidr = request.form("cidr", default="").strip()
            resultat = None
            erreur = None
            try:
                resultat = describe_subnet(cidr)
            except ValueError:
                erreur = "Notation CIDR invalide (exemple attendu : 192.168.1.10/24)."
            response = BaseController.render(
                "sandbox/subnet.html",
                request=request,
                context={"csrf_token": csrf_token, "resultat": resultat, "erreur": erreur},
            )
            set_session_cookie(response, session_id)
            return response
    ```

    | Élément | Rôle |
    |---|---|
    | `_start_session(request)` | Garantit une session active et un jeton CSRF non vide (même helper que le parcours cœur). |
    | `request.form("cidr", default="")` | Lit le champ soumis en POST. |
    | `describe_subnet(cidr)` | Le calcul, délégué au service pur. |
    | `try / except ValueError` | La validation reste côté serveur, aucun message d'erreur brut renvoyé au client. |

    L'outil ne persiste rien : un calculateur sans état n'a pas à écrire en base.

??? note "Routes"
    Ajoutez les deux routes dans le groupe public de `mvc/routes/__init__.py` :

    ```python
    # mvc/routes/__init__.py
    from mvc.controllers.sandbox_controller import SandboxController

    with router.group("", public=True) as public:
        # ... routes existantes ...
        public.add("GET",  "/sandbox/subnet", SandboxController.subnet_form, name="sandbox-subnet_form")
        public.add("POST", "/sandbox/subnet", SandboxController.subnet_compute, name="sandbox-subnet_compute")
    ```

    Deux routes sur le même chemin : `GET` affiche le formulaire, `POST` traite la saisie.

??? note "Vue"
    Créez `mvc/views/sandbox/subnet.html`, sans une ligne de JavaScript :

    ```html
    {% extends "layouts/public.html" %}

    {% block title %}Calculateur de sous-réseau{% endblock %}

    {% block content %}
    <h1>Calculateur de sous-réseau</h1>

    <form method="post" action="/sandbox/subnet">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <label>Notation CIDR :
            <input type="text" name="cidr" value="192.168.1.10/24" required>
        </label>
        <button type="submit">Calculer</button>
    </form>

    {% if erreur %}
        <p role="alert">{{ erreur }}</p>
    {% endif %}

    {% if resultat %}
        <table>
            <tr><th>Adresse réseau</th><td>{{ resultat.reseau }}</td></tr>
            <tr><th>Masque</th><td>{{ resultat.masque }}</td></tr>
            <tr><th>Diffusion</th><td>{{ resultat.diffusion }}</td></tr>
            <tr><th>Premier hôte</th><td>{{ resultat.premier_hote }}</td></tr>
            <tr><th>Dernier hôte</th><td>{{ resultat.dernier_hote }}</td></tr>
            <tr><th>Nombre d'hôtes</th><td>{{ resultat.nb_hotes }}</td></tr>
        </table>
    {% endif %}
    {% endblock %}
    ```

    Chaque `{{ resultat.xxx }}` est échappé par Jinja : aucune valeur ne peut injecter de balise.

??? note "Tests"
    | Action | Résultat |
    |---|---|
    | `GET https://localhost:8000/sandbox/subnet` | le formulaire, prérempli avec `192.168.1.10/24` |
    | Soumettre `192.168.1.10/24` | réseau `192.168.1.0`, masque `255.255.255.0`, 254 hôtes |
    | Soumettre `nimportequoi` | le message d'erreur, sans plantage |

    Le service se teste aussi hors HTTP :

    ```python
    from mvc.services.subnet import describe_subnet

    def test_subnet_24():
        assert describe_subnet("10.0.0.5/24")["nb_hotes"] == "254"
    ```

??? note "À retenir"
    - Le calcul vit dans un **service Python pur**, testable sans requête HTTP.
    - Le contrôleur relie HTTP et service, la validation reste côté serveur.
    - La vue Jinja échappe toutes les valeurs : aucun HTML construit à la main.
    - Zéro JavaScript : c'est le motif à préférer chaque fois qu'il suffit.

Au palier suivant, nous construisons un outil temps réel qui, lui, a besoin d'un peu de JavaScript local.

[Continuer avec l'oscilloscope](oscilloscope.md)
