"""Garde-fou LANDING-CONTACT-NAV-FORM-001 — identité publique Forge.

Verrouille (refondu pour RELEASE-BETA10-LANDING-CONTACT-HOTFIX-001) :

  * la **navigation** principale de la landing canonique
    (``mvc/views/landing/index.html``) se termine par une entrée
    ``Contact`` placée APRÈS l'entrée ``GitHub`` ;
  * une section ``<section id="contact">`` existe dans la landing ;
  * cette section affiche **Roger Lequette** et **forgemvc@gmail.com** ;
  * un lien ``mailto:forgemvc@gmail.com`` est exposé ;
  * un bouton/lien d'action **Écrire à Forge** est visible et porte
    un ``mailto:`` pré-rempli (``subject=Contact%20Forge``) ;
  * la section ne contient **AUCUN** ``<form>``, ``<input>`` ou
    ``<textarea>`` (carte statique, pas de saisie navigateur) ;
  * aucun texte technique visible (``ContactController``, ``/contact``,
    ``SMTP``, « traitement serveur ») n'apparaît dans le contenu rendu —
    ces règles vivent dans le commentaire HTML mainteneur, pas dans la
    landing publique ;
  * la landing canonique et ``docs/index.html`` sont synchronisées
    (mêmes éléments de navigation et de contact) ;
  * AUCUNE occurrence de l'ancienne identité (``Roger Cauchon`` ou
    ``caucroge@gmail.com``) ne subsiste dans le dépôt suivi.

Décision définitive — la landing reste STATIQUE
-----------------------------------------------
Forge ne doit pas créer de route ``/contact``, ni de
``ContactController``, ni de logique serveur d'envoi mail pour la landing
officielle. Le bouton **Écrire à Forge** est un simple lien ``mailto:``
côté client — il ne déclenche aucun traitement serveur Forge.

Raison : Forge est un framework générique. Le site officiel peut proposer
un moyen de contact, mais il ne doit pas polluer le framework avec une
route ou une logique applicative qui ne concerne pas les projets futurs
des développeurs Forge.

Cette frontière est verrouillée par ``TestNoContactRouteOrController``.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


_REPO_ROOT = Path(__file__).resolve().parents[2]
_LANDING_SRC = _REPO_ROOT / "mvc" / "views" / "landing" / "index.html"
_LANDING_PUB = _REPO_ROOT / "docs" / "index.html"


@pytest.fixture(scope="module")
def landing_src() -> str:
    return _LANDING_SRC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def landing_pub() -> str:
    return _LANDING_PUB.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------


class TestNavigationContactEntry:
    def test_nav_has_contact_link(self, landing_src):
        assert 'href="#contact"' in landing_src, (
            "La landing doit contenir un lien vers `#contact`."
        )
        assert ">Contact</a>" in landing_src or ">Contact<" in landing_src

    def test_contact_link_placed_after_github_in_nav(self, landing_src):
        nav_end = landing_src.find("</nav>")
        assert nav_end > 0, "Élément `<nav>` introuvable dans la landing."
        nav_block = landing_src[:nav_end]
        github_pos = nav_block.rfind(">GitHub</a>")
        contact_pos = nav_block.rfind(">Contact</a>")
        assert github_pos > 0, "Lien GitHub absent de la nav."
        assert contact_pos > 0, "Lien Contact absent de la nav."
        assert contact_pos > github_pos, (
            "Le lien Contact doit être placé APRÈS le lien GitHub dans la nav."
        )


# ---------------------------------------------------------------------------
# Section #contact — carte statique mailto
# ---------------------------------------------------------------------------


class TestContactSection:
    def test_section_exists(self, landing_src):
        assert 'id="contact"' in landing_src, (
            "La landing doit contenir `<section id=\"contact\">`."
        )

    def test_section_title(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        assert ">Contact</h2>" in section, (
            "La section contact doit avoir un titre `<h2>Contact</h2>`."
        )

    def test_section_displays_owner_name(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        assert "Roger Lequette" in section, (
            "La section contact doit afficher le nom `Roger Lequette`."
        )

    def test_section_displays_email(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        assert "forgemvc@gmail.com" in section, (
            "La section contact doit afficher l'adresse `forgemvc@gmail.com`."
        )

    def test_section_has_mailto_link(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        assert "mailto:forgemvc@gmail.com" in section, (
            "La section contact doit contenir un lien "
            "`mailto:forgemvc@gmail.com`."
        )

    def test_section_has_action_button(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        assert "Écrire à Forge" in section, (
            "La section contact doit afficher un bouton/lien "
            "`Écrire à Forge`."
        )

    def test_action_button_carries_mailto_subject(self, landing_src):
        """Le lien d'action `Écrire à Forge` doit pré-remplir le sujet."""
        section = _extract_section(landing_src, 'id="contact"')
        # On accepte `Contact%20Forge` (URL-encoded) ou `Contact Forge`
        # (espace littéral si l'auteur préfère ce style).
        assert (
            "subject=Contact%20Forge" in section
            or "subject=Contact Forge" in section
        ), (
            "Le lien d'action de contact doit porter un `subject=...` "
            "pré-rempli (`Contact%20Forge` ou équivalent)."
        )


class TestContactSectionNoFormFields:
    """La section contact doit rester une carte statique : aucun formulaire,
    aucun champ de saisie. Le bouton `Écrire à Forge` est un lien `mailto:`,
    pas un `<form>`."""

    def test_no_form_in_section(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        assert "<form" not in section, (
            "La section contact ne doit contenir AUCUN `<form>` "
            "(carte statique mailto uniquement — décision "
            "RELEASE-BETA10-LANDING-CONTACT-HOTFIX-001)."
        )

    def test_no_input_in_section(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        assert "<input" not in section, (
            "La section contact ne doit contenir AUCUN `<input>`."
        )

    def test_no_textarea_in_section(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        assert "<textarea" not in section, (
            "La section contact ne doit contenir AUCUN `<textarea>`."
        )

    def test_no_button_submit_in_section(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        assert 'type="submit"' not in section, (
            "La section contact ne doit contenir AUCUN bouton submit "
            "(aucun formulaire à soumettre — lien `mailto:` uniquement)."
        )


class TestContactSectionNoTechnicalText:
    """Le texte technique (ContactController, route /contact, SMTP,
    « traitement serveur ») doit rester dans le commentaire HTML mainteneur,
    PAS dans le contenu rendu de la section publique."""

    @pytest.mark.parametrize("forbidden", [
        "ContactController",
        "/contact",
        "SMTP",
        "traitement serveur",
        "base SMTP",
    ])
    def test_no_technical_text_in_visible_section(self, landing_src, forbidden):
        section = _extract_section(landing_src, 'id="contact"')
        visible = _strip_html_comments(section)
        assert forbidden not in visible, (
            f"Texte technique `{forbidden}` détecté dans le contenu visible "
            "de la section contact. Ces détails doivent rester dans le "
            "commentaire HTML mainteneur qui précède la section, pas dans "
            "le rendu public."
        )


# ---------------------------------------------------------------------------
# Synchronisation landing canonique ↔ docs/index.html
# ---------------------------------------------------------------------------


class TestLandingSyncedWithDocsIndex:
    """`docs/index.html` doit refléter la landing canonique après
    `forge sync:landing`."""

    def test_pub_contains_contact_nav(self, landing_pub):
        assert 'href="#contact"' in landing_pub
        assert ">Contact</a>" in landing_pub

    def test_pub_contains_contact_section(self, landing_pub):
        assert 'id="contact"' in landing_pub

    def test_pub_contains_owner_name(self, landing_pub):
        assert "Roger Lequette" in landing_pub

    def test_pub_contains_contact_email(self, landing_pub):
        assert "forgemvc@gmail.com" in landing_pub

    def test_pub_contains_action_button(self, landing_pub):
        assert "Écrire à Forge" in landing_pub

    def test_pub_has_no_form_in_contact(self, landing_pub):
        section = _extract_section(landing_pub, 'id="contact"')
        assert "<form" not in section, (
            "`docs/index.html` contient encore un `<form>` dans la section "
            "contact — relancer `forge sync:landing`."
        )

    def test_pub_no_old_owner_name(self, landing_pub):
        assert "Roger Cauchon" not in landing_pub

    def test_pub_no_old_email(self, landing_pub):
        assert "caucroge@gmail.com" not in landing_pub


# ---------------------------------------------------------------------------
# Aucune occurrence de l'ancienne identité dans le dépôt suivi
# ---------------------------------------------------------------------------


def _tracked_files() -> list[Path]:
    """Liste des fichiers suivis par Git (équivalent à `git ls-files`)."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return [_REPO_ROOT / line for line in result.stdout.splitlines() if line]


_BINARY_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pdf", ".zip", ".gz", ".tar",
})


def _searchable_files() -> list[Path]:
    out = []
    for p in _tracked_files():
        if p.suffix.lower() in _BINARY_EXTENSIONS:
            continue
        # Le test méta lui-même mentionne `Roger Cauchon` / `caucroge` dans
        # ses docstrings (« interdit »). On l'exclut pour éviter une
        # auto-collision.
        if p.resolve() == Path(__file__).resolve():
            continue
        if not p.is_file():
            continue
        out.append(p)
    return out


class TestNoLegacyIdentityInTrackedFiles:
    """L'ancien nom et l'ancien email ne doivent apparaître nulle part
    dans le dépôt suivi (Git)."""

    def test_no_old_owner_name(self):
        offenders = []
        for path in _searchable_files():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if "Roger Cauchon" in text:
                offenders.append(str(path.relative_to(_REPO_ROOT)))
        assert not offenders, (
            f"Occurrences résiduelles de `Roger Cauchon` dans : {offenders}. "
            "Remplacer par `Roger Lequette`."
        )

    def test_no_old_email(self):
        offenders = []
        for path in _searchable_files():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if "caucroge@gmail.com" in text:
                offenders.append(str(path.relative_to(_REPO_ROOT)))
        assert not offenders, (
            f"Occurrences résiduelles de `caucroge@gmail.com` dans : "
            f"{offenders}. Remplacer par `forgemvc@gmail.com`."
        )


# ---------------------------------------------------------------------------
# Frontière framework — pas de route /contact, pas de ContactController
# ---------------------------------------------------------------------------


class TestNoContactRouteOrController:
    """Décision définitive LANDING-CONTACT-NAV-FORM-001 (renforcée par
    RELEASE-BETA10-LANDING-CONTACT-HOTFIX-001).

    La landing reste statique (``mailto:forgemvc@gmail.com``). Forge **ne
    doit pas** ajouter :

      * une route ``/contact`` (GET ou POST) ;
      * un fichier ``mvc/controllers/contact_controller.py`` ou tout
        ``ContactController`` enregistré ;
      * un handler POST côté serveur traitant un formulaire de contact ;
      * une logique d'envoi SMTP déclenchée depuis la landing ;
      * une dépendance à un service tiers de formulaire.
    """

    def test_no_contact_route_in_routes_py(self):
        routes_path = _REPO_ROOT / "mvc" / "routes.py"
        if not routes_path.is_file():
            pytest.skip("mvc/routes.py absent — projet sans routes applicatives.")
        text = routes_path.read_text(encoding="utf-8")
        forbidden_patterns = (
            'add("GET", "/contact"',
            'add("POST", "/contact"',
            "add('GET', '/contact'",
            "add('POST', '/contact'",
            '"/contact",',
            "'/contact',",
        )
        offenders = [p for p in forbidden_patterns if p in text]
        assert not offenders, (
            f"`mvc/routes.py` contient un pattern de route `/contact` : "
            f"{offenders}. Le contact landing reste volontairement statique "
            "(mailto:forgemvc@gmail.com) — voir commentaire HTML dans "
            "`mvc/views/landing/index.html`."
        )

    def test_no_contact_controller_in_mvc_controllers(self):
        controllers_dir = _REPO_ROOT / "mvc" / "controllers"
        if not controllers_dir.is_dir():
            pytest.skip("mvc/controllers/ absent.")
        for path in controllers_dir.rglob("*.py"):
            assert "contact_controller" not in path.name.lower(), (
                f"Fichier interdit : `{path.relative_to(_REPO_ROOT)}`. "
                "Aucun `ContactController` ne doit exister dans Forge — "
                "la landing utilise `mailto:` côté client uniquement."
            )
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            assert "class ContactController" not in text, (
                f"`{path.relative_to(_REPO_ROOT)}` définit `ContactController`. "
                "Décision définitive LANDING-CONTACT-NAV-FORM-001 : pas de "
                "logique serveur de contact dans Forge."
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_section(html: str, marker: str) -> str:
    """Retourne le contenu de la première `<section ... marker ...>` jusqu'à
    son `</section>` fermante. Marker typique : `id="contact"`."""
    start_search = html.find(marker)
    assert start_search > 0, f"Marker `{marker}` introuvable."
    open_tag = html.rfind("<section", 0, start_search)
    assert open_tag > 0, f"Pas de `<section>` ouvrante avant `{marker}`."
    close_tag = html.find("</section>", start_search)
    assert close_tag > 0, "Pas de `</section>` fermante après le marker."
    return html[open_tag : close_tag + len("</section>")]


def _strip_html_comments(html: str) -> str:
    """Retire les blocs `<!-- ... -->` pour isoler le contenu visible."""
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
