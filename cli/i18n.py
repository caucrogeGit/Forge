from __future__ import annotations

import json
import sys
from pathlib import Path

from cli.output import created, error, info, ok, preserved

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
        for k, v in data.items():
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
            if not isinstance(v, str):
                file_errors.append(f'la clé "{k}" a une valeur non-chaîne')
            elif not v.strip():
                file_errors.append(f'la clé "{k}" a une valeur vide')

        if file_errors:
            for msg in file_errors:
                print(error(f"{rel} : {msg}"))
            all_ok = False
        else:
            print(ok(f"Catalogue {catalog_path.name} valide — {key_count} clés vérifiées"))

    return 0 if all_ok else 1


def main(args: list[str]) -> None:
    command = args[0] if args else ""
    if command == "i18n:init":
        cmd_i18n_init(args)
    elif command == "i18n:check":
        result = cmd_i18n_check(args)
        if result != 0:
            sys.exit(result)
    else:
        print(f"Commande inconnue : {command}")
