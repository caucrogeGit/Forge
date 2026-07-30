#!/usr/bin/env python3
"""RELEASE-PYPI-COMPLETENESS-GUARD-001 — croiser le dépôt, la construction et PyPI.

La rc2 a été publiée avec vingt-quatre distributions sur vingt-sept. Les trois
absentes ne manquaient pas par accident de construction : elles sont nées après
la dernière publication, et rien ne vérifiait qu'une distribution du dépôt avait
bien une contrepartie publiée. Le pré-mortem du 2026-07-28 a montré ce que cela
coûte : le cœur n'a plus `cli/entities` depuis l'ADR-070, la rc2 publiée
l'embarque encore, donc publier une rc3 sans `forge-mvc-entities` retirerait
`make:entity`, `make:crud`, les migrations et `db:*` à tous les projets. Une
release peut ainsi être une régression sans qu'aucune étape ne le dise.

Trois ensembles, trois questions.

    dépôt      packages/*/pyproject.toml, plus le cœur à la racine
    build      dist/ et packages/*/dist/
    PyPI       ce qu'un utilisateur peut réellement installer

- Une distribution du dépôt absente de la construction ne sera pas publiée.
- Une distribution du dépôt absente de PyPI n'a jamais atteint personne.
- Une distribution sur PyPI absente du dépôt est **orpheline** : plus
  maintenue, toujours installable, elle continue de servir du code mort.

Le réseau peut manquer. Dans ce cas le script le **dit** et échoue si on le lui
demande, plutôt que de passer en silence : un garde qui se tait quand il ne
peut pas vérifier ne garde rien.
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Distributions publiées un jour, puis retirées du dépôt (absorbées). Elles
#: restent installables depuis PyPI tant qu'elles ne sont pas retirées
#: (« yank »), et servent alors un code que le dépôt ne maintient plus. Toute
#: suppression d'un paquet de `packages/` doit s'inscrire ici.
ABSORBED: "dict[str, str]" = {
    "forge-mvc-pivot": "absorbé par forge-mvc-entities (ADR-070)",
    "forge-mvc-media": "absorbé par forge-mvc-images (ADR-018)",
}


def repo_distributions() -> "list[str]":
    """Noms de distribution portés par le dépôt : le cœur et chaque opt-in."""
    noms: "list[str]" = []
    for pyproject in [PROJECT_ROOT / "pyproject.toml",
                      *sorted(PROJECT_ROOT.glob("packages/*/pyproject.toml"))]:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        nom = data.get("project", {}).get("name")
        if nom:
            noms.append(str(nom))
    return noms


def built_distributions() -> "set[str]":
    """Noms lus dans les artefacts construits (`dist/`), wheels et sdists."""
    noms: "set[str]" = set()
    for dossier in [PROJECT_ROOT / "dist", *PROJECT_ROOT.glob("packages/*/dist")]:
        for artefact in dossier.glob("*"):
            if artefact.suffix not in {".whl", ".gz"}:
                continue
            # forge_mvc_entities-1.0.0rc3-py3-none-any.whl -> forge-mvc-entities
            noms.add(artefact.name.split("-")[0].replace("_", "-"))
    return noms


def pypi_versions(nom: str, *, timeout: float = 10.0) -> "list[str] | None":
    """Versions **installables**, `[]` si aucune, `None` si PyPI est muet.

    Une version retirée (« yank ») ne compte pas : elle reste servie à qui
    l'épingle déjà, mais sort de toute résolution nouvelle. C'est exactement
    l'état visé pour une distribution absorbée, et le garde doit donc cesser
    d'avertir une fois le retrait fait, sans quoi il crierait pour toujours
    (PKG-ORPHAN-YANK-001).
    """
    url = f"https://pypi.org/pypi/{nom}/json"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as reponse:
            releases = json.load(reponse).get("releases", {})
    except urllib.error.HTTPError as erreur:
        if erreur.code == 404:
            return []
        return None
    except Exception:  # noqa: BLE001 — réseau absent, DNS, proxy : tous muets
        return None
    vivantes: "list[str]" = []
    for version, fichiers in releases.items():
        # Une version sans fichier n'est pas installable ; une version dont
        # tous les fichiers sont retirés ne l'est plus non plus.
        if fichiers and not all(f.get("yanked", False) for f in fichiers):
            vivantes.append(str(version))
    return sorted(vivantes)


def verifier(*, check_build: bool, offline_ok: bool) -> int:
    depot = repo_distributions()
    erreurs: "list[str]" = []
    avertissements: "list[str]" = []

    print(f"Dépôt : {len(depot)} distribution(s)")

    if check_build:
        construites = built_distributions()
        print(f"Construites : {len(construites)}")
        manquantes = [n for n in depot if n not in construites]
        for nom in manquantes:
            erreurs.append(f"{nom} : présent au dépôt, ABSENT de la construction")
        orphelines_build = sorted(construites - set(depot))
        for nom in orphelines_build:
            avertissements.append(
                f"{nom} : artefact construit sans source au dépôt (dist/ à nettoyer)"
            )

    muets = 0
    for nom in depot:
        versions = pypi_versions(nom)
        if versions is None:
            muets += 1
            continue
        if not versions:
            erreurs.append(
                f"{nom} : présent au dépôt, JAMAIS PUBLIÉ sur PyPI. Publier une "
                "release sans lui la rendrait régressive pour qui l'utilise."
            )

    for nom, raison in sorted(ABSORBED.items()):
        if nom in depot:
            erreurs.append(
                f"{nom} : déclaré absorbé mais toujours présent au dépôt "
                f"({raison}) — la liste ABSORBED est fausse"
            )
            continue
        versions = pypi_versions(nom)
        if versions is None:
            muets += 1
            continue
        if versions:
            avertissements.append(
                f"{nom} : ORPHELIN sur PyPI ({versions[-1]}), {raison}. "
                "Toujours installable, plus maintenu : à retirer (yank) ou à "
                "remplacer par un shim, décision de release."
            )

    if muets:
        message = f"PyPI injoignable pour {muets} nom(s) : vérification incomplète"
        if offline_ok:
            avertissements.append(message)
        else:
            erreurs.append(message + " (utiliser --offline-ok pour tolérer)")

    for ligne in avertissements:
        print(f"  [WARN] {ligne}")
    for ligne in erreurs:
        print(f"  [FAIL] {ligne}")

    if erreurs:
        print(f"ÉCHEC : {len(erreurs)} problème(s) de complétude")
        return 1
    print(f"OK : complétude vérifiée ({len(avertissements)} avertissement(s))")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-build", action="store_true",
                        help="croise aussi avec les artefacts de dist/")
    parser.add_argument("--offline-ok", action="store_true",
                        help="tolère un PyPI injoignable (avertissement au lieu d'échec)")
    args = parser.parse_args(argv)
    return verifier(check_build=args.check_build, offline_ok=args.offline_ok)


if __name__ == "__main__":
    sys.exit(main())
