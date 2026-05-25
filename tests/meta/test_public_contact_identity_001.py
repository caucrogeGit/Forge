"""Garde-fou LANDING-CONTACT-NAV-FORM-001 — identité publique Forge.

Verrouille :

  * la **navigation** principale de la landing canonique
    (``mvc/views/landing/index.html``) se termine par une entrée
    ``Contact`` placée APRÈS l'entrée ``GitHub`` ;
  * une section ``<section id="contact">`` existe dans la landing ;
  * cette section affiche **Roger Lequette** et **forgemvc@gmail.com** ;
  * un bouton ``Envoyer`` permet de déclencher l'envoi vers
    ``forgemvc@gmail.com`` (cible ``mailto:`` ou équivalent
    ``action="mailto:..."``) ;
  * la landing canonique et ``docs/index.html`` sont synchronisées
    (mêmes éléments de navigation et de contact) ;
  * AUCUNE occurrence de l'ancienne identité (``Roger Cauchon`` ou
    ``caucroge@gmail.com``) ne subsiste dans le dépôt suivi.

Décision définitive — le formulaire reste STATIQUE
--------------------------------------------------
Forge ne doit pas créer de route ``/contact``, ni de
``ContactController``, ni de logique serveur d'envoi mail pour la landing
officielle. Le bouton ``Envoyer`` ouvre un email vers
``forgemvc@gmail.com`` côté client — il ne déclenche aucun traitement
serveur Forge.

Raison : Forge est un framework générique. Le site officiel peut proposer
un moyen de contact, mais il ne doit pas polluer le framework avec une
route ou une logique applicative qui ne concerne pas les projets futurs
des développeurs Forge.

Cette frontière est verrouillée par ``TestNoContactRouteOrController``.
"""
from __future__ import annotations

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
        # Il faut une ancre `<a ... href="#contact">Contact</a>` quelque part
        # dans la nav (les ancres autorisent les attributs en n'importe quel
        # ordre — on cherche la cible + le label).
        assert 'href="#contact"' in landing_src, (
            "La landing doit contenir un lien vers `#contact`."
        )
        # Le mot Contact apparaît au moins une fois comme texte de lien
        # ou de titre.
        assert ">Contact</a>" in landing_src or ">Contact<" in landing_src

    def test_contact_link_placed_after_github_in_nav(self, landing_src):
        # On cherche la position du lien GitHub de la nav (le premier qui
        # n'est pas dans le footer).
        # Approche : la navigation principale se termine par `</div>` puis
        # `<form` (barre de recherche) puis `</nav>`. On coupe le HTML
        # jusqu'à `</nav>` et on vérifie l'ordre.
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
# Section #contact
# ---------------------------------------------------------------------------


class TestContactSection:
    def test_section_exists(self, landing_src):
        assert 'id="contact"' in landing_src, (
            "La landing doit contenir `<section id=\"contact\">`."
        )

    def test_section_titles(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        # Le titre H2 « Contact » est obligatoire pour la lisibilité.
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

    def test_form_targets_contact_email(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        # Le formulaire doit pointer vers mailto:forgemvc@gmail.com
        # (ou contenir le lien mailto si un click direct est proposé).
        assert "mailto:forgemvc@gmail.com" in section, (
            "Le formulaire de contact doit cibler `mailto:forgemvc@gmail.com`."
        )

    def test_form_has_send_button(self, landing_src):
        section = _extract_section(landing_src, 'id="contact"')
        # Un bouton « Envoyer » doit être présent.
        assert "Envoyer" in section, (
            "La section contact doit afficher un bouton `Envoyer`."
        )

    @pytest.mark.parametrize("field_name", ["nom", "email", "sujet", "message"])
    def test_form_has_required_fields(self, landing_src, field_name):
        section = _extract_section(landing_src, 'id="contact"')
        assert f'name="{field_name}"' in section, (
            f"Le formulaire de contact doit exposer un champ `{field_name}`."
        )


# ---------------------------------------------------------------------------
# Synchronisation landing canonique ↔ docs/index.html
# ---------------------------------------------------------------------------


class TestLandingSyncedWithDocsIndex:
    """`docs/index.html` doit refléter la landing canonique après
    `forge sync:landing`. On vérifie les marqueurs nouveaux du ticket."""

    def test_pub_contains_contact_nav(self, landing_pub):
        assert 'href="#contact"' in landing_pub
        assert ">Contact</a>" in landing_pub

    def test_pub_contains_contact_section(self, landing_pub):
        assert 'id="contact"' in landing_pub

    def test_pub_contains_owner_name(self, landing_pub):
        assert "Roger Lequette" in landing_pub

    def test_pub_contains_contact_email(self, landing_pub):
        assert "forgemvc@gmail.com" in landing_pub

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


# Quelques fichiers binaires ou volumineux à exclure de la recherche
# (ils ne peuvent pas contenir de texte sensible).
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
    """Décision définitive LANDING-CONTACT-NAV-FORM-001.

    Le formulaire de contact de la landing reste statique
    (``mailto:forgemvc@gmail.com``). Forge **ne doit pas** ajouter :

      * une route ``/contact`` (GET ou POST) ;
      * un fichier ``mvc/controllers/contact_controller.py`` ou tout
        ``ContactController`` enregistré ;
      * un handler POST côté serveur traitant un formulaire de contact ;
      * une logique d'envoi SMTP déclenchée depuis la landing ;
      * une dépendance à un service tiers de formulaire.

    Raison : Forge est un framework générique. Le site officiel propose
    un moyen de contact, mais le core ne doit pas imposer cette logique
    aux projets futurs.
    """

    def test_no_contact_route_in_routes_py(self):
        routes_path = _REPO_ROOT / "mvc" / "routes.py"
        if not routes_path.is_file():
            pytest.skip("mvc/routes.py absent — projet sans routes applicatives.")
        text = routes_path.read_text(encoding="utf-8")
        # Cherche des marqueurs précis. Le doublon `"/contact"` ou
        # `'/contact'` au niveau d'une déclaration de route serait suspect.
        # On accepte des mentions dans des chaînes de description mais on
        # interdit les patterns d'enregistrement de route.
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
            f"{offenders}. Le formulaire de contact landing reste "
            "volontairement statique (mailto:forgemvc@gmail.com) — voir "
            "commentaire HTML dans `mvc/views/landing/index.html`."
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

    def test_form_action_is_mailto_only(self):
        """Le `<form action="...">` du bloc contact doit cibler `mailto:`,
        jamais une URL applicative Forge."""
        text = _LANDING_SRC.read_text(encoding="utf-8")
        section = _extract_section(text, 'id="contact"')
        # On capture tous les `action="..."` de la section.
        import re
        actions = re.findall(r'action="([^"]+)"', section)
        assert actions, (
            "La section #contact doit contenir au moins un `<form action=...>`."
        )
        for action in actions:
            assert action.startswith("mailto:"), (
                f"Le formulaire de contact ne doit pas pointer vers une URL "
                f"applicative : `action=\"{action}\"`. Seul `mailto:` est "
                "autorisé (LANDING-CONTACT-NAV-FORM-001)."
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_section(html: str, marker: str) -> str:
    """Retourne le contenu de la première `<section ... marker ...>` jusqu'à
    son `</section>` fermante. Marker typique : `id="contact"`."""
    start_search = html.find(marker)
    assert start_search > 0, f"Marker `{marker}` introuvable."
    # Remonte au `<section` ouvrant le plus proche.
    open_tag = html.rfind("<section", 0, start_search)
    assert open_tag > 0, f"Pas de `<section>` ouvrante avant `{marker}`."
    close_tag = html.find("</section>", start_search)
    assert close_tag > 0, "Pas de `</section>` fermante après le marker."
    return html[open_tag : close_tag + len("</section>")]
