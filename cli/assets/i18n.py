# pyright: strict
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

from cli._support.output import created, error, info, ok, preserved


def _formes_de_pluriel() -> "tuple[str, ...]":
    """Formes attendues, demandées à l'opt-in quand il est installé.

    Le cœur ne dépend pas de `forge-mvc-i18n` (ADR-027), et cette commande doit
    marcher sans lui. Elle vérifie donc ce qu'elle peut : une valeur composite
    dont toutes les formes sont des textes. Quand l'opt-in est là, elle exige
    en plus les formes qu'il sait choisir, plutôt que de dupliquer ici un
    vocabulaire dont il est la source.
    """
    try:
        from forge_mvc_i18n import PLURAL_FORMS  # noqa: PLC0415
    except ImportError:
        return ()
    return tuple(PLURAL_FORMS)


def _erreurs_de_pluriel(cle: str, formes: "dict[Any, Any]") -> "list[str]":
    """Reproches à faire à une entrée pluralisée, du plus grave au plus léger.

    Une forme absente ne se voit sinon qu'à la requête qui porte le nombre
    correspondant : la page marche pour un élève et casse pour deux.
    """
    erreurs: "list[str]" = []
    if not formes:
        return [f'la clé "{cle}" a un objet de formes vide']
    for nom, texte in formes.items():
        if not isinstance(nom, str):
            erreurs.append(f'la clé "{cle}" a un nom de forme non-chaîne : {nom!r}')
        elif not isinstance(texte, str) or not texte.strip():
            erreurs.append(f'la forme "{nom}" de la clé "{cle}" est vide ou non-chaîne')
    manquantes = [f for f in _formes_de_pluriel() if f not in formes]
    if manquantes:
        erreurs.append(
            f'la clé "{cle}" ne porte pas la forme {", ".join(manquantes)}'
        )
    return erreurs

_FR_CATALOG: dict[str, str] = {
    "common.save": "Enregistrer",
    "common.cancel": "Annuler",
    "common.delete": "Supprimer",
    "common.edit": "Modifier",
    "common.create": "Créer",
    "common.back": "Retour",
    "common.search": "Rechercher",
    "common.yes": "Oui",
    "common.no": "Non",
    "crud.list": "Liste",
    "crud.create": "Créer",
    "crud.edit": "Modifier",
    "crud.delete": "Supprimer",
    "crud.show": "Voir",
    "crud.empty": "Aucun élément à afficher.",
    "crud.confirm_delete": "Confirmer la suppression ?",
    "crud.actions": "Actions",
    "validation.required": "Ce champ est obligatoire.",
    "validation.invalid": "La valeur saisie est invalide.",
}

_FORBIDDEN_KEY_TERMS = (
    "commune",
    "sejour",
    "séjour",
    "hebergement",
    "hébergement",
    "reservation",
    "réservation",
)


def cmd_i18n_init(args: list[str], root: Path | None = None) -> None:
    root = root or Path.cwd()
    translations_dir = root / "translations"

    if translations_dir.exists():
        print(info(f"{translations_dir.relative_to(root)}  (dossier déjà présent)"))
    else:
        translations_dir.mkdir(parents=True)
        print(created(str(translations_dir.relative_to(root))))

    catalog_path = translations_dir / "fr.json"
    if catalog_path.exists():
        print(preserved(str(catalog_path.relative_to(root)), "catalogue non écrasé"))
    else:
        catalog_path.write_text(
            json.dumps(_FR_CATALOG, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(created(str(catalog_path.relative_to(root))))


def cmd_i18n_check(args: list[str], root: Path | None = None) -> int:
    root = root or Path.cwd()
    translations_dir = root / "translations"

    if not translations_dir.is_dir():
        print(error("Dossier translations/ absent"))
        return 1
    print(ok("Dossier translations présent"))

    if not (translations_dir / "fr.json").is_file():
        print(error("translations/fr.json absent"))
        return 1

    catalog_files = sorted(translations_dir.glob("*.json"))
    all_ok = True

    for catalog_path in catalog_files:
        rel = catalog_path.relative_to(root)
        file_errors: list[str] = []

        try:
            data = json.loads(catalog_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(error(f"{rel} : JSON invalide — {exc}"))
            all_ok = False
            continue

        if not isinstance(data, dict):
            print(error(f"{rel} : doit être un objet JSON"))
            all_ok = False
            continue

        key_count = 0
        for k, v in cast("dict[Any, Any]", data).items():
            key_count += 1

            if not isinstance(k, str):
                file_errors.append(f"clé non-chaîne détectée : {k!r}")
                continue
            if not k.strip():
                file_errors.append("clé vide détectée")
                continue
            if "." not in k:
                file_errors.append(f'la clé "{k}" n\'utilise pas la notation pointée')
            k_lower = k.lower()
            for term in _FORBIDDEN_KEY_TERMS:
                if term in k_lower:
                    file_errors.append(
                        f'la clé "{k}" contient un terme métier interdit : {term}'
                    )
                    break
            if isinstance(v, dict):
                file_errors.extend(_erreurs_de_pluriel(k, cast("dict[Any, Any]", v)))
            elif not isinstance(v, str):
                file_errors.append(
                    f'la clé "{k}" a une valeur qui n\'est ni une chaîne ni un '
                    "objet de formes de pluriel"
                )
            elif not v.strip():
                file_errors.append(f'la clé "{k}" a une valeur vide')

        if file_errors:
            for msg in file_errors:
                print(error(f"{rel} : {msg}"))
            all_ok = False
        else:
            print(ok(f"Catalogue {catalog_path.name} valide — {key_count} clés vérifiées"))

    return 0 if all_ok else 1


def cmd_i18n_extract(args: list[str], root: Path | None = None) -> int:
    """`forge i18n:extract` — clés employées dans les gabarits (I18N-EXTRACT-CLI-001).

    `i18n:check` compare deux catalogues entre eux : il dit quelle clé du
    français manque à l'anglais. Il ne peut rien dire d'une clé employée dans
    un gabarit et absente **des deux**, puisqu'il ne lit que les catalogues.

    C'est pourtant le cas le plus fréquent : on ajoute `trans("panier_vide")`
    dans une page, on oublie de l'ajouter au catalogue, et la page affiche
    « panier_vide » à l'utilisateur.

    La logique d'extraction vit dans l'opt-in, qui seul connaît la forme des
    appels à `trans()`. Elle est importée paresseusement, comme
    `cli.assets.uploads` le fait pour `forge-mvc-files` : le cœur ne dépend pas
    d'un opt-in (ADR-004).
    """
    try:
        from forge_mvc_i18n.extract import extract_from_directory
    except ImportError:
        print(
            "[ERREUR] i18n:extract requiert l'opt-in forge-mvc-i18n "
            "(pip install forge-mvc-i18n)."
        )
        return 2

    base = root or Path.cwd()
    dossier = base / "mvc" / "views"
    locale = _extract_locale(args)

    resultat = extract_from_directory(dossier)
    print(
        f"[INFO] {resultat.files_scanned} fichier(s) balayé(s) dans "
        f"{dossier}, {len(resultat.keys)} clé(s) trouvée(s)."
    )
    if not resultat.is_complete:
        print(
            f"[ATTENTION] {resultat.dynamic_calls} appel(s) à clé calculée, "
            "que le balayage ne peut pas nommer. La liste ci-dessous est donc "
            "un minorant."
        )

    catalogue = _load_catalog_keys(base, locale)
    if catalogue is None:
        print(f"[INFO] Aucun catalogue pour la locale « {locale} ».")
        for cle in resultat.keys:
            print(f"    {cle}")
        return 0

    manquantes = [cle for cle in resultat.keys if cle not in catalogue]
    inutilisees = sorted(catalogue - set(resultat.keys))

    if manquantes:
        print(f"[ERREUR] {len(manquantes)} clé(s) employée(s) et absente(s) du catalogue :")
        for cle in manquantes:
            print(f"    {cle}")
    else:
        print(f"[OK] Toutes les clés employées sont dans le catalogue « {locale} ».")

    if inutilisees:
        # Signalé sans être une erreur : une clé peut servir à un appel calculé,
        # ou à un gabarit qui n'est pas sous mvc/views.
        print(f"[INFO] {len(inutilisees)} clé(s) du catalogue non trouvée(s) dans les gabarits :")
        for cle in inutilisees[:20]:
            print(f"    {cle}")
        if len(inutilisees) > 20:
            print(f"    et {len(inutilisees) - 20} autres")

    return 1 if manquantes else 0


def _extract_locale(args: list[str]) -> str:
    """Locale demandée par `--locale`, défaut `fr`."""
    for index, argument in enumerate(args):
        if argument.startswith("--locale="):
            return argument.partition("=")[2].strip() or "fr"
        if argument == "--locale" and index + 1 < len(args):
            return args[index + 1].strip() or "fr"
    return "fr"


def _load_catalog_keys(root: Path, locale: str) -> "set[str] | None":
    """Clés du catalogue d'une locale, ou `None` s'il est absent ou illisible."""
    chemin = root / "translations" / f"{locale}.json"
    if not chemin.is_file():
        return None
    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(donnees, dict):
        return None
    # `json.loads` rend un objet non typé : la vue typée évite que les clés
    # remontent en `Unknown` jusqu'à `str()`.
    catalogue = cast("dict[str, Any]", donnees)
    return {str(cle) for cle in catalogue}


def main(args: list[str]) -> None:
    command = args[0] if args else ""
    if command == "i18n:init":
        cmd_i18n_init(args)
    elif command == "i18n:check":
        result = cmd_i18n_check(args)
        if result != 0:
            sys.exit(result)
    elif command == "i18n:extract":
        result = cmd_i18n_extract(args)
        if result != 0:
            sys.exit(result)
    else:
        print(f"Commande inconnue : {command}")
