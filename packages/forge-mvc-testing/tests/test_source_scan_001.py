"""Le retrait de la prose d'un source (SOURCE-SCAN-001).

`code_sans_prose` sert de socle à plusieurs garde-fous de structure. Un défaut
y serait donc silencieux dans les deux sens : trop retirer laisserait passer un
vrai manquement, trop peu ferait échouer un code correct sur un commentaire.

Les cas couverts sont ceux qui ont réellement mis des garde-fous en défaut au
cours d'un même cycle de pré-mortem.
"""
from __future__ import annotations

import textwrap

from forge_mvc_testing.source_scan import code_sans_prose, lignes_de_prose


def test_la_docstring_de_module_est_retiree() -> None:
    source = '"""Ce module ne fait pas de SELECT."""\nx = 1\n'

    assert "SELECT" not in code_sans_prose(source)
    assert "x = 1" in code_sans_prose(source)


def test_la_docstring_de_fonction_est_retiree() -> None:
    """Le cas exact du mot « forme » qui a fait échouer un garde-fou d'authentification."""
    source = textwrap.dedent('''
        def f():
            """Explique la forme attendue."""
            return 1
    ''')

    code = code_sans_prose(source)

    assert "forme" not in code
    assert "return 1" in code


def test_les_commentaires_sont_retires() -> None:
    """Le cas des commentaires citant `CURRENT_TIMESTAMP` pour dire qu'il n'est plus employé."""
    source = "# On n'emploie plus CURRENT_TIMESTAMP ici.\nvaleur = utc_now()\n"

    code = code_sans_prose(source)

    assert "CURRENT_TIMESTAMP" not in code
    assert "utc_now()" in code


def test_une_chaine_ordinaire_survit() -> None:
    """Seule la **première** instruction d'un corps est une docstring.

    Retirer toutes les chaînes viderait le SQL des modules, et le garde-fou ne
    verrait plus rien. C'est le mode de défaillance le plus dangereux : il rend
    tout vert.
    """
    source = 'def f():\n    """Doc."""\n    return "SELECT * FROM t"\n'

    code = code_sans_prose(source)

    assert "Doc." not in code
    assert "SELECT * FROM t" in code


def test_le_source_d_une_methode_est_dedente() -> None:
    """`inspect.getsource` d'une méthode rend son indentation de classe.

    Le source ne s'analyse alors pas tel quel. `inspect.cleandoc` ne convient
    pas : il aligne toutes les lignes sur la première et aplatit le corps, ce
    qui casse la syntaxe et laissait la docstring intacte.
    """
    source = '    def m(self):\n        """Cite 42P01 pour l\'expliquer."""\n        return self.x\n'

    code = code_sans_prose(source)

    assert "42P01" not in code, "la docstring d'une méthode indentée doit être retirée"
    assert "return self.x" in code


def test_la_numerotation_des_lignes_est_conservee() -> None:
    """Les lignes retirées deviennent vides, faute de quoi les messages mentent."""
    source = '"""Doc\nsur deux lignes."""\nx = 1\n'

    lignes = code_sans_prose(source).splitlines()

    assert len(lignes) == 3
    assert lignes[2] == "x = 1"


def test_un_source_invalide_ne_leve_pas() -> None:
    """Un garde-fou n'a pas à se transformer en analyseur de syntaxe."""
    source = "def f(:\n    # commentaire\n    pass\n"

    code = code_sans_prose(source)

    assert "commentaire" not in code
    assert "def f(:" in code


def test_les_lignes_de_prose_sont_reportees() -> None:
    source = '"""Doc."""\n# note\nx = 1\n'

    assert lignes_de_prose(source) == {1, 2}
