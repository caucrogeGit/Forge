"""DOC-CLI-INVOCATIONS-001 — les commandes et options montrées par la doc existent.

La documentation vivante contient plus de huit cents blocs bash, dont quatre
cent trente-trois commencent par `forge`. Aucun n'était vérifié : une commande
retirée ou une option renommée y survivait indéfiniment.

Ce fichier ne les **exécute** pas, et ce choix est délibéré. Ces blocs
contiennent des `sudo`, des `pip install`, des `git push` et des commandes de
publication : les jouer serait imprudent, et la plupart supposent un projet
existant. Il vérifie ce qui se vérifie sans risque et couvre la majorité des
défauts observés :

- chaque `forge <commande>` citée est annoncée par `forge --help`, seule
  surface où l'utilisateur peut la découvrir ;
- chaque `--option` citée figure dans l'aide de sa commande, quand cette
  commande a une aide détaillée.

## Ce qui a été trouvé en l'écrivant

Cinq invocations de `cli/security/docs/auth.md` employaient encore `--email`
comme identifiant de connexion, alors que l'ADR-089 en a fait une adresse de
contact. Elles avaient survécu à la correction du ticket
`AUTH-DOC-LOGIN-CONTRACT-001`, qui n'avait repris que les exemples et pas les
tableaux ni la section d'options : troisième correctif de ce pré-mortem livré à
moitié, d'où ce relevé automatique plutôt qu'une relecture de plus.
"""
from __future__ import annotations

import collections
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_BLOC = re.compile(r"^```(?:bash|shell|sh|console)\s*$(.*?)^```", re.M | re.S)
#: `forge` doit être **invoqué**, pas cité. Le motif exige donc un début de
#: ligne, une invite `$`, un opérateur de shell, ou un chemin d'accès qui s'y
#: termine. Sans cette exigence, `git commit -m "... preparer forge x.y.z"`
#: était relevé comme une commande `forge x`.
_INVOCATION = re.compile(
    r"(?:^|[|;&]\s*|\$\s+)(?:[\w./-]*/)?forge\s+([a-z][a-z0-9:_-]*)((?:\s+[^\n|;&]*)?)"
)
_OPTION = re.compile(r"(--[a-z][a-z0-9-]*)")

#: Servies par le dispatcher, jamais par la commande elle-même.
_GENERIQUES = frozenset({"--help", "--version"})

#: `new` n'est pas dans la table des commandes, il est traité en amont.
_HORS_REGISTRE = frozenset({"new", "help"})

#: Documents qui citent délibérément une commande retirée ou renommée, chacun
#: portant déjà l'encart qui l'explique. Les vérifier reviendrait à leur
#: demander de mentir sur l'histoire qu'ils racontent.
_DOCUMENTS_HISTORIQUES = frozenset({
    "docs/architecture/optins-cli-enable-audit.md",  # nom d'époque `optin:enable` (ADR-016)
    "docs/adr/023-starter-build-canonical.md",       # `starter:build`, retiré par l'ADR-035
})


def _pages() -> list[Path]:
    pages: list[Path] = []
    for chemin in sorted(PROJECT_ROOT.rglob("*.md")):
        rel = chemin.relative_to(PROJECT_ROOT).as_posix()
        if not rel.startswith(("docs/", "core/", "cli/", "packages/")):
            continue
        if "/history/" in rel or "/build/" in rel or "official-site" in rel:
            continue
        if rel in _DOCUMENTS_HISTORIQUES:
            continue
        pages.append(chemin)
    return pages


def _invocations() -> dict[str, dict[str, list[str]]]:
    """`{commande: {option: [pages]}}`, options vides comprises."""
    trouvees: dict[str, dict[str, list[str]]] = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    for chemin in _pages():
        rel = chemin.relative_to(PROJECT_ROOT).as_posix()
        for bloc in _BLOC.finditer(chemin.read_text(encoding="utf-8")):
            for ligne in bloc.group(1).splitlines():
                nue = ligne.strip()
                if nue.startswith("#"):
                    continue
                for commande, reste in _INVOCATION.findall(nue):
                    if commande in _HORS_REGISTRE:
                        continue
                    trouvees[commande].setdefault("", []).append(rel)
                    for option in _OPTION.findall(reste):
                        if option not in _GENERIQUES:
                            trouvees[commande][option].append(rel)
    return trouvees


def _aide_generale() -> str:
    resultat = subprocess.run(
        [sys.executable, "forge.py", "--help"],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120,
    )
    return resultat.stdout


def test_le_releve_trouve_bien_des_invocations() -> None:
    """Un relevé vide passerait tous les tests suivants.

    C'est le mode de défaillance des garde-fous par balayage, et il se lit
    comme un succès.
    """
    invocations = _invocations()

    assert len(invocations) >= 50, (
        f"seulement {len(invocations)} commandes relevées : le motif s'est "
        "resserré et le garde-fou ne garde plus grand-chose"
    )


def test_chaque_commande_documentee_est_annoncee_par_l_aide() -> None:
    """Une commande que `forge --help` n'annonce pas est introuvable par l'utilisateur.

    Peu importe qu'elle fonctionne encore : la documentation la montre, l'aide
    la tait, et l'utilisateur n'a aucun moyen de trancher.
    """
    aide = _aide_generale()
    annoncees = set(re.findall(r"^\s{2,}([a-z][a-z0-9:_-]*)\s{2,}\S", aide, re.M))
    assert annoncees, "`forge --help` n'annonce aucune commande"

    fantomes: list[str] = []
    for commande, options in sorted(_invocations().items()):
        if commande not in annoncees:
            pages = sorted(set(options.get("", [])))
            fantomes.append(f"forge {commande} ({', '.join(pages[:3])})")

    assert not fantomes, (
        "Ces commandes sont montrées par la documentation et absentes de "
        "`forge --help` :\n  " + "\n  ".join(fantomes)
    )


def _commandes_avec_aide_detaillee() -> dict[str, str]:
    """Aide de chaque commande citée, quand elle en a une.

    Les commandes d'opt-in sans aide propre rendent un texte de repli et sont
    écartées : leur reprocher une option absente reviendrait à leur reprocher
    de ne pas avoir d'aide, ce qui est un autre sujet.
    """
    aides: dict[str, str] = {}
    invocations = _invocations()
    # Seules les commandes dont la doc cite une option sont interrogées : les
    # autres n'ont rien à contredire, et chaque appel est un sous-processus.
    interessantes = [c for c, opts in invocations.items() if any(o for o in opts)]
    for commande in sorted(interessantes):
        resultat = subprocess.run(
            [sys.executable, "forge.py", commande, "--help"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120,
        )
        texte = resultat.stdout + resultat.stderr
        if not texte.strip() or "n'expose pas d'aide détaillée" in texte:
            continue
        aides[commande] = texte
    return aides


def test_chaque_option_documentee_figure_dans_l_aide() -> None:
    """LE test du ticket : c'est par là que les `--email` périmés ont survécu.

    Une option renommée reste plausible dans un bloc de code : rien ne la
    distingue d'une option valide tant que personne ne l'exécute.
    """
    invocations = _invocations()
    aides = _commandes_avec_aide_detaillee()

    absentes: list[str] = []
    for commande, aide in aides.items():
        for option, pages in invocations[commande].items():
            if not option or option in aide:
                continue
            uniques = sorted(set(pages))
            absentes.append(f"forge {commande} {option}  ({', '.join(uniques[:2])})")

    assert not absentes, (
        "Ces options sont montrées par la documentation et absentes de l'aide "
        "de leur commande :\n  " + "\n  ".join(sorted(absentes))
    )


def test_les_documents_historiques_portent_leur_avertissement() -> None:
    """Une exemption sans son motif est une porte laissée ouverte.

    Ces deux pages citent une commande retirée **à dessein**, et le disent.
    Si l'encart disparaît, l'exemption doit tomber avec lui.
    """
    manquants: list[str] = []
    for rel in _DOCUMENTS_HISTORIQUES:
        chemin = PROJECT_ROOT / rel
        if not chemin.exists():
            manquants.append(f"{rel} (le fichier n'existe plus)")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if "ADR-016" not in texte and "ADR-035" not in texte and "n'existe plus" not in texte:
            manquants.append(f"{rel} (ne renvoie plus à la décision qui l'explique)")

    assert not manquants, (
        "Ces pages sont exemptées au motif qu'elles expliquent la commande "
        "retirée qu'elles citent :\n  " + "\n  ".join(manquants)
    )
